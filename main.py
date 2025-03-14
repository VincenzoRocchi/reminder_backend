from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def index():
    return {"message": "Reminders App Backend is running!"}

all_todos = [
    {"todo_id": 1, "todo_name": "Do homework"},
    {"todo_id": 2, "todo_name": "Do laundry"},
    {"todo_id": 3, "todo_name": "Do dishes"},
    {"todo_id": 4, "todo_name": "Do groceries"}
]

#call the endpoint with PATH PARAMETER http://0.0.0.0:1111/todo/1 

@app.get("/todos/{todo_id}")
def todo(todo_id: int):
    for todo in all_todos:
        if todo["todo_id"] == todo_id:
            return {"result" : todo}
    return {"result" : "Not found"}

#call the endpoint with QUERY PARAMETER http://0.0.0.0:1111/todos?first_n=2
@app.get("/todos")
def todos(first_n : int = None):
    if first_n:
        return {"result" : all_todos[:first_n]}
    return {"result" : all_todos}

#to make post calls no other service is required other then accessing the docs of fastAPI
@app.post("/todos")
def create_todo(todo: dict):
    new_todo_id = len(all_todos) + 1
    
    new_todo = {
        "todo_id": new_todo_id,
        "todo_name": todo["todo_name"]
    }
    all_todos.append(new_todo)
    return {"result": "Added successfully", "new_todo": new_todo}

@app.put("/todos/{todo_id}")
def update_todo(todo_id: int, updated_todo: dict):
    for todo in all_todos:
        if todo["todo_id"] == todo_id:
            todo["todo_name"] = updated_todo["todo_name"]
            return {"result": "Updated successfully", "todo": todo}
    return {"result": "Not found"}