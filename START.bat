@echo off
chcp 65001 >nul
title FAZZYTOOL - Menu chính

REM Kiểm tra Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python không tìm thấy! Chạy SETUP.bat trước.
    pause
    exit /b 1
)

:main
cls
echo.
echo ═══════════════════════════════════════════════════════════
echo 🚀 FAZZYTOOL - MENU CHÍNH
echo ═══════════════════════════════════════════════════════════
echo.

echo 📋 CHỌN CHỨC NĂNG:
echo.
echo 1. 🔥 Batch - Xử lý hàng loạt (KHUYÊN DÙNG)
echo 2. 🔍 Test Batch - Xem trước không chạy
echo 3. 🤖 AI - Tạo 1 ảnh/video bằng AI
echo 4. 📁 File - Tạo từ file prompt có sẵn
echo.
echo ⚙️  CÀI ĐẶT:
echo 5. 📝 Chỉnh Cookie Freepik
echo 6. ✍️  Chỉnh Prompt Template
echo 7. 🔧 Chỉnh Cấu hình
echo.
echo 📊 KHÁC:
echo 8. 📂 Xem kết quả
echo 9. 📖 Hướng dẫn sử dụng
echo 0. ❌ Thoát
echo.

set /p choice="Nhập lựa chọn (0-9): "

if "%choice%"=="1" goto batch
if "%choice%"=="2" goto test_batch
if "%choice%"=="3" goto ai_single
if "%choice%"=="4" goto file_single
if "%choice%"=="5" goto edit_cookie
if "%choice%"=="6" goto edit_prompt
if "%choice%"=="7" goto edit_config
if "%choice%"=="8" goto view_results
if "%choice%"=="9" goto help
if "%choice%"=="0" goto exit

echo ❌ Lựa chọn không hợp lệ!
timeout /t 2 >nul
goto main

:batch
echo.
echo 🔥 BATCH - XỬ LÝ HÀNG LOẠT
echo ═══════════════════════════════════════════════════════════
echo.
echo 💡 Đảm bảo đã cập nhật:
echo ├─ cookie_template.txt (Cookie Freepik)
echo └─ prompts_template.txt (Danh sách prompt)
echo.
echo 🚀 Bắt đầu xử lý batch...
py main.py batch
echo.
echo 📊 Hoàn tất! Kiểm tra thư mục output/ để xem kết quả.
pause
goto main

:test_batch
echo.
echo 🔍 TEST BATCH - XEM TRƯỚC
echo ═══════════════════════════════════════════════════════════
echo.
echo 📋 Chế độ này chỉ hiển thị thông tin, không tạo ảnh/video thật
py main.py batch --dry-run
pause
goto main

:ai_single
echo.
echo 🤖 AI - TẠO BẰNG TRÍ TUỆ NHÂN TẠO
echo ═══════════════════════════════════════════════════════════
echo.
set /p topic="Nhập chủ đề (VD: mèo dễ thương, logo công ty): "
if "%topic%"=="" (
    echo ❌ Vui lòng nhập chủ đề!
    timeout /t 2 >nul
    goto main
)
echo.
echo 🤖 Đang tạo với AI cho chủ đề: %topic%
py main.py ai -t "%topic%"
pause
goto main

:file_single
echo.
echo 📁 FILE - TẠO TỪ FILE CÓ SẴN
echo ═══════════════════════════════════════════════════════════
echo.
echo 📋 Các file prompt có sẵn:
if exist "sample_prompts.json" echo ├─ sample_prompts.json
if exist "prompts\landscape_prompt.json" echo ├─ prompts\landscape_prompt.json
if exist "prompts\portrait_prompt.json" echo └─ prompts\portrait_prompt.json
echo.
set /p filename="Nhập tên file (hoặc Enter để dùng sample_prompts.json): "
if "%filename%"=="" set filename=sample_prompts.json

if not exist "%filename%" (
    echo ❌ File không tồn tại: %filename%
    timeout /t 2 >nul
    goto main
)

echo.
echo 📁 Đang tạo từ file: %filename%
py main.py file -f "%filename%"
pause
goto main

:edit_cookie
echo.
echo 📝 CHỈNH COOKIE FREEPIK
echo ═══════════════════════════════════════════════════════════
echo.
echo 💡 File sẽ mở trong Notepad. Làm theo hướng dẫn trong file!
start "" notepad.exe cookie_template.txt
echo.
echo ✅ Đã mở file cookie_template.txt
echo 💾 Nhớ lưu file sau khi chỉnh sửa (Ctrl+S)
pause
goto main

:edit_prompt
echo.
echo ✍️ CHỈNH PROMPT TEMPLATE
echo ═══════════════════════════════════════════════════════════
echo.
echo 💡 File sẽ mở trong Notepad. Chọn 1 trong 3 cách viết prompt!
start "" notepad.exe prompts_template.txt
echo.
echo ✅ Đã mở file prompts_template.txt
echo 💾 Nhớ lưu file sau khi chỉnh sửa (Ctrl+S)
pause
goto main

:edit_config
echo.
echo 🔧 CHỈNH CẤU HÌNH
echo ═══════════════════════════════════════════════════════════
echo.
echo 💡 File sẽ mở trong Notepad. Chỉnh tốc độ, số lượng đồng thời!
start "" notepad.exe config_template.txt
echo.
echo ✅ Đã mở file config_template.txt
echo 💾 Nhớ lưu file sau khi chỉnh sửa (Ctrl+S)
pause
goto main

:view_results
echo.
echo 📂 XEM KẾT QUẢ
echo ═══════════════════════════════════════════════════════════
echo.
echo 📁 Mở thư mục output...
start "" explorer.exe output
echo.
echo ✅ Đã mở thư mục output
pause
goto main

:help
echo.
echo 📖 HƯỚNG DẪN SỬ DỤNG
echo ═══════════════════════════════════════════════════════════
echo.
echo 📄 Mở file hướng dẫn chi tiết...
start "" notepad.exe HUONG_DAN_SU_DUNG.txt
echo.
echo ✅ Đã mở file HUONG_DAN_SU_DUNG.txt
pause
goto main

:exit
echo.
echo 👋 CẢM ƠN BẠN ĐÃ SỬ DỤNG FAZZYTOOL!
echo.
echo 💡 Tips: 
echo ├─ Bookmark file START.bat để dễ tìm
echo ├─ Backup cookie khi nó hết hạn
echo └─ Chia sẻ tool này cho bạn bè nếu hữu ích!
echo.
timeout /t 3 >nul
exit 