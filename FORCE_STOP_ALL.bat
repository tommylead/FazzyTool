@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   FORCE STOP ALL FAZZYTOOL PROCESSES
echo ========================================
echo WARNING: This will forcefully terminate
echo all Python processes and browsers!
echo.
set /p confirm="Continue? (y/n): "
if /i not "%confirm%"=="y" goto :end

echo.
echo [1] Force stopping all Python processes...
taskkill /f /im python.exe 2>nul
if %errorlevel%==0 echo - Python processes terminated
if %errorlevel%==128 echo - No Python processes found

echo [2] Force stopping all browser processes...
taskkill /f /im chrome.exe 2>nul
taskkill /f /im chromium.exe 2>nul
taskkill /f /im msedge.exe 2>nul
taskkill /f /im firefox.exe 2>nul
echo - Browser processes terminated

echo [3] Stopping Playwright browser processes...
taskkill /f /im playwright.exe 2>nul
wmic process where "commandline like '%%playwright%%'" delete 2>nul
echo - Playwright processes terminated

echo [4] Cleaning up ports (5000, 8080, 3000)...
netstat -ano | findstr :5000 > temp_ports.txt 2>nul
if exist temp_ports.txt (
    for /f "tokens=5" %%a in (temp_ports.txt) do (
        taskkill /f /pid %%a 2>nul
    )
    del temp_ports.txt
)
echo - Port 5000 freed

echo [5] Cleaning up temporary files and folders...
if exist "*.tmp" del /q "*.tmp" 2>nul
if exist "temp" rmdir /s /q "temp" 2>nul
if exist "__pycache__" rmdir /s /q "__pycache__" 2>nul
if exist "*.pyc" del /q "*.pyc" 2>nul
if exist ".pytest_cache" rmdir /s /q ".pytest_cache" 2>nul
echo - Temporary files cleaned

echo [6] Stopping Windows services related to browsers...
sc stop "gupdate" 2>nul
sc stop "gupdatem" 2>nul
echo - Browser services stopped

echo [7] Killing any hung processes...
wmic process where "name='python.exe' and PageFileUsage>100000" delete 2>nul
echo - Hung processes terminated

echo [8] Clearing browser cache locks...
taskkill /f /im "BrowserBroker.exe" 2>nul
taskkill /f /im "RuntimeBroker.exe" 2>nul
echo - Browser locks cleared

echo [9] Final cleanup...
timeout /t 2 /nobreak >nul
echo - Waiting for processes to fully terminate...

echo.
echo ========================================
echo     FORCE STOP COMPLETED
echo ========================================
echo.
echo All processes have been forcefully stopped:
echo ✓ All Python processes
echo ✓ All browser processes  
echo ✓ Playwright automation
echo ✓ Port 5000 freed
echo ✓ Temporary files cleaned
echo ✓ Cache locks cleared
echo.
echo System is now clean and ready for restart.
echo.

:end
pause 