from typing import Dict, List, Optional, Any
import pandas as pd
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, date
import logging

from ..models.case_info import CaseInfo
from ..schemas.case_info import CaseInfoCreate, CaseInfoUpdate

logger = logging.getLogger(__name__)


class CaseImportService:
    """案件信息Excel导入服务"""
    
    # Excel列名映射到数据库字段
    COLUMN_MAPPING = {
        '案号': 'case_number',
        '申请人': 'applicant', 
        '被申请人': 'respondent',
        '第三人': 'third_party',
        '联系地址': 'applicant_address',  # 申请人联系地址
        '被申请人联系地址': 'respondent_address',
        '第三人联系地址': 'third_party_address',
        '结案日期': 'closure_date'
    }
    
    # 必填字段
    REQUIRED_FIELDS = ['案号', '申请人', '被申请人', '联系地址']
    
    def __init__(self, db: Session):
        self.db = db
    
    async def import_cases_from_excel(self, file: UploadFile) -> Dict[str, Any]:
        """
        从Excel文件导入案件信息
        
        Args:
            file: 上传的Excel文件
            
        Returns:
            导入结果统计
        """
        try:
            # 验证文件类型
            if not file.filename.endswith(('.xlsx', '.xls')):
                raise HTTPException(status_code=400, detail="仅支持Excel文件(.xlsx, .xls)")
            
            # 读取Excel文件
            df = pd.read_excel(file.file)
            logger.info(f"读取Excel文件成功，共{len(df)}行数据")
            
            # 验证必要列是否存在
            missing_columns = []
            for required_col in self.REQUIRED_FIELDS:
                if required_col not in df.columns:
                    missing_columns.append(required_col)
            
            if missing_columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Excel文件缺少必要列: {', '.join(missing_columns)}"
                )
            
            # 处理数据
            result = await self._process_dataframe(df)
            
            return result
            
        except Exception as e:
            logger.error(f"Excel导入失败: {str(e)}")
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=f"Excel文件处理失败: {str(e)}")
    
    async def _process_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """处理DataFrame数据"""
        imported_count = 0
        updated_count = 0
        errors = []
        
        # 统计信息
        total_rows = len(df)
        
        for index, row in df.iterrows():
            try:
                # 验证必填字段
                validation_error = self._validate_row(row, index + 2)  # +2 因为Excel从第2行开始
                if validation_error:
                    errors.append(validation_error)
                    continue
                
                # 转换数据
                case_data = self._convert_row_to_case_data(row)
                
                # 检查案件是否已存在
                case_number = case_data['case_number']
                existing_case = self.db.query(CaseInfo).filter(
                    CaseInfo.case_number == case_number
                ).first()
                
                if existing_case:
                    # 更新现有案件
                    await self._update_existing_case(existing_case, case_data)
                    updated_count += 1
                    logger.debug(f"更新案件: {case_number}")
                else:
                    # 创建新案件
                    await self._create_new_case(case_data)
                    imported_count += 1
                    logger.debug(f"新增案件: {case_number}")
                
            except Exception as e:
                error_msg = f"第{index + 2}行处理失败: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                continue
        
        # 提交数据库事务
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise HTTPException(status_code=500, detail=f"数据库保存失败: {str(e)}")
        
        return {
            "total_rows": total_rows,
            "imported": imported_count,
            "updated": updated_count,
            "errors": errors,
            "success_rate": round((imported_count + updated_count) / total_rows * 100, 2) if total_rows > 0 else 0
        }
    
    def _validate_row(self, row: pd.Series, row_number: int) -> Optional[str]:
        """验证行数据"""
        for field in self.REQUIRED_FIELDS:
            value = row.get(field)
            if pd.isna(value) or str(value).strip() == '':
                return f"第{row_number}行: 必填字段'{field}'为空"
        return None
    
    def _convert_row_to_case_data(self, row: pd.Series) -> Dict[str, Any]:
        """将Excel行数据转换为案件数据"""
        case_data = {}
        
        for excel_col, db_field in self.COLUMN_MAPPING.items():
            value = row.get(excel_col)
            
            # 处理空值
            if pd.isna(value):
                if db_field in ['third_party', 'third_party_address', 'closure_date']:
                    case_data[db_field] = None
                else:
                    case_data[db_field] = ""
            else:
                # 特殊处理日期字段
                if db_field == 'closure_date':
                    case_data[db_field] = self._parse_date(value)
                else:
                    case_data[db_field] = str(value).strip()
        
        # 设置默认状态
        case_data['status'] = 'active'
        
        return case_data
    
    def _parse_date(self, value: Any) -> Optional[date]:
        """解析日期"""
        if pd.isna(value):
            return None
        
        try:
            if isinstance(value, datetime):
                return value.date()
            elif isinstance(value, date):
                return value
            elif isinstance(value, str):
                # 尝试解析字符串日期
                dt = pd.to_datetime(value, errors='coerce')
                if pd.isna(dt):
                    return None
                return dt.date()
            else:
                return None
        except Exception:
            return None
    
    async def _create_new_case(self, case_data: Dict[str, Any]):
        """创建新案件"""
        case_create = CaseInfoCreate(**case_data)
        case = CaseInfo(**case_create.model_dump())
        self.db.add(case)
    
    async def _update_existing_case(self, existing_case: CaseInfo, case_data: Dict[str, Any]):
        """更新现有案件"""
        case_update = CaseInfoUpdate(**case_data)
        update_data = case_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if value is not None:  # 只更新非None的字段
                setattr(existing_case, field, value)
        
        # 更新时间
        existing_case.updated_at = datetime.utcnow()


async def import_cases_from_excel(file: UploadFile, db: Session) -> Dict[str, Any]:
    """
    便捷函数：从Excel文件导入案件信息
    
    Args:
        file: 上传的Excel文件
        db: 数据库会话
        
    Returns:
        导入结果
    """
    service = CaseImportService(db)
    return await service.import_cases_from_excel(file)