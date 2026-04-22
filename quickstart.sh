#!/bin/bash
# Quick Start Script - Production-RAG System
# Run this to get everything up and running

echo "================================"
echo "Production-RAG Quick Start"
echo "================================"

cd "$(dirname "$0")" || exit

echo ""
echo "Step 1: Setting up environment..."
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv --python 3.11
fi

source .venv/bin/activate

if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    uv sync
fi

echo "✓ Environment ready"

echo ""
echo "Step 2: Running system validation..."
python test_system.py

echo ""
echo "Step 3: Starting backend API (port 8000)..."
echo "   Run in Terminal 1:"
echo "   $ cd backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
echo ""
echo "Step 4: Starting frontend (port 8080)..."
echo "   Run in Terminal 2:"
echo "   $ uv run serve_frontend.py"
echo "   Then open: http://localhost:8080"
echo ""
echo "Step 5: Run evaluation..."
echo "   $ python scripts/evaluate.py"
echo ""
echo "================================"
echo "System is ready!"
echo "================================"
