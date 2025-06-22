@echo off
echo ========================================
echo    STOP ALL FAZZYTOOL PROCESSES
echo ========================================
echo.

echo [1] Stopping Web Server (Python web_app.py)...
taskkill /f /im python.exe /fi "WINDOWTITLE eq *web_app*" 2>nul
taskkill /f /im python.exe /fi "COMMANDLINE eq *web_app.py*" 2>nul

echo [2] Stopping Main Process (Python main.py)...
taskkill /f /im python.exe /fi "WINDOWTITLE eq *main*" 2>nul
taskkill /f /im python.exe /fi "COMMANDLINE eq *main.py*" 2>nul

echo [3] Stopping Browser Automation Processes...
taskkill /f /im python.exe /fi "COMMANDLINE eq *browser*" 2>nul
taskkill /f /im python.exe /fi "COMMANDLINE eq *playwright*" 2>nul

echo [4] Stopping Chrome/Chromium Processes...
taskkill /f /im chrome.exe 2>nul
taskkill /f /im chromium.exe 2>nul
taskkill /f /im msedge.exe 2>nul

echo [5] Stopping All Python Processes in Current Directory...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find /c /v ""') do (
    if %%i gtr 1 (
        echo Found Python processes, attempting to stop...
        wmic process where "name='python.exe' and commandline like '%%FazzyTool%%'" delete 2>nul
    )
)

echo [6] Cleaning up temporary files...
if exist "*.tmp" del /q "*.tmp" 2>nul
if exist "temp\*" del /q "temp\*" 2>nul

echo [7] Stopping any remaining background tasks...
taskkill /f /im python.exe /fi "WINDOWTITLE eq *FazzyTool*" 2>nul

echo.
echo ========================================
echo    ALL PROCESSES STOPPED
echo ========================================
echo.
echo Processes that were stopped:
echo - Web server (web_app.py)
echo - Main application (main.py)
echo - Browser automation
echo - Chrome/Edge browsers
echo - Background Python tasks
echo.
echo You can now safely close this window.
echo.
pause 