#!/bin/bash

# Apply database migrations
echo "Applying database migrations..."
alembic upgrade head

# Start the FastAPI application
echo "Starting Reminder App API server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload