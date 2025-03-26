import os
import uvicorn
from dotenv import load_dotenv

def choose_environment():
    """
    Allows the user to select the environment for running the application.
    """
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
    # Let the user choose the environment
    env = choose_environment()
    os.environ["ENV"] = env
    
    # Load the appropriate environment file
    env_file = f".env.{env}"
    load_dotenv(env_file)
    
    # Configure uvicorn based on the environment
    if env == "development":
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_level="info"
        )
    elif env == "production":
        uvicorn.run(
            "app.main:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=False,
            workers=4,
            log_level="warning"
        )
    elif env == "testing":
        uvicorn.run(
            "app.main:app", 
            host="127.0.0.1", 
            port=8000, 
            reload=True, 
            log_level="debug"
        )
    else:
        raise ValueError(f"Unknown environment: {env}")