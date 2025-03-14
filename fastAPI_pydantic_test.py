from typing import list, Optional
from enum import IntEnum

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()

class Priority(IntEnum):
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    
class TodoBase(BaseModel):
    todo_name: str = Field(..., min_length=3, max_length=512, description="The name of the todo")
    todo_description = str = Field(..., description="The description of the todo")
    priority: Priority = Field(default = Priority.LOW, description="The priority of the todo")
    
class TodoCreate(TodoBase):
    pass

class Todo(TodoBase):
    todo_id: int = Field(..., description="Unique identifier of the todo")

class TodoUpdate(BaseModel):
    todo_name: Optional[str] = Field(None, min_length=3, max_length=512, description="The name of the todo")
    todo_description: Optional[str] = Field(None, description="The description of the todo")
    priority: Optional[Priority] = Field(None, description="The priority of the todo")
       
all_todos = [
    Todo(todo_id=1, todo_name="Do homework", todo_description="Do math homework", priority=Priority.HIGH),
    Todo(todo_id=2, todo_name="Do laundry", todo_description="Wash clothes", priority=Priority.MEDIUM),
    Todo(todo_id=3, todo_name="Do dishes", todo_description="Clean the dishes", priority=Priority.LOW),
    Todo(todo_id=4, todo_name="Do groceries", todo_description="Buy groceries", priority=Priority.MEDIUM)
]


@app.get("/todos/{todo_id}", response_model=Todo)
def todo(todo_id: int):
    for todo in all_todos:
        if todo.todo_id == todo_id:
            return todo
    return {"result" : "Not found"}

@app.get("/todos", response_model=list[Todo])
def todos(first_n : int = None):
    if first_n:
        return {"result" : all_todos[:first_n]}
    else:
        return {"result" : all_todos}

@app.post("/todos", response_model=Todo)
def create_todo(todo: TodoCreate):
    new_todo_id = len(all_todos) + 1
    
    new_todo = Todo(
        todo_id=new_todo_id,
        todo_name=todo.todo_name,
        todo_description=todo.todo_description,
        priority=todo.priority
    )
    all_todos.append(new_todo)
    return {"result": "Added successfully", "new_todo": new_todo}

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, updated_todo: TodoUpdate):
    for todo in all_todos:
        if todo.todo_id == todo_id:
            todo.todo_name = updated_todo.todo_name
            todo.todo_description = updated_todo.todo_description
            return {"result": "Updated successfully", "todo": todo}
    return {"result": "Error: Not found"}

@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int):
    for index, todo in enumerate(all_todos):
        if todo["todo_id"] == todo_id:
            all_todos.pop(index)
            return {"result": "Deleted successfully"}
    return {"result": "Error: Not found"}