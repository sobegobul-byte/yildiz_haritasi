@echo off
rem Yildiz Haritasi Studyosu — backend + frontend baslatici
rem Cift tiklayin; iki pencere acilir. Kapatmak icin pencereleri kapatin.
cd /d "%~dp0"

start "StarMap Backend (port 8000)" cmd /k "cd backend && python -m uvicorn app.main:app --port 8000"
start "StarMap Frontend (port 3000)" cmd /k "cd frontend && npm run dev"

echo Sunucular baslatiliyor...
echo Tarayicida acin: http://localhost:3000
timeout /t 5 >nul
start http://localhost:3000
