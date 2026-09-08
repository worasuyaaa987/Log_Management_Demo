@echo off
echo ===================================================
echo 🚀 Starting Log Management Demo (Windows Mode)
echo ===================================================

echo.
echo [1/4] Checking .env configuration...
IF NOT EXIST .env (
    IF EXIST env.local (
        echo 📄 Copying env.local to .env...
        copy env.local .env >nul
    ) ELSE (
        echo ⚠️ No .env or env.local found.
    )
) ELSE (
    echo ✅ .env file already exists.
)

echo.
echo [2/4] Starting Docker containers...
echo 🐳 Running docker-compose up -d --build...
docker-compose up -d --build

echo.
echo [3/4] Waiting for services to initialize (15 seconds)...
timeout /t 15 /nobreak >nul

echo.
echo [4/4] Running Python Ingestion Simulator...
echo 📦 Installing required Python library (requests)...
pip install requests >nul 2>&1

echo 📜 Executing samples\post_logs.py...
python samples\post_logs.py

echo.
echo ===================================================
echo ✅ Deployment complete!
echo Dashboard is available at: http://localhost
echo Backend API is available at: http://localhost:8000
echo ===================================================
pause
