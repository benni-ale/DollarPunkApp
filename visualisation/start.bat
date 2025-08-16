@echo off
REM DollarPunk Visualization Dashboard Startup Script for Windows

echo 🚀 Starting DollarPunk Visualization Dashboard...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker and try again.
    pause
    exit /b 1
)

REM Check if the network exists, create if it doesn't
docker network ls | findstr "dollarpunk-network" >nul 2>&1
if errorlevel 1 (
    echo 📡 Creating dollarpunk-network...
    docker network create dollarpunk-network
)

REM Build and start the visualization service
echo 🔨 Building and starting visualization service...
docker-compose up --build -d

REM Wait a moment for the service to start
timeout /t 5 /nobreak >nul

REM Check if the service is running
docker-compose ps | findstr "Up" >nul 2>&1
if not errorlevel 1 (
    echo ✅ DollarPunk Visualization Dashboard is running!
    echo 🌐 Access the dashboard at: http://localhost:8501
    echo.
    echo 📋 Useful commands:
    echo   - View logs: docker-compose logs -f visualization
    echo   - Stop service: docker-compose down
    echo   - Restart service: docker-compose restart
) else (
    echo ❌ Failed to start the visualization service.
    echo 📋 Check the logs with: docker-compose logs visualization
    pause
    exit /b 1
)

pause
