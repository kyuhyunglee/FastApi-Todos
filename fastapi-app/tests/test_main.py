import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from fastapi.testclient import TestClient
from main import app, save_todos, load_todos, TodoItem

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_and_teardown():
    # 테스트 전 초기화
    save_todos([])
    yield
    # 테스트 후 정리
    save_todos([])

def test_get_todos_empty():
    response = client.get("/todos")
    assert response.status_code == 200
    assert response.json() == []

def test_create_todo_with_priority():
    todo = {
        "title": "Test Priority",
        "description": "Testing priority",
        "completed": False,
        "priority": 5.0
    }
    response = client.post("/todos", json=todo)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Priority"
    assert data["priority"] == 5.0
    assert "id" in data

def test_create_todo_without_priority():
    todo = {
        "title": "Auto Priority",
        "description": "Should auto-set priority",
        "completed": False
    }
    response = client.post("/todos", json=todo)
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == 1.0  # 첫 번째라면 1.0이어야 함

def test_update_todo():
    # 먼저 생성
    todo = {
        "title": "ToUpdate",
        "description": "Before update",
        "completed": False
    }
    create_resp = client.post("/todos", json=todo)
    todo_id = create_resp.json()["id"]

    updated_todo = {
        "id": todo_id,
        "title": "Updated Title",
        "description": "Updated Desc",
        "completed": True,
        "priority": 10.0
    }
    update_resp = client.put(f"/todos/{todo_id}", json=updated_todo)
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Title"
    assert update_resp.json()["completed"] is True

def test_update_todo_not_found():
    fake_id = "nonexistent-id"
    updated = {
        "id": fake_id,
        "title": "Doesn't Matter",
        "description": "N/A",
        "completed": False,
        "priority": 1.0
    }
    response = client.put(f"/todos/{fake_id}", json=updated)
    assert response.status_code == 404

def test_toggle_todo():
    todo = {
        "title": "Toggle Me",
        "description": "Should be toggled",
        "completed": False
    }
    create_resp = client.post("/todos", json=todo)
    todo_id = create_resp.json()["id"]

    toggle_resp = client.patch(f"/todos/{todo_id}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["completed"] is True

def test_toggle_todo_not_found():
    response = client.patch("/todos/nonexistent-id/toggle")
    assert response.status_code == 404

def test_delete_todo():
    todo = {
        "title": "Delete Me",
        "description": "To be deleted",
        "completed": False
    }
    create_resp = client.post("/todos", json=todo)
    todo_id = create_resp.json()["id"]

    del_resp = client.delete(f"/todos/{todo_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["message"] == "To-Do item deleted"

def test_delete_todo_not_found():
    response = client.delete("/todos/invalid-id")
    assert response.status_code == 404

