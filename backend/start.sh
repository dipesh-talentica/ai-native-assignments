#!/bin/bash

# Start script for the CI/CD Dashboard Backend
echo "Starting CI/CD Pipeline Health Dashboard Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create data directory if it doesn't exist
mkdir -p data

# Start the application
echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
