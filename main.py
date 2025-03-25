import os
import uvicorn

def choose_environment():
    print("Choose the environment:")
    print("1. Development")
    print("2. Production")
    print("3. Testing")
    
    choice = input("Enter the number of the environment: ")
    
    if choice == "1":
        return "development"
    elif choice == "2":
        return "production"
    elif choice == "3":
        return "testing"
    else:
        print("Invalid choice. Defaulting to development.")
        return "development"

if __name__ == "__main__":
    """
    Run the FastAPI application with uvicorn
    """
    env = choose_environment()
    os.environ["ENV"] = env
    
    if env == "development":
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    elif env == "production":
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
    elif env == "testing":
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
    else:
        raise ValueError(f"Unknown environment: {env}")