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

echo 🎨 CHỌN LOẠI NỘI DUNG:
echo.
echo 1. 🖼️  TẠO ẢNH
echo 2. 🎬 TẠO VIDEO  
echo 3. 🎬🖼️  TẠO CẢ ẢNH VÀ VIDEO
echo.
echo 🔧 BATCH VA TOOLS:
echo 4. 🔥 Batch - Xử lý hàng loạt
echo 5. 🔍 Test Batch - Xem trước
echo.
echo ⚙️  CÀI ĐẶT:
echo 6. 📝 Chỉnh Cookie Freepik
echo 7. ✍️  Chỉnh Prompt Template
echo 8. 🔧 Chỉnh Cấu hình
echo.
echo 📊 KHÁC:
echo 9. 📂 Xem kết quả
echo 10. 📖 Hướng dẫn sử dụng
echo 0. ❌ Thoát
echo.

set /p choice="Nhập lựa chọn (0-10): "

if "%choice%"=="1" goto image_menu
if "%choice%"=="2" goto video_menu
if "%choice%"=="3" goto both_menu
if "%choice%"=="4" goto batch
if "%choice%"=="5" goto test_batch
if "%choice%"=="6" goto edit_cookie
if "%choice%"=="7" goto edit_prompt
if "%choice%"=="8" goto edit_config
if "%choice%"=="9" goto view_results
if "%choice%"=="10" goto help
if "%choice%"=="0" goto exit

echo ❌ Lựa chọn không hợp lệ!
timeout /t 2 >nul
goto main

REM ========== MENU TẠO ẢNH ==========
:image_menu
cls
echo.
echo ═══════════════════════════════════════════════════════════
echo 🖼️  MENU TẠO ẢNH
echo ═══════════════════════════════════════════════════════════
echo.

echo 📝 CHỌN CÁCH TẠO PROMPT:
echo.
echo 1. 🤖 AI - Nhập chủ đề (AI tự sinh prompt)
echo 2. ✍️  Prompt - Nhập prompt trực tiếp
echo 3. 📁 File - Từ file prompt có sẵn
echo.
echo 🔄 Quay lại menu chính (0)
echo.

set /p img_choice="Nhập lựa chọn (0-3): "

if "%img_choice%"=="1" goto image_ai
if "%img_choice%"=="2" goto image_prompt
if "%img_choice%"=="3" goto image_file
if "%img_choice%"=="0" goto main

echo ❌ Lựa chọn không hợp lệ!
timeout /t 2 >nul
goto image_menu

:image_ai
echo.
echo 🤖 TẠO ẢNH BẰNG AI
echo ═══════════════════════════════════════════════════════════
echo.
set /p topic="Nhập chủ đề (VD: mèo orange dễ thương, cảnh hoàng hôn): "
if "%topic%"=="" (
    echo ❌ Vui lòng nhập chủ đề!
    timeout /t 2 >nul
    goto image_menu
)

echo.
set /p num_images="Số ảnh sinh ra (mặc định 4): "
if "%num_images%"=="" set num_images=4

set /p download_count="Số ảnh tải về (mặc định tất cả): "
if "%download_count%"=="" (
    set download_param=
) else (
    set download_param=--download-count %download_count%
)

echo.
echo 🎨 Đang tạo ảnh với AI...
echo 📝 Chủ đề: %topic%
echo 🖼️  Sinh %num_images% ảnh
py main.py image --topic "%topic%" --num-images %num_images% %download_param%
pause
goto main

:image_prompt
echo.
echo ✍️ TẠO ẢNH TỪ PROMPT TRỰC TIẾP
echo ═══════════════════════════════════════════════════════════
echo.
set /p prompt="Nhập prompt (tiếng Anh): "
if "%prompt%"=="" (
    echo ❌ Vui lòng nhập prompt!
    timeout /t 2 >nul
    goto image_menu
)

echo.
set /p num_images="Số ảnh sinh ra (mặc định 4): "
if "%num_images%"=="" set num_images=4

set /p download_count="Số ảnh tải về (mặc định tất cả): "
if "%download_count%"=="" (
    set download_param=
) else (
    set download_param=--download-count %download_count%
)

echo.
echo 🎨 Đang tạo ảnh từ prompt...
echo 📝 Prompt: %prompt%
echo 🖼️  Sinh %num_images% ảnh
py main.py image --prompt "%prompt%" --num-images %num_images% %download_param%
pause
goto main

:image_file
echo.
echo 📁 TẠO ẢNH TỪ FILE
echo ═══════════════════════════════════════════════════════════
echo.
echo 📋 Các file prompt có sẵn:
if exist "sample_prompts.json" echo ├─ sample_prompts.json
if exist "prompts\landscape_prompt.json" echo ├─ prompts\landscape_prompt.json
if exist "prompts\portrait_prompt.json" echo └─ prompts\portrait_prompt.json
echo.
set /p filename="Nhập tên file (mặc định sample_prompts.json): "
if "%filename%"=="" set filename=sample_prompts.json

if not exist "%filename%" (
    echo ❌ File không tồn tại: %filename%
    timeout /t 2 >nul
    goto image_menu
)

echo.
echo 🎨 Đang tạo ảnh từ file: %filename%
py main.py image --file "%filename%"
pause
goto main

REM ========== MENU TẠO VIDEO ==========
:video_menu
cls
echo.
echo ═══════════════════════════════════════════════════════════
echo 🎬 MENU TẠO VIDEO
echo ═══════════════════════════════════════════════════════════
echo.

echo 📝 CHỌN CÁCH TẠO VIDEO:
echo.
echo 1. 🤖 AI - Nhập chủ đề (AI tự sinh prompt)
echo 2. ✍️  Prompt - Nhập prompt trực tiếp  
echo 3. 📁 File - Từ file prompt có sẵn
echo 4. 🖼️  Ảnh - Từ ảnh có sẵn (image-to-video)
echo 5. 📂 Batch - Từ nhiều ảnh trong thư mục
echo.
echo 🔄 Quay lại menu chính (0)
echo.

set /p vid_choice="Nhập lựa chọn (0-5): "

if "%vid_choice%"=="1" goto video_ai
if "%vid_choice%"=="2" goto video_prompt
if "%vid_choice%"=="3" goto video_file
if "%vid_choice%"=="4" goto video_from_image
if "%vid_choice%"=="5" goto video_batch
if "%vid_choice%"=="0" goto main

echo ❌ Lựa chọn không hợp lệ!
timeout /t 2 >nul
goto video_menu

:video_ai
echo.
echo 🤖 TẠO VIDEO BẰNG AI
echo ═══════════════════════════════════════════════════════════
echo.
set /p topic="Nhập chủ đề (VD: chó corgi chạy, cảnh núi hùng vĩ): "
if "%topic%"=="" (
    echo ❌ Vui lòng nhập chủ đề!
    timeout /t 2 >nul
    goto video_menu
)

echo.
echo ⏱️ Thời lượng video:
echo 1. 5 giây (nhanh)
echo 2. 10 giây (chi tiết)
set /p duration_choice="Chọn (1-2): "
if "%duration_choice%"=="2" (
    set duration=10s
) else (
    set duration=5s
)

echo.
echo 📐 Tỉ lệ khung hình:
echo 1. 1:1 (Instagram, Facebook)
echo 2. 16:9 (YouTube, Landscape)
echo 3. 9:16 (TikTok, Stories)
set /p ratio_choice="Chọn (1-3): "
if "%ratio_choice%"=="1" set ratio=1:1
if "%ratio_choice%"=="2" set ratio=16:9
if "%ratio_choice%"=="3" set ratio=9:16
if "%ratio%"=="" set ratio=16:9

echo.
echo 🎬 Đang tạo video với AI...
echo 📝 Chủ đề: %topic%
echo ⏱️ Thời lượng: %duration%
echo 📐 Tỉ lệ: %ratio%
py main.py video --topic "%topic%" --duration %duration% --ratio %ratio%
pause
goto main

:video_prompt
echo.
echo ✍️ TẠO VIDEO TỪ PROMPT TRỰC TIẾP
echo ═══════════════════════════════════════════════════════════
echo.
set /p prompt="Nhập prompt (tiếng Anh): "
if "%prompt%"=="" (
    echo ❌ Vui lòng nhập prompt!
    timeout /t 2 >nul
    goto video_menu
)

echo.
echo ⏱️ Thời lượng video:
echo 1. 5 giây (nhanh)
echo 2. 10 giây (chi tiết)
set /p duration_choice="Chọn (1-2): "
if "%duration_choice%"=="2" (
    set duration=10s
) else (
    set duration=5s
)

echo.
echo 📐 Tỉ lệ khung hình:
echo 1. 1:1 (Instagram, Facebook)
echo 2. 16:9 (YouTube, Landscape)
echo 3. 9:16 (TikTok, Stories)
set /p ratio_choice="Chọn (1-3): "
if "%ratio_choice%"=="1" set ratio=1:1
if "%ratio_choice%"=="2" set ratio=16:9
if "%ratio_choice%"=="3" set ratio=9:16
if "%ratio%"=="" set ratio=16:9

echo.
echo 🎬 Đang tạo video từ prompt...
echo 📝 Prompt: %prompt%
echo ⏱️ Thời lượng: %duration%
echo 📐 Tỉ lệ: %ratio%
py main.py video --prompt "%prompt%" --duration %duration% --ratio %ratio%
pause
goto main

:video_file
echo.
echo 📁 TẠO VIDEO TỪ FILE
echo ═══════════════════════════════════════════════════════════
echo.
echo 📋 Các file prompt có sẵn:
if exist "sample_prompts.json" echo ├─ sample_prompts.json
if exist "prompts\landscape_prompt.json" echo ├─ prompts\landscape_prompt.json
if exist "prompts\portrait_prompt.json" echo └─ prompts\portrait_prompt.json
echo.
set /p filename="Nhập tên file (mặc định sample_prompts.json): "
if "%filename%"=="" set filename=sample_prompts.json

if not exist "%filename%" (
    echo ❌ File không tồn tại: %filename%
    timeout /t 2 >nul
    goto video_menu
)

echo.
echo 🎬 Đang tạo video từ file: %filename%
py main.py video --file "%filename%"
pause
goto main

:video_from_image
echo.
echo 🖼️ TẠO VIDEO TỪ ẢNH
echo ═══════════════════════════════════════════════════════════
echo.
echo 📂 Mở thư mục output để xem ảnh có sẵn...
start "" explorer.exe output
echo.
set /p image_path="Nhập đường dẫn ảnh (VD: output/my_cat.png): "
if "%image_path%"=="" (
    echo ❌ Vui lòng nhập đường dẫn ảnh!
    timeout /t 2 >nul
    goto video_menu
)

if not exist "%image_path%" (
    echo ❌ Ảnh không tồn tại: %image_path%
    timeout /t 2 >nul
    goto video_menu
)

echo.
echo ⏱️ Thời lượng video:
echo 1. 5 giây (nhanh)
echo 2. 10 giây (chi tiết)
set /p duration_choice="Chọn (1-2): "
if "%duration_choice%"=="2" (
    set duration=10s
) else (
    set duration=5s
)

echo.
echo 📐 Tỉ lệ khung hình:
echo 1. 1:1 (Instagram, Facebook)
echo 2. 16:9 (YouTube, Landscape)
echo 3. 9:16 (TikTok, Stories)
set /p ratio_choice="Chọn (1-3): "
if "%ratio_choice%"=="1" set ratio=1:1
if "%ratio_choice%"=="2" set ratio=16:9
if "%ratio_choice%"=="3" set ratio=9:16
if "%ratio%"=="" set ratio=16:9

echo.
echo 🎬 Đang tạo video từ ảnh...
echo 🖼️  Ảnh: %image_path%
echo ⏱️ Thời lượng: %duration%
echo 📐 Tỉ lệ: %ratio%
py main.py video --image "%image_path%" --duration %duration% --ratio %ratio%
pause
goto main

:video_batch
echo.
echo 📂 TẠO VIDEO TỪ NHIỀU ẢNH
echo ═══════════════════════════════════════════════════════════
echo.
set /p images_dir="Thư mục ảnh (mặc định output): "
if "%images_dir%"=="" set images_dir=output

if not exist "%images_dir%" (
    echo ❌ Thư mục không tồn tại: %images_dir%
    timeout /t 2 >nul
    goto video_menu
)

echo.
echo ⏱️ Thời lượng video:
echo 1. 5 giây (nhanh)
echo 2. 10 giây (chi tiết)
set /p duration_choice="Chọn (1-2): "
if "%duration_choice%"=="2" (
    set duration=10s
) else (
    set duration=5s
)

echo.
echo 📐 Tỉ lệ khung hình:
echo 1. 1:1 (Instagram, Facebook)
echo 2. 16:9 (YouTube, Landscape)
echo 3. 9:16 (TikTok, Stories)
set /p ratio_choice="Chọn (1-3): "
if "%ratio_choice%"=="1" set ratio=1:1
if "%ratio_choice%"=="2" set ratio=16:9
if "%ratio_choice%"=="3" set ratio=9:16
if "%ratio%"=="" set ratio=16:9

echo.
echo 🎬 Đang tạo video từ nhiều ảnh...
echo 📂 Thư mục: %images_dir%
echo ⏱️ Thời lượng: %duration%
echo 📐 Tỉ lệ: %ratio%
py main.py images-to-videos --images-dir "%images_dir%" --duration %duration% --ratio %ratio%
pause
goto main

REM ========== MENU TẠO CẢ ẢNH VÀ VIDEO ==========
:both_menu
cls
echo.
echo ═══════════════════════════════════════════════════════════
echo 🎬🖼️ MENU TẠO CẢ ẢNH VÀ VIDEO
echo ═══════════════════════════════════════════════════════════
echo.

echo 📝 CHỌN CÁCH TẠO NỘI DUNG:
echo.
echo 1. 🤖 AI - Nhập chủ đề (AI tự sinh prompt)
echo 2. 📁 File - Từ file prompt có sẵn
echo.
echo 🔄 Quay lại menu chính (0)
echo.

set /p both_choice="Nhập lựa chọn (0-2): "

if "%both_choice%"=="1" goto both_ai
if "%both_choice%"=="2" goto both_file
if "%both_choice%"=="0" goto main

echo ❌ Lựa chọn không hợp lệ!
timeout /t 2 >nul
goto both_menu

:both_ai
echo.
echo 🤖 TẠO CẢ ẢNH VÀ VIDEO BẰNG AI
echo ═══════════════════════════════════════════════════════════
echo.
set /p topic="Nhập chủ đề (VD: mèo orange dễ thương): "
if "%topic%"=="" (
    echo ❌ Vui lòng nhập chủ đề!
    timeout /t 2 >nul
    goto both_menu
)

echo.
echo 🎬🖼️ Đang tạo cả ảnh và video với AI...
echo 📝 Chủ đề: %topic%
py main.py ai --topic "%topic%"
pause
goto main

:both_file
echo.
echo 📁 TẠO CẢ ẢNH VÀ VIDEO TỪ FILE
echo ═══════════════════════════════════════════════════════════
echo.
echo 📋 Các file prompt có sẵn:
if exist "sample_prompts.json" echo ├─ sample_prompts.json
if exist "prompts\landscape_prompt.json" echo ├─ prompts\landscape_prompt.json
if exist "prompts\portrait_prompt.json" echo └─ prompts\portrait_prompt.json
echo.
set /p filename="Nhập tên file (mặc định sample_prompts.json): "
if "%filename%"=="" set filename=sample_prompts.json

if not exist "%filename%" (
    echo ❌ File không tồn tại: %filename%
    timeout /t 2 >nul
    goto both_menu
)

echo.
echo 🎬🖼️ Đang tạo cả ảnh và video từ file: %filename%
py main.py file --file "%filename%"
pause
goto main

REM ========== CÁC MENU KHÁC ==========
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
start "" notepad.exe HUONG_DAN_SU_DUNG_COMMANDS.md
echo.
echo ✅ Đã mở file hướng dẫn mới
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