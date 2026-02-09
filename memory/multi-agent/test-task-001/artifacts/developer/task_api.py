"""
任务管理系统API
FastAPI实现
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import jwt
from datetime import datetime, timedelta
from typing import List, Optional
from models import User, UserCreate, Task, TaskCreate, TaskUpdate, Token, TaskStatus

# 安全配置
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 模拟数据库
db_users = {}
db_tasks = {}
next_user_id = 1
next_task_id = 1


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    print("应用启动...")
    yield
    print("应用关闭...")


app = FastAPI(
    title="任务管理系统API",
    description="简单任务管理系统",
    version="1.0.0",
    lifespan=lifespan
)

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT Token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """验证JWT Token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证凭据"
            )
        return int(user_id)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已过期"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的Token"
        )


@app.post("/auth/register", response_model=dict)
async def register(user_create: UserCreate):
    """用户注册"""
    global next_user_id
    
    # 检查用户名是否已存在
    for user in db_users.values():
        if user.username == user_create.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
    
    # 创建用户
    user = User(
        id=next_user_id,
        username=user_create.username,
        email=user_create.email,
        password_hash=f"hashed_{user_create.password}"
    )
    db_users[next_user_id] = user
    next_user_id += 1
    
    return {"message": "注册成功", "user_id": user.id}


@app.post("/auth/login", response_model=Token)
async def login(user_create: UserCreate):
    """用户登录"""
    user = None
    for u in db_users.values():
        if u.username == user_create.username:
            user = u
            break
    
    if not user or user.password_hash != f"hashed_{user_create.password}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token)


@app.get("/tasks", response_model=List[Task])
async def get_tasks(current_user_id: int = Depends(verify_token)):
    """获取任务列表"""
    user_tasks = [
        task for task in db_tasks.values()
        if task.user_id == current_user_id
    ]
    return sorted(user_tasks, key=lambda x: x.created_at, reverse=True)


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: TaskCreate,
    current_user_id: int = Depends(verify_token)
):
    """创建任务"""
    global next_task_id
    
    task = Task(
        id=next_task_id,
        title=task_create.title,
        description=task_create.description,
        priority=task_create.priority,
        user_id=current_user_id
    )
    db_tasks[next_task_id] = task
    next_task_id += 1
    
    return task


@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: int, current_user_id: int = Depends(verify_token)):
    """获取任务详情"""
    task = db_tasks.get(task_id)
    if not task or task.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    return task


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user_id: int = Depends(verify_token)
):
    """更新任务"""
    task = db_tasks.get(task_id)
    if not task or task.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    update_data = task_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    task.updated_at = datetime.utcnow()
    
    return task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, current_user_id: int = Depends(verify_token)):
    """删除任务"""
    task = db_tasks.get(task_id)
    if not task or task.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    del db_tasks[task_id]
    return {"message": "任务已删除"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
