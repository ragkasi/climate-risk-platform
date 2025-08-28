@echo off
REM Climate Risk Lens Setup Script for Windows
REM This script helps users get started with the Climate Risk Lens application

echo Climate Risk Lens Setup Script
echo ==============================
echo.

REM Check if required tools are installed
echo Checking requirements...

REM Check Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Check Docker Compose
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Compose is not installed. Please install Docker Compose.
    pause
    exit /b 1
)

REM Check Git
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Git is not installed. Please install Git from https://git-scm.com/downloads
    pause
    exit /b 1
)

REM Check Make
make --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Make is not installed. Please install Make via Chocolatey or WSL.
    pause
    exit /b 1
)

echo ✓ All requirements are installed
echo.

REM Check if Docker is running
echo Checking if Docker is running...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)
echo ✓ Docker is running
echo.

REM Setup environment file
echo Setting up environment configuration...
if not exist .env (
    copy .env.example .env
    echo ✓ Created .env file from .env.example
) else (
    echo ✓ .env file already exists
)
echo.

REM Install dependencies and start services
echo Installing dependencies and starting services...
echo This may take a few minutes on first run...
echo.

REM Run setup
make setup
if %errorlevel% neq 0 (
    echo ERROR: Setup failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo Starting development environment...
make dev
if %errorlevel% neq 0 (
    echo ERROR: Failed to start development environment. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo Waiting for services to be ready...
timeout /t 30 /nobreak >nul

echo.
echo Checking service status...
docker-compose ps

echo.
echo Setup Complete!
echo ================
echo.
echo Your Climate Risk Lens application is now running!
echo.
echo Access the application at:
echo   • Main Application: http://localhost:3000
echo   • API Documentation: http://localhost:8000/docs
echo   • MLflow (ML Tracking): http://localhost:5000
echo   • Grafana (Monitoring): http://localhost:3001 (admin/admin)
echo   • MinIO (File Storage): http://localhost:9001 (minioadmin/minioadmin)
echo.
echo To stop the application, run: make stop
echo To view logs, run: docker-compose logs -f
echo To check status, run: docker-compose ps
echo.
echo For troubleshooting, see the README.md file.
echo.
pause
