import os
import subprocess
import tempfile
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.delivery_receipt import DeliveryReceipt
from app.models.tracking import TrackingInfo
from app.services.delivery_receipt import DeliveryReceiptService


class DeliveryReceiptGeneratorService:
    """送达回证生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.delivery_receipt_service = DeliveryReceiptService(db)
        self.legacy_dir = Path(__file__).parent.parent / "utils" / "legacy"
        self.template_path = self.legacy_dir / "template.docx"
        self.script_path = self.legacy_dir / "insert_imgs_delivery_receipt.py"
        
        # 输出目录 - 确保使用绝对路径
        project_root = Path(__file__).parent.parent.parent
        if os.path.isabs(settings.UPLOAD_DIR):
            upload_dir = Path(settings.UPLOAD_DIR)
        else:
            upload_dir = project_root / settings.UPLOAD_DIR
        
        self.output_dir = upload_dir / "delivery_receipts"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def _format_timestamp_to_chinese(self, timestamp: datetime) -> str:
        """
        将时间戳转换为中文格式: "xxxx年xx月xx日"
        
        Args:
            timestamp: 时间戳对象
            
        Returns:
            格式化的中文时间字符串
        """
        return f"{timestamp.year}年{timestamp.month:02d}月{timestamp.day:02d}日"
    
    def _extract_pickup_time(self, tracking_data) -> Optional[datetime]:
        """
        从物流轨迹数据中提取揽收时间（快递寄出时间）
        
        Args:
            tracking_data: 物流轨迹数据，可以是JSON字符串或dict对象
            
        Returns:
            揽收时间的datetime对象，如果未找到则返回None
        """
        if not tracking_data:
            return None
        
        try:
            # 如果是字符串，则解析为dict
            if isinstance(tracking_data, str):
                data = json.loads(tracking_data)
            else:
                data = tracking_data
                
            traces = data.get('traces', [])
            
            # 查找状态为"揽收"的记录
            for trace in traces:
                status = trace.get('status', '').strip()
                if status == '揽收':
                    time_str = trace.get('time', '').strip()
                    if time_str:
                        try:
                            # 解析时间字符串，格式如: "2025-07-07 18:18:37"
                            return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                        except ValueError:
                            continue
            
            # 如果没找到"揽收"状态，尝试查找最早的物流记录
            if traces:
                last_trace = traces[-1]  # 物流记录通常按时间倒序排列，最后一个是最早的
                time_str = last_trace.get('time', '').strip()
                if time_str:
                    try:
                        return datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass
                        
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"解析物流数据失败: {e}")
            return None
        
        return None
    
    def _format_case_number(self, case_number: str) -> str:
        """
        格式化案号，从数字转为完整格式
        
        Args:
            case_number: 案号数字部分，如 "1129"
            
        Returns:
            完整格式的案号，如 "沪松府复字（2025）第1129号"
        """
        # 如果已经是完整格式，直接返回
        if "沪松府复字" in case_number or "第" in case_number:
            return case_number
        
        # 提取数字部分
        import re
        numbers = re.findall(r'\d+', case_number)
        if numbers:
            number = numbers[0]
            return f"沪松府复字（2025）第{number}号"
        else:
            # 如果没有数字，直接加前缀后缀
            return f"沪松府复字（2025）第{case_number}号"
    
    def _format_delivery_time(self, delivery_time: str) -> str:
        """
        格式化送达时间，只保留日期部分
        
        Args:
            delivery_time: 原始时间字符串，如 "2025/07/09 09:00:45"
            
        Returns:
            格式化后的日期，如 "2025/07/09"
        """
        if not delivery_time:
            return delivery_time
        
        # 如果包含时间部分，提取日期部分
        if ' ' in delivery_time:
            date_part = delivery_time.split(' ')[0]
            return date_part
        
        # 如果只有日期，直接返回
        return delivery_time
    
    async def generate_delivery_receipt_smart(
        self,
        tracking_number: str,
        document_type: str,
        case_number: str,
        recipient_type: str,
        recipient_name: str,
        delivery_time: str,
        delivery_address: str,
        sender: Optional[str] = None
    ) -> Dict:
        """
        智能填充生成送达回证Word文档
        
        Args:
            tracking_number: 快递单号
            document_type: 文书类型
            case_number: 案号
            recipient_type: 受送达人类型
            recipient_name: 受送达人姓名
            delivery_time: 送达时间
            delivery_address: 送达地点
            sender: 送达人
            
        Returns:
            生成结果
        """
        try:
            # 格式化案号
            formatted_case_number = self._format_case_number(case_number)
            
            # 格式化送达时间
            formatted_delivery_time = self._format_delivery_time(delivery_time)
            
            # 构建文书名称及文号 - 两行格式
            doc_title = f"行政复议{document_type}\n{formatted_case_number}"
            
            print(f"DEBUG: 格式化结果:")
            print(f"  - 原始案号: '{case_number}'")
            print(f"  - 格式化案号: '{formatted_case_number}'")
            print(f"  - 原始时间: '{delivery_time}'")
            print(f"  - 格式化时间: '{formatted_delivery_time}'")
            print(f"  - 最终标题: '{doc_title}'")
            
            # 调用原有的生成方法，但使用智能填充的参数
            return self.generate_delivery_receipt(
                tracking_number=tracking_number,
                doc_title=doc_title,
                sender=sender,
                send_time=formatted_delivery_time,
                send_location=delivery_address,
                receiver=recipient_name
            )
            
        except Exception as e:
            return {
                "success": False,
                "error": f"智能生成送达回证过程中发生错误: {str(e)}",
                "tracking_number": tracking_number
            }
    
    def generate_delivery_receipt(
        self,
        tracking_number: str,
        doc_title: str = "送达回证",
        sender: Optional[str] = None,
        send_time: Optional[str] = None,
        send_location: Optional[str] = None,
        receiver: Optional[str] = None
    ) -> Dict:
        """
        生成送达回证Word文档
        
        Args:
            tracking_number: 快递单号
            doc_title: 送达文书名称及文号
            sender: 送达人
            send_time: 送达时间
            send_location: 送达地点
            receiver: 受送达人
            
        Returns:
            生成结果
        """
        try:
            # 1. 查找或创建送达回证记录
            receipt = self.delivery_receipt_service.get_delivery_receipt_by_tracking(tracking_number)
            if not receipt:
                # 创建基础记录
                receipt = DeliveryReceipt(
                    tracking_number=tracking_number,
                    doc_title=doc_title,
                    sender=sender,
                    send_time=send_time,
                    send_location=send_location,
                    receiver=receiver
                )
                self.db.add(receipt)
                self.db.commit()
                self.db.refresh(receipt)
            else:
                # 更新现有记录
                receipt.doc_title = doc_title
                receipt.sender = sender
                receipt.send_time = send_time
                receipt.send_location = send_location
                receipt.receiver = receiver
                self.db.commit()
            
            # 2. 自动生成send_time（如果未提供且有跟踪信息）
            if not send_time:
                tracking_info = self.db.query(TrackingInfo).join(DeliveryReceipt).filter(
                    DeliveryReceipt.tracking_number == tracking_number
                ).first()
                
                if tracking_info and tracking_info.tracking_data:
                    # 从物流数据中提取揽收时间（寄出时间）
                    pickup_time = self._extract_pickup_time(tracking_info.tracking_data)
                    if pickup_time:
                        send_time = self._format_timestamp_to_chinese(pickup_time)
                        receipt.send_time = send_time
                        self.db.commit()
            
            # 3. 获取二维码和截图文件路径
            qr_image_path, screenshot_path = self._get_required_files(tracking_number, receipt)
            
            print(f"文件路径查找结果 - 快递单号: {tracking_number}")
            print(f"  二维码文件路径: {qr_image_path}")
            print(f"  截图文件路径: {screenshot_path}")
            print(f"  DeliveryReceipt ID: {receipt.id if receipt else 'None'}")
            
            if not qr_image_path:
                error_msg = f"未找到快递单号 {tracking_number} 对应的二维码文件，请先生成二维码"
                print(f"ERROR: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "tracking_number": tracking_number
                }
            
            if not screenshot_path:
                error_msg = f"未找到快递单号 {tracking_number} 对应的物流截图，请先生成截图"
                print(f"ERROR: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "tracking_number": tracking_number
                }
            
            # 4. 清理旧文件（如果存在）
            old_doc_path = receipt.delivery_receipt_doc_path
            if old_doc_path and os.path.exists(old_doc_path):
                try:
                    os.remove(old_doc_path)
                    print(f"DEBUG: 已删除旧的Word文档: {old_doc_path}")
                except Exception as e:
                    print(f"DEBUG: 删除旧文档失败: {e}")
            
            # 5. 生成Word文档
            doc_result = self._generate_word_document(
                tracking_number=tracking_number,
                doc_title=doc_title,
                qr_image_path=qr_image_path,
                screenshot_path=screenshot_path,
                sender=sender,
                send_time=send_time,
                send_location=send_location,
                receiver=receiver
            )
            
            if not doc_result["success"]:
                return doc_result
            
            # 6. 更新数据库记录
            old_path = receipt.delivery_receipt_doc_path
            receipt.delivery_receipt_doc_path = doc_result["doc_path"]
            self.db.commit()
            
            
            return {
                "success": True,
                "message": "送达回证生成成功",
                "tracking_number": tracking_number,
                "receipt_id": receipt.id,
                "doc_path": doc_result["doc_path"],
                "doc_filename": doc_result["doc_filename"],
                "file_size": doc_result["file_size"],
                "qr_image_used": qr_image_path,
                "screenshot_used": screenshot_path
            }
            
        except Exception as e:
            self.db.rollback()
            return {
                "success": False,
                "error": f"生成送达回证过程中发生错误: {str(e)}",
                "tracking_number": tracking_number
            }
    
    def _get_required_files(self, tracking_number: str, receipt: DeliveryReceipt) -> tuple:
        """
        获取生成送达回证所需的文件路径
        
        Returns:
            (qr_image_path, screenshot_path) 元组
        """
        qr_image_path = None
        screenshot_path = None
        
        print(f"DEBUG: 开始查找文件 - 快递单号: {tracking_number}")
        print(f"DEBUG: DeliveryReceipt字段:")
        if receipt:
            print(f"  - receipt_file_path: {receipt.receipt_file_path}")
            print(f"  - qr_code_path: {receipt.qr_code_path}")
            print(f"  - tracking_screenshot_path: {receipt.tracking_screenshot_path}")
        else:
            print("  - Receipt为空")
        
        # 项目根目录路径
        project_root = Path(__file__).parent.parent.parent
        
        def resolve_file_path(file_path: str) -> str:
            """将相对路径转换为绝对路径"""
            if not file_path:
                return None
            
            # 如果已经是绝对路径，直接返回
            if os.path.isabs(file_path):
                return file_path if os.path.exists(file_path) else None
            
            # 尝试相对于项目根目录解析
            abs_path = project_root / file_path
            if abs_path.exists():
                return str(abs_path)
            
            # 尝试相对于当前工作目录解析
            abs_path = Path.cwd() / file_path
            if abs_path.exists():
                return str(abs_path)
            
            return None
        
        # 1. 查找二维码文件 - 优先使用标签文件，其次使用单独的二维码文件
        if receipt.receipt_file_path:
            qr_image_path = resolve_file_path(receipt.receipt_file_path)
        
        if not qr_image_path and receipt.qr_code_path:
            qr_image_path = resolve_file_path(receipt.qr_code_path)
        
        # 2. 查找截图文件 - 优先从TrackingInfo表查找，其次使用DeliveryReceipt表
        tracking_info = self.db.query(TrackingInfo).join(DeliveryReceipt).filter(
            DeliveryReceipt.tracking_number == tracking_number
        ).first()
        
        print(f"DEBUG: TrackingInfo查询结果:")
        if tracking_info:
            print(f"  - TrackingInfo ID: {tracking_info.id}")
            print(f"  - screenshot_path: {tracking_info.screenshot_path}")
            print(f"  - screenshot_filename: {tracking_info.screenshot_filename}")
        else:
            print("  - TrackingInfo为空")
        
        if tracking_info and tracking_info.screenshot_path:
            screenshot_path = resolve_file_path(tracking_info.screenshot_path)
            print(f"DEBUG: 从TrackingInfo解析截图路径: {screenshot_path}")
        
        if not screenshot_path and receipt.tracking_screenshot_path:
            screenshot_path = resolve_file_path(receipt.tracking_screenshot_path)
            print(f"DEBUG: 从DeliveryReceipt解析截图路径: {screenshot_path}")
        
        print(f"DEBUG: 最终文件路径:")
        print(f"  - qr_image_path: {qr_image_path}")
        print(f"  - screenshot_path: {screenshot_path}")
        
        return qr_image_path, screenshot_path
    
    def _generate_word_document(
        self,
        tracking_number: str,
        doc_title: str,
        qr_image_path: str,
        screenshot_path: str,
        sender: Optional[str] = None,
        send_time: Optional[str] = None,
        send_location: Optional[str] = None,
        receiver: Optional[str] = None
    ) -> Dict:
        """
        调用insert_imgs_delivery_receipt.py生成Word文档
        """
        try:
            # 生成输出文件名 - 使用毫秒级时间戳确保唯一性
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 去掉最后3位，保留毫秒
            doc_filename = f"delivery_receipt_{tracking_number}_{timestamp}.docx"
            output_path = self.output_dir / doc_filename
            
            # 确保生成的文件名是唯一的
            counter = 1
            while output_path.exists():
                doc_filename = f"delivery_receipt_{tracking_number}_{timestamp}_{counter}.docx"
                output_path = self.output_dir / doc_filename
                counter += 1
            
            # 构建命令参数
            cmd = [
                "python3", str(self.script_path),
                "--template", str(self.template_path),
                "--output", str(output_path),
                "--doc-title", doc_title,
                "--note-img", qr_image_path,
                "--footer-img", screenshot_path
            ]
            
            # 添加可选参数
            if sender:
                cmd.extend(["--sender", sender])
            if send_time:
                cmd.extend(["--send-time", send_time])
            if send_location:
                cmd.extend(["--send-location", send_location])
            if receiver:
                cmd.extend(["--receiver", receiver])
            
            
            # 添加命令执行日志
            print(f"DEBUG: 执行Word生成命令:")
            print(f"DEBUG: 命令: {' '.join(cmd)}")
            print(f"DEBUG: 工作目录: {self.legacy_dir}")
            
            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.legacy_dir)
            )
            
            # 添加执行结果日志
            print(f"DEBUG: subprocess执行结果:")
            print(f"  - 返回码: {result.returncode}")
            print(f"  - stdout: {result.stdout}")
            print(f"  - stderr: {result.stderr}")
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"Word文档生成失败: {result.stderr}",
                    "stdout": result.stdout
                }
            
            # 检查文件是否生成成功
            if not output_path.exists():
                return {
                    "success": False,
                    "error": "Word文档生成失败，输出文件不存在"
                }
            
            file_size = output_path.stat().st_size
            
            return {
                "success": True,
                "doc_path": str(output_path),
                "doc_filename": doc_filename,
                "file_size": file_size
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Word文档生成超时"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"调用Word生成脚本失败: {str(e)}"
            }
    
    def get_receipt_info(self, tracking_number: str) -> Dict:
        """
        获取送达回证信息
        
        Args:
            tracking_number: 快递单号
            
        Returns:
            送达回证信息
        """
        try:
            receipt = self.delivery_receipt_service.get_delivery_receipt_by_tracking(tracking_number)
            
            if not receipt:
                return {
                    "success": False,
                    "message": f"未找到快递单号 {tracking_number} 的送达回证记录",
                    "tracking_number": tracking_number
                }
            
            # 检查Word文档是否存在
            doc_exists = False
            file_size = 0
            if receipt.delivery_receipt_doc_path:
                doc_exists = os.path.exists(receipt.delivery_receipt_doc_path)
                if doc_exists:
                    file_size = os.path.getsize(receipt.delivery_receipt_doc_path)
            
            return {
                "success": True,
                "message": "获取送达回证信息成功",
                "tracking_number": tracking_number,
                "receipt_info": {
                    "id": receipt.id,
                    "doc_title": receipt.doc_title,
                    "sender": receipt.sender,
                    "send_time": receipt.send_time,
                    "send_location": receipt.send_location,
                    "receiver": receipt.receiver,
                    "status": receipt.status.value if receipt.status else None,
                    "created_at": receipt.created_at.isoformat() if receipt.created_at else None,
                    "updated_at": receipt.updated_at.isoformat() if receipt.updated_at else None
                },
                "document_info": {
                    "doc_path": receipt.delivery_receipt_doc_path,
                    "doc_exists": doc_exists,
                    "file_size": file_size
                },
                "files_info": {
                    "qr_code_path": receipt.qr_code_path,
                    "barcode_path": receipt.barcode_path,
                    "receipt_file_path": receipt.receipt_file_path,
                    "tracking_screenshot_path": receipt.tracking_screenshot_path
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取送达回证信息失败: {str(e)}",
                "tracking_number": tracking_number
            }
    
    def list_delivery_receipts(self, limit: int = 50) -> Dict:
        """
        列出所有送达回证
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            送达回证列表
        """
        try:
            receipts = self.db.query(DeliveryReceipt).order_by(
                DeliveryReceipt.created_at.desc()
            ).limit(limit).all()
            
            results = []
            for receipt in receipts:
                # 检查Word文档是否存在
                doc_exists = False
                file_size = 0
                if receipt.delivery_receipt_doc_path:
                    doc_exists = os.path.exists(receipt.delivery_receipt_doc_path)
                    if doc_exists:
                        file_size = os.path.getsize(receipt.delivery_receipt_doc_path)
                
                results.append({
                    "id": receipt.id,
                    "tracking_number": receipt.tracking_number,
                    "doc_title": receipt.doc_title,
                    "sender": receipt.sender,
                    "send_time": receipt.send_time,
                    "send_location": receipt.send_location,
                    "receiver": receipt.receiver,
                    "status": receipt.status.value if receipt.status else None,
                    "created_at": receipt.created_at.isoformat() if receipt.created_at else None,
                    "doc_exists": doc_exists,
                    "file_size": file_size
                })
            
            return {
                "success": True,
                "message": f"获取送达回证列表成功，共 {len(results)} 条记录",
                "receipts": results,
                "count": len(results),
                "limit": limit
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取送达回证列表失败: {str(e)}"
            }