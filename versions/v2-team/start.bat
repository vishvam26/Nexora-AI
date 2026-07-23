@echo off
echo ============================================
echo  Nexora AI — V2 Team Edition
echo ============================================
echo.
echo Copying V2 .env.example to apps/backend/.env ...
copy /Y "versions\v2-team\.env.example" "apps\backend\.env"
echo.
echo Starting Nexora AI in TEAM mode...
echo.
cd apps\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
