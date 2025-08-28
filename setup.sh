#!/bin/bash

# Climate Risk Lens Setup Script
# This script helps users get started with the Climate Risk Lens application

set -e  # Exit on any error

echo "Climate Risk Lens Setup Script"
echo "=============================="
echo ""

# Check if required tools are installed
check_requirements() {
    echo "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo "ERROR: Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        echo "ERROR: Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    
    # Check Git
    if ! command -v git &> /dev/null; then
        echo "ERROR: Git is not installed. Please install Git from https://git-scm.com/downloads"
        exit 1
    fi
    
    # Check Make
    if ! command -v make &> /dev/null; then
        echo "ERROR: Make is not installed. Please install Make."
        exit 1
    fi
    
    echo "✓ All requirements are installed"
    echo ""
}

# Check if Docker is running
check_docker_running() {
    echo "Checking if Docker is running..."
    if ! docker info &> /dev/null; then
        echo "ERROR: Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
    echo "✓ Docker is running"
    echo ""
}

# Setup environment file
setup_environment() {
    echo "Setting up environment configuration..."
    if [ ! -f .env ]; then
        cp .env.example .env
        echo "✓ Created .env file from .env.example"
    else
        echo "✓ .env file already exists"
    fi
    echo ""
}

# Install dependencies and start services
start_application() {
    echo "Installing dependencies and starting services..."
    echo "This may take a few minutes on first run..."
    echo ""
    
    # Run setup
    make setup
    
    echo ""
    echo "Starting development environment..."
    make dev
    
    echo ""
    echo "Waiting for services to be ready..."
    sleep 30
    
    echo ""
    echo "Checking service status..."
    docker-compose ps
}

# Show success message
show_success() {
    echo ""
    echo "🎉 Setup Complete!"
    echo "=================="
    echo ""
    echo "Your Climate Risk Lens application is now running!"
    echo ""
    echo "Access the application at:"
    echo "  • Main Application: http://localhost:3000"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • MLflow (ML Tracking): http://localhost:5000"
    echo "  • Grafana (Monitoring): http://localhost:3001 (admin/admin)"
    echo "  • MinIO (File Storage): http://localhost:9001 (minioadmin/minioadmin)"
    echo ""
    echo "To stop the application, run: make stop"
    echo "To view logs, run: docker-compose logs -f"
    echo "To check status, run: docker-compose ps"
    echo ""
    echo "For troubleshooting, see the README.md file."
    echo ""
}

# Main execution
main() {
    check_requirements
    check_docker_running
    setup_environment
    start_application
    show_success
}

# Run main function
main "$@"
