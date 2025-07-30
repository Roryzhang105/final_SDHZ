from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import desc
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
import os
from datetime import datetime
import uuid
import shutil

from app.models.task import Task, TaskStatusEnum
from app.services.file import FileService
from app.services.qr_recognition import QRRecognitionService
from app.services.express_tracking import ExpressTrackingService
from app.core.config import settings


class TaskService:
    """任务服务类"""
    
    def __init__(self, db: Session):
        self.db = db
        self.file_service = FileService(db)
        self.qr_service = QRRecognitionService(db)
        self.tracking_service = ExpressTrackingService(db)
    
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
            
            # 3. 自动进行二维码识别
            await self._trigger_qr_recognition(task)
            
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
        """根据任务ID获取任务"""
        return self.db.query(Task).filter(Task.task_id == task_id).first()
    
    def get_tasks_by_user(self, user_id: int, limit: int = 50, offset: int = 0) -> List[Task]:
        """获取用户的任务列表"""
        return self.db.query(Task).filter(
            Task.user_id == user_id
        ).order_by(desc(Task.created_at)).limit(limit).offset(offset).all()
    
    def get_all_tasks(self, limit: int = 50, offset: int = 0) -> List[Task]:
        """获取所有任务列表"""
        return self.db.query(Task).order_by(desc(Task.created_at)).limit(limit).offset(offset).all()
    
    def update_task_status(self, task_id: str, status: TaskStatusEnum, **kwargs) -> bool:
        """更新任务状态"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                return False
            
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
            return True
            
        except Exception as e:
            self.db.rollback()
            print(f"Error updating task status: {e}")
            return False
    
    def update_task_recognition_result(self, task_id: str, qr_code: str, tracking_number: str = None) -> bool:
        """更新任务识别结果"""
        return self.update_task_status(
            task_id, 
            TaskStatusEnum.RECOGNIZING,
            qr_code=qr_code,
            tracking_number=tracking_number
        )
    
    def update_task_tracking_result(self, task_id: str, tracking_data: Dict, delivery_status: str = None) -> bool:
        """更新任务物流跟踪结果"""
        return self.update_task_status(
            task_id,
            TaskStatusEnum.TRACKING,
            tracking_data=tracking_data,
            delivery_status=delivery_status
        )
    
    def mark_task_delivered(self, task_id: str, delivery_time: datetime = None) -> bool:
        """标记任务为已签收"""
        return self.update_task_status(
            task_id,
            TaskStatusEnum.DELIVERED,
            delivery_time=delivery_time or datetime.now()
        )
    
    def mark_task_completed(self, task_id: str, document_url: str = None, screenshot_url: str = None) -> bool:
        """标记任务为已完成"""
        return self.update_task_status(
            task_id,
            TaskStatusEnum.COMPLETED,
            document_url=document_url,
            screenshot_url=screenshot_url
        )
    
    def mark_task_failed(self, task_id: str, error_message: str) -> bool:
        """标记任务为失败"""
        return self.update_task_status(
            task_id,
            TaskStatusEnum.FAILED,
            error_message=error_message
        )
    
    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        task = self.get_task_by_id(task_id)
        if not task or task.status != TaskStatusEnum.FAILED:
            return False
        
        task.status = TaskStatusEnum.PENDING
        task.retry_count += 1
        task.error_message = None
        task.started_at = datetime.now()
        
        self.db.commit()
        return True
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            task = self.get_task_by_id(task_id)
            if not task:
                return False
            
            # 删除相关文件
            self._cleanup_task_files(task)
            
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
        files_to_remove = [
            task.image_path,
            task.document_path,
            task.screenshot_path
        ]
        
        for file_path in files_to_remove:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    print(f"Failed to remove file {file_path}: {e}")
    
    def get_task_statistics(self, user_id: Optional[int] = None) -> Dict[str, int]:
        """获取任务统计信息"""
        query = self.db.query(Task)
        if user_id:
            query = query.filter(Task.user_id == user_id)
        
        tasks = query.all()
        
        stats = {
            "total": len(tasks),
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0
        }
        
        for task in tasks:
            if task.status == TaskStatusEnum.COMPLETED:
                stats["completed"] += 1
            elif task.status == TaskStatusEnum.FAILED:
                stats["failed"] += 1
            elif task.is_processing:
                stats["processing"] += 1
            else:
                stats["pending"] += 1
        
        return stats
    
    async def _trigger_qr_recognition(self, task: Task):
        """触发二维码识别处理"""
        try:
            print(f"开始进行二维码识别 - 任务: {task.task_id}")
            
            # 更新任务状态为识别中
            task.status = TaskStatusEnum.RECOGNIZING
            self.db.commit()
            
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
                    task.status = TaskStatusEnum.TRACKING
                    
                    print(f"识别成功 - 快递单号: {tracking_number}, 快递公司: {courier_company}")
                    
                    # 触发物流跟踪
                    await self._trigger_tracking(task)
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
            
            self.db.commit()
            
        except Exception as e:
            print(f"二维码识别处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            task.status = TaskStatusEnum.FAILED
            task.error_message = f"二维码识别失败: {str(e)}"
            self.db.commit()
    
    async def _trigger_tracking(self, task: Task):
        """触发物流跟踪处理"""
        try:
            print(f"开始物流查询 - 任务: {task.task_id}, 快递单号: {task.tracking_number}")
            
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
                    
                    # TODO: 触发后续处理（生成截图、回证等）
                    # await self._trigger_document_generation(task)
                else:
                    # 保持追踪状态，等待后续检查
                    print(f"快递尚未签收 - 任务: {task.task_id}, 当前状态: {task.delivery_status}")
                
            else:
                # 查询失败，但不标记任务失败，可能是临时问题
                task.error_message = f"物流查询失败: {tracking_result.get('message', '未知错误')}"
                print(f"物流查询失败: {task.error_message}")
            
            self.db.commit()
            
        except Exception as e:
            print(f"物流查询处理失败: {str(e)}")
            import traceback
            traceback.print_exc()
            
            task.error_message = f"物流查询失败: {str(e)}"
            self.db.commit()