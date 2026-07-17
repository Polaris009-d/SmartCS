"""
Agent Schema
"""
from datetime import datetime
from pydantic import BaseModel, Field


class OrderQueryRequest(BaseModel):
    order_no: str = Field(..., min_length=1, description="订单号")


class OrderQueryResponse(BaseModel):
    order_no: str
    product_name: str
    quantity: int
    total_amount: float
    status: str
    payment_status: str
    logistics_no: str | None = None
    logistics_status: str | None = None
    created_at: datetime


class LogisticsQueryRequest(BaseModel):
    order_no: str = Field(..., min_length=1)


class LogisticsQueryResponse(BaseModel):
    order_no: str
    logistics_no: str
    logistics_status: str
    shipped_at: datetime | None = None
    tracking_details: str = ""


class AgentLogResponse(BaseModel):
    id: int
    conversation_id: str | None = None
    agent_type: str
    action: str
    input_params: dict
    validation_result: dict
    execution_result: dict
    status: str
    error_message: str | None = None
    execution_time_ms: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
