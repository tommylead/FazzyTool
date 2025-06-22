@echo off
chcp 65001 >nul
echo.
echo ========================================
echo 🎬 FAZZYTOOL QUICK TEST - VIDEO GENERATION
echo ========================================
echo.
echo 🚀 Đang test video generation với prompt mặc định...
echo.
py main.py test-video
echo.
echo ========================================
echo 📋 Các command hữu ích khác:
echo ========================================
echo.
echo 🔧 Test cookie: py main.py debug-cookie
echo 🎬 Tạo video:   py main.py video --prompt "Your prompt here"
echo 🎨 Tạo ảnh:     py main.py image --prompt "Your prompt here"
echo 📊 Xem session: py main.py sessions
echo 📖 Help:       py main.py --help
echo.
pause 