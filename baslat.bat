@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
title Yildiz Haritasi Studyosu
echo == Yildiz Haritasi Studyosu ==

where python >nul 2>nul
if errorlevel 1 goto :nopython
where npm >nul 2>nul
if errorlevel 1 goto :nonode

if exist "backend\.venv\Scripts\python.exe" goto :venvok
echo -^> Python ortami kuruluyor, ilk sefer...
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -q -r backend\requirements.txt
:venvok

if exist "frontend\node_modules\.bin\next.cmd" goto :nodeok
echo -^> Node paketleri kuruluyor, ilk sefer...
pushd frontend
call npm install --no-audit --no-fund
popd
if not exist "frontend\node_modules\.bin\next.cmd" goto :npmfail
:nodeok

echo -^> Site derleniyor...
pushd frontend
call npm run build
if errorlevel 1 goto :buildfail
popd

start "Yildiz Backend - port 8000" /min cmd /c "backend\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend"
start "Yildiz Site - port 3000" /min cmd /c "cd /d frontend && npx next start -p 3000"
timeout /t 5 >nul
echo.
echo Site hazir: http://localhost:3000
echo Siparisler: %~dp0backend\orders\
echo Kapatmak icin: bu pencereyi ve gorev cubugundaki "Yildiz Backend" ile "Yildiz Site" pencerelerini kapatin.
echo.

where cloudflared >nul 2>nul
if errorlevel 1 goto :notunnel
if exist tunel-adi.txt goto :namedtunnel
echo -^> Gecici tunel baslatiliyor, adres asagida trycloudflare.com ile biter
cloudflared tunnel --url http://localhost:3000
goto :end

:namedtunnel
set /p TUNEL=<tunel-adi.txt
echo -^> Kalici tunel baslatiliyor: %TUNEL%
cloudflared tunnel run %TUNEL%
goto :end

:notunnel
echo cloudflared kurulu degil, tunel baslatilmadi.
echo Kurulum: winget install --id Cloudflare.cloudflared
pause
goto :end

:nopython
echo HATA: Python bulunamadi. https://www.python.org adresinden kurun, kurulumda "Add Python to PATH" isaretleyin.
pause
exit /b 1

:nonode
echo HATA: Node.js bulunamadi. https://nodejs.org adresinden LTS surumunu kurun.
pause
exit /b 1

:npmfail
echo.
echo HATA: Node paketleri kurulamadi. TAR_ENTRY_ERROR gorduyseniz:
echo  1. Projeyi OneDrive disinda kisa bir klasore tasiyin, ornek C:\yildiz
echo  2. frontend\node_modules klasorunu silin
echo  3. cmd'de calistirin: npm cache clean --force
echo  4. baslat.bat'i tekrar calistirin
pause
exit /b 1

:buildfail
popd
echo HATA: Site derlenemedi, yukaridaki hataya bakin.
pause
exit /b 1

:end
