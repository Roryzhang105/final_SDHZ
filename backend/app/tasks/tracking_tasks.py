import requests
from celery import current_app as celery_app
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.tracking import TrackingService


@celery_app.task
def update_tracking_info(tracking_number: str):
    """
    更新物流跟踪信息的异步任务
    """
    db: Session = SessionLocal()
    try:
        service = TrackingService(db)
        receipt = service.get_receipt_by_tracking_number(tracking_number)
        
        if not receipt:
            return {"error": "未找到对应的送达回证"}
        
        # 调用快递查询API
        tracking_data = fetch_tracking_data(tracking_number, receipt.courier_code or receipt.courier_company)
        
        if tracking_data:
            # 更新物流信息
            service.create_or_update_tracking(
                receipt_id=receipt.id,
                current_status=tracking_data.get("status", ""),
                tracking_data=tracking_data,
                notes=f"自动更新于 {tracking_data.get('update_time', '')}"
            )
            
            return {"message": "物流信息更新成功", "tracking_number": tracking_number}
        else:
            return {"error": "获取物流信息失败"}
            
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


def fetch_tracking_data(tracking_number: str, courier_code: str) -> dict:
    """
    调用快递查询API获取物流数据
    """
    try:
        # 这里应该调用实际的快递查询API
        # 暂时返回模拟数据
        return {
            "tracking_number": tracking_number,
            "courier_code": courier_code,
            "status": "运输中",
            "update_time": "2024-01-01 12:00:00",
            "traces": [
                {
                    "time": "2024-01-01 10:00:00",
                    "status": "已发货",
                    "location": "发货地"
                },
                {
                    "time": "2024-01-01 12:00:00", 
                    "status": "运输中",
                    "location": "中转站"
                }
            ]
        }
    except Exception as e:
        print(f"获取物流数据失败: {e}")
        return None


@celery_app.task
def batch_update_tracking(tracking_numbers: list):
    """
    批量更新物流信息
    """
    results = []
    for tracking_number in tracking_numbers:
        result = update_tracking_info.delay(tracking_number)
        results.append({"tracking_number": tracking_number, "task_id": result.id})
    
    return {"message": f"批量更新 {len(tracking_numbers)} 个物流信息", "tasks": results}