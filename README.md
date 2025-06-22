# FAZZYTOOL - Công cụ tự động sinh ảnh và video AI từ Freepik Pikaso

🎨 **Tool tự động hóa việc sinh ảnh và video trên nền tảng Freepik Pikaso** thông qua trình duyệt tự động, dựa trên prompt do người dùng hoặc Gemini AI sinh ra.

## ✨ Tính năng chính

### 🎬 **Video Generation (MỚI!)**
- **Text-to-Video**: Tạo video từ prompt text
- **Image-to-Video**: Tạo video từ ảnh có sẵn
- **Multiple Models**: Hỗ trợ Kling AI 2.1 và Kling Master 2.1
- **Flexible Settings**: Tùy chỉnh duration (5s/10s) và ratio (1:1/16:9/9:16)
- **Session Management**: Lưu trữ có tổ chức theo session

### 🎨 **Image Generation**
- Sinh ảnh từ prompt text
- Batch processing
- Tùy chỉnh số lượng ảnh
- Download selective

### 🤖 **AI Integration**
- Tích hợp Gemini AI để sinh prompt tự động
- Fallback manual prompt khi API limit
- Batch processing từ topic list

## 🚀 Installation & Setup

### 1. Clone repository
```bash
git clone <repository-url>
cd FazzyTool
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Setup Cookie Authentication
Cập nhật cookie trong file `cookie_template.txt`:

```
=== HƯỚNG DẪN COOKIE ===
1. Truy cập https://www.freepik.com/pikaso/ai-image-generator
2. Đăng nhập tài khoản Freepik
3. Mở Developer Tools (F12) → Application → Cookies
4. Copy all cookies và paste vào đây dưới dạng JSON array

=== PASTE COOKIE JSON VÀO ĐÂY ===
[
  {
    "name": "GR_TOKEN",
    "value": "your_token_here",
    "domain": ".freepik.com",
    "path": "/",
    "secure": true,
    "httpOnly": false,
    "sameSite": "Lax"
  }
  // ... thêm các cookies khác
]
=== KẾT THÚC COOKIE ===
```

### 4. Setup Gemini API (Optional)
Tạo file `.env`:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

## 📖 Usage

### 🎬 Video Generation

#### Test nhanh video generation
```bash
py main.py test-video
py main.py test-video --prompt "A dog running in the park"
```

#### Tạo video từ prompt trực tiếp
```bash
py main.py video --prompt "A cat playing with a ball"
py main.py video --prompt "Dancing robot" --duration 10s --ratio 16:9
```

#### Tạo video từ topic (sử dụng AI)
```bash
py main.py video --topic "Mèo dễ thương"
py main.py video --topic "Chó con chạy trong công viên"
```

#### Image-to-Video
```bash
py main.py video --prompt "Dancing gracefully" --image path/to/image.jpg
```

#### Video với model và settings tùy chỉnh
```bash
py main.py video --prompt "Sunset landscape" --model kling_master_2_1 --duration 10s --ratio 16:9
```

### 🎨 Image Generation

#### Tạo ảnh từ prompt
```bash
py main.py image --prompt "Beautiful sunset landscape"
py main.py image --prompt "Cat portrait" --num-images 6 --download-count 3
```

#### Tạo ảnh từ topic AI
```bash
py main.py image --topic "Mèo dễ thương"
```

### 🔄 Combined Image + Video
```bash
py main.py ai --topic "Chó con dễ thương" --image --video
py main.py file --file sample_prompts.json --image --video
```

### 📊 Session Management
```bash
py main.py sessions  # Xem thống kê sessions
```

### 🛠️ Debug & Testing
```bash
py main.py debug-cookie  # Test cookie authentication
py main.py test          # Test toàn bộ hệ thống
```

## 📁 Project Structure

```
FazzyTool/
├── main.py                 # CLI chính
├── browser_video.py        # Video generation engine (MỚI!)
├── browser_image.py        # Image generation engine  
├── gemini_prompt.py        # AI prompt generation
├── prompt_loader.py        # Prompt file handling
├── batch_processor.py      # Batch processing
├── cookie_template.txt     # Cookie configuration
├── output/                 # Generated files
│   ├── text_to_video_*/   # Video sessions
│   └── text_to_image_*/   # Image sessions
├── prompts/               # AI generated prompts
└── templates/             # Web interface templates
```

## 🎯 Quick Examples

### Workflow đơn giản nhất:
```bash
# 1. Test cookie
python main.py debug-cookie

# 2. Test video generation
python main.py test-video

# 3. Tạo video thật
python main.py video --prompt "A beautiful landscape"
```

### Workflow advanced:
```bash
# 1. Tạo prompt AI batch
python main.py ai-batch -t "Mèo dễ thương" -t "Chó con" -t "Cảnh thiên nhiên"

# 2. Batch process tất cả
python main.py batch

# 3. Xem kết quả
python main.py sessions
```

## 🔧 Configuration

### Video Settings
- **Models**: `kling_2_1`, `kling_master_2_1`
- **Duration**: `5s`, `10s`  
- **Ratio**: `1:1`, `16:9`, `9:16`

### Browser Settings
- `--show-browser`: Hiển thị trình duyệt (debug mode)
- `--headless`: Chạy ẩn (production mode)

## 🐛 Troubleshooting

### Cookie Issues
```bash
python main.py debug-cookie  # Test authentication
```

### Video Generation Issues
```bash
python main.py test-video --show-browser  # Debug với visible browser
```

### API Issues
- Check Gemini API key trong `.env`
- Sử dụng manual prompt khi API limit

## 📈 Recent Updates

### ✅ Video Generation Hoàn Chỉnh (v2.0)
- **Model Selection**: Kling AI 2.1 Master working 100%
- **Download Logic**: Button-based download fallback
- **Wait Logic**: Duration detection + banner filtering  
- **Session Management**: Organized output structure
- **Error Handling**: Comprehensive error recovery

### ✅ Authentication Cải Thiện
- Cookie template parsing
- Multi-format cookie support
- Authentication status detection

## 💡 Tips

1. **Chạy test đầu tiên**: `python main.py test-video`
2. **Sử dụng show-browser** khi debug: `--show-browser`
3. **Kling Master 2.1** cho chất lượng tốt nhất
4. **Duration 5s** cho test nhanh, **10s** cho production
5. **Ratio 1:1** cho social media, **16:9** cho YouTube

## 🔗 Links

- [Freepik Pikaso](https://www.freepik.com/pikaso/ai-video-generator)
- [Gemini API](https://makersuite.google.com/app/apikey)

---

**🎉 FazzyTool v2.0 - Video Generation Ready! 🎬** 