import os
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.recognition import (
    RecognitionTask, RecognitionResult, CourierPattern,
    RecognitionTypeEnum, RecognitionStatusEnum
)
from app.utils.legacy.robust_qr_reader import decode_qr
from app.core.config import settings


class QRRecognitionService:
    """二维码/条形码识别服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self._init_courier_patterns()
    
    def _init_courier_patterns(self):
        """初始化快递单号识别模式"""
        patterns = [
            {
                "courier_name": "EMS中国邮政",
                "courier_code": "ems",
                "pattern_regex": r"^[A-Z]{2}\d{9}[A-Z]{2}$",
                "pattern_length": 13,
                "pattern_prefix": "",
                "description": "EMS单号格式：2个字母+9个数字+2个字母",
                "examples": ["EA123456789CN", "CP123456789CN"]
            },
            {
                "courier_name": "顺丰速运",
                "courier_code": "shunfeng", 
                "pattern_regex": r"^SF\d{12}$",
                "pattern_length": 14,
                "pattern_prefix": "SF",
                "description": "顺丰单号格式：SF+12位数字",
                "examples": ["SF1234567890123"]
            },
            {
                "courier_name": "中通快递",
                "courier_code": "zhongtong",
                "pattern_regex": r"^\d{12}$",
                "pattern_length": 12,
                "pattern_prefix": "",
                "description": "中通单号格式：12位数字",
                "examples": ["123456789012"]
            },
            {
                "courier_name": "EMS数字单号",
                "courier_code": "ems_number",
                "pattern_regex": r"^\d{13}$",
                "pattern_length": 13,
                "pattern_prefix": "",
                "description": "EMS数字单号：13位数字",
                "examples": ["1151242358360"]
            },
            {
                "courier_name": "通用数字单号",
                "courier_code": "generic_number",
                "pattern_regex": r"^\d{10,18}$",
                "pattern_length": 0,
                "pattern_prefix": "",
                "description": "通用数字单号：10-18位数字",
                "examples": ["1234567890", "123456789012345678"]
            }
        ]
        
        # 检查是否已存在模式，不存在则创建
        existing_count = self.db.query(CourierPattern).count()
        if existing_count == 0:
            for pattern_data in patterns:
                pattern = CourierPattern(**pattern_data)
                self.db.add(pattern)
            self.db.commit()
    
    def recognize_single_image(self, image_path: str, task_id: Optional[int] = None) -> Dict[str, Any]:
        """识别单张图片中的二维码/条形码"""
        start_time = time.time()
        
        try:
            # 使用robust_qr_reader识别
            qr_texts = decode_qr(image_path)
            
            # 解析识别结果
            parsed_results = self._parse_recognition_results(qr_texts)
            
            processing_time = time.time() - start_time
            
            result = {
                "file_path": image_path,
                "file_name": os.path.basename(image_path),
                "file_size": os.path.getsize(image_path) if os.path.exists(image_path) else 0,
                "recognition_type": self._determine_recognition_type(parsed_results),
                "raw_results": qr_texts,
                "tracking_numbers": parsed_results["tracking_numbers"],
                "qr_contents": parsed_results["qr_contents"],
                "barcode_contents": parsed_results["barcode_contents"],
                "confidence_score": parsed_results["confidence_score"],
                "detection_count": len(qr_texts),
                "is_success": "true" if qr_texts else "false",
                "processing_time": processing_time,
                "extra_metadata": {
                    "recognition_engine": "robust_qr_reader",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # 如果有任务ID，保存到数据库
            if task_id:
                self._save_recognition_result(task_id, result)
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_result = {
                "file_path": image_path,
                "file_name": os.path.basename(image_path),
                "file_size": 0,
                "recognition_type": RecognitionTypeEnum.MIXED.value,
                "raw_results": [],
                "tracking_numbers": [],
                "qr_contents": [],
                "barcode_contents": [],
                "confidence_score": 0.0,
                "detection_count": 0,
                "is_success": "false",
                "error_message": str(e),
                "processing_time": processing_time,
                "extra_metadata": {"error": True}
            }
            
            if task_id:
                self._save_recognition_result(task_id, error_result)
            
            return error_result
    
    def _parse_recognition_results(self, raw_texts: List[str]) -> Dict[str, Any]:
        """解析识别结果，提取快递单号等信息"""
        tracking_numbers = []
        qr_contents = []
        barcode_contents = []
        
        # 获取所有激活的识别模式
        patterns = self.db.query(CourierPattern).filter(
            CourierPattern.is_active == "true"
        ).order_by(CourierPattern.priority.desc()).all()
        
        for text in raw_texts:
            text = text.strip()
            if not text:
                continue
                
            # 先尝试从URL中提取快递单号
            extracted_number = self._extract_tracking_from_url(text)
            
            # 尝试匹配快递单号
            matched_tracking = False
            
            # 如果从URL提取到了数字，尝试匹配模式
            if extracted_number:
                for pattern in patterns:
                    if pattern.pattern_regex:
                        if re.match(pattern.pattern_regex, extracted_number):
                            tracking_numbers.append({
                                "number": extracted_number,
                                "courier_name": pattern.courier_name,
                                "courier_code": pattern.courier_code,
                                "pattern_matched": pattern.pattern_regex,
                                "source_url": text  # 保存原始URL
                            })
                            matched_tracking = True
                            break
            
            # 如果没有从URL提取到，直接匹配原文本
            if not matched_tracking:
                for pattern in patterns:
                    if pattern.pattern_regex:
                        if re.match(pattern.pattern_regex, text):
                            tracking_numbers.append({
                                "number": text,
                                "courier_name": pattern.courier_name,
                                "courier_code": pattern.courier_code,
                                "pattern_matched": pattern.pattern_regex
                            })
                            matched_tracking = True
                            break
            
            # 如果不是快递单号，按内容特征分类
            if not matched_tracking:
                if self._is_likely_qr_content(text):
                    qr_contents.append(text)
                elif self._is_likely_barcode_content(text):
                    barcode_contents.append(text)
                else:
                    qr_contents.append(text)  # 默认归类为二维码内容
        
        # 计算置信度分数
        confidence_score = self._calculate_confidence_score(
            raw_texts, tracking_numbers, qr_contents, barcode_contents
        )
        
        return {
            "tracking_numbers": tracking_numbers,
            "qr_contents": qr_contents,
            "barcode_contents": barcode_contents,
            "confidence_score": confidence_score
        }
    
    def _is_likely_qr_content(self, text: str) -> bool:
        """判断是否可能是二维码内容"""
        # 二维码通常包含URL、复杂文本等
        qr_indicators = [
            "http://", "https://", "www.", ".com", ".cn",
            "微信", "支付宝", "扫码", "二维码"
        ]
        return any(indicator in text for indicator in qr_indicators) or len(text) > 20
    
    def _is_likely_barcode_content(self, text: str) -> bool:
        """判断是否可能是条形码内容"""
        # 条形码通常是纯数字，长度适中
        return text.isdigit() and 8 <= len(text) <= 20
    
    def _determine_recognition_type(self, parsed_results: Dict) -> str:
        """根据识别结果确定识别类型"""
        has_qr = bool(parsed_results["qr_contents"])
        has_barcode = bool(parsed_results["barcode_contents"]) or bool(parsed_results["tracking_numbers"])
        
        if has_qr and has_barcode:
            return RecognitionTypeEnum.MIXED.value
        elif has_qr:
            return RecognitionTypeEnum.QRCODE.value
        elif has_barcode:
            return RecognitionTypeEnum.BARCODE.value
        else:
            return RecognitionTypeEnum.MIXED.value
    
    def _calculate_confidence_score(self, raw_texts: List[str], tracking_numbers: List, 
                                  qr_contents: List, barcode_contents: List) -> float:
        """计算识别置信度分数"""
        if not raw_texts:
            return 0.0
        
        score = 0.5  # 基础分数
        
        # 成功识别内容加分
        if tracking_numbers:
            score += 0.3  # 识别到快递单号高分
        if qr_contents:
            score += 0.1
        if barcode_contents:
            score += 0.1
            
        # 识别数量加分
        detection_bonus = min(len(raw_texts) * 0.05, 0.2)
        score += detection_bonus
        
        return min(score, 1.0)
    
    def _extract_tracking_from_url(self, text: str) -> Optional[str]:
        """从URL中提取快递单号"""
        try:
            # 检查是否为URL
            if text.startswith(('http://', 'https://')):
                # 从URL路径中提取数字
                import urllib.parse
                parsed = urllib.parse.urlparse(text)
                path_parts = parsed.path.split('/')
                
                # 查找路径中的数字部分，支持更广泛的长度范围
                for part in reversed(path_parts):
                    if part.isdigit() and len(part) >= 8:  # 降低最小长度要求
                        print(f"从URL {text} 提取到快递单号: {part}")
                        return part
                
                # 从查询参数中查找
                if parsed.query:
                    query_params = urllib.parse.parse_qs(parsed.query)
                    for key, values in query_params.items():
                        for value in values:
                            if value.isdigit() and len(value) >= 8:  # 降低最小长度要求
                                print(f"从URL查询参数提取到快递单号: {value}")
                                return value
                
                # 如果路径和查询参数都没找到，尝试从整个URL中提取数字
                import re
                number_matches = re.findall(r'\d{8,}', text)  # 查找8位以上的数字
                if number_matches:
                    # 返回最长的数字串
                    longest_number = max(number_matches, key=len)
                    print(f"从URL整体提取到快递单号: {longest_number}")
                    return longest_number
            
            return None
            
        except Exception as e:
            print(f"从URL提取快递单号失败: {e}")
            return None
    
    def _save_recognition_result(self, task_id: int, result_data: Dict[str, Any]):
        """保存识别结果到数据库"""
        try:
            result = RecognitionResult(
                task_id=task_id,
                file_name=result_data["file_name"],
                file_path=result_data["file_path"],
                file_size=result_data["file_size"],
                recognition_type=RecognitionTypeEnum(result_data["recognition_type"]),
                raw_results=result_data["raw_results"],
                tracking_numbers=result_data["tracking_numbers"],
                qr_contents=result_data["qr_contents"],
                barcode_contents=result_data["barcode_contents"],
                confidence_score=result_data["confidence_score"],
                detection_count=result_data["detection_count"],
                is_success=result_data["is_success"],
                error_message=result_data.get("error_message"),
                processing_time=result_data["processing_time"],
                extra_metadata=result_data["extra_metadata"]
            )
            self.db.add(result)
            self.db.commit()
        except Exception as e:
            print(f"保存识别结果失败: {e}")
            self.db.rollback()
    
    def create_recognition_task(self, task_name: str, description: str = "", 
                              user_id: Optional[int] = None) -> RecognitionTask:
        """创建识别任务"""
        task = RecognitionTask(
            task_name=task_name,
            description=description,
            user_id=user_id,
            status=RecognitionStatusEnum.PENDING
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def update_task_status(self, task_id: int, status: RecognitionStatusEnum, 
                          error_message: str = None):
        """更新任务状态"""
        task = self.db.query(RecognitionTask).filter(RecognitionTask.id == task_id).first()
        if task:
            task.status = status
            if error_message:
                task.error_message = error_message
            if status == RecognitionStatusEnum.PROCESSING:
                task.started_at = datetime.utcnow()
            elif status in [RecognitionStatusEnum.COMPLETED, RecognitionStatusEnum.FAILED]:
                task.completed_at = datetime.utcnow()
            self.db.commit()
    
    def get_task_results(self, task_id: int, skip: int = 0, limit: int = 100) -> List[RecognitionResult]:
        """获取任务识别结果"""
        return self.db.query(RecognitionResult).filter(
            RecognitionResult.task_id == task_id
        ).offset(skip).limit(limit).all()
    
    def get_task_stats(self, task_id: int) -> Dict[str, Any]:
        """获取任务统计信息"""
        task = self.db.query(RecognitionTask).filter(RecognitionTask.id == task_id).first()
        if not task:
            return {}
        
        results = self.db.query(RecognitionResult).filter(RecognitionResult.task_id == task_id).all()
        
        success_count = sum(1 for r in results if r.is_success == "true")
        total_detections = sum(r.detection_count for r in results)
        avg_confidence = sum(r.confidence_score for r in results) / len(results) if results else 0.0
        
        return {
            "task_id": task_id,
            "task_name": task.task_name,
            "status": task.status.value,
            "total_files": len(results),
            "success_count": success_count,
            "error_count": len(results) - success_count,
            "total_detections": total_detections,
            "average_confidence": round(avg_confidence, 3),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None
        }