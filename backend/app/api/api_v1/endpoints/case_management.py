from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
import logging

from ....core.database import get_db
from ....models.case_info import CaseInfo
from ....schemas.case_info import CaseInfo as CaseInfoSchema, CaseInfoCreate, CaseInfoUpdate
from ....services.case_import import import_cases_from_excel
from ....schemas.auth import ApiResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/import", response_model=Dict[str, Any])
async def import_cases_excel(
    file: UploadFile = File(..., description="Excel文件"),
    db: Session = Depends(get_db)
):
    """
    从Excel文件导入案件信息
    
    - **file**: Excel文件，支持.xlsx和.xls格式
    - 支持增量更新：根据案号判断是新增还是更新
    - 返回导入统计信息
    """
    try:
        result = await import_cases_from_excel(file, db)
        
        return {
            "success": True,
            "message": "Excel文件导入完成",
            "data": result
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"案件导入失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("", response_model=Dict[str, Any])
async def get_cases(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取案件列表（分页）
    
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大100
    - **status**: 状态筛选（active/inactive）
    """
    try:
        # 构建查询
        query = db.query(CaseInfo)
        
        # 状态筛选
        if status:
            query = query.filter(CaseInfo.status == status)
        
        # 总数统计
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * size
        cases = query.order_by(CaseInfo.created_at.desc()).offset(offset).limit(size).all()
        
        # 转换为响应格式
        cases_data = [CaseInfoSchema.model_validate(case) for case in cases]
        
        return {
            "success": True,
            "message": "获取案件列表成功",
            "data": {
                "cases": cases_data,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取案件列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取案件列表失败: {str(e)}")


@router.get("/search", response_model=Dict[str, Any])
async def search_cases(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    搜索案件
    
    - **q**: 搜索关键词，支持案号、申请人、被申请人、第三人模糊搜索
    - **page**: 页码，从1开始
    - **size**: 每页数量，最大100
    """
    try:
        # 构建搜索查询
        search_term = f"%{q}%"
        query = db.query(CaseInfo).filter(
            or_(
                CaseInfo.case_number.ilike(search_term),
                CaseInfo.applicant.ilike(search_term),
                CaseInfo.respondent.ilike(search_term),
                CaseInfo.third_party.ilike(search_term)
            )
        )
        
        # 总数统计
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * size
        cases = query.order_by(CaseInfo.created_at.desc()).offset(offset).limit(size).all()
        
        # 转换为响应格式
        cases_data = [CaseInfoSchema.model_validate(case) for case in cases]
        
        return {
            "success": True,
            "message": f"搜索到{total}个结果",
            "data": {
                "cases": cases_data,
                "pagination": {
                    "page": page,
                    "size": size,
                    "total": total,
                    "pages": (total + size - 1) // size
                },
                "search_term": q
            }
        }
        
    except Exception as e:
        logger.error(f"搜索案件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/{case_number}", response_model=Dict[str, Any])
async def get_case_by_number(
    case_number: str,
    db: Session = Depends(get_db)
):
    """
    根据案号获取案件信息
    
    - **case_number**: 案号
    """
    try:
        case = db.query(CaseInfo).filter(CaseInfo.case_number == case_number).first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"未找到案号为 {case_number} 的案件")
        
        case_data = CaseInfoSchema.model_validate(case)
        
        return {
            "success": True,
            "message": "获取案件信息成功",
            "data": case_data
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"获取案件信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取案件信息失败: {str(e)}")


@router.post("", response_model=Dict[str, Any])
async def create_case(
    case_data: CaseInfoCreate,
    db: Session = Depends(get_db)
):
    """
    创建新案件
    
    - **case_data**: 案件信息
    """
    try:
        # 检查案号是否已存在
        existing_case = db.query(CaseInfo).filter(
            CaseInfo.case_number == case_data.case_number
        ).first()
        
        if existing_case:
            raise HTTPException(status_code=400, detail=f"案号 {case_data.case_number} 已存在")
        
        # 创建新案件
        case = CaseInfo(**case_data.model_dump())
        db.add(case)
        db.commit()
        db.refresh(case)
        
        case_response = CaseInfoSchema.model_validate(case)
        
        return {
            "success": True,
            "message": "案件创建成功",
            "data": case_response
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"创建案件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建案件失败: {str(e)}")


@router.put("/{case_id}", response_model=Dict[str, Any])
async def update_case(
    case_id: int,
    case_data: CaseInfoUpdate,
    db: Session = Depends(get_db)
):
    """
    更新案件信息
    
    - **case_id**: 案件ID
    - **case_data**: 更新的案件信息
    """
    try:
        case = db.query(CaseInfo).filter(CaseInfo.id == case_id).first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {case_id} 的案件")
        
        # 更新案件信息
        update_data = case_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(case, field, value)
        
        db.commit()
        db.refresh(case)
        
        case_response = CaseInfoSchema.model_validate(case)
        
        return {
            "success": True,
            "message": "案件更新成功",
            "data": case_response
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"更新案件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新案件失败: {str(e)}")


@router.delete("/{case_id}", response_model=Dict[str, Any])
async def delete_case(
    case_id: int,
    db: Session = Depends(get_db)
):
    """
    删除案件
    
    - **case_id**: 案件ID
    """
    try:
        case = db.query(CaseInfo).filter(CaseInfo.id == case_id).first()
        
        if not case:
            raise HTTPException(status_code=404, detail=f"未找到ID为 {case_id} 的案件")
        
        db.delete(case)
        db.commit()
        
        return {
            "success": True,
            "message": "案件删除成功",
            "data": {"deleted_case_id": case_id}
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        logger.error(f"删除案件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除案件失败: {str(e)}")


@router.get("/stats/summary", response_model=Dict[str, Any])
async def get_cases_stats(
    db: Session = Depends(get_db)
):
    """
    获取案件统计信息
    
    返回案件总数、状态分布等统计信息
    """
    try:
        # 总案件数
        total_cases = db.query(CaseInfo).count()
        
        # 按状态统计
        status_stats = db.query(
            CaseInfo.status,
            func.count(CaseInfo.id).label('count')
        ).group_by(CaseInfo.status).all()
        
        # 今月新增案件数
        current_year = func.extract('year', func.now())
        current_month = func.extract('month', func.now())
        this_month_cases = db.query(CaseInfo).filter(
            func.extract('year', CaseInfo.created_at) == current_year,
            func.extract('month', CaseInfo.created_at) == current_month
        ).count()
        
        # 已结案件数
        closed_cases = db.query(CaseInfo).filter(
            CaseInfo.closure_date.isnot(None)
        ).count()
        
        return {
            "success": True,
            "message": "获取统计信息成功",
            "data": {
                "total_cases": total_cases,
                "this_month_cases": this_month_cases,
                "closed_cases": closed_cases,
                "active_cases": total_cases - closed_cases,
                "status_distribution": {
                    status: count for status, count in status_stats
                }
            }
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")