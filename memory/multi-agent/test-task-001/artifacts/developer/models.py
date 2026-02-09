"""
数据模型定义
基于架构师设计和安全审计建议
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class User(BaseModel):
    """用户模型"""
    id: int
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """用户创建请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., max_length=100)
    password: str = Field(..., min_length=8, max_length=100)


class Task(BaseModel):
    """任务模型"""
    id: int
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: TaskStatus = TaskStatus.TODO
    priority: int = Field(3, ge=1, le=5)
    user_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class TaskCreate(BaseModel):
    """任务创建请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: int = Field(3, ge=1, le=5)


class TaskUpdate(BaseModel):
    """任务更新请求"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=5)


class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
