#!/bin/bash
"""
Startup script for the complete backend system
Starts both the main API and featured image generator service
"""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Backend Services${NC}"
echo "=================================="

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Please create one first.${NC}"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}⚠️ Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Start services in the background
echo -e "${GREEN}🔧 Starting Main API on port 8000...${NC}"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
MAIN_PID=$!

echo -e "${GREEN}🎨 Starting Featured Image Generator on port 8001...${NC}"
cd app/featured-image-generator
python run_server.py &
IMG_PID=$!

cd ../..

echo -e "${GREEN}✅ Services started successfully!${NC}"
echo "=================================="
echo "📊 Main API: http://localhost:8000"
echo "📊 API Docs: http://localhost:8000/docs"
echo "🎨 Image Generator: http://localhost:8001"
echo "🎨 Image Generator Docs: http://localhost:8001/docs"
echo ""
echo "🤖 Available automation scripts:"
echo "  - Outline Generation: python3 app/outline_generation.py"
echo "  - Blog Generation: python3 run_blog_generation.py"
echo "  - Blog Generation (dry-run): python3 run_blog_generation.py --dry-run"
echo "  - Full Automation: python3 full_automation_workflow.py"
echo ""
echo "Press Ctrl+C to stop all services..."

# Function to handle cleanup
cleanup() {
    echo -e "\n${YELLOW}🛑 Stopping services...${NC}"
    kill $MAIN_PID $IMG_PID 2>/dev/null
    echo -e "${GREEN}✅ All services stopped.${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for services to finish
wait $MAIN_PID $IMG_PID
