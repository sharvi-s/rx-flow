#!/bin/bash
# Quick start script for RxFlow development

set -e

echo "🚀 RxFlow Quick Start"
echo "====================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

echo "📦 Starting services with Docker Compose..."
docker compose up --build

echo ""
echo "✅ Services started!"
echo ""
echo "🔗 API: http://localhost:8001"
echo "📖 Docs: http://localhost:8001/docs"
echo "💻 Client: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
