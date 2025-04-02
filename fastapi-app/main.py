from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uuid
import json
import os

app = FastAPI()

# To-Do 항목 모델
class TodoItem(BaseModel):
    id: str
    title: str
    description: str
    completed: bool
    priority: float

# To-Do 생성 모델
class TodoCreate(BaseModel):
    title: str
    description: str
    completed: bool = False
    priority: float | None = None

# 우선순위 변경 모델
class PriorityUpdate(BaseModel):
    priority: float

# JSON 파일 경로
TODO_FILE = "todo.json"

# JSON 파일에서 To-Do 항목 로드
def load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r") as file:
            return json.load(file)
    return []

# JSON 파일에 To-Do 항목 저장
def save_todos(todos):
    with open(TODO_FILE, "w") as file:
        json.dump(todos, file, indent=4)

# To-Do 목록 조회
@app.get("/todos", response_model=list[TodoItem])
def get_todos():
    todos = load_todos()
    return todos

# 신규 To-Do 항목 추가
@app.post("/todos", response_model=TodoItem)
def create_todo(todo: TodoCreate):
    todos = load_todos()
    #유니크한 새 id 생성
    new_id = str(uuid.uuid4())
    #새 인스턴스의 우선순위 결정
    if todo.priority is not None:
        new_priority = todo.priority
    else:
        uncompleted = [t for t in todos if not t.get("completed", False)]
        if uncompleted:
            max_priority = max(t.get("priority",0) for t in uncompleted)
            new_priority = max_priority + 1
        else:
            new_priority = 1.0

    new_item = {
        "id": new_id,
        "title": todo.title,
        "description": todo.description,
        "completed": todo.completed,
        "priority": new_priority
    }
    todos.append(new_item)
    save_todos(todos)
    return new_item

# To-Do 항목 수정
@app.put("/todos/{todo_id}", response_model=TodoItem)
def update_todo(todo_id: str, updated_todo: TodoItem):
    todos = load_todos()
    for todo in todos:
        if str(todo["id"]) == str(todo_id):
            data = updated_todo.dict()
            data["id"] = str(todo_id)
            todo.update(data)
            save_todos(todos)
            return todo
    raise HTTPException(status_code=404, detail="To-Do item not found")

@app.patch("/todos/{todo_id}/toggle", response_model=TodoItem)
def toggle_todo(todo_id: str):
    todos = load_todos()
    for todo in todos:
        if str(todo["id"]) == str(todo_id):
            todo["completed"] = not todo.get("completed",False)
            save_todos(todos)
            return todo
    raise HTTPException(status_code=404, detail="To-Do item not found")

# To-Do 항목 삭제
@app.delete("/todos/{todo_id}", response_model=dict)
def delete_todo(todo_id: str):
    todos = load_todos()
    new_todos = [todo for todo in todos if str(todo["id"]) != str(todo_id)]
    if len(new_todos) != len(todos):
        save_todos(new_todos)
        return {"message": "To-Do item deleted"}
    raise HTTPException(status_code=404, detail="To-Do item not found")

# HTML 파일 서빙
@app.get("/", response_class=HTMLResponse)
def read_root():
    with open("templates/index.html", "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content)

