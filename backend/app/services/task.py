from sqlalchemy.orm import Session, sessionmaker, joinedload
from sqlalchemy import desc, func, text
from sqlalchemy.orm.exc import DetachedInstanceError
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
import os
from datetime import datetime
import uuid
import shutil
import asyncio
import logging

from app.models.task import Task, TaskStatusEnum
from app.services.file import FileService
from app.services.qr_recognition import QRRecognitionService
from app.services.express_tracking import ExpressTrackingService
from app.services.tracking_screenshot import TrackingScreenshotService
from app.services.qr_generation import QRGenerationService
from app.services.delivery_receipt_generator import DeliveryReceiptGeneratorService
from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskService:
    """任务服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_service = FileService(db)
        self.qr_service = QRRecognitionService(db)
        self.tracking_service = ExpressTrackingService(db)
        self.screenshot_service = TrackingScreenshotService(db)
        self.qr_generation_service = QRGenerationService(db)
        self.receipt_generator_service = DeliveryReceiptGeneratorService(db)
    
    async def _send_websocket_update(self, task: Task, message_type: str = "task_update", extra_data: Dict[str, Any] = None):
        """发送WebSocket任务状态更新"""
        try:
            from app.api.api_v1.websocket import manager
            
            # 构建推送消息
            message = {
                "type": message_type,
                "task_id": task.task_id,
                "status": task.status.value,
                "message": self._get_status_message(task.status),
                "progress": self._calculate_progress(task.status),
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "task_name": task.task_name,
                    "description": task.description,
                    "qr_code": task.qr_code,
                    "tracking_number": task.tracking_number,
                    "courier_company": task.courier_company,
                    "delivery_status": task.delivery_status,
                    "error_message": task.error_message,
                    "document_url": task.document_url,
                    "screenshot_url": task.screenshot_url,
                    "created_at": task.created_at.isoformat() if task.created_at else None,
                    "started_at": task.started_at.isoformat() if task.started_at else None,
                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                    "delivery_time": task.delivery_time.isoformat() if task.delivery_time else None,
                    "processing_time": task.processing_time
                }
            }
            
            # 添加额外数据
            if extra_data:
                message["data"].update(extra_data)
            
            # 发送给任务所属用户
            if task.user_id:
                await manager.send_personal_message(message, task.user_id)
                logger.info(f"WebSocket推送发送成功 - 用户: {task.user_id}, 任务: {task.task_id}, 状态: {task.status.value}")
            
        except Exception as e:
            logger.error(f"WebSocket推送失败: {str(e)}")
    
    def _get_status_message(self, status: TaskStatusEnum) -> str:
        """获取状态对应的消息"""
        status_messages = {
            TaskStatusEnum.PENDING: "任务等待处理",
            TaskStatusEnum.RECOGNIZING: "正在识别二维码",
            TaskStatusEnum.TRACKING: "正在查询物流信息",
            TaskStatusEnum.DELIVERED: "快递已签收",
            TaskStatusEnum.GENERATING: "正在生成文档",
            TaskStatusEnum.COMPLETED: "任务处理完成",
            TaskStatusEnum.FAILED: "任务处理失败"
        }
        return status_messages.get(status, "未知状态")
    
    def _calculate_progress(self, status: TaskStatusEnum) -> int:
        """计算任务进度百分比"""
        progress_map = {
            TaskStatusEnum.PENDING: 10,
            TaskStatusEnum.RECOGNIZING: 25,
            TaskStatusEnum.TRACKING: 50,
            TaskStatusEnum.DELIVERED: 75,
            TaskStatusEnum.GENERATING: 90,
            TaskStatusEnum.COMPLETED: 100,
            TaskStatusEnum.FAILED: 0
        }
        return progress_map.get(status, 0)
    
    async def create_task_from_upload(self, file: UploadFile, user_id: Optional[int] = None) -> Dict[str, Any]:
        """从上传的文件创建任务"""
        try:
            print(f"开始创建任务 - 文件名: {file.filename}, 文件大小: {file.size}")
            
            # 1. 保存文件
            file_info = await self.file_service.save_file(file)
            print(f"文件保存成功: {file_info}")
            
            # 2. 创建任务
            task = Task(
                task_name=f"处理_{file.filename}",
                description=f"处理上传的图片文件: {file.filename}",
                status=TaskStatusEnum.PENDING,
                image_path=file_info.get("file_path"),
                image_url=file_info.get("file_url", ""),
                file_size=file.size,
                user_id=user_id,
                started_at=datetime.now()
            )
            
            print(f"创建Task对象: task_id={task.task_id}, status={task.status}")
            
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            
            print(f"任务保存成功到数据库: id={task.id}, task_id={task.task_id}")
            
            # 3. 启动异步二维码识别（不等待完成）
            asyncio.create_task(self._trigger_qr_recognition(task.task_id))
            
            return {
                "success": True,
                "message": "任务创建成功",
                "data": {
                    "task_id": task.task_id,
                    "image_url": task.image_url,
                    "status": task.status.value,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }
            }
            
        except Exception as e:
            print(f"创建任务失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            return {
                "success": False,
                "message": f"创建任务失败: {str(e)}"
            }
    
    def get_task_by_id(self, task_id: str) -> Optional[Task]:
        """根据任务ID获取任务 - 优化版本"""
        # 添加查询超时和eager loading
        return self.db.query(Task).options(
            joinedload(Task.user)
        ).filter(Task.task_id == task_id).execution_options(
            compiled_cache={},
            query_timeout=15
        ).first()
    
    def get_tasks_by_user(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Task]:
        """获取用户的任务列表 - 优化版本"""
        # 添加查询超时并使用eager loading避免N+1问题
        return self.db.query(Task).options(
            joinedload(Task.user)
        ).filter(
            Task.user_id == user_id
        ).order_by(desc(Task.created_at)).limit(limit).offset(offset).execution_options(
            compiled_cache={},
            query_timeout=30
        ).all()
    
    def get_all_tasks(self, limit: int = 50, offset: int = 0) -> List[Task]:
        """获取所有任务列表 - 优化版本"""
        # 添加查询超时并使用eager loading避免N+1问题
        return self.db.query(Task).options(
            joinedload(Task.user)
        ).order_by(desc(Task.created_at)).limit(limit).offset(offset).execution_options(
            compiled_cache={},
            query_timeout=30
        ).all()
    
    async def update_task_status(self, task_id: str, status: TaskStatusEnum, **kwargs) -> bool:
        """更新任务状态"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                return False
            
            old_status = task.status
            task.status = status
            
            # 更新其他字段
            for key, value in kwargs.items():
                if hasattr(task, key):
                    setattr(task, key, value)
            
            # 设置完成时间
            if status == TaskStatusEnum.COMPLETED:
                task.completed_at = datetime.now()
                if task.started_at:
                    task.processing_time = (task.completed_at - task.started_at).total_seconds()
            
            self.db.commit()
            
            # 发送WebSocket推送（仅在状态真正改变时）
            if old_status != status:
                await self._send_websocket_update(task, "status_changed", {
                    "old_status": old_status.value,
                    "new_status": status.value
                })
            
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error updating task status: {e}")
            return False
    
    async def update_task_recognition_result(self, task_id: str, qr_code: str, tracking_number: str = None) -> bool:
        """更新任务识别结果"""
        return await self.update_task_status(
            task_id, 
            TaskStatusEnum.RECOGNIZING,
            qr_code=qr_code,
            tracking_number=tracking_number
        )
    
    async def update_task_tracking_result(self, task_id: str, tracking_data: Dict, delivery_status: str = None) -> bool:
        """更新任务物流跟踪结果"""
        return await self.update_task_status(
            task_id,
            TaskStatusEnum.TRACKING,
            tracking_data=tracking_data,
            delivery_status=delivery_status
        )
    
    async def mark_task_delivered(self, task_id: str, delivery_time: datetime = None) -> bool:
        """标记任务为已签收"""
        return await self.update_task_status(
            task_id,
            TaskStatusEnum.DELIVERED,
            delivery_time=delivery_time or datetime.now()
        )
    
    async def mark_task_completed(self, task_id: str, document_url: str = None, screenshot_url: str = None) -> bool:
        """标记任务为已完成"""
        return await self.update_task_status(
            task_id,
            TaskStatusEnum.COMPLETED,
            document_url=document_url,
            screenshot_url=screenshot_url
        )
    
    async def mark_task_failed(self, task_id: str, error_message: str) -> bool:
        """标记任务为失败"""
        return await self.update_task_status(
            task_id,
            TaskStatusEnum.FAILED,
            error_message=error_message
        )
    
    async def check_and_update_task_progress(self, task_id: str) -> bool:
        """检查并更新任务进度 - 用于处理可能卡住的任务"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                return False
            
            # 如果任务处于TRACKING状态且有物流数据，重新检查是否已签收
            if task.status == TaskStatusEnum.TRACKING and task.tracking_data:
                if task.tracking_data.get("is_signed"):
                    # 如果已签收但状态还是TRACKING，更新为DELIVERED并触发文档生成
                    task.status = TaskStatusEnum.DELIVERED
                    if not task.delivery_time:
                        task.delivery_time = datetime.now()
                    self.db.commit()
                    
                    print(f"更新任务状态为已签收 - 任务: {task.task_id}")
                    asyncio.create_task(self._trigger_document_generation(task.task_id))
                    return True
            
            # 如果任务处于DELIVERED状态但没有文档，触发文档生成
            elif task.status == TaskStatusEnum.DELIVERED and not task.document_url:
                print(f"重新触发文档生成 - 任务: {task.task_id}")
                asyncio.create_task(self._trigger_document_generation(task.task_id))
                return True
            
            return False
            
        except Exception as e:
            print(f"检查任务进度失败: {str(e)}")
            return False
    
    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        task = self.get_task_by_id(task_id)
        if not task or task.status != TaskStatusEnum.FAILED:
            return False
        
        # 重置任务状态但保留已完成的数据
        old_status = task.status
        task.status = TaskStatusEnum.PENDING
        task.retry_count += 1
        task.error_message = None
        task.started_at = datetime.now()
        
        print(f"重试任务 - 任务: {task.task_id}, 重试次数: {task.retry_count}, 原状态: {old_status}")
        
        self.db.commit()
        
        # 根据任务进度决定从哪一步开始重试
        try:
            if task.qr_code and task.tracking_number and not task.tracking_data:
                # 有二维码和快递单号但没有物流数据，从物流查询开始
                print(f"从物流查询步骤开始重试 - 任务: {task.task_id}")
                asyncio.create_task(self._trigger_tracking(task.task_id))
            elif task.tracking_data and task.tracking_data.get("is_signed") and not task.document_url:
                # 有物流数据且已签收但没有文档，从文档生成开始
                print(f"从文档生成步骤开始重试 - 任务: {task.task_id}")
                asyncio.create_task(self._trigger_document_generation(task.task_id))
            else:
                # 从二维码识别开始重试
                print(f"从二维码识别步骤开始重试 - 任务: {task.task_id}")
                asyncio.create_task(self._trigger_qr_recognition(task.task_id))
        except Exception as e:
            print(f"重试任务时启动后续流程失败: {str(e)}")
            # 如果启动后续流程失败，任务状态已经设为PENDING，用户可以手动重试
        
        return True
    
    def delete_task(self, task_id: str, admin_user_id: Optional[int] = None) -> bool:
        """删除任务（管理员操作）"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                return False
            
            # 记录删除操作日志
            if admin_user_id:
                self._log_task_deletion(task, admin_user_id)
            
            # 删除相关文件
            self._cleanup_task_files(task)
            
            # 删除相关的送达回证记录
            self._cleanup_delivery_receipt(task)
            
            # 删除数据库记录
            self.db.delete(task)
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting task: {e}")
            return False
    
    def _cleanup_task_files(self, task: Task):
        """清理任务相关文件"""
        files_to_remove = []
        
        # 基本文件路径
        if task.image_path:
            files_to_remove.append(task.image_path)
        if task.document_path:
            files_to_remove.append(task.document_path)
        if task.screenshot_path:
            files_to_remove.append(task.screenshot_path)
        
        # QR标签文件（从extra_metadata中获取）
        if task.extra_metadata and task.extra_metadata.get("qr_label_path"):
            files_to_remove.append(task.extra_metadata["qr_label_path"])
        
        # 基于tracking_number的相关文件
        if task.tracking_number:
            tracking_number = task.tracking_number
            
            # 快递缓存文件
            express_cache_patterns = [
                f"uploads/express_cache/ems_{tracking_number}.json",
                f"uploads/express_cache/sf_{tracking_number}.json",
                f"uploads/express_cache/sto_{tracking_number}.json"
            ]
            
            # 送达回证文档
            delivery_receipt_pattern = f"uploads/delivery_receipts/delivery_receipt_{tracking_number}_*.docx"
            
            # 物流截图
            tracking_screenshot_pattern = f"uploads/tracking_screenshots/tracking_{tracking_number}_*.png"
            
            # QR标签
            qr_label_pattern = f"uploads/label_{tracking_number}_*_final.png"
            
            # 物流HTML文件
            tracking_html_pattern = f"uploads/tracking_html/tracking_{tracking_number}_*.html"
            
            # 添加模式匹配的文件
            import glob
            for pattern in [delivery_receipt_pattern, tracking_screenshot_pattern, 
                          qr_label_pattern, tracking_html_pattern]:
                files_to_remove.extend(glob.glob(pattern))
            
            # 添加确定路径的文件
            files_to_remove.extend(express_cache_patterns)
        
        # 删除文件
        for file_path in files_to_remove:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    print(f"删除文件: {file_path}")
                except Exception as e:
                    print(f"删除文件失败 {file_path}: {e}")
    
    def _cleanup_delivery_receipt(self, task: Task):
        """删除相关的送达回证记录"""
        if task.tracking_number:
            try:
                from app.models.delivery_receipt import DeliveryReceipt
                receipt = self.db.query(DeliveryReceipt).filter(
                    DeliveryReceipt.tracking_number == task.tracking_number
                ).first()
                
                if receipt:
                    self.db.delete(receipt)
                    print(f"删除送达回证记录: {task.tracking_number}")
            except Exception as e:
                print(f"删除送达回证记录失败: {e}")
    
    def _log_task_deletion(self, task: Task, admin_user_id: int):
        """记录任务删除日志"""
        try:
            from app.services.activity_log import ActivityLogService
            activity_service = ActivityLogService(self.db)
            
            activity_service.log_activity(
                action_type="task_deleted",
                description=f"管理员删除任务 #{task.task_id}，快递单号: {task.tracking_number or '未知'}",
                entity_type="task",
                entity_id=task.task_id,
                status="warning",
                user_id=admin_user_id
            )
        except Exception as e:
            print(f"记录删除日志失败: {e}")
    
    def get_task_statistics(self, user_id: Optional[int] = None) -> Dict[str, int]:
        """获取任务统计信息 - 优化版本，避免N+1查询"""
        # 使用聚合查询避免加载所有任务数据
        base_query = self.db.query(
            Task.status,
            func.count(Task.id).label('count')
        ).execution_options(
            compiled_cache={},
            query_timeout=20
        )
        
        if user_id:
            base_query = base_query.filter(Task.user_id == user_id)
        
        # 按状态分组统计
        status_counts = base_query.group_by(Task.status).all()
        
        # 初始化统计结果
        stats = {
            "total": 0,
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0
        }
        
        # 处理统计结果
        for status, count in status_counts:
            stats["total"] += count
            
            if status == TaskStatusEnum.COMPLETED:
                stats["completed"] = count
            elif status == TaskStatusEnum.FAILED:
                stats["failed"] = count
            elif status in [TaskStatusEnum.PENDING, TaskStatusEnum.RECOGNIZING, 
                           TaskStatusEnum.TRACKING, TaskStatusEnum.GENERATING]:
                stats["processing"] += count
            else:
                stats["pending"] += count
        
        return stats
    
    async def _trigger_qr_recognition(self, task_id: str):
        """触发二维码识别处理"""
        try:
            # 获取task对象确保数据库会话有效
            task = self.get_task_by_id(task_id)
            if not task:
                print(f"任务不存在 - {task_id}")
                return
            
            # 刷新对象确保与数据库同步
            self.db.refresh(task)
                
            print(f"开始进行二维码识别 - 任务: {task.task_id}")
            
            # 更新任务状态为识别中
            task.status = TaskStatusEnum.RECOGNIZING
            self.db.commit()
            
            # 发送WebSocket推送
            await self._send_websocket_update(task, "recognition_started")
            
            # 进行二维码识别
            recognition_result = self.qr_service.recognize_single_image(task.image_path)
            print(f"二维码识别结果: {recognition_result}")
            
            if recognition_result["is_success"] == "true":
                # 更新二维码内容
                task.qr_code = recognition_result["qr_contents"][0] if recognition_result["qr_contents"] else recognition_result["raw_results"][0] if recognition_result["raw_results"] else ""
                
                if recognition_result["tracking_numbers"]:
                    # 识别成功并提取到快递单号
                    first_tracking = recognition_result["tracking_numbers"][0]
                    tracking_number = first_tracking["number"]
                    courier_company = first_tracking["courier_name"]
                    
                    task.tracking_number = tracking_number
                    task.courier_company = courier_company
                    # 不要在这里更新为TRACKING状态，让_trigger_tracking自己更新
                    
                    print(f"识别成功 - 快递单号: {tracking_number}, 快递公司: {courier_company}")
                    
                    # 先提交识别结果
                    self.db.commit()
                    
                    # 发送WebSocket推送
                    await self._send_websocket_update(task, "recognition_completed", {
                        "qr_code": task.qr_code,
                        "tracking_number": task.tracking_number,
                        "courier_company": task.courier_company
                    })
                    
                    # 触发物流跟踪 - 异步执行
                    asyncio.create_task(self._trigger_tracking(task.task_id))
                else:
                    # 识别到二维码但未提取到快递单号
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = "二维码识别成功，但未能从中提取到快递单号"
                    print(f"部分失败: 识别到二维码但未提取到快递单号")
                
            else:
                # 识别失败
                task.status = TaskStatusEnum.FAILED
                task.error_message = recognition_result.get("error_message", "未能识别到二维码")
                print(f"识别失败: {task.error_message}")
                
                # 发送WebSocket推送
                await self._send_websocket_update(task, "recognition_failed", {
                    "error_message": task.error_message
                })
            
            self.db.commit()
            
        except DetachedInstanceError as e:
            print(f"数据库会话错误 - 二维码识别: {str(e)}")
            # 重新获取任务并更新状态
            try:
                task = self.get_task_by_id(task_id)
                if task:
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = f"数据库会话错误: {str(e)}"
                    self.db.commit()
            except Exception as commit_error:
                print(f"更新任务状态失败: {str(commit_error)}")
        except Exception as e:
            print(f"二维码识别处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                task = self.get_task_by_id(task_id)
                if task:
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = f"二维码识别失败: {str(e)}"
                    self.db.commit()
            except Exception as commit_error:
                print(f"更新任务状态失败: {str(commit_error)}")
    
    async def _trigger_tracking(self, task_id: str):
        """触发物流跟踪处理"""
        try:
            # 获取task对象确保数据库会话有效
            task = self.get_task_by_id(task_id)
            if not task:
                print(f"任务不存在 - {task_id}")
                return
            
            # 刷新对象确保与数据库同步
            self.db.refresh(task)
                
            print(f"开始物流查询 - 任务: {task.task_id}, 快递单号: {task.tracking_number}")
            
            # 更新任务状态为物流跟踪中
            task.status = TaskStatusEnum.TRACKING
            self.db.commit()
            
            # 发送WebSocket推送
            await self._send_websocket_update(task, "tracking_started")
            
            # 查询物流信息
            company_code = "ems"  # 根据实际情况确定快递公司代码
            tracking_result = self.tracking_service.query_express(task.tracking_number, company_code)
            print(f"物流查询结果: {tracking_result}")
            
            if tracking_result.get("success"):
                # 更新物流数据 - 保存完整的tracking_result作为tracking_data
                task.tracking_data = tracking_result
                task.delivery_status = tracking_result.get("current_status", "")
                
                # 检查是否已签收 - 从顶层获取is_signed字段
                if tracking_result.get("is_signed"):
                    task.status = TaskStatusEnum.DELIVERED
                    # 解析签收时间
                    sign_time_str = tracking_result.get("sign_time", "")
                    if sign_time_str:
                        try:
                            # 处理不同的时间格式
                            if "T" in sign_time_str:
                                task.delivery_time = datetime.fromisoformat(sign_time_str)
                            else:
                                task.delivery_time = datetime.strptime(sign_time_str, "%Y-%m-%d %H:%M:%S")
                        except Exception as e:
                            print(f"解析签收时间失败: {e}")
                            task.delivery_time = datetime.now()
                    else:
                        task.delivery_time = datetime.now()
                    
                    print(f"快递已签收 - 任务: {task.task_id}, 签收时间: {task.delivery_time}")
                    
                    # 立即提交状态更新
                    self.db.commit()
                    
                    # 发送WebSocket推送
                    await self._send_websocket_update(task, "package_delivered", {
                        "delivery_time": task.delivery_time.isoformat() if task.delivery_time else None,
                        "tracking_data": task.tracking_data
                    })
                    
                    # 触发后续处理（生成截图、回证等）- 异步执行
                    asyncio.create_task(self._trigger_document_generation(task.task_id))
                else:
                    # 保持TRACKING状态，等待后续检查
                    print(f"快递尚未签收 - 任务: {task.task_id}, 当前状态: {task.delivery_status}")
                    # 确保状态保持在TRACKING
                    task.status = TaskStatusEnum.TRACKING
                
            else:
                # 查询失败，但不标记任务失败，保持TRACKING状态等待重试
                task.error_message = f"物流查询暂时失败: {tracking_result.get('message', '未知错误')}"
                print(f"物流查询失败: {task.error_message}")
                # 保持TRACKING状态，不设为FAILED
            
            self.db.commit()
            
        except DetachedInstanceError as e:
            print(f"数据库会话错误 - 物流查询: {str(e)}")
            # 重新获取任务并更新状态
            try:
                task = self.get_task_by_id(task_id)
                if task:
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = f"数据库会话错误: {str(e)}"
                    self.db.commit()
            except Exception as commit_error:
                print(f"更新任务状态失败: {str(commit_error)}")
        except Exception as e:
            print(f"物流查询处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # 严重错误才标记为失败
            try:
                task = self.get_task_by_id(task_id)
                if task:
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = f"物流查询严重错误: {str(e)}"
                    self.db.commit()
            except Exception as commit_error:
                print(f"更新任务状态失败: {str(commit_error)}")
    
    async def _trigger_document_generation(self, task_id: str):
        """触发文档生成处理 - 按步骤顺序执行"""
        try:
            # 获取task对象确保数据库会话有效
            task = self.get_task_by_id(task_id)
            if not task:
                print(f"任务不存在 - {task_id}")
                return
            
            # 刷新对象确保与数据库同步
            self.db.refresh(task)
                
            print(f"开始文档生成 - 任务: {task.task_id}")
            
            # 更新任务状态为生成中
            task.status = TaskStatusEnum.GENERATING
            self.db.commit()
            
            # 发送WebSocket推送
            await self._send_websocket_update(task, "generating_documents")
            
            # 第一步：生成物流轨迹截图
            screenshot_success = await self._generate_tracking_screenshot(task)
            if not screenshot_success:
                # 截图生成失败，但不阻断整个流程，继续后续步骤
                print(f"物流截图生成失败，但继续后续流程 - 任务: {task.task_id}")
            
            # 第二步：生成二维码条形码标签
            qr_label_success = await self._generate_qr_barcode_label(task)
            if not qr_label_success:
                # 二维码标签生成失败，但不阻断整个流程
                print(f"二维码标签生成失败，但继续后续流程 - 任务: {task.task_id}")
            
            # 第三步：只有在至少有一个文件生成成功的情况下才生成最终文档
            if screenshot_success or qr_label_success:
                receipt_success = await self._generate_delivery_receipt(task)
                if receipt_success:
                    # 全部完成，标记任务为成功
                    task.status = TaskStatusEnum.COMPLETED
                    task.completed_at = datetime.now()
                    if task.started_at:
                        task.processing_time = (task.completed_at - task.started_at).total_seconds()
                    
                    # 立即提交状态更新
                    self.db.commit()
                    
                    # 发送WebSocket推送
                    await self._send_websocket_update(task, "task_completed", {
                        "document_url": task.document_url,
                        "screenshot_url": task.screenshot_url,
                        "processing_time": task.processing_time
                    })
                    
                    print(f"✓ 任务完成并提交到数据库 - 任务: {task.task_id}, 状态: {task.status.value}")
                else:
                    # 最终文档生成失败，但保留已生成的文件信息
                    task.status = TaskStatusEnum.FAILED
                    # 构建详细的错误信息
                    success_parts = []
                    if screenshot_success:
                        success_parts.append("物流截图")
                    if qr_label_success:
                        success_parts.append("二维码标签")
                    
                    if success_parts:
                        task.error_message = f"送达回证生成失败，但{'/'.join(success_parts)}已成功生成"
                    else:
                        task.error_message = "送达回证生成失败"
                    print(f"送达回证生成失败 - 任务: {task.task_id}, 已生成: {success_parts}")
            else:
                # 所有前置步骤都失败
                task.status = TaskStatusEnum.FAILED
                task.error_message = "物流截图和二维码标签生成均失败"
                print(f"所有文件生成步骤都失败 - 任务: {task.task_id}")
            
            # 如果状态不是成功，则提交失败状态
            self.db.commit()
            print(f"✓ 文档生成流程结束 - 任务: {task.task_id}, 最终状态: {task.status.value}")
            
        except DetachedInstanceError as e:
            print(f"数据库会话错误 - 文档生成: {str(e)}")
            # 重新获取任务并更新状态
            try:
                task = self.get_task_by_id(task_id)
                if task:
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = f"数据库会话错误: {str(e)}"
                    self.db.commit()
            except Exception as commit_error:
                print(f"更新任务状态失败: {str(commit_error)}")
        except Exception as e:
            print(f"文档生成处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            try:
                task = self.get_task_by_id(task_id)
                if task:
                    task.status = TaskStatusEnum.FAILED
                    task.error_message = f"文档生成失败: {str(e)}"
                    self.db.commit()
            except Exception as commit_error:
                print(f"更新任务状态失败: {str(commit_error)}")
    
    async def _generate_tracking_screenshot(self, task: Task) -> bool:
        """生成物流轨迹截图"""
        try:
            print(f"生成物流轨迹截图 - 任务: {task.task_id}")
            screenshot_result = self.screenshot_service.generate_screenshot_from_tracking_data(
                task.tracking_data
            )
            
            if screenshot_result.get("success"):
                # 从返回结果中获取正确的字段名
                screenshot_path = screenshot_result.get("screenshot_path")
                if screenshot_path:
                    task.screenshot_path = screenshot_path
                    # 生成URL（相对于静态文件目录）
                    import os
                    filename = os.path.basename(screenshot_path)
                    task.screenshot_url = f"/static/tracking_screenshots/{filename}"
                    
                    # 保存到数据库但不提交事务
                    self.db.flush()
                    print(f"物流截图生成成功: {task.screenshot_url}")
                    return True
                elif screenshot_result.get("html_fallback_path"):
                    # 如果生成了HTML备用文件也算成功
                    task.screenshot_path = screenshot_result.get("html_fallback_path")
                    filename = os.path.basename(task.screenshot_path)
                    task.screenshot_url = f"/static/tracking_html/{filename}"
                    
                    # 保存到数据库但不提交事务
                    self.db.flush()
                    print(f"物流HTML文件生成成功: {task.screenshot_url}")
                    return True
            else:
                print(f"物流截图生成失败: {screenshot_result.get('message', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"物流截图生成异常: {str(e)}")
            return False
    
    async def _generate_qr_barcode_label(self, task: Task) -> bool:
        """生成二维码条形码标签"""
        try:
            print(f"生成二维码条形码 - 任务: {task.task_id}")
            if not task.qr_code:
                print(f"任务没有二维码内容，跳过标签生成 - 任务: {task.task_id}")
                return False
                
            qr_result = self.qr_generation_service.generate_qr_barcode_label(task.qr_code)
            
            if qr_result.get("success"):
                # 将二维码文件信息保存到任务的额外数据中
                if not task.extra_metadata:
                    task.extra_metadata = {}
                
                data = qr_result.get("data", {})
                final_label_path = data.get("final_label_path", "")
                
                if final_label_path:
                    task.extra_metadata["qr_label_path"] = final_label_path
                    # 生成URL
                    import os
                    filename = os.path.basename(final_label_path)
                    task.extra_metadata["qr_label_url"] = f"/static/uploads/{filename}"
                    
                    # 保存到数据库但不提交事务
                    self.db.flush()
                    print(f"二维码标签生成成功: {task.extra_metadata['qr_label_url']}")
                    return True
            else:
                print(f"二维码标签生成失败: {qr_result.get('error', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"二维码标签生成异常: {str(e)}")
            return False
    
    async def _generate_delivery_receipt(self, task: Task) -> bool:
        """生成送达回证文档"""
        try:
            print(f"生成送达回证文档 - 任务: {task.task_id}")
            
            # 1. 确保DeliveryReceipt记录存在并同步文件路径
            await self._sync_file_paths_to_delivery_receipt(task)
            
            # 2. 获取已保存的回证信息
            from app.models.delivery_receipt import DeliveryReceipt
            receipt = self.db.query(DeliveryReceipt).filter(
                DeliveryReceipt.tracking_number == task.tracking_number
            ).first()
            
            # 3. 准备生成参数，优先使用保存的信息
            doc_title = receipt.doc_title if receipt and receipt.doc_title else "送达回证"
            sender = receipt.sender if receipt and receipt.sender else ""
            send_location = receipt.send_location if receipt and receipt.send_location else ""
            receiver = receipt.receiver if receipt and receipt.receiver else ""
            
            # 时间优先使用保存的时间，其次使用签收时间
            send_time_str = None
            if receipt and receipt.send_time:
                send_time_str = receipt.send_time
            elif task.delivery_time:
                send_time_str = task.delivery_time.strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"使用回证信息 - 文档标题: {doc_title}, 送达人: {sender}, 送达地点: {send_location}, 受送达人: {receiver}, 送达时间: {send_time_str}")
            
            # 4. 调用生成服务
            receipt_result = self.receipt_generator_service.generate_delivery_receipt(
                tracking_number=task.tracking_number,
                doc_title=doc_title,
                sender=sender,
                send_location=send_location,
                receiver=receiver,
                send_time=send_time_str
            )
            
            if receipt_result.get("success"):
                task.document_path = receipt_result.get("doc_path", "")
                if task.document_path:
                    # 生成URL
                    import os
                    filename = os.path.basename(task.document_path)
                    task.document_url = f"/static/documents/{filename}"
                    
                    # 保存到数据库但不提交事务
                    self.db.flush()
                    print(f"送达回证生成成功: {task.document_url}")
                    return True
            else:
                error_msg = receipt_result.get("error", receipt_result.get("message", "未知错误"))
                print(f"送达回证生成失败: {error_msg}")
                return False
                
        except Exception as e:
            print(f"送达回证生成异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _sync_file_paths_to_delivery_receipt(self, task: Task):
        """将Task中的文件路径同步到DeliveryReceipt和TrackingInfo表"""
        try:
            print(f"同步文件路径到数据库 - 任务: {task.task_id}")
            
            # 1. 创建或获取DeliveryReceipt记录，使用eager loading
            from app.models.delivery_receipt import DeliveryReceipt
            from app.models.tracking import TrackingInfo
            
            receipt = self.db.query(DeliveryReceipt).options(
                joinedload(DeliveryReceipt.tracking_info)
            ).filter(
                DeliveryReceipt.tracking_number == task.tracking_number
            ).execution_options(
                compiled_cache={},
                query_timeout=15
            ).first()
            
            if not receipt:
                # 创建新的DeliveryReceipt记录
                receipt = DeliveryReceipt(
                    tracking_number=task.tracking_number,
                    doc_title="送达回证"
                )
                self.db.add(receipt)
                self.db.flush()  # 获取ID但不提交
                print(f"创建DeliveryReceipt记录: {receipt.id}")
            
            # 2. 同步二维码标签文件路径
            if task.extra_metadata and "qr_label_path" in task.extra_metadata:
                receipt.receipt_file_path = task.extra_metadata["qr_label_path"]
                print(f"同步二维码标签路径: {receipt.receipt_file_path}")
            
            # 3. 创建或更新TrackingInfo记录
            tracking_info = self.db.query(TrackingInfo).filter(
                TrackingInfo.delivery_receipt_id == receipt.id
            ).first()
            
            if not tracking_info:
                tracking_info = TrackingInfo(
                    delivery_receipt_id=receipt.id,
                    tracking_data=task.tracking_data,
                    current_status=task.delivery_status,
                    is_signed="true" if task.tracking_data and task.tracking_data.get("is_signed") else "false"
                )
                self.db.add(tracking_info)
                print(f"创建TrackingInfo记录")
            
            # 4. 同步截图文件路径
            if task.screenshot_path:
                import os
                tracking_info.screenshot_path = task.screenshot_path
                tracking_info.screenshot_filename = os.path.basename(task.screenshot_path) if task.screenshot_path else None
                tracking_info.screenshot_generated_at = datetime.now()
                print(f"同步截图路径: {tracking_info.screenshot_path}")
            
            # 5. 提交更改
            self.db.commit()
            print(f"文件路径同步完成 - DeliveryReceipt: {receipt.id}, TrackingInfo: {tracking_info.id if tracking_info else 'None'}")
            
        except Exception as e:
            print(f"同步文件路径失败: {str(e)}")
            import traceback
            traceback.print_exc()
            self.db.rollback()
            # 不抛出异常，继续尝试生成文档