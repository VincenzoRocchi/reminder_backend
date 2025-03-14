from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def index():
    return {"message": "Reminders App Backend is running!"}

all_todos = [
    {"todos_id": 1, "todos_name": "Do homework"},
    {"todos_id": 2, "todos_name": "Do laundry"},
    {"todos_id": 3, "todos_name": "Do dishes"},
    {"todos_id": 4, "todos_name": "Do groceries"}
]

#call the endpoint with http://0.0.0.0:1111/todo/1

@app.get("/todo/{todos_id}")
def todo(todos_id: int):
    for todo in all_todos:
        if todo["todos_id"] == todos_id:
            return {"result" : todo}
    return {"result" : "Not found"}

#call the endpoint with query parameter http://0.0.0.0:1111/todos?first_n=2
@app.get("/todos")
def todos(first_n : int):
    if first_n:
        return {"result" : all_todos[:first_n]}
    return {"result" : all_todos}