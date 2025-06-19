# 🎨 HƯỚNG DẪN SỬ DỤNG COMMANDS RIÊNG BIỆT

FazzyTool giờ đã có các commands riêng biệt để tạo ảnh và video!

## 📋 DANH SÁCH COMMANDS

### 1. 🎨 `image` - CHỈ TẠO ẢNH

```bash
python main.py image --topic "mèo dễ thương"
python main.py image --file "sample_prompts.json"  
python main.py image --prompt "cute cat sitting by window"
```

**Tùy chọn:**
- `--file` / `-f`: Đọc prompt từ file (.txt, .json, .docx)
- `--topic` / `-t`: Chủ đề tiếng Việt (AI sẽ sinh prompt)
- `--prompt` / `-p`: Prompt trực tiếp tiếng Anh
- `--num-images`: Số ảnh sinh ra (mặc định: 4)
- `--download-count`: Số ảnh tải về (mặc định: tất cả)
- `--filename-prefix`: Tiền tố tên file
- `--show-browser`: Hiển thị trình duyệt

### 2. 🎬 `video` - CHỈ TẠO VIDEO

```bash
# Tạo video từ prompt
python main.py video --topic "mèo con chạy nhảy"

# Tạo video từ ảnh có sẵn
python main.py video --image "output/my_cat.png"

# Tùy chỉnh video
python main.py video --topic "chó corgi" --duration 10s --ratio 16:9
```

**Tùy chọn:**
- `--file` / `-f`: Đọc prompt từ file
- `--topic` / `-t`: Chủ đề tiếng Việt (AI sinh prompt)
- `--prompt` / `-p`: Prompt trực tiếp tiếng Anh
- `--image` / `-i`: Ảnh để tạo video (image-to-video)
- `--duration`: Thời lượng (5s hoặc 10s)
- `--ratio`: Tỉ lệ khung hình (1:1, 16:9, 9:16)
- `--show-browser`: Hiển thị trình duyệt

### 3. 🎬🎨 `images-to-videos` - TẠO VIDEO TỪ NHIỀU ẢNH

```bash
# Tạo video từ tất cả ảnh trong thư mục output
python main.py images-to-videos

# Tùy chỉnh thư mục và prompts
python main.py images-to-videos --images-dir "my_images" --prompts-file "video_prompts.txt"
```

**Tùy chọn:**
- `--images-dir`: Thư mục chứa ảnh (mặc định: output)
- `--prompts-file`: File prompts (mỗi dòng một prompt)
- `--duration`: Thời lượng video
- `--ratio`: Tỉ lệ khung hình
- `--show-browser`: Hiển thị trình duyệt

## 🚀 CÁC VÍ DỤ THỰC TẾ

### 📸 Tạo ảnh chuyên nghiệp

```bash
# Tạo 8 ảnh, chỉ tải về 3 ảnh đẹp nhất
python main.py image --topic "cảnh hoàng hôn trên biển" --num-images 8 --download-count 3

# Tạo ảnh với tiền tố tên file
python main.py image --prompt "mountain landscape" --filename-prefix "landscape_"
```

### 🎬 Tạo video từ ảnh

```bash
# Tạo video 10s từ ảnh, tỉ lệ 16:9
python main.py video --image "output/sunset.png" --duration 10s --ratio 16:9

# Tạo video ngắn cho social media
python main.py video --image "output/cat.jpg" --duration 5s --ratio 9:16
```

### 🔄 Workflow hoàn chỉnh

```bash
# Bước 1: Tạo nhiều ảnh đẹp
python main.py image --topic "khu vườn hoa anh đào" --num-images 6 --download-count 4

# Bước 2: Tạo video từ tất cả ảnh
python main.py images-to-videos --duration 10s --ratio 16:9
```

## 📋 COMMANDS CŨ VẪN CÓ THỂ DÙNG

```bash
# Commands tổng hợp cũ vẫn hoạt động
python main.py ai --topic "mèo dễ thương"        # Tạo cả ảnh và video
python main.py file --file "sample_prompts.json" # Từ file
python main.py batch                             # Xử lý hàng loạt
python main.py setup                             # Thiết lập
python main.py test                              # Kiểm tra
```

## 💡 TIPS & TRICKS

### 🎯 Chọn command phù hợp

- **Chỉ cần ảnh**: Dùng `image`
- **Chỉ cần video**: Dùng `video`
- **Có ảnh rồi, muốn tạo video**: Dùng `video --image`
- **Có nhiều ảnh, muốn tạo video hàng loạt**: Dùng `images-to-videos`

### 📐 Chọn tỉ lệ khung hình

- **1:1**: Instagram post, Facebook
- **16:9**: YouTube, landscape video
- **9:16**: TikTok, Instagram Stories, YouTube Shorts

### ⏱️ Chọn thời lượng

- **5s**: Nhanh, tiết kiệm quota
- **10s**: Chi tiết hơn, chất lượng cao

### 🎨 Tối ưu số lượng ảnh

```bash
# Sinh nhiều để chọn lọc
python main.py image --topic "phong cảnh núi" --num-images 8 --download-count 3

# Sinh ít để tiết kiệm thời gian
python main.py image --topic "chó corgi" --num-images 2 --download-count 2
```

## 🔧 XỬ LÝ LỖI

### ❌ Lỗi thường gặp

1. **"Prompt rỗng"**: Kiểm tra file input hoặc topic
2. **"Không tìm thấy ảnh"**: Kiểm tra đường dẫn file ảnh
3. **"Cookie lỗi"**: Cập nhật cookie trong `cookie_template.txt`

### 🔍 Debug mode

```bash
python main.py image --topic "test" --show-browser
```

## 🎉 VÍ DỤ WORKFLOW HOÀN CHỈNH

```bash
# 1. Tạo ảnh cho nhiều chủ đề
python main.py image --topic "mèo orange dễ thương" --num-images 4
python main.py image --topic "cảnh hoàng hôn" --num-images 4
python main.py image --topic "hoa anh đào" --num-images 4

# 2. Tạo video từ tất cả ảnh vừa tạo
python main.py images-to-videos --duration 10s --ratio 16:9

# 3. Hoặc tạo video riêng cho ảnh đẹp nhất
python main.py video --image "output/best_sunset.png" --duration 10s
```

---

✨ **Chúc bạn tạo được những nội dung tuyệt vời với FazzyTool!** ✨ 