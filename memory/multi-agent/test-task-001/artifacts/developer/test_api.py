"""
API单元测试
覆盖率目标: >= 80%
"""
import pytest
from fastapi.testclient import TestClient
from task_api import app, db_users, db_tasks

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    """重置数据库"""
    db_users.clear()
    db_tasks.clear()
    yield


class TestAuth:
    """认证测试"""
    
    def test_register_success(self):
        """测试注册成功"""
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        assert response.json()["user_id"] == 1
    
    def test_register_duplicate_username(self):
        """测试重复用户名"""
        client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        response = client.post("/auth/register", json={
            "username": "testuser",
            "email": "test2@example.com",
            "password": "password123"
        })
        assert response.status_code == 400
    
    def test_login_success(self):
        """测试登录成功"""
        client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_invalid_credentials(self):
        """测试无效凭据"""
        response = client.post("/auth/login", json={
            "username": "nonexistent",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestTasks:
    """任务管理测试"""
    
    def get_auth_token(self):
        """获取认证Token"""
        client.post("/auth/register", json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123"
        })
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })
        return response.json()["access_token"]
    
    def test_create_task(self):
        """测试创建任务"""
        token = self.get_auth_token()
        response = client.post(
            "/tasks",
            json={"title": "测试任务", "description": "任务描述", "priority": 3},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 201
        assert response.json()["title"] == "测试任务"
    
    def test_get_tasks(self):
        """测试获取任务列表"""
        token = self.get_auth_token()
        client.post(
            "/tasks",
            json={"title": "任务1", "priority": 3},
            headers={"Authorization": f"Bearer {token}"}
        )
        response = client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_update_task(self):
        """测试更新任务"""
        token = self.get_auth_token()
        create_resp = client.post(
            "/tasks",
            json={"title": "原任务", "priority": 3},
            headers={"Authorization": f"Bearer {token}"}
        )
        task_id = create_resp.json()["id"]
        response = client.put(
            f"/tasks/{task_id}",
            json={"title": "更新后的任务", "status": "in_progress"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["title"] == "更新后的任务"
        assert response.json()["status"] == "in_progress"
    
    def test_delete_task(self):
        """测试删除任务"""
        token = self.get_auth_token()
        create_resp = client.post(
            "/tasks",
            json={"title": "待删除任务", "priority": 3},
            headers={"Authorization": f"Bearer {token}"}
        )
        task_id = create_resp.json()["id"]
        response = client.delete(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        get_resp = client.get(
            f"/tasks/{task_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert get_resp.status_code == 404
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        response = client.get("/tasks")
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=task_api", "--cov-report=term-missing"])
