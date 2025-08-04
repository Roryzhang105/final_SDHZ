from sqlalchemy import Column, String, Date, Boolean
from sqlalchemy.orm import relationship

from .base import BaseModel


class CaseInfo(BaseModel):
    __tablename__ = "cases"
    
    case_number = Column(String(100), unique=True, index=True, nullable=False)  # 案号
    applicant = Column(String(100), nullable=False)  # 申请人
    respondent = Column(String(100), nullable=False)  # 被申请人
    third_party = Column(String(100), nullable=True)  # 第三人
    applicant_address = Column(String(500), nullable=False)  # 申请人联系地址
    respondent_address = Column(String(500), nullable=False)  # 被申请人联系地址
    third_party_address = Column(String(500), nullable=True)  # 第三人联系地址
    closure_date = Column(Date, nullable=True)  # 结案日期
    status = Column(String(20), default="active", nullable=False)  # 状态 (active/inactive)