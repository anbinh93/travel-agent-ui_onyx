#!/bin/bash

# Set environment variables
export POSTGRES_HOST=127.0.0.1
export POSTGRES_PORT=5433
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=password
export POSTGRES_DB=postgres
export REDIS_HOST=127.0.0.1
export REDIS_PORT=6379
export PYTHONPATH=/Users/nguyenbinhan/Workspace/AgentAI/Onyx/onyx/backend

# Add current directory to Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Activate virtual environment
source .venv/bin/activate

# Run the server
uvicorn onyx.main:app --host 0.0.0.0 --port 8080 --reload