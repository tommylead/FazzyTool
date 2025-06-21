@echo off
chcp 65001 >nul
title FazzyTool - Stop Web Server

echo.
echo ===============================================
echo      FazzyTool - Dung Web Server
echo ===============================================
echo.

echo [INFO] Dang tim va dung web server...

:: Tìm và kill process Python chạy web_app.py
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv /nh ^| findstr web_app') do (
    echo [INFO] Da tim thay web server (PID: %%i)
    taskkill /pid %%i /f >nul 2>&1
    echo [SUCCESS] Da dung web server!
    goto :done
)

for /f "tokens=2" %%i in ('tasklist /fi "imagename eq py.exe" /fo csv /nh ^| findstr web_app') do (
    echo [INFO] Da tim thay web server (PID: %%i)
    taskkill /pid %%i /f >nul 2>&1
    echo [SUCCESS] Da dung web server!
    goto :done
)

:: Nếu không tìm thấy process cụ thể, kill tất cả Python process trên port 5000
echo [INFO] Dang kiem tra port 5000...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5000') do (
    echo [INFO] Da tim thay process tren port 5000 (PID: %%i)
    taskkill /pid %%i /f >nul 2>&1
    echo [SUCCESS] Da giai phong port 5000!
    goto :done
)

echo [WARNING] Khong tim thay web server dang chay
echo [INFO] Co the web server da tat roi

:done
echo.
echo ===============================================
echo [INFO] Hoan thanh! Ban co the dong terminal nay.
echo ===============================================
echo.
pause 