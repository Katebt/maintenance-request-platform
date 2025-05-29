# app/schemas.py
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str
    department: Optional[str] = None
    phone_number: str = Field(..., max_length=15, description="رقم الجوال")

class UserCreate(UserBase):
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    department: Optional[str] = None
    phone_number: str

    class Config:
        from_attributes = True  # (أو orm_mode = True إذا تستخدم Pydantic v1)

class RequestBase(BaseModel):
    requester_name: str
    email: EmailStr
    phone_number: str
    title: str
    description: str
    location: str
    department: str

class RequestCreate(RequestBase):
    category: Optional[str] = None
    sub_category: Optional[str] = None
    assigned_engineer_id: Optional[int] = None

class RequestOut(RequestBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    category: Optional[str] = None
    sub_category: Optional[str] = None
    assigned_engineer_id: Optional[int] = None

    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    content: str

class CommentCreate(CommentBase):
    request_id: int
    user_id: int

class CommentOut(CommentBase):
    id: int
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    message: str

class NotificationCreate(NotificationBase):
    request_id: int
    user_id: int

class NotificationOut(NotificationBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class AttachmentBase(BaseModel):
    file_name: str
    file_path: str

class AttachmentCreate(AttachmentBase):
    request_id: int
    file_type: str = "initial"

class AttachmentOut(AttachmentBase):
    id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int
    email: EmailStr

