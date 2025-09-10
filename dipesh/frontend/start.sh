#!/bin/bash

# Start script for the CI/CD Dashboard Frontend
echo "Starting CI/CD Pipeline Health Dashboard Frontend..."

# Install dependencies
echo "Installing dependencies..."
npm install

# Start the development server
echo "Starting Vite development server..."
npm run dev
