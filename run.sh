#!/bin/bash
# ไฟล์: run.sh

echo "🚀 Starting Log Management Demo (Appliance Mode)..."

# 1. เช็คสิทธิ์ Root เพื่อปรับค่า Sysctl ของ Ubuntu[cite: 1]
if [ "$EUID" -ne 0 ]; then
  echo "⚠️ Please run as root (sudo ./run.sh) to configure system parameters."
  exit
fi

# 2. ปรับค่า Virtual Memory เพื่อให้ OpenSearch ทำงานได้
echo "⚙️ Configuring vm.max_map_count for OpenSearch..."
sysctl -w vm.max_map_count=262144

# 3. สร้างไฟล์ .env หากยังไม่มี
if [ ! -f .env ]; then
    echo "📄 Creating .env file from .env.example..."
    cp .env.example .env
fi

# 4. Build และ Start Docker Containers
echo "🐳 Building and starting containers..."
docker-compose up -d --build

echo "✅ Deployment complete!"
echo "Dashboard is available at: http://localhost"
echo "Backend API is available at: http://localhost:8000"