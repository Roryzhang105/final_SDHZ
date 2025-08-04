from pydantic import BaseModel, Field
from typing import Optional


class DeliveryReceiptSmartCreate(BaseModel):
    """
    智能填充送达回证创建模型
    """
    tracking_number: str = Field(..., description="快递单号")
    document_type: str = Field(..., description="文书类型", examples=["补正通知书", "申请告知书", "决定书"])
    case_number: str = Field(..., description="案号")
    recipient_type: str = Field(..., description="受送达人类型", examples=["申请人", "被申请人", "第三人"])
    recipient_name: str = Field(..., description="受送达人姓名")
    delivery_time: str = Field(..., description="送达时间")
    delivery_address: str = Field(..., description="送达地点")
    sender: Optional[str] = Field(default=None, description="送达人")


class DeliveryReceiptGenerateRequest(BaseModel):
    """
    传统送达回证生成请求模型
    """
    tracking_number: str
    doc_title: str = "送达回证"
    sender: Optional[str] = None
    send_time: Optional[str] = None
    send_location: Optional[str] = None
    receiver: Optional[str] = None


class DeliveryReceiptUpdateRequest(BaseModel):
    """
    送达回证更新请求模型
    """
    doc_title: str = "送达回证"
    sender: Optional[str] = None
    send_time: Optional[str] = None
    send_location: Optional[str] = None
    receiver: Optional[str] = None
    remarks: Optional[str] = None


class DeliveryReceiptResponse(BaseModel):
    """
    送达回证响应模型
    """
    success: bool
    message: str
    data: Optional[dict] = None


class DeliveryReceiptInfo(BaseModel):
    """
    送达回证详细信息模型
    """
    id: int
    tracking_number: str
    doc_title: str
    sender: Optional[str] = None
    send_time: Optional[str] = None
    send_location: Optional[str] = None
    receiver: Optional[str] = None
    remarks: Optional[str] = None
    delivery_receipt_doc_path: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None