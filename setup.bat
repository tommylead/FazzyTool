@echo off
chcp 65001 >nul
title FAZZYTOOL - Thiết lập lần đầu

echo.
echo ═══════════════════════════════════════════════════════════
echo 🔧 FAZZYTOOL - THIẾT LẬP LẦN ĐẦU
echo ═══════════════════════════════════════════════════════════
echo.

echo 📋 Chương trình này sẽ:
echo ├─ Cài đặt Python và các thư viện cần thiết
echo ├─ Tạo các file cấu hình mẫu
echo ├─ Thiết lập môi trường Playwright
echo └─ Chuẩn bị sẵn sàng để sử dụng
echo.

pause

echo.
echo ⏳ Bước 1/5: Kiểm tra Python...
echo ═══════════════════════════════════════════════════════════

py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không tìm thấy!
    echo.
    echo 💡 Hướng dẫn cài đặt Python:
    echo 1. Tải Python từ: https://www.python.org/downloads/
    echo 2. Chọn "Add Python to PATH" khi cài đặt
    echo 3. Chạy lại file này sau khi cài xong
    echo.
    pause
    exit /b 1
)

echo ✅ Python đã cài đặt:
py --version
echo.

echo ⏳ Bước 2/5: Cài đặt thư viện Python...
echo ═══════════════════════════════════════════════════════════

echo 📦 Đang cài đặt các thư viện cần thiết...
py -m pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Lỗi cài đặt thư viện!
    echo 💡 Thử chạy lệnh này thủ công:
    echo py -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo ✅ Đã cài đặt thư viện thành công!
echo.

echo ⏳ Bước 3/5: Cài đặt trình duyệt Playwright...
echo ═══════════════════════════════════════════════════════════

echo 🌐 Đang cài đặt Firefox cho Playwright...
py -m playwright install firefox

if errorlevel 1 (
    echo ❌ Lỗi cài đặt Playwright!
    echo 💡 Thử chạy lệnh này thủ công:
    echo py -m playwright install firefox
    pause
    exit /b 1
)

echo ✅ Đã cài đặt Playwright thành công!
echo.

echo ⏳ Bước 4/5: Tạo file cấu hình...
echo ═══════════════════════════════════════════════════════════

echo 📝 Đang tạo file .env...
py main.py setup

echo 📁 Tạo thư mục output...
if not exist "output" mkdir output

echo ✅ Đã tạo file cấu hình!
echo.

echo ⏳ Bước 5/5: Kiểm tra cài đặt...
echo ═══════════════════════════════════════════════════════════

echo 🧪 Test import thư viện...
py -c "import playwright; import google.generativeai; import click; print('✅ Tất cả thư viện OK!')"

if errorlevel 1 (
    echo ❌ Có lỗi với thư viện!
    pause
    exit /b 1
)

echo.
echo ═══════════════════════════════════════════════════════════
echo 🎉 THIẾT LẬP HOÀN TẤT!
echo ═══════════════════════════════════════════════════════════
echo.

echo ✅ FAZZYTOOL đã sẵn sàng sử dụng!
echo.
echo 📋 BƯỚC TIẾP THEO:
echo ├─ 1. Chỉnh sửa file: cookie_template.txt (paste cookie Freepik)
echo ├─ 2. Chỉnh sửa file: prompts_template.txt (viết prompt)
echo └─ 3. Chạy file: START.bat để bắt đầu
echo.

echo 💡 Hoặc đọc file: HUONG_DAN_SU_DUNG.txt để biết chi tiết
echo.

echo 🚀 Bấm phím bất kỳ để mở START.bat...
pause >nul

if exist "START.bat" (
    call START.bat
) else (
    echo ❌ File START.bat không tìm thấy!
    pause
) 