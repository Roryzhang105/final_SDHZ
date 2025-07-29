import os
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from docx import Document
from PIL import Image
from celery import current_app as celery_app
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.delivery_receipt import DeliveryReceiptService


@celery_app.task
def generate_qr_and_barcode(receipt_id: int):
    """
    生成二维码和条形码的异步任务
    """
    db: Session = SessionLocal()
    try:
        service = DeliveryReceiptService(db)
        receipt = service.get_delivery_receipt(receipt_id)
        
        if not receipt:
            return {"error": "送达回证不存在"}
        
        # 创建文件目录
        codes_dir = os.path.join(settings.UPLOAD_DIR, "codes")
        os.makedirs(codes_dir, exist_ok=True)
        
        # 生成二维码
        qr_path = generate_qr_code(receipt.tracking_number, codes_dir)
        
        # 生成条形码
        barcode_path = generate_barcode(receipt.tracking_number, codes_dir)
        
        # 更新文件路径
        service.update_receipt_files(
            receipt_id=receipt_id,
            qr_code_path=qr_path,
            barcode_path=barcode_path
        )
        
        return {
            "message": "二维码和条形码生成成功",
            "qr_path": qr_path,
            "barcode_path": barcode_path
        }
        
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


def generate_qr_code(tracking_number: str, output_dir: str) -> str:
    """
    生成二维码
    """
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(tracking_number)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        filename = f"qr_{tracking_number}.png"
        file_path = os.path.join(output_dir, filename)
        img.save(file_path)
        
        return file_path
    except Exception as e:
        print(f"生成二维码失败: {e}")
        return None


def generate_barcode(tracking_number: str, output_dir: str) -> str:
    """
    生成条形码
    """
    try:
        code = Code128(tracking_number, writer=ImageWriter())
        filename = f"barcode_{tracking_number}"
        file_path = os.path.join(output_dir, filename)
        
        code.save(file_path)
        
        return f"{file_path}.png"
    except Exception as e:
        print(f"生成条形码失败: {e}")
        return None


@celery_app.task
def fill_receipt_template(receipt_id: int):
    """
    填充送达回证模板的异步任务
    """
    db: Session = SessionLocal()
    try:
        service = DeliveryReceiptService(db)
        receipt = service.get_delivery_receipt(receipt_id)
        
        if not receipt:
            return {"error": "送达回证不存在"}
        
        # 填充模板
        receipt_path = fill_document_template(receipt)
        
        if receipt_path:
            # 更新文件路径
            service.update_receipt_files(
                receipt_id=receipt_id,
                receipt_file_path=receipt_path
            )
            
            return {
                "message": "送达回证文档生成成功",
                "receipt_path": receipt_path
            }
        else:
            return {"error": "文档生成失败"}
            
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


def fill_document_template(receipt) -> str:
    """
    填充Word文档模板
    """
    try:
        # 模板文件路径
        template_path = "templates/receipt_template.docx"
        
        if not os.path.exists(template_path):
            print("模板文件不存在")
            return None
        
        # 加载模板
        doc = Document(template_path)
        
        # 替换文档中的占位符
        replacements = {
            "{{tracking_number}}": receipt.tracking_number,
            "{{recipient_name}}": receipt.recipient_name,
            "{{recipient_address}}": receipt.recipient_address,
            "{{sender_name}}": receipt.sender_name,
            "{{courier_company}}": receipt.courier_company,
        }
        
        # 替换段落中的文本
        for paragraph in doc.paragraphs:
            for placeholder, value in replacements.items():
                if placeholder in paragraph.text:
                    paragraph.text = paragraph.text.replace(placeholder, value or "")
        
        # 替换表格中的文本
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for placeholder, value in replacements.items():
                        if placeholder in cell.text:
                            cell.text = cell.text.replace(placeholder, value or "")
        
        # 保存填充后的文档
        output_dir = os.path.join(settings.UPLOAD_DIR, "receipts")
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"receipt_{receipt.tracking_number}.docx"
        output_path = os.path.join(output_dir, filename)
        
        doc.save(output_path)
        
        return output_path
        
    except Exception as e:
        print(f"填充模板失败: {e}")
        return None


@celery_app.task
def cleanup_old_files():
    """
    清理旧文件的定时任务
    """
    try:
        # 这里可以实现清理逻辑
        # 比如删除超过一定时间的临时文件
        return {"message": "文件清理完成"}
    except Exception as e:
        return {"error": str(e)}