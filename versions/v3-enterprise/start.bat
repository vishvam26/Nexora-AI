@echo off
echo ============================================
echo  Nexora AI — V3 Enterprise Edition
echo ============================================
echo.
echo WARNING: V3 is for enterprise use.
echo Make sure PostgreSQL is running.
echo.
echo Copying V3 .env.example to apps/backend/.env ...
copy /Y "versions\v3-enterprise\.env.example" "apps\backend\.env"
echo.
echo Starting Nexora AI in ENTERPRISE mode...
echo.
cd apps\backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
