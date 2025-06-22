@echo off
chcp 65001 >nul
title FazzyTool - Stop Web Server

echo.
echo ===============================================
echo      FazzyTool - Dừng Web Server
echo ===============================================
echo.

echo [1] Đang tìm và dừng web server...

:: Method 1: Tìm process Python chạy web_app.py
taskkill /f /im python.exe /fi "COMMANDLINE eq *web_app.py*" 2>nul
if %errorlevel%==0 (
    echo [SUCCESS] Đã dừng web server (python.exe)!
    goto :port_check
)

taskkill /f /im py.exe /fi "COMMANDLINE eq *web_app.py*" 2>nul
if %errorlevel%==0 (
    echo [SUCCESS] Đã dừng web server (py.exe)!
    goto :port_check
)

echo [INFO] Không tìm thấy process web_app.py

:port_check
echo [2] Đang kiểm tra và giải phóng port 5000...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5000 2^>nul') do (
    echo [INFO] Đã tìm thấy process trên port 5000 (PID: %%i)
    taskkill /pid %%i /f >nul 2>&1
    if !errorlevel!==0 (
        echo [SUCCESS] Đã giải phóng port 5000!
    )
)

echo [3] Dọn dẹp các process liên quan...
:: Kill any remaining Flask processes
taskkill /f /im python.exe /fi "WINDOWTITLE eq *Flask*" 2>nul
taskkill /f /im python.exe /fi "COMMANDLINE eq *flask*" 2>nul

echo [4] Kiểm tra kết quả...
timeout /t 1 /nobreak >nul
netstat -ano | findstr :5000 >nul 2>&1
if %errorlevel%==0 (
    echo [WARNING] Port 5000 vẫn đang được sử dụng
    echo [INFO] Có thể cần chạy FORCE_STOP_ALL.bat
) else (
    echo [SUCCESS] Port 5000 đã được giải phóng hoàn toàn!
)

echo.
echo ===============================================
echo [INFO] Hoàn thành! Web server đã được dừng.
echo ===============================================
echo.
echo Nếu vẫn có vấn đề, hãy chạy:
echo - FORCE_STOP_ALL.bat (để force stop tất cả)
echo - STOP_ALL.bat (để stop an toàn)
echo.
pause 