import os
import shutil
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.tracking import TrackingInfo
from app.models.delivery_receipt import DeliveryReceipt


class FileManagementService:
    """通用文件管理服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.upload_dir.mkdir(exist_ok=True)
    
    def get_file_info(self, file_path: str) -> Dict:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "exists": False,
                    "error": "文件不存在"
                }
            
            stat = os.stat(file_path)
            return {
                "exists": True,
                "file_path": file_path,
                "file_name": os.path.basename(file_path),
                "file_size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "is_readable": os.access(file_path, os.R_OK),
                "extension": os.path.splitext(file_path)[1].lower()
            }
        except Exception as e:
            return {
                "exists": False,
                "error": f"获取文件信息失败: {str(e)}"
            }
    
    def list_tracking_screenshots(self, limit: int = 50) -> List[Dict]:
        """
        列出所有物流截图文件
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            截图记录列表
        """
        try:
            tracking_records = self.db.query(TrackingInfo).filter(
                TrackingInfo.screenshot_path.isnot(None)
            ).order_by(TrackingInfo.screenshot_generated_at.desc()).limit(limit).all()
            
            results = []
            for record in tracking_records:
                file_info = self.get_file_info(record.screenshot_path)
                
                results.append({
                    "tracking_number": record.delivery_receipt.tracking_number if record.delivery_receipt else "Unknown",
                    "screenshot_path": record.screenshot_path,
                    "screenshot_filename": record.screenshot_filename,
                    "screenshot_generated_at": record.screenshot_generated_at.isoformat() if record.screenshot_generated_at else None,
                    "current_status": record.current_status,
                    "is_signed": record.is_signed == "true",
                    "file_exists": file_info["exists"],
                    "file_size": file_info.get("file_size", 0),
                    "last_update": record.last_update.isoformat() if record.last_update else None
                })
            
            return results
            
        except Exception as e:
            return []
    
    def list_delivery_receipt_docs(self, limit: int = 50) -> List[Dict]:
        """
        列出所有送达回证Word文档
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            送达回证文档记录列表
        """
        try:
            receipt_records = self.db.query(DeliveryReceipt).filter(
                DeliveryReceipt.delivery_receipt_doc_path.isnot(None)
            ).order_by(DeliveryReceipt.created_at.desc()).limit(limit).all()
            
            results = []
            for record in receipt_records:
                doc_file_info = self.get_file_info(record.delivery_receipt_doc_path) if record.delivery_receipt_doc_path else {"exists": False}
                
                results.append({
                    "id": record.id,
                    "tracking_number": record.tracking_number,
                    "doc_title": record.doc_title,
                    "sender": record.sender,
                    "send_time": record.send_time,
                    "send_location": record.send_location,
                    "receiver": record.receiver,
                    "status": record.status.value if record.status else None,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "document_info": {
                        "doc_path": record.delivery_receipt_doc_path,
                        "doc_exists": doc_file_info["exists"],
                        "file_size": doc_file_info.get("file_size", 0),
                        "modified_time": doc_file_info.get("modified_time", None)
                    }
                })
            
            return results
            
        except Exception as e:
            return []
    
    def list_qr_labels(self, limit: int = 50) -> List[Dict]:
        """
        列出所有二维码标签文件
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            二维码标签记录列表
        """
        try:
            receipt_records = self.db.query(DeliveryReceipt).filter(
                DeliveryReceipt.receipt_file_path.isnot(None)
            ).order_by(DeliveryReceipt.created_at.desc()).limit(limit).all()
            
            results = []
            for record in receipt_records:
                # 检查主要文件
                main_file_info = self.get_file_info(record.receipt_file_path) if record.receipt_file_path else {"exists": False}
                
                # 检查二维码文件
                qr_file_info = self.get_file_info(record.qr_code_path) if record.qr_code_path else {"exists": False}
                
                # 检查条形码文件  
                barcode_file_info = self.get_file_info(record.barcode_path) if record.barcode_path else {"exists": False}
                
                results.append({
                    "tracking_number": record.tracking_number,
                    "doc_title": record.doc_title,
                    "sender": record.sender,
                    "status": record.status.value if record.status else None,
                    "created_at": record.created_at.isoformat() if record.created_at else None,
                    "files": {
                        "main_label": {
                            "path": record.receipt_file_path,
                            "exists": main_file_info["exists"],
                            "size": main_file_info.get("file_size", 0)
                        },
                        "qr_code": {
                            "path": record.qr_code_path,
                            "exists": qr_file_info["exists"],
                            "size": qr_file_info.get("file_size", 0)
                        },
                        "barcode": {
                            "path": record.barcode_path,
                            "exists": barcode_file_info["exists"],
                            "size": barcode_file_info.get("file_size", 0)
                        }
                    }
                })
            
            return results
            
        except Exception as e:
            return []
    
    def cleanup_orphaned_files(self, dry_run: bool = True) -> Dict:
        """
        清理孤立的文件（数据库中没有记录的文件）
        
        Args:
            dry_run: 是否为试运行模式，不实际删除文件
            
        Returns:
            清理结果
        """
        try:
            # 获取数据库中所有文件路径
            db_screenshot_paths = set()
            tracking_records = self.db.query(TrackingInfo).filter(
                TrackingInfo.screenshot_path.isnot(None)
            ).all()
            for record in tracking_records:
                db_screenshot_paths.add(record.screenshot_path)
            
            db_receipt_paths = set()
            receipt_records = self.db.query(DeliveryReceipt).all()
            for record in receipt_records:
                if record.qr_code_path:
                    db_receipt_paths.add(record.qr_code_path)
                if record.barcode_path:
                    db_receipt_paths.add(record.barcode_path)
                if record.receipt_file_path:
                    db_receipt_paths.add(record.receipt_file_path)
                if record.tracking_screenshot_path:
                    db_receipt_paths.add(record.tracking_screenshot_path)
                if record.delivery_receipt_doc_path:
                    db_receipt_paths.add(record.delivery_receipt_doc_path)
            
            all_db_paths = db_screenshot_paths | db_receipt_paths
            
            # 扫描文件系统中的文件
            orphaned_files = []
            total_size = 0
            
            for file_type_dir in ["tracking_screenshots", "tracking_html", "delivery_receipts"]:
                dir_path = self.upload_dir / file_type_dir
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file():
                            abs_path = str(file_path)
                            if abs_path not in all_db_paths:
                                file_size = file_path.stat().st_size
                                orphaned_files.append({
                                    "file_path": abs_path,
                                    "file_size": file_size,
                                    "modified_time": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                                    "file_type": file_type_dir
                                })
                                total_size += file_size
            
            # 如果不是试运行，删除孤立文件
            deleted_count = 0
            if not dry_run:
                for file_info in orphaned_files:
                    try:
                        os.unlink(file_info["file_path"])
                        deleted_count += 1
                    except Exception:
                        pass
            
            return {
                "success": True,
                "dry_run": dry_run,
                "orphaned_files_count": len(orphaned_files),
                "total_size": total_size,
                "deleted_count": deleted_count,
                "orphaned_files": orphaned_files if dry_run else []
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"清理孤立文件失败: {str(e)}"
            }
    
    def cleanup_old_files(self, days: int = 30, dry_run: bool = True) -> Dict:
        """
        清理旧文件
        
        Args:
            days: 保留天数
            dry_run: 是否为试运行模式
            
        Returns:
            清理结果
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            old_files = []
            total_size = 0
            
            # 查找旧的截图文件
            old_tracking_records = self.db.query(TrackingInfo).filter(
                TrackingInfo.screenshot_generated_at < cutoff_time,
                TrackingInfo.screenshot_path.isnot(None)
            ).all()
            
            for record in old_tracking_records:
                if os.path.exists(record.screenshot_path):
                    file_size = os.path.getsize(record.screenshot_path)
                    old_files.append({
                        "file_path": record.screenshot_path,
                        "file_size": file_size,
                        "tracking_number": record.delivery_receipt.tracking_number if record.delivery_receipt else "Unknown",
                        "generated_at": record.screenshot_generated_at.isoformat() if record.screenshot_generated_at else None,
                        "type": "screenshot"
                    })
                    total_size += file_size
            
            # 如果不是试运行，删除旧文件并清理数据库记录
            deleted_count = 0
            if not dry_run:
                for file_info in old_files:
                    try:
                        # 删除文件
                        os.unlink(file_info["file_path"])
                        
                        # 清理数据库记录中的文件路径
                        if file_info["type"] == "screenshot":
                            tracking_record = self.db.query(TrackingInfo).filter(
                                TrackingInfo.screenshot_path == file_info["file_path"]
                            ).first()
                            if tracking_record:
                                tracking_record.screenshot_path = None
                                tracking_record.screenshot_filename = None
                        
                        deleted_count += 1
                    except Exception:
                        pass
                
                self.db.commit()
            
            return {
                "success": True,
                "dry_run": dry_run,
                "cutoff_date": cutoff_time.isoformat(),
                "old_files_count": len(old_files),
                "total_size": total_size,
                "deleted_count": deleted_count,
                "old_files": old_files if dry_run else []
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"清理旧文件失败: {str(e)}"
            }
    
    def get_storage_stats(self) -> Dict:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息
        """
        try:
            stats = {
                "upload_dir": str(self.upload_dir),
                "directories": {},
                "total_files": 0,
                "total_size": 0
            }
            
            # 统计各个目录
            for subdir in ["tracking_screenshots", "tracking_html", "delivery_receipts"]:
                dir_path = self.upload_dir / subdir
                if dir_path.exists():
                    file_count = 0
                    dir_size = 0
                    
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file():
                            file_count += 1
                            file_size = file_path.stat().st_size
                            dir_size += file_size
                    
                    stats["directories"][subdir] = {
                        "file_count": file_count,
                        "size": dir_size,
                        "size_mb": round(dir_size / 1024 / 1024, 2)
                    }
                    
                    stats["total_files"] += file_count
                    stats["total_size"] += dir_size
                else:
                    stats["directories"][subdir] = {
                        "file_count": 0,
                        "size": 0,
                        "size_mb": 0
                    }
            
            stats["total_size_mb"] = round(stats["total_size"] / 1024 / 1024, 2)
            
            # 数据库统计
            screenshot_count = self.db.query(TrackingInfo).filter(
                TrackingInfo.screenshot_path.isnot(None)
            ).count()
            
            receipt_file_count = self.db.query(DeliveryReceipt).filter(
                DeliveryReceipt.receipt_file_path.isnot(None)
            ).count()
            
            delivery_receipt_doc_count = self.db.query(DeliveryReceipt).filter(
                DeliveryReceipt.delivery_receipt_doc_path.isnot(None)
            ).count()
            
            stats["database"] = {
                "screenshot_records": screenshot_count,
                "receipt_file_records": receipt_file_count,
                "delivery_receipt_doc_records": delivery_receipt_doc_count
            }
            
            return {
                "success": True,
                "stats": stats
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"获取存储统计失败: {str(e)}"
            }