# FAZZYTOOL

Tool tự động hóa việc sinh ảnh và video trên nền tảng [Freepik Pikaso](https://www.freepik.com/pikaso) thông qua trình duyệt tự động, dựa trên prompt do người dùng nhập hoặc do AI (Gemini API) sinh ra.

## 🚀 Tính năng chính

- **🖼️ Tạo ảnh AI**: Sử dụng Freepik AI Image Generator
- **🎬 Tạo video AI**: Chuyển ảnh thành video hoặc text-to-video
- **🤖 AI Prompt**: Tự động sinh prompt từ chủ đề tiếng Việt bằng Gemini AI
- **📦 Xử lý hàng loạt**: Batch processing với file template
- **🌐 Giao diện Web**: Web interface hiện đại với real-time tracking
- **⚙️ Cấu hình linh hoạt**: Tùy chỉnh số lượng ảnh, browser, timeout...

## 🔧 Cài đặt nhanh

### Bước 1: Cài đặt dependencies
```bash
# Chạy file .bat tự động
INSTALL_REQUIREMENTS.bat

# Hoặc cài thủ công
pip install -r requirements.txt
playwright install chromium firefox
```

### Bước 2: Khởi chạy
```bash
# Giao diện web (khuyến nghị)
START_WEB.bat

# Menu CLI
START.bat
```

## 🌐 Browser Configuration

**FazzyTool mặc định sử dụng Chrome (Chromium) để đảm bảo tính ổn định và hiệu suất tốt nhất.**

### Cấu hình browser trong `config_template.txt`:
```
=== BROWSER SETTINGS ===
browser=chrome               # Loại browser: chrome hoặc firefox (KHUYẾN NGHỊ: chrome)
headless=false               # true = chạy ẩn browser, false = hiển thị UI
show_browser=false           # Riêng cho Freepik operations
```

### Ưu điểm của Chrome:
- ✅ Tính ổn định cao hơn
- ✅ Hỗ trợ tốt hơn cho Freepik AI Generator
- ✅ Render JavaScript nhanh hơn
- ✅ Ít lỗi timeout

### Nếu gặp lỗi với Chrome:
1. Thử set `show_browser=true` trong config
2. Hoặc đổi sang `browser=firefox`
3. Chạy lại `INSTALL_REQUIREMENTS.bat`

## �� Cấu trúc project

```
/fazzytool/
├── main.py               # CLI chính để chọn chế độ
├── gemini_prompt.py      # Gửi yêu cầu tới Gemini để lấy JSON prompt
├── browser_image.py      # Điều khiển trình duyệt tạo ảnh Freepik
├── browser_video.py      # Điều khiển trình duyệt tạo video Freepik
├── prompt_loader.py      # Đọc prompt từ .txt / .json / .docx
├── .env                  # Chứa GEMINI_API_KEY và FREEPIK_COOKIE
├── requirements.txt      # Danh sách các thư viện cần thiết
└── output/               # Thư mục lưu ảnh/video kết quả
```

## Lưu ý

- Tool yêu cầu cookie Freepik Premium để vận hành. Cookie này cần được cập nhật trong file `.env`
- Để sử dụng chế độ AI, bạn cần API key của Google Gemini, cũng cần cập nhật vào file `.env`
- Video có thể mất nhiều thời gian hơn để tạo (tối đa 5 phút timeout)

## Cách lấy cookie Freepik

1. Đăng nhập vào tài khoản Freepik Premium của bạn
2. Mở DevTools (F12) > Tab Application > Storage > Cookies
3. Tìm domain freepik.com và sao chép toàn bộ cookie
4. Dán vào biến FREEPIK_COOKIE trong file .env 