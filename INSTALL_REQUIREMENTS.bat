@echo off
title FazzyTool - Cai dat Dependencies
color 0B

echo.
echo ===============================================
echo    FAZZYTOOL - CAI DAT DEPENDENCIES
echo ===============================================
echo.

:: Tìm Python
set PYTHON_CMD=

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto found_python
)

py --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=py
    goto found_python
)

python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto found_python
)

echo [ERROR] Khong tim thay Python!
echo [INFO] Vui long cai dat Python truoc: https://www.python.org/downloads/
pause
exit /b 1

:found_python
echo [SUCCESS] Tim thay Python: %PYTHON_CMD%
%PYTHON_CMD% --version
echo.

:: Kiểm tra file requirements.txt
if not exist "requirements.txt" (
    echo [ERROR] Khong tim thay file requirements.txt!
    pause
    exit /b 1
)

:: Cài đặt requirements
echo [INFO] Cai dat tat ca dependencies tu requirements.txt...
echo.
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Co loi khi cai dat dependencies!
    echo [INFO] Thu cai dat tung package rieng le...
    echo.
    
    :: Cài đặt từng package một
    %PYTHON_CMD% -m pip install playwright==1.44.0
    %PYTHON_CMD% -m pip install google-generativeai==0.7.2
    %PYTHON_CMD% -m pip install python-docx==1.1.0
    %PYTHON_CMD% -m pip install python-dotenv==1.0.0
    %PYTHON_CMD% -m pip install requests==2.31.0
    %PYTHON_CMD% -m pip install click==8.1.7
    %PYTHON_CMD% -m pip install colorama==0.4.6
    %PYTHON_CMD% -m pip install tqdm==4.66.1
    %PYTHON_CMD% -m pip install flask==3.0.0
)

echo.
echo [SUCCESS] Hoan thanh cai dat dependencies!
echo.
echo [INFO] Cai dat Playwright browsers...
echo [INFO] Cai dat Chrome (chromium)...
%PYTHON_CMD% -m playwright install chromium
echo [INFO] Cai dat Firefox (fallback)...
%PYTHON_CMD% -m playwright install firefox

echo.
echo ===============================================
echo [HOAN THANH] Tat ca dependencies da duoc cai dat!
echo.
echo Ban co the chay:
echo - START_WEB.bat: De mo giao dien web
echo - START.bat: De mo menu CLI
echo ===============================================
echo.
pause 