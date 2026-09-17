@echo off
echo ===================================================
echo 🚀 Starting Log Management Demo (Windows Mode)
echo ===================================================

echo.
echo [1/5] Checking .env configuration...
IF NOT EXIST .env (
    IF EXIST .env.example (
        echo 📄 Copying .env.example to .env...
        copy .env.example .env >nul
    ) ELSE (
        echo ⚠️ No .env or .env.example found.
    )
) ELSE (
    echo ✅ .env file already exists.
)

echo.
echo [2/5] Starting Docker containers...
echo 🐳 Running docker-compose up -d --build...
docker-compose up -d --build

echo.
echo [3/5] Waiting for services to initialize (15 seconds)...
timeout /t 15 /nobreak >nul

echo.
echo [4/5] Initializing Retention Policy...
echo NOTE: Running init_retention.sh requires Git Bash or WSL on Windows.
where bash >nul 2>&1 && (
    bash init_retention.sh
) || (
    echo ⚠️ bash not found. Skipping retention policy setup.
    echo    Please run "bash init_retention.sh" manually from Git Bash or WSL.
)

echo.
echo [5/5] Running Python Ingestion Simulator...
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
