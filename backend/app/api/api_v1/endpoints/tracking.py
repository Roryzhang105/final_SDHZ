from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.services.tracking import TrackingService
from app.services.express_tracking import ExpressTrackingService
from app.services.tracking_screenshot import TrackingScreenshotService
from app.tasks.tracking_tasks import update_tracking_info


class BatchQueryRequest(BaseModel):
    tracking_numbers: List[str]
    company_code: str = "ems"

router = APIRouter()


@router.get("/{tracking_number}")
async def get_tracking_info(
    tracking_number: str,
    company_code: str = "ems",
    db: Session = Depends(get_db)
):
    """
    获取物流跟踪信息
    优先从数据库查询，如果没有则调用快递100 API
    """
    tracking_service = TrackingService(db)
    express_service = ExpressTrackingService(db)
    
    # 1. 先尝试从数据库获取
    tracking_info = tracking_service.get_tracking_by_number(tracking_number)
    
    if tracking_info:
        # 数据库中有记录，直接返回
        return {
            "success": True,
            "source": "database",
            "tracking_number": tracking_number,
            "data": {
                "current_status": tracking_info.current_status,
                "last_update": tracking_info.last_update.isoformat() if tracking_info.last_update else None,
                "tracking_data": tracking_info.tracking_data,
                "notes": tracking_info.notes,
                "delivery_receipt_id": tracking_info.delivery_receipt_id
            }
        }
    
    # 2. 数据库中没有记录，调用快递100 API
    try:
        # 推断快递公司编码
        if company_code == "ems":
            company_code = express_service.get_company_code_by_number(tracking_number)
        
        # 调用快递100 API
        api_result = express_service.query_express(tracking_number, company_code)
        
        if not api_result["success"]:
            raise HTTPException(
                status_code=404, 
                detail=f"未找到物流信息: {api_result.get('error', '快递100查询失败')}"
            )
        
        # 3. 尝试保存到数据库（如果有对应的送达回证记录）
        receipt = tracking_service.get_receipt_by_tracking_number(tracking_number)
        if receipt:
            # 有对应的送达回证，保存物流信息到数据库
            tracking_service.create_or_update_tracking(
                receipt_id=receipt.id,
                current_status=api_result["current_status"],
                tracking_data=api_result,
                notes=f"从快递100 API获取，查询时间: {api_result['last_update']}"
            )
        
        # 4. 返回API查询结果
        return {
            "success": True,
            "source": "kuaidi100_api",
            "tracking_number": tracking_number,
            "company_code": company_code,
            "data": {
                "current_status": api_result["current_status"],
                "is_signed": api_result.get("is_signed", False),
                "sign_time": api_result.get("sign_time", ""),
                "last_update": api_result["last_update"],
                "traces": api_result.get("traces", []),
                "from_cache": api_result.get("from_cache", False),
                "message": api_result.get("message", "")
            },
            "saved_to_database": receipt is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询物流信息失败: {str(e)}")


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


@router.post("/query")
async def query_express_directly(
    tracking_number: str = Form(...),
    company_code: str = Form(default="ems"),
    db: Session = Depends(get_db)
):
    """
    直接查询快递100 API获取物流信息
    """
    try:
        express_service = ExpressTrackingService(db)
        
        # 推断快递公司编码
        if company_code == "ems":
            company_code = express_service.get_company_code_by_number(tracking_number)
        
        # 调用快递100 API
        result = express_service.query_express(tracking_number, company_code)
        
        if result["success"]:
            return {
                "success": True,
                "message": "查询成功",
                "data": result
            }
        else:
            raise HTTPException(status_code=404, detail=result.get("error", "查询失败"))
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询快递信息失败: {str(e)}")


@router.post("/query-with-screenshot")
async def query_with_screenshot(
    tracking_number: str = Form(...),
    company_code: str = Form(default="ems"),
    force_screenshot: bool = Form(default=False),
    db: Session = Depends(get_db)
):
    """
    查询快递信息并生成轨迹截图（已签收时或强制生成）
    """
    try:
        express_service = ExpressTrackingService(db)
        screenshot_service = TrackingScreenshotService(db)
        
        # 推断快递公司编码
        if company_code == "ems":
            company_code = express_service.get_company_code_by_number(tracking_number)
        
        # 查询快递信息
        tracking_result = express_service.query_express(tracking_number, company_code)
        
        if not tracking_result["success"]:
            raise HTTPException(status_code=404, detail=tracking_result.get("error", "查询失败"))
        
        response_data = {
            "success": True,
            "message": "查询成功",
            "tracking_data": tracking_result,
            "screenshot": None
        }
        
        # 判断是否需要生成截图
        should_screenshot = force_screenshot or tracking_result.get("is_signed", False)
        
        if should_screenshot:
            # 生成截图
            screenshot_result = screenshot_service.generate_screenshot_from_tracking_data(tracking_result)
            
            if screenshot_result["success"]:
                response_data["screenshot"] = {
                    "success": True,
                    "screenshot_path": screenshot_result["screenshot_path"],
                    "screenshot_filename": screenshot_result["screenshot_filename"],
                    "file_size": screenshot_result["file_size"]
                }
                response_data["message"] += "，截图生成成功"
            else:
                response_data["screenshot"] = {
                    "success": False,
                    "error": screenshot_result["error"]
                }
                response_data["message"] += "，但截图生成失败"
        else:
            response_data["message"] += "，快递未签收，无需生成截图"
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询和截图过程中发生错误: {str(e)}")


@router.post("/batch-query")
async def batch_query_express(
    request: BatchQueryRequest,
    db: Session = Depends(get_db)
):
    """
    批量查询多个快递单号的物流信息
    """
    try:
        if not request.tracking_numbers:
            raise HTTPException(status_code=400, detail="快递单号列表不能为空")
        
        if len(request.tracking_numbers) > 20:
            raise HTTPException(status_code=400, detail="单次批量查询不能超过20个快递单号")
        
        express_service = ExpressTrackingService(db)
        
        # 批量查询
        results = express_service.batch_query_express(request.tracking_numbers, request.company_code)
        
        # 统计结果
        success_count = sum(1 for result in results if result["success"])
        failed_count = len(results) - success_count
        
        return {
            "success": True,
            "message": f"批量查询完成，成功 {success_count} 个，失败 {failed_count} 个",
            "summary": {
                "total_count": len(results),
                "success_count": success_count,
                "failed_count": failed_count,
                "company_code": request.company_code
            },
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量查询失败: {str(e)}")


@router.post("/clear-cache")
async def clear_express_cache(
    tracking_number: str = Form(default=None),
    company_code: str = Form(default=None),
    db: Session = Depends(get_db)
):
    """
    清理快递查询缓存
    """
    try:
        express_service = ExpressTrackingService(db)
        result = express_service.clear_cache(tracking_number, company_code)
        
        return {
            "success": True,
            "message": result["message"],
            "cleared_count": result.get("cleared_count", 0)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理缓存失败: {str(e)}")


@router.get("/test/{tracking_number}")
async def test_tracking_query(
    tracking_number: str,
    company_code: str = "ems",
    db: Session = Depends(get_db)
):
    """
    测试快递查询功能
    """
    try:
        express_service = ExpressTrackingService(db)
        
        # 推断快递公司编码
        if company_code == "ems":
            company_code = express_service.get_company_code_by_number(tracking_number)
        
        # 查询快递信息
        result = express_service.query_express(tracking_number, company_code)
        
        return {
            "success": True,
            "message": f"测试查询快递单号: {tracking_number}",
            "inferred_company": company_code,
            "data": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试查询失败: {str(e)}")