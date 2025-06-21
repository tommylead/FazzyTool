@echo off
title FazzyTool Web Interface
color 0A

echo.
echo ===============================================
echo    FAZZYTOOL - WEB INTERFACE LAUNCHER
echo ===============================================
echo.
echo [INFO] Dang khoi dong giao dien web...
echo [INFO] Vui long doi vai giay...
echo.

:: Thử các cách tìm Python khác nhau
set PYTHON_CMD=

:: Thử python
python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto found_python
)

:: Thử py (Python Launcher)
py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto found_python
)

:: Thử python3
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto found_python
)

:: Thử tìm trong đường dẫn phổ biến
if exist "C:\Python*\python.exe" (
    for /f "delims=" %%i in ('dir /b /od "C:\Python*\python.exe" 2^>nul') do set PYTHON_CMD=%%i
    if defined PYTHON_CMD goto found_python
)

:: Không tìm thấy Python
echo [ERROR] Khong tim thay Python tren he thong!
echo.
echo [HUONG DAN] Vui long lam theo cac buoc sau:
echo 1. Tai Python tu: https://www.python.org/downloads/
echo 2. Khi cai dat, CHECK vao "Add Python to PATH"
echo 3. Khoi dong lai may tinh sau khi cai dat
echo 4. Chay lai file nay
echo.
echo [HOAC] Ban co the thu cac lenh sau:
echo - Nhan Win+R, go "cmd", Enter
echo - Go: python --version
echo - Neu khong co loi thi Python da duoc cai dat
echo.
pause
exit /b 1

:found_python
echo [SUCCESS] Tim thay Python: %PYTHON_CMD%
%PYTHON_CMD% --version

:: Kiểm tra pip
echo [INFO] Kiem tra pip...
%PYTHON_CMD% -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Pip khong hoat dong!
    echo [INFO] Thu cai dat pip...
    %PYTHON_CMD% -m ensurepip --upgrade
)

:: Kiểm tra và cài đặt dependencies
echo [INFO] Kiem tra dependencies...
%PYTHON_CMD% -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Flask chua duoc cai dat. Dang cai dat...
    %PYTHON_CMD% -m pip install flask==3.0.0
)

%PYTHON_CMD% -c "import click" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Click chua duoc cai dat. Dang cai dat...
    %PYTHON_CMD% -m pip install click==8.1.7
)

%PYTHON_CMD% -c "import werkzeug" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Werkzeug chua duoc cai dat. Dang cai dat...
    %PYTHON_CMD% -m pip install werkzeug
)

:: Kiểm tra file cần thiết
if not exist "web_app.py" (
    echo [ERROR] Khong tim thay file web_app.py!
    echo [INFO] Vui long dam bao ban dang o dung thu muc FazzyTool.
    pause
    exit /b 1
)

:: Khởi động web app
echo.
echo [SUCCESS] Tat ca dependencies da duoc cai dat!
echo [INFO] Khoi dong FazzyTool Web Interface...
echo [INFO] Giao dien web se mo tai: http://127.0.0.1:5000
echo [INFO] Nhan Ctrl+C de dung web server
echo.
echo ===============================================
echo [QUAN TRONG] Web server se tu dong:
echo - Khoi dong tai http://127.0.0.1:5000
echo - Mo trinh duyet sau 2 giay
echo - Vao Settings de cau hinh API key va cookie
echo ===============================================
echo.

::Khởi động web server trong background và mở Chrome
echo [INFO] Khoi dong web server...
start /b %PYTHON_CMD% web_app.py

:: Chờ web server khởi động
echo [INFO] Cho web server khoi dong... (3 giay)
timeout /t 3 /nobreak >nul

:: Tự động mở Chrome
echo [INFO] Mo Chrome tai http://127.0.0.1:5000...

:: Thử các đường dẫn Chrome phổ biến
set CHROME_FOUND=0

:: Chrome 64-bit
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    echo [SUCCESS] Tim thay Chrome 64-bit
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" "http://127.0.0.1:5000"
    set CHROME_FOUND=1
    goto wait_server
)

:: Chrome 32-bit
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    echo [SUCCESS] Tim thay Chrome 32-bit
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" "http://127.0.0.1:5000"
    set CHROME_FOUND=1
    goto wait_server
)

:: Chrome trong user folder
if exist "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" (
    echo [SUCCESS] Tim thay Chrome user install
    start "" "%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe" "http://127.0.0.1:5000"
    set CHROME_FOUND=1
    goto wait_server
)

:: Không tìm thấy Chrome, dùng default browser
if %CHROME_FOUND%==0 (
    echo [WARNING] Khong tim thay Chrome, su dung trinh duyet mac dinh...
    start http://127.0.0.1:5000
)

:wait_server
echo.
echo ===============================================
echo [THANH CONG] FazzyTool Web Interface da khoi dong!
echo.
echo - URL: http://127.0.0.1:5000
echo - Trinh duyet: Chrome (neu co) hoac mac dinh
echo - Nhan Ctrl+C trong cua so nay de dung server
echo ===============================================
echo.
echo [INFO] Web server dang chay... Nhan phim bat ky de dung.
pause >nul

:: Dừng web server khi người dùng nhấn phím
echo [INFO] Dang dung web server...
taskkill /f /im python.exe /fi "WINDOWTITLE eq *web_app*" >nul 2>&1
taskkill /f /im py.exe /fi "WINDOWTITLE eq *web_app*" >nul 2>&1

echo [INFO] Web interface da dung.
pause 
