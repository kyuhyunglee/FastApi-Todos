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
    assert data["description"] == "Testing priority"
    assert data["completed"] is False
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
    assert data["title"] == "Auto Priority"
    assert data["description"] == "Should auto-set priority"
    assert data["completed"] is False
    assert data["priority"] == 1.0  # 첫 번째라면 1.0이어야 함
    assert "id" in data

def test_create_todo_empty_title():
    # description은 주어졌지만 title이 빈 문자열
    todo = {
        "title": "",
        "description": "No title task",
        "completed": False
    }
    response = client.post("/todos", json=todo)
    # 빈 문자열도 유효한 입력으로 처리됨
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == ""
    assert data["description"] == "No title task"
    assert data["completed"] is False
    # 첫 번째 미완료 항목이므로 우선순위는 1.0으로 설정됨
    assert data["priority"] == 1.0
    assert "id" in data

def test_create_todo_empty_description():
    # title은 주어졌지만 description이 빈 문자열
    todo = {
        "title": "No Description",
        "description": "",
        "completed": False
    }
    response = client.post("/todos", json=todo)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "No Description"
    assert data["description"] == ""
    assert data["completed"] is False
    # 첫 번째 할일 항목이므로 우선순위는 1.0
    assert data["priority"] == 1.0
    assert "id" in data

def test_create_todo_missing_title():
    # title 필드가 없는 JSON
    todo = {
        "description": "Missing title field",
        "completed": False
    }
    response = client.post("/todos", json=todo)
    assert response.status_code == 422
    data = response.json()
    # 'title' 필드 누락에 대한 유효성 오류인지 확인
    assert data["detail"][0]["msg"].lower() == "field required"
    assert data["detail"][0]["loc"][-1] == "title"

def test_create_todo_missing_description():
    # description 필드가 없는 JSON
    todo = {
        "title": "Missing Description",
        "completed": False
    }
    response = client.post("/todos", json=todo)
    assert response.status_code == 422
    data = response.json()
    # 'description' 필드 누락에 대한 유효성 오류인지 확인
    assert data["detail"][0]["msg"].lower() == "field required"
    assert data["detail"][0]["loc"][-1] == "description"

def test_create_duplicate_todos():
    # 동일한 제목과 내용을 가진 To-Do 항목을 두 번 생성
    todo = {
        "title": "Duplicate",
        "description": "Same content",
        "completed": False
    }
    resp1 = client.post("/todos", json=todo)
    assert resp1.status_code == 200
    data1 = resp1.json()
    # 첫 번째 항목의 우선순위는 1.0
    assert data1["priority"] == 1.0

    # 같은 내용으로 두 번째 항목 생성
    resp2 = client.post("/todos", json=todo)
    assert resp2.status_code == 200
    data2 = resp2.json()
    # 새 항목이 생성되어 ID가 다르고, 우선순위가 증가했는지 확인 (2.0이어야 함)
    assert data2["id"] != data1["id"]
    assert data2["priority"] == data1["priority"] + 1

    # 두 항목이 모두 목록에 존재하는지 확인
    list_resp = client.get("/todos")
    assert list_resp.status_code == 200
    todos = list_resp.json()
    assert len(todos) == 2
    ids = [t["id"] for t in todos]
    assert data1["id"] in ids and data2["id"] in ids

def test_create_todo_negative_priority():
    # 음수 우선순위 값 처리 테스트
    todo = {
        "title": "Negative Priority",
        "description": "Priority set to negative",
        "completed": False,
        "priority": -5.0
    }
    response = client.post("/todos", json=todo)
    # 음수 우선순위도 현재는 그대로 저장됨
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == -5.0
    assert data["title"] == "Negative Priority"
    assert data["description"] == "Priority set to negative"
    assert data["completed"] is False
    assert "id" in data

def test_create_todo_large_priority():
    # 매우 큰 우선순위 값 처리 테스트
    large_value = 1000000.0
    todo = {
        "title": "Large Priority",
        "description": "Priority set very large",
        "completed": False,
        "priority": large_value
    }
    response = client.post("/todos", json=todo)
    assert response.status_code == 200
    data = response.json()
    assert data["priority"] == large_value
    assert data["title"] == "Large Priority"
    assert data["description"] == "Priority set very large"
    assert data["completed"] is False
    assert "id" in data

def test_update_todo():
    # 먼저 하나 생성
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
    data = update_resp.json()
    assert data["id"] == todo_id
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Desc"
    assert data["completed"] is True
    assert data["priority"] == 10.0

    # 업데이트 후 목록을 조회하여 변경사항이 반영되었는지 확인
    list_resp = client.get("/todos")
    items = list_resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["id"] == todo_id
    assert item["title"] == "Updated Title"
    assert item["description"] == "Updated Desc"
    assert item["completed"] is True
    assert item["priority"] == 10.0

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
    # 요청된 ID가 없을 경우 적절한 오류 메시지 확인
    assert response.json()["detail"] == "To-Do item not found"

def test_update_priority():
    # 우선순위만 업데이트하는 엔드포인트 테스트
    todo = {
        "title": "Needs Priority Update",
        "description": "Will change priority",
        "completed": False
    }
    create_resp = client.post("/todos", json=todo)
    todo_id = create_resp.json()["id"]
    initial_priority = create_resp.json()["priority"]
    assert initial_priority == 1.0

    # 우선순위를 5.5로 변경
    new_priority = 5.5
    resp = client.patch(f"/todos/{todo_id}/priority", json={"priority": new_priority})
    assert resp.status_code == 200
    data = resp.json()
    # 동일한 ID에 대해 priority 필드만 업데이트되고 다른 필드는 변경되지 않았는지 확인
    assert data["id"] == todo_id
    assert data["title"] == "Needs Priority Update"
    assert data["description"] == "Will change priority"
    assert data["completed"] is False
    assert data["priority"] == new_priority

    # 실제 저장된 데이터도 업데이트되었는지 확인
    get_resp = client.get("/todos")
    items = get_resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["id"] == todo_id
    assert item["priority"] == new_priority

def test_update_priority_not_found():
    fake_id = "does-not-exist"
    resp = client.patch(f"/todos/{fake_id}/priority", json={"priority": 42.0})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "To-Do item not found"

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
    data = toggle_resp.json()
    assert data["id"] == todo_id
    assert data["completed"] is True
    assert data["title"] == "Toggle Me"
    assert data["description"] == "Should be toggled"

def test_toggle_todo_twice():
    # 한 항목에 대해 두 번 연속 토글
    todo = {
        "title": "Double Toggle",
        "description": "Toggle twice",
        "completed": False
    }
    create_resp = client.post("/todos", json=todo)
    todo_id = create_resp.json()["id"]
    initial_completed = create_resp.json()["completed"]
    assert initial_completed is False

    # 첫 번째 토글 (False -> True)
    resp1 = client.patch(f"/todos/{todo_id}/toggle")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["completed"] is True

    # 두 번째 토글 (True -> False, 원래대로 복귀)
    resp2 = client.patch(f"/todos/{todo_id}/toggle")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["completed"] is False

    # 두 번째 토글 후 completed 상태가 초기값과 같은지 확인
    assert data2["completed"] == initial_completed

def test_toggle_todo_not_found():
    response = client.patch("/todos/nonexistent-id/toggle")
    assert response.status_code == 404
    assert response.json()["detail"] == "To-Do item not found"

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

def test_delete_todo_twice():
    # 동일 항목 두 번 삭제 시도
    todo = {
        "title": "Delete Twice",
        "description": "Will delete twice",
        "completed": False
    }
    create_resp = client.post("/todos", json=todo)
    todo_id = create_resp.json()["id"]
    # 첫 번째 삭제
    del_resp1 = client.delete(f"/todos/{todo_id}")
    assert del_resp1.status_code == 200
    assert del_resp1.json()["message"] == "To-Do item deleted"
    # 동일한 항목 다시 삭제 시도
    del_resp2 = client.delete(f"/todos/{todo_id}")
    assert del_resp2.status_code == 404
    assert del_resp2.json()["detail"] == "To-Do item not found"

def test_delete_todo_not_found():
    response = client.delete("/todos/invalid-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "To-Do item not found"

