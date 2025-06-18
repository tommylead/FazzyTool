# FAZZYTOOL - Công cụ tự động sinh ảnh và video AI

Tool tự động hóa việc sinh ảnh và video trên nền tảng Freepik Pikaso thông qua trình duyệt tự động, dựa trên prompt do người dùng nhập hoặc do AI (Gemini API) sinh ra.

## Hướng dẫn sử dụng

### Lần đầu sử dụng

1. Chạy file `setup.bat` để thiết lập ban đầu:
   - Cài đặt trình duyệt Firefox cho Playwright
   - Nhập API key Gemini và cookie Freepik vào file .env

### Sử dụng hàng ngày

#### **Chế độ Menu (Có giao diện):**
```bash
run.bat
```

#### **Chế độ Tự động (Không hiển thị trình duyệt):**
```bash
# Chạy hoàn toàn tự động với file mẫu
auto_run.bat

# Hoặc command line:
py main.py file --file sample_prompts.json --headless
py main.py ai --topic "cartoon dog and cat" --headless
```

#### **Các tùy chọn nâng cao:**
```bash
# Chỉ sinh ảnh
py main.py file --file sample_prompts.json --headless --no-video

# Chỉ sinh video  
py main.py file --file sample_prompts.json --headless --no-image

# Sử dụng prompt khác
py main.py file --file prompts/landscape_prompt.json --headless
```

### Yêu cầu

- **API key Gemini**: Đăng ký tại https://ai.google.dev/
- **Cookie Freepik**: Từ tài khoản Freepik Premium 

### Định dạng file prompt

Nếu sử dụng định dạng JSON:
```json
{
  "image_prompt": "Prompt cho tạo ảnh (bằng tiếng Anh)",
  "video_prompt": "Prompt cho tạo video (bằng tiếng Anh)",
  "video_duration": "5s", 
  "video_ratio": "1:1"
}
```

### Lưu ý

- Kết quả được lưu trong thư mục `output`
- Không đòi hỏi cài đặt Python riêng, tất cả đã được nhúng sẵn
- Cookie Freepik có thể hết hạn sau một thời gian, cần cập nhật qua `setup.bat` 