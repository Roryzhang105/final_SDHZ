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
    智能获取物流跟踪信息
    - 已签收快递：永久使用数据库缓存
    - 未签收快递：30分钟内使用缓存，超时重新查询API
    - 无记录快递：调用快递100 API并缓存结果
    """
    tracking_service = TrackingService(db)
    express_service = ExpressTrackingService(db)
    
    # 1. 查询数据库中的物流记录
    tracking_info = tracking_service.get_tracking_by_number(tracking_number)
    
    # 2. 如果数据库中有记录，使用智能缓存策略
    if tracking_info:
        should_refresh = tracking_service.should_refresh_tracking(tracking_info)
        
        if not should_refresh:
            # 不需要刷新（已签收或30分钟内），直接返回数据库记录
            cache_reason = "已签收，使用永久缓存" if tracking_info.is_signed == "true" else "30分钟内，使用时效缓存"
            
            return {
                "success": True,
                "source": "database_cache",
                "cache_reason": cache_reason,
                "tracking_number": tracking_number,
                "data": {
                    "current_status": tracking_info.current_status,
                    "is_signed": tracking_info.is_signed == "true",
                    "last_update": tracking_info.last_update.isoformat() if tracking_info.last_update else None,
                    "tracking_data": tracking_info.tracking_data,
                    "notes": tracking_info.notes,
                    "delivery_receipt_id": tracking_info.delivery_receipt_id
                }
            }
        else:
            # 需要刷新（未签收且超过30分钟），调用API更新
            source_reason = "未签收且超过30分钟，重新查询API"
    else:
        # 数据库中没有记录
        source_reason = "数据库中无记录，首次查询API"
    
    # 3. 调用快递100 API获取最新信息
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
        
        # 4. 尝试保存到数据库（如果有对应的送达回证记录）
        receipt = tracking_service.get_receipt_by_tracking_number(tracking_number)
        saved_to_database = False
        
        if receipt:
            # 有对应的送达回证，保存物流信息到数据库
            tracking_service.create_or_update_tracking(
                receipt_id=receipt.id,
                current_status=api_result["current_status"],
                tracking_data=api_result,
                notes=f"智能查询更新，查询时间: {api_result['last_update']}"
            )
            saved_to_database = True
        
        # 5. 返回API查询结果
        return {
            "success": True,
            "source": "kuaidi100_api",
            "source_reason": source_reason,
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
            "saved_to_database": saved_to_database
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
    company_code: str = Form(default="ems"),
    force_update: bool = Form(default=False),
    db: Session = Depends(get_db)
):
    """
    为任何快递单号生成物流轨迹截图
    - 优先使用数据库中的物流信息
    - 如无记录或需要强制更新，则调用快递100 API
    - 支持Chrome截图和HTML备用方案
    """
    try:
        tracking_service = TrackingService(db)
        express_service = ExpressTrackingService(db)
        screenshot_service = TrackingScreenshotService(db)
        
        # 1. 尝试从数据库获取物流信息
        tracking_info = tracking_service.get_tracking_by_number(tracking_number)
        tracking_data = None
        
        if tracking_info and not force_update:
            # 数据库中有记录且不强制更新，检查是否需要刷新
            should_refresh = tracking_service.should_refresh_tracking(tracking_info)
            
            if not should_refresh:
                # 使用数据库缓存数据
                tracking_data = tracking_info.tracking_data
                if tracking_data:
                    tracking_data["source"] = "database_cache"
        
        # 2. 如果没有可用的缓存数据，调用API
        if not tracking_data:
            if company_code == "ems":
                company_code = express_service.get_company_code_by_number(tracking_number)
            
            api_result = express_service.query_express(tracking_number, company_code)
            
            if not api_result["success"]:
                raise HTTPException(
                    status_code=404, 
                    detail=f"无法获取物流信息: {api_result.get('error', '查询失败')}"
                )
            
            tracking_data = api_result
            tracking_data["source"] = "kuaidi100_api"
            
            # 如果有对应的送达回证，保存到数据库
            receipt = tracking_service.get_receipt_by_tracking_number(tracking_number)
            if receipt:
                tracking_service.create_or_update_tracking(
                    receipt_id=receipt.id,
                    current_status=api_result["current_status"],
                    tracking_data=api_result,
                    notes=f"截图功能调用，查询时间: {api_result['last_update']}"
                )
        
        # 3. 生成截图
        screenshot_result = screenshot_service.generate_screenshot_from_tracking_data(tracking_data)
        
        # 4. 处理返回结果
        response = {
            "success": True,
            "tracking_number": tracking_number,
            "company_code": tracking_data.get("company_code", company_code),
            "data_source": tracking_data.get("source", "unknown"),
            "screenshot_result": screenshot_result
        }
        
        if screenshot_result["success"]:
            if screenshot_result.get("screenshot_path"):
                response["message"] = "物流轨迹截图生成成功"
            elif screenshot_result.get("html_fallback_path"):
                response["message"] = "截图功能不可用，已生成HTML轨迹文件"
        else:
            response["success"] = False
            response["message"] = "截图生成失败"
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成截图过程中发生错误: {str(e)}")


@router.post("/smart-screenshot")
async def smart_screenshot(
    tracking_number: str = Form(...),
    company_code: str = Form(default="ems"),
    db: Session = Depends(get_db)
):
    """
    智能截图功能 - 用户建议的核心功能
    - 已签收快递：直接从数据库缓存生成截图，无需调用API
    - 未签收快递：检查缓存时效(30分钟)，超时则更新后生成截图
    - 无记录快递：调用快递100 API获取数据后生成截图
    """
    try:
        tracking_service = TrackingService(db)
        express_service = ExpressTrackingService(db)
        screenshot_service = TrackingScreenshotService(db)
        
        # 1. 查询数据库中的物流记录
        tracking_info = tracking_service.get_tracking_by_number(tracking_number)
        tracking_data = None
        data_source = None
        
        if tracking_info:
            # 2. 使用智能缓存策略判断是否需要刷新
            should_refresh = tracking_service.should_refresh_tracking(tracking_info)
            
            if not should_refresh:
                # 不需要刷新（已签收或30分钟内）
                tracking_data = tracking_info.tracking_data
                is_signed = tracking_info.is_signed == "true"
                data_source = "已签收，使用永久缓存" if is_signed else "30分钟内，使用时效缓存"
            else:
                # 需要刷新（未签收且超过30分钟）
                data_source = "未签收且超过30分钟，重新查询API"
        else:
            # 数据库中没有记录
            data_source = "数据库中无记录，首次查询API"
        
        # 3. 如果需要API查询
        if not tracking_data:
            if company_code == "ems":
                company_code = express_service.get_company_code_by_number(tracking_number)
            
            api_result = express_service.query_express(tracking_number, company_code)
            
            if not api_result["success"]:
                raise HTTPException(
                    status_code=404, 
                    detail=f"无法获取物流信息: {api_result.get('error', '查询失败')}"
                )
            
            tracking_data = api_result
            
            # 尝试保存到数据库
            receipt = tracking_service.get_receipt_by_tracking_number(tracking_number)
            if receipt:
                tracking_service.create_or_update_tracking(
                    receipt_id=receipt.id,
                    current_status=api_result["current_status"],
                    tracking_data=api_result,
                    notes=f"智能截图调用，查询时间: {api_result['last_update']}"
                )
        
        # 4. 生成截图
        screenshot_result = screenshot_service.generate_screenshot_from_tracking_data(tracking_data)
        
        # 5. 构造返回结果
        response = {
            "success": True,
            "message": "智能截图完成",
            "tracking_number": tracking_number,
            "company_code": tracking_data.get("company_code", company_code),
            "data_source": data_source,
            "tracking_status": {
                "current_status": tracking_data.get("current_status", ""),
                "is_signed": tracking_data.get("is_signed", False),
                "sign_time": tracking_data.get("sign_time", ""),
                "traces_count": len(tracking_data.get("traces", []))
            },
            "screenshot_result": screenshot_result
        }
        
        # 6. 根据截图结果调整消息
        if screenshot_result["success"]:
            if screenshot_result.get("screenshot_path"):
                response["message"] = "智能截图生成成功"
                response["screenshot_info"] = {
                    "type": "png_image",
                    "path": screenshot_result["screenshot_path"],
                    "file_size": screenshot_result.get("file_size", 0),
                    "method": screenshot_result.get("screenshot_method", "unknown")
                }
            elif screenshot_result.get("html_fallback_path"):
                response["message"] = "智能截图：Chrome不可用，已生成HTML文件"
                response["screenshot_info"] = {
                    "type": "html_file",
                    "path": screenshot_result["html_fallback_path"],
                    "file_size": screenshot_result.get("file_size", 0),
                    "note": screenshot_result.get("note", "")
                }
        else:
            response["success"] = False
            response["message"] = "智能截图失败"
            response["error"] = screenshot_result.get("error", "未知错误")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"智能截图过程中发生错误: {str(e)}")


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
    - 支持Chrome截图和HTML备用方案
    - 改进的错误处理和用户友好的返回信息
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
        
        # 构造基础响应
        response_data = {
            "success": True,
            "message": "查询成功",
            "tracking_number": tracking_number,
            "company_code": company_code,
            "tracking_data": {
                "current_status": tracking_result.get("current_status", ""),
                "is_signed": tracking_result.get("is_signed", False),
                "sign_time": tracking_result.get("sign_time", ""),
                "last_update": tracking_result.get("last_update", ""),
                "traces": tracking_result.get("traces", []),
                "from_cache": tracking_result.get("from_cache", False)
            },
            "screenshot": None
        }
        
        # 判断是否需要生成截图
        should_screenshot = force_screenshot or tracking_result.get("is_signed", False)
        
        if should_screenshot:
            # 生成截图
            try:
                screenshot_result = screenshot_service.generate_screenshot_from_tracking_data(tracking_result)
                
                # 处理截图结果
                if screenshot_result["success"]:
                    if screenshot_result.get("screenshot_path"):
                        # 成功生成PNG截图
                        response_data["screenshot"] = {
                            "success": True,
                            "type": "png_image",
                            "screenshot_path": screenshot_result["screenshot_path"],
                            "file_size": screenshot_result.get("file_size", 0),
                            "method": screenshot_result.get("screenshot_method", "chrome_screenshot")
                        }
                        response_data["message"] += "，PNG截图生成成功"
                        
                    elif screenshot_result.get("html_fallback_path"):
                        # 生成HTML备用文件
                        response_data["screenshot"] = {
                            "success": True,
                            "type": "html_file",
                            "html_fallback_path": screenshot_result["html_fallback_path"],
                            "file_size": screenshot_result.get("file_size", 0),
                            "method": screenshot_result.get("screenshot_method", "html_fallback"),
                            "note": "Chrome浏览器不可用，已生成HTML格式的轨迹文件"
                        }
                        response_data["message"] += "，Chrome不可用已生成HTML文件"
                else:
                    # 截图完全失败
                    response_data["screenshot"] = {
                        "success": False,
                        "error": screenshot_result.get("error", "未知错误"),
                        "suggestion": "请检查服务器环境或联系管理员"
                    }
                    response_data["message"] += "，但截图生成失败"
                    
            except Exception as screenshot_error:
                # 截图过程中发生异常
                response_data["screenshot"] = {
                    "success": False,
                    "error": f"截图服务异常: {str(screenshot_error)}",
                    "suggestion": "截图功能暂时不可用，请稍后重试"
                }
                response_data["message"] += "，截图服务发生异常"
        else:
            # 不需要生成截图
            is_signed = tracking_result.get("is_signed", False)
            if is_signed:
                response_data["message"] += "，快递已签收但未要求生成截图"
            else:
                response_data["message"] += "，快递未签收，无需生成截图"
            
            response_data["screenshot"] = {
                "success": False,
                "reason": "未要求生成截图",
                "suggestion": "如需生成截图，请设置force_screenshot=true"
            }
        
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