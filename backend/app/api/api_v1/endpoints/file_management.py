from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.services.file_management import FileManagementService

router = APIRouter()


@router.get("/screenshots")
async def list_screenshots(
    limit: int = Query(50, description="返回记录数限制", ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    获取所有截图文件列表
    
    Args:
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        截图文件列表
    """
    try:
        file_service = FileManagementService(db)
        screenshots = file_service.list_tracking_screenshots(limit)
        
        return {
            "success": True,
            "message": f"获取截图列表成功，共 {len(screenshots)} 条记录",
            "data": {
                "screenshots": screenshots,
                "count": len(screenshots),
                "limit": limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取截图列表失败: {str(e)}")


@router.get("/qr-labels")
async def list_qr_labels(
    limit: int = Query(50, description="返回记录数限制", ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    获取所有二维码标签文件列表
    
    Args:
        limit: 返回记录数限制
        db: 数据库会话
    
    Returns:
        二维码标签文件列表
    """
    try:
        file_service = FileManagementService(db)
        qr_labels = file_service.list_qr_labels(limit)
        
        return {
            "success": True,
            "message": f"获取二维码标签列表成功，共 {len(qr_labels)} 条记录",
            "data": {
                "qr_labels": qr_labels,
                "count": len(qr_labels),
                "limit": limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取二维码标签列表失败: {str(e)}")


@router.get("/stats")
async def get_storage_stats(db: Session = Depends(get_db)):
    """
    获取存储统计信息
    
    Args:
        db: 数据库会话
    
    Returns:
        存储统计信息
    """
    try:
        file_service = FileManagementService(db)
        result = file_service.get_storage_stats()
        
        if result["success"]:
            return {
                "success": True,
                "message": "获取存储统计信息成功",
                "data": result["stats"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取存储统计信息失败: {str(e)}")


@router.post("/cleanup/orphaned")
async def cleanup_orphaned_files(
    dry_run: bool = Query(True, description="是否为试运行模式（不实际删除文件）"),
    db: Session = Depends(get_db)
):
    """
    清理孤立的文件（数据库中没有记录的文件）
    
    Args:
        dry_run: 是否为试运行模式
        db: 数据库会话
    
    Returns:
        清理结果
    """
    try:
        file_service = FileManagementService(db)
        result = file_service.cleanup_orphaned_files(dry_run)
        
        if result["success"]:
            action = "扫描" if dry_run else "清理"
            return {
                "success": True,
                "message": f"孤立文件{action}完成",
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理孤立文件失败: {str(e)}")


@router.post("/cleanup/old")
async def cleanup_old_files(
    days: int = Query(30, description="保留天数", ge=1, le=365),
    dry_run: bool = Query(True, description="是否为试运行模式（不实际删除文件）"),
    db: Session = Depends(get_db)
):
    """
    清理旧文件
    
    Args:
        days: 保留天数
        dry_run: 是否为试运行模式
        db: 数据库会话
    
    Returns:
        清理结果
    """
    try:
        file_service = FileManagementService(db)
        result = file_service.cleanup_old_files(days, dry_run)
        
        if result["success"]:
            action = "扫描" if dry_run else "清理"
            return {
                "success": True,
                "message": f"旧文件{action}完成（{days}天前）",
                "data": result
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理旧文件失败: {str(e)}")


@router.get("/file-info")
async def get_file_info(
    file_path: str = Query(..., description="文件路径"),
    db: Session = Depends(get_db)
):
    """
    获取指定文件的详细信息
    
    Args:
        file_path: 文件路径
        db: 数据库会话
    
    Returns:
        文件详细信息
    """
    try:
        file_service = FileManagementService(db)
        file_info = file_service.get_file_info(file_path)
        
        return {
            "success": file_info["exists"],
            "message": "获取文件信息成功" if file_info["exists"] else file_info.get("error", "文件不存在"),
            "data": file_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件信息失败: {str(e)}")