#!/bin/bash

# DollarPunk Visualization Dashboard Startup Script

echo "🚀 Starting DollarPunk Visualization Dashboard..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if the network exists, create if it doesn't
if ! docker network ls | grep -q "dollarpunk-network"; then
    echo "📡 Creating dollarpunk-network..."
    docker network create dollarpunk-network
fi

# Build and start the visualization service
echo "🔨 Building and starting visualization service..."
docker-compose up --build -d

# Wait a moment for the service to start
sleep 5

# Check if the service is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ DollarPunk Visualization Dashboard is running!"
    echo "🌐 Access the dashboard at: http://localhost:8501"
    echo ""
    echo "📋 Useful commands:"
    echo "  - View logs: docker-compose logs -f visualization"
    echo "  - Stop service: docker-compose down"
    echo "  - Restart service: docker-compose restart"
else
    echo "❌ Failed to start the visualization service."
    echo "📋 Check the logs with: docker-compose logs visualization"
    exit 1
fi
