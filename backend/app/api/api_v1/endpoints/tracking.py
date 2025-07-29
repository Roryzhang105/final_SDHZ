from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.tracking import TrackingService
from app.tasks.tracking_tasks import update_tracking_info

router = APIRouter()


@router.get("/{tracking_number}")
async def get_tracking_info(
    tracking_number: str,
    db: Session = Depends(get_db)
):
    """
    获取物流跟踪信息
    """
    service = TrackingService(db)
    tracking_info = service.get_tracking_by_number(tracking_number)
    if not tracking_info:
        raise HTTPException(status_code=404, detail="未找到物流信息")
    return tracking_info


@router.post("/{tracking_number}/update")
async def update_tracking(
    tracking_number: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    更新物流跟踪信息
    """
    service = TrackingService(db)
    receipt = service.get_receipt_by_tracking_number(tracking_number)
    if not receipt:
        raise HTTPException(status_code=404, detail="未找到送达回证")
    
    # 异步更新物流信息
    background_tasks.add_task(update_tracking_info, tracking_number)
    
    return {"message": "物流信息更新中"}


@router.post("/{tracking_number}/screenshot")
async def capture_tracking_screenshot(
    tracking_number: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    截取物流跟踪页面截图
    """
    service = TrackingService(db)
    receipt = service.get_receipt_by_tracking_number(tracking_number)
    if not receipt:
        raise HTTPException(status_code=404, detail="未找到送达回证")
    
    # 异步截图
    from app.tasks.screenshot_tasks import capture_tracking_screenshot_task
    background_tasks.add_task(capture_tracking_screenshot_task, tracking_number)
    
    return {"message": "正在生成物流跟踪截图"}