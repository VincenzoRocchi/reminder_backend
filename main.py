import os
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

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
    env_file = Path(f"env/.env.{env}")
    if env_file.exists():
        print(f"Loading environment from: {env_file}")
        load_dotenv(env_file)
    else:
        print(f"Warning: Environment file {env_file} not found")
        fallback_env = Path("env/.env")
        if fallback_env.exists():
            print(f"Loading fallback environment from: {fallback_env}")
            load_dotenv(fallback_env)
    
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