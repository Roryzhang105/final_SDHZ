import os
from typing import List, Dict, Any
from celery import current_app as celery_app
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.qr_recognition import QRRecognitionService
from app.models.recognition import RecognitionStatusEnum


@celery_app.task
def process_batch_recognition(task_id: int, file_infos: List[Dict[str, Any]], save_files: bool = False):
    """
    批量处理图片识别的异步任务
    
    Args:
        task_id: 识别任务ID
        file_infos: 文件信息列表
        save_files: 是否保存文件
    
    Returns:
        处理结果统计
    """
    db: Session = SessionLocal()
    
    try:
        recognition_service = QRRecognitionService(db)
        
        # 更新任务状态为处理中
        recognition_service.update_task_status(task_id, RecognitionStatusEnum.PROCESSING)
        
        total_files = len(file_infos)
        success_count = 0
        error_count = 0
        
        # 逐个处理文件
        for i, file_info in enumerate(file_infos):
            try:
                file_path = file_info.get("file_path")
                if not file_path or not os.path.exists(file_path):
                    error_count += 1
                    continue
                
                # 进行识别
                result = recognition_service.recognize_single_image(file_path, task_id)
                
                if result["is_success"] == "true":
                    success_count += 1
                else:
                    error_count += 1
                
                # 如果是临时文件且不需要保存，删除它
                if file_info.get("is_temp", False) and not save_files:
                    try:
                        os.unlink(file_path)
                    except:
                        pass
                
            except Exception as e:
                error_count += 1
                print(f"处理文件 {file_info.get('filename', 'unknown')} 时发生错误: {e}")
                continue
        
        # 更新任务状态为完成
        recognition_service.update_task_status(task_id, RecognitionStatusEnum.COMPLETED)
        
        return {
            "task_id": task_id,
            "total_files": total_files,
            "success_count": success_count,
            "error_count": error_count,
            "message": "批量识别任务完成"
        }
        
    except Exception as e:
        # 更新任务状态为失败
        recognition_service.update_task_status(
            task_id, 
            RecognitionStatusEnum.FAILED, 
            error_message=str(e)
        )
        
        return {
            "task_id": task_id,
            "error": str(e),
            "message": "批量识别任务失败"
        }
    
    finally:
        db.close()


@celery_app.task
def process_single_recognition(file_path: str, task_id: int = None):
    """
    单个文件识别的异步任务
    
    Args:
        file_path: 文件路径
        task_id: 可选的任务ID
    
    Returns:
        识别结果
    """
    db: Session = SessionLocal()
    
    try:
        recognition_service = QRRecognitionService(db)
        result = recognition_service.recognize_single_image(file_path, task_id)
        
        return {
            "success": True,
            "file_path": file_path,
            "result": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "file_path": file_path,
            "error": str(e)
        }
    
    finally:
        db.close()


@celery_app.task
def cleanup_temp_files():
    """
    清理临时文件的定时任务
    """
    try:
        from app.core.config import settings
        import time
        
        temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
        if not os.path.exists(temp_dir):
            return {"message": "临时目录不存在"}
        
        cleaned_count = 0
        current_time = time.time()
        
        # 删除1小时前的临时文件
        for filename in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, filename)
            try:
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > 3600:  # 1小时 = 3600秒
                        os.unlink(file_path)
                        cleaned_count += 1
            except:
                continue
        
        return {
            "message": "临时文件清理完成",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "临时文件清理失败"
        }


@celery_app.task
def batch_process_test_images():
    """
    批量处理测试图片的任务（用于系统测试）
    """
    db: Session = SessionLocal()
    
    try:
        recognition_service = QRRecognitionService(db)
        
        # 创建测试任务
        task = recognition_service.create_recognition_task(
            task_name="测试图片批量识别",
            description="对所有测试图片进行批量识别测试"
        )
        
        # 获取测试图片目录
        test_images_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            "tests"
        )
        
        if not os.path.exists(test_images_dir):
            recognition_service.update_task_status(
                task.id, 
                RecognitionStatusEnum.FAILED,
                error_message="测试图片目录不存在"
            )
            return {"error": "测试图片目录不存在"}
        
        # 更新任务状态为处理中
        recognition_service.update_task_status(task.id, RecognitionStatusEnum.PROCESSING)
        
        # 获取所有测试图片
        test_images = [f for f in os.listdir(test_images_dir) if f.startswith('photo')]
        
        results = []
        success_count = 0
        
        for image_name in test_images:
            image_path = os.path.join(test_images_dir, image_name)
            try:
                result = recognition_service.recognize_single_image(image_path, task.id)
                results.append({
                    "image_name": image_name,
                    "success": result["is_success"] == "true",
                    "detection_count": result["detection_count"],
                    "tracking_numbers": result["tracking_numbers"],
                    "confidence_score": result["confidence_score"]
                })
                
                if result["is_success"] == "true":
                    success_count += 1
                    
            except Exception as e:
                results.append({
                    "image_name": image_name,
                    "success": False,
                    "error": str(e)
                })
        
        # 更新任务状态为完成
        recognition_service.update_task_status(task.id, RecognitionStatusEnum.COMPLETED)
        
        return {
            "task_id": task.id,
            "total_images": len(test_images),
            "success_count": success_count,
            "results": results,
            "message": "测试图片批量识别完成"
        }
        
    except Exception as e:
        if 'task' in locals():
            recognition_service.update_task_status(
                task.id,
                RecognitionStatusEnum.FAILED,
                error_message=str(e)
            )
        
        return {
            "error": str(e),
            "message": "测试图片批量识别失败"
        }
    
    finally:
        db.close()


@celery_app.task
def update_courier_patterns_from_results():
    """
    根据识别结果更新快递单号模式的任务
    """
    db: Session = SessionLocal()
    
    try:
        from app.models.recognition import RecognitionResult, CourierPattern
        import re
        from collections import Counter
        
        # 获取所有成功的识别结果
        successful_results = db.query(RecognitionResult).filter(
            RecognitionResult.is_success == "true"
        ).all()
        
        # 分析快递单号模式
        tracking_patterns = []
        for result in successful_results:
            if result.tracking_numbers:
                for tracking_info in result.tracking_numbers:
                    number = tracking_info.get("number", "")
                    if number:
                        tracking_patterns.append(number)
        
        # 统计模式
        pattern_stats = {}
        for number in tracking_patterns:
            # 分析数字和字母模式
            if re.match(r'^[A-Z]{2}\d+[A-Z]{2}$', number):
                pattern_type = "EMS_PATTERN"
            elif re.match(r'^SF\d+$', number):
                pattern_type = "SF_PATTERN"
            elif re.match(r'^\d+$', number):
                length = len(number)
                pattern_type = f"NUMERIC_{length}"
            else:
                pattern_type = "OTHER"
            
            if pattern_type not in pattern_stats:
                pattern_stats[pattern_type] = []
            pattern_stats[pattern_type].append(number)
        
        # 更新或创建模式
        updated_patterns = []
        for pattern_type, numbers in pattern_stats.items():
            if len(numbers) >= 3:  # 至少出现3次才创建模式
                updated_patterns.append({
                    "pattern_type": pattern_type,
                    "count": len(numbers),
                    "examples": numbers[:5]  # 保存前5个示例
                })
        
        return {
            "message": "快递单号模式分析完成",
            "total_numbers": len(tracking_patterns),
            "pattern_stats": pattern_stats,
            "updated_patterns": updated_patterns
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "message": "快递单号模式更新失败"
        }
    
    finally:
        db.close()