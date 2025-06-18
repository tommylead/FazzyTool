# FAZZYTOOL

Tool tự động hóa việc sinh ảnh và video trên nền tảng [Freepik Pikaso](https://www.freepik.com/pikaso) thông qua trình duyệt tự động, dựa trên prompt do người dùng nhập hoặc do AI (Gemini API) sinh ra.

## Tính năng chính

1. **Hai chế độ đầu vào:**
   - Nhập prompt trực tiếp từ file `text / json / docx`
   - Hoặc nhập **chủ đề tiếng Việt**, tool sẽ gọi Gemini API để sinh prompt tự động

2. **Tự động hóa sinh ảnh:**
   - Truy cập Freepik AI Image Generator
   - Sử dụng model `Flux Kontext Pro`
   - Dán prompt vào và sinh ảnh

3. **Tự động hóa sinh video:**
   - Truy cập Freepik AI Video Generator
   - Sử dụng model `Kling Master 2.1`
   - Hỗ trợ nhiều thời lượng và tỉ lệ khung hình

## Yêu cầu

- Python 3.10 trở lên
- Tài khoản Freepik Premium (để lấy cookie)
- API Key của Gemini (nếu muốn dùng chế độ AI)

## Cài đặt

1. **Clone repository:**
   ```bash
   git clone https://github.com/yourusername/fazzytool.git
   cd fazzytool
   ```

2. **Cài đặt thư viện:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Thiết lập môi trường:**
   ```bash
   python main.py setup
   ```
   Sau đó, cập nhật file `.env` với API key Gemini và cookie Freepik của bạn.

4. **Cài đặt trình duyệt cho Playwright:**
   ```bash
   playwright install
   ```

## Cách sử dụng

### 1. Sinh ảnh và video từ chủ đề bằng AI

```bash
python main.py ai --topic "Khu vườn nhiệt đới với hoa lan đầy màu sắc"
```

Tùy chọn:
- `--no-image`: Chỉ sinh video, không sinh ảnh
- `--no-video`: Chỉ sinh ảnh, không sinh video
- `--show-browser`: Hiển thị trình duyệt khi đang chạy (hữu ích để debug)

### 2. Sinh ảnh và video từ file prompt

```bash
python main.py file --file /path/to/prompt.json
```

Định dạng file JSON:
```json
{
  "image_prompt": "Tropical garden with colorful orchids...",
  "video_prompt": "Tropical garden with colorful orchids...",
  "video_duration": "5s",
  "video_ratio": "1:1"
}
```

Bạn cũng có thể sử dụng file .txt hoặc .docx, nhưng cần lưu ý rằng trong trường hợp đó, nội dung sẽ được sử dụng làm prompt cho cả ảnh và video, với các thông số mặc định.

## Cấu trúc thư mục

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