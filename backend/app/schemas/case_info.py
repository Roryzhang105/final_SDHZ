from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class CaseInfoCreate(BaseModel):
    """创建案件请求模型"""
    case_number: str  # 案号
    applicant: str  # 申请人
    respondent: str  # 被申请人
    third_party: Optional[str] = None  # 第三人
    applicant_address: str  # 申请人联系地址
    respondent_address: str  # 被申请人联系地址
    third_party_address: Optional[str] = None  # 第三人联系地址
    closure_date: Optional[date] = None  # 结案日期
    status: str = "active"  # 状态


class CaseInfoUpdate(BaseModel):
    """更新案件请求模型"""
    case_number: Optional[str] = None
    applicant: Optional[str] = None
    respondent: Optional[str] = None
    third_party: Optional[str] = None
    applicant_address: Optional[str] = None
    respondent_address: Optional[str] = None
    third_party_address: Optional[str] = None
    closure_date: Optional[date] = None
    status: Optional[str] = None


class CaseInfo(BaseModel):
    """案件信息响应模型"""
    id: int
    case_number: str
    applicant: str
    respondent: str
    third_party: Optional[str] = None
    applicant_address: str
    respondent_address: str
    third_party_address: Optional[str] = None
    closure_date: Optional[date] = None
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True