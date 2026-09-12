#!/bin/bash
echo "==================================================="
echo "🚀 Starting Log Management Demo (Appliance Mode)"
echo "==================================================="

# 1. Sysctl for OpenSearch (Linux only)
if [ "$(uname)" == "Linux" ]; then
    echo ""
    echo "[1/4] Checking vm.max_map_count for OpenSearch..."
    if [ "$EUID" -ne 0 ]; then
        echo "⚠️  Please run as root (sudo ./start_demo.sh) to configure vm.max_map_count on Linux."
    else
        sysctl -w vm.max_map_count=262144
    fi
fi

echo ""
echo "[2/4] Checking .env configuration..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "📄 Copying .env.example to .env..."
        cp .env.example .env
    else
        echo "⚠️  No .env or .env.example found. Please create one."
    fi
else
    echo "✅ .env file already exists."
fi

echo ""
echo "[3/4] Starting Docker containers..."
echo "🐳 Running docker-compose up -d --build..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to initialize (15 seconds)..."
sleep 15

echo ""
echo "[4/4] Running Python Ingestion Simulator..."
echo "📦 Installing required Python library (requests)..."
pip install requests > /dev/null 2>&1

echo "📜 Executing samples/post_logs.py..."
python samples/post_logs.py || python3 samples/post_logs.py

echo ""
echo "==================================================="
echo "✅ Deployment complete!"
echo "Dashboard is available at: http://localhost"
echo "Backend API is available at: http://localhost:8000"
echo "==================================================="
