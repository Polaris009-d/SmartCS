"""
认证相关 Schema
"""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="登录邮箱")
    password: str = Field(..., min_length=1, description="密码")


class RegisterRequest(BaseModel):
    email: str = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    display_name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    role: str = Field(default="agent", pattern="^(admin|agent)$")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserProfile(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    availability: str
    avatar_url: str | None = None

    class Config:
        from_attributes = True
