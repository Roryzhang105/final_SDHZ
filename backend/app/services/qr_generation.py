import os
import re
import subprocess
import tempfile
import time
import uuid
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.config import settings
from app.services.delivery_receipt import DeliveryReceiptService


class QRGenerationService:
    """二维码条形码生成服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.delivery_receipt_service = DeliveryReceiptService(db)
        self.legacy_dir = Path(__file__).parent.parent / "utils" / "legacy"
        self.template_path = self.legacy_dir / "template.png"
        
    def generate_qr_barcode_label(self, url: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        根据URL生成二维码条形码标签
        
        Args:
            url: 要生成二维码的URL
            output_dir: 输出目录，如果为None则使用临时目录
            
        Returns:
            包含生成结果的字典
        """
        start_time = time.time()
        
        try:
            # 验证URL格式并提取数字
            tracking_number = self._extract_tracking_number(url)
            if not tracking_number:
                return {
                    "success": False,
                    "error": "无法从URL中提取有效的追踪号",
                    "url": url
                }
            
            # 设置输出目录
            if output_dir is None:
                output_dir = settings.UPLOAD_DIR
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成唯一的文件名前缀
            file_prefix = f"label_{tracking_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 生成二维码和条形码
            qr_path, barcode_path = self._generate_qr_and_barcode(url, tracking_number, output_dir, file_prefix)
            
            # 合成最终标签
            final_label_path = self._compose_label(qr_path, barcode_path, output_dir, file_prefix)
            
            # 保存路径信息用于数据库更新
            qr_path_str = str(qr_path)
            barcode_path_str = str(barcode_path)
            
            # 清理中间文件
            self._cleanup_intermediate_files([qr_path, barcode_path])
            
            processing_time = time.time() - start_time
            
            # 尝试更新或创建数据库中的送达回证记录
            db_updated = False
            receipt = self.delivery_receipt_service.get_delivery_receipt_by_tracking(tracking_number)
            if receipt:
                # 更新现有记录的文件路径
                updated_receipt = self.delivery_receipt_service.update_receipt_files(
                    receipt_id=receipt.id,
                    qr_code_path=qr_path_str,
                    barcode_path=barcode_path_str,
                    receipt_file_path=str(final_label_path)
                )
                db_updated = updated_receipt is not None
            else:
                # 创建新的送达回证记录
                try:
                    new_receipt = self.delivery_receipt_service.create_delivery_receipt(
                        tracking_number=tracking_number,
                        doc_title="送达回证"
                    )
                    # 更新文件路径
                    updated_receipt = self.delivery_receipt_service.update_receipt_files(
                        receipt_id=new_receipt.id,
                        qr_code_path=qr_path_str,
                        barcode_path=barcode_path_str,
                        receipt_file_path=str(final_label_path)
                    )
                    db_updated = updated_receipt is not None
                except Exception as e:
                    # 如果创建失败，不影响文件生成结果
                    print(f"创建送达回证记录失败: {e}")
            
            return {
                "success": True,
                "message": "二维码条形码标签生成成功",
                "data": {
                    "url": url,
                    "tracking_number": tracking_number,
                    "final_label_path": str(final_label_path),
                    "qr_code_path": qr_path_str,
                    "barcode_path": barcode_path_str,
                    "file_size": os.path.getsize(final_label_path),
                    "processing_time": round(processing_time, 3),
                    "db_updated": db_updated
                }
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            return {
                "success": False,
                "error": f"生成过程中发生错误: {str(e)}",
                "processing_time": round(processing_time, 3)
            }
    
    def _extract_tracking_number(self, url: str) -> Optional[str]:
        """从URL中提取追踪号"""
        # 使用正则表达式提取URL末尾的数字
        pattern = r"(\d+)(?:/)?$"
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def _generate_qr_and_barcode(self, url: str, tracking_number: str, output_dir: str, file_prefix: str) -> Tuple[Path, Path]:
        """
        调用make_qr_and_barcode.py生成二维码和条形码
        
        Returns:
            二维码文件路径和条形码文件路径的元组
        """
        # 导入生成函数
        import sys
        sys.path.append(str(self.legacy_dir))
        
        from make_qr_and_barcode import make_qr, make_barcode
        
        # 设置输出路径
        qr_path = Path(output_dir) / f"{file_prefix}_qr.png"
        barcode_path = Path(output_dir) / f"{file_prefix}_barcode.png"
        
        # 生成二维码和条形码
        make_qr(url, qr_path)
        make_barcode(tracking_number, barcode_path)
        
        return qr_path, barcode_path
    
    def _compose_label(self, qr_path: Path, barcode_path: Path, output_dir: str, file_prefix: str) -> Path:
        """
        调用compose_label.py合成最终标签
        
        Args:
            qr_path: 二维码文件路径
            barcode_path: 条形码文件路径
            output_dir: 输出目录
            file_prefix: 文件前缀
            
        Returns:
            最终标签文件路径
        """
        # 导入合成函数
        import sys
        sys.path.append(str(self.legacy_dir))
        
        from compose_label import paste_with_alpha
        from PIL import Image
        
        # 设置输出路径
        final_path = Path(output_dir) / f"{file_prefix}_final.png"
        
        # 打开图片
        template = Image.open(self.template_path).convert("RGBA")
        qr_img = Image.open(qr_path).convert("RGBA")
        bc_img = Image.open(barcode_path).convert("RGBA")
        
        # 使用默认位置参数进行合成（与compose_label.py中的默认值一致）
        qr_x, qr_y = 80, 260  # 二维码位置
        bc_x, bc_y = 365, 30  # 条形码位置
        
        # 贴图
        paste_with_alpha(template, qr_img, (qr_x, qr_y))
        paste_with_alpha(template, bc_img, (bc_x, bc_y))
        
        # 保存最终结果
        template.save(final_path)
        
        return final_path
    
    def _cleanup_intermediate_files(self, file_paths: list):
        """清理中间生成的文件"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception:
                # 忽略清理失败的错误
                pass
    
    def generate_from_recognition_result(self, qr_contents: list, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        从识别结果生成二维码条形码标签
        
        Args:
            qr_contents: 二维码识别结果列表，如 ["https://mini.ems.com.cn/youzheng/mini/1151240728560"]
            output_dir: 输出目录
            
        Returns:
            生成结果字典
        """
        if not qr_contents or len(qr_contents) == 0:
            return {
                "success": False,
                "error": "qr_contents为空或无效"
            }
        
        # 取第一个二维码内容
        url = qr_contents[0]
        
        # 验证URL格式
        if not url.startswith(('http://', 'https://')):
            return {
                "success": False,
                "error": "无效的URL格式"
            }
        
        # 调用主要生成方法
        return self.generate_qr_barcode_label(url, output_dir)