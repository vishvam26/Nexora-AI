@echo off
echo ============================================
echo  Nexora AI — V1 Personal Edition
echo ============================================
echo.
echo Copying V1 .env.example to apps/backend/.env ...
copy /Y "versions\v1-personal\.env.example" "apps\backend\.env"
echo.
echo Starting Nexora AI in PERSONAL mode...
echo.
cd apps\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
