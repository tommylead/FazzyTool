# FazzyTool Web Interface

Giao diện web hiện đại cho FazzyTool - Công cụ AI tự động tạo ảnh và video từ Freepik Pikaso.

## 🚀 Khởi động nhanh

### Bước 1: Cài đặt dependencies (chỉ làm 1 lần)
```bash
# Double-click vào file INSTALL_REQUIREMENTS.bat
INSTALL_REQUIREMENTS.bat
```

### Bước 2: Khởi động web interface
```bash
# Double-click vào file START_WEB.bat
START_WEB.bat
```

**🌐 Trình duyệt sẽ TỰ ĐỘNG mở** tại **http://localhost:5000** sau 2 giây!

### Cách thủ công (nếu cần)
```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Chạy ứng dụng web (tự động mở browser)
python web_app.py
```

### Dừng web server
- Nhấn **Ctrl+C** trong terminal
- Hoặc double-click **STOP_WEB.bat**

## 📋 Tính năng chính

### 🏠 Trang chủ
- Dashboard tổng quan với thống kê
- Hiển thị ảnh và prompt gần đây
- Các liên kết nhanh đến các chức năng

### 🖼️ Tạo ảnh AI
- Nhập prompt tiếng Anh để tạo ảnh
- Tùy chọn số lượng ảnh sinh ra/tải về
- Hiển thị tiến trình realtime
- Preview và download ảnh đã tạo

### 🧠 Tạo prompt AI
- Nhập chủ đề tiếng Việt
- AI tự động sinh prompt tiếng Anh chi tiết
- Liên kết trực tiếp đến trang tạo ảnh
- Lưu trữ prompt đã tạo

### ⚙️ Cài đặt
- Cấu hình Google Gemini API key
- Hướng dẫn setup cookie Freepik
- Kiểm tra trạng thái hệ thống
- Test kết nối API/Cookie

### 📦 Batch Processing
- Hướng dẫn sử dụng CLI
- Thông tin về các file config
- Liên kết đến chức năng đơn lẻ

## 🔧 Cài đặt chi tiết

### 1. Cấu hình API Key
1. Vào trang **Cài đặt**
2. Lấy API key từ [Google AI Studio](https://makersuite.google.com/app/apikey)
3. Nhập và lưu API key

### 2. Cấu hình Cookie Freepik
1. Đăng nhập vào [Freepik.com](https://www.freepik.com) bằng Firefox
2. Nhấn F12 → tab Storage/Application → Cookies → freepik.com
3. Select All → Copy cookie JSON
4. Paste vào file `cookie_template.txt` giữa các marker
5. Kiểm tra lại trong trang Cài đặt

### 3. Test kết nối
- Sử dụng nút "Test Gemini API" và "Test Freepik Cookie"
- Đảm bảo cả hai đều hiển thị thành công

## 📁 Cấu trúc file

```
FazzyTool/
├── web_app.py              # Flask app chính
├── START_WEB.bat           # Script khởi động
├── templates/              # Template HTML
│   ├── base.html          # Template gốc
│   ├── index.html         # Trang chủ
│   ├── generate_image.html # Trang tạo ảnh
│   ├── generate_prompt.html # Trang tạo prompt
│   ├── settings.html      # Trang cài đặt
│   └── batch_process.html # Trang batch
├── output/                 # Thư mục ảnh đã tạo
├── prompts/               # Thư mục prompt đã tạo
├── config_template.txt    # File cấu hình API
└── cookie_template.txt    # File cấu hình cookie
```

## 🌟 Ưu điểm giao diện web

### So với CLI:
- ✅ Giao diện trực quan, dễ sử dụng
- ✅ Hiển thị tiến trình realtime
- ✅ Preview ảnh ngay lập tức
- ✅ Quản lý prompt/ảnh dễ dàng
- ✅ Không cần nhớ lệnh CLI

### Tính năng độc quyền:
- 🔄 Background processing
- 📊 Dashboard thống kê
- 🔗 Liên kết giữa các chức năng
- 📱 Responsive design
- 🎨 UI hiện đại với Bootstrap

## 🛠️ Tech Stack

- **Backend**: Flask 3.0.0
- **Frontend**: Bootstrap 5.3, Font Awesome 6.4
- **JavaScript**: Vanilla JS với modern features
- **Styling**: CSS3 với gradient và glassmorphism
- **Integration**: Tích hợp hoàn toàn với code hiện có

## 🔄 Tích hợp với CLI

Giao diện web **không thay thế** CLI mà bổ sung:
- Tất cả chức năng CLI vẫn hoạt động bình thường
- Giao diện web chỉ thêm UI cho các chức năng chính
- Batch processing phức tạp vẫn dùng CLI

## 🚨 Lưu ý quan trọng

1. **Không thay đổi logic cốt lõi**: Tất cả code xử lý giữ nguyên
2. **Cookie bảo mật**: Cookie chỉ lưu local, không gửi lên server
3. **Background tasks**: Task chạy background để không block UI
4. **File permissions**: Đảm bảo quyền ghi vào thư mục output/prompts

## 🐛 Troubleshooting

### Python không tìm thấy
**Triệu chứng**: "Python khong duoc tim thay!"
**Giải pháp**:
1. Tải Python từ: https://www.python.org/downloads/
2. **QUAN TRỌNG**: Khi cài đặt, tick vào "Add Python to PATH"
3. Khởi động lại máy tính
4. Thử chạy lại `START_WEB.bat`

### Dependencies bị lỗi
**Triệu chứng**: "ModuleNotFoundError" hoặc import errors
**Giải pháp**:
1. Chạy `INSTALL_REQUIREMENTS.bat` trước
2. Nếu vẫn lỗi, mở Command Prompt và chạy:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Port đã được sử dụng
**Triệu chứng**: "Address already in use"
**Giải pháp**:
```bash
# Đổi port trong web_app.py
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Flask không tìm thấy
```bash
pip install --upgrade flask==3.0.0
```

### Template không load
Đảm bảo thư mục `templates/` ở cùng level với `web_app.py`

### Cookie không hoạt động
1. Kiểm tra format JSON trong cookie_template.txt
2. Đảm bảo đăng nhập Freepik trước khi copy
3. Sử dụng Firefox (khuyến nghị)

### Web không mở được
**Triệu chứng**: Browser không load http://localhost:5000
**Giải pháp**:
1. Kiểm tra console terminal có lỗi không
2. Thử port khác: http://localhost:5001
3. Tắt Windows Defender/Antivirus tạm thời
4. Kiểm tra Windows Firewall

## 📞 Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra console browser (F12)
2. Xem log trong terminal chạy Flask
3. Đảm bảo tất cả dependencies đã cài đặt
4. Test lại CLI trước khi dùng web interface

---

🎉 **Chúc bạn sử dụng FazzyTool Web Interface hiệu quả!** 