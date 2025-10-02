#!/bin/bash

# Change to backend directory
cd /Users/nguyenbinhan/Workspace/AgentAI/Onyx/onyx/backend

# Load environment variables from .env file - more compatible way
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Activate virtual environment
source .venv/bin/activate

# Set additional environment variables
export PYTHONPATH=/Users/nguyenbinhan/Workspace/AgentAI/Onyx/onyx/backend:$PYTHONPATH

# Run the server
uvicorn onyx.main:app --host 0.0.0.0 --port 8080 --reload