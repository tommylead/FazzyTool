# 📝 Hướng Dẫn Sử Dụng Batch Prompts - FazzyTool

## 🎯 Mục đích
Chức năng Batch Prompts giúp bạn tạo nhiều ảnh cùng lúc từ một file chứa nhiều prompts khác nhau.

## 📋 Format File Prompts

### ✅ Format Đúng:
```
Prompt 1
Mô tả ảnh đầu tiên ở đây...

Prompt 2
Mô tả ảnh thứ hai ở đây...

Prompt 3
Mô tả ảnh thứ ba ở đây...
```

### ❌ Lưu Ý Quan Trọng:
- **BẮT BUỘC** bắt đầu mỗi prompt bằng "Prompt X" (X là số thứ tự)
- **KHÔNG** được thiếu dòng trống giữa các prompt
- **KHÔNG** sử dụng ký tự đặc biệt trong tên prompt
- File phải có đuôi `.txt`

## 🚀 Cách Sử Dụng

### Bước 1: Chuẩn bị file prompts
1. Tạo file `.txt` theo format ở trên
2. Hoặc sử dụng file mẫu có sẵn:
   - `batch_prompts_sample.txt` - Prompts đa dạng
   - `batch_prompts_vietnam.txt` - Chủ đề Việt Nam

### Bước 2: Upload và xử lý
1. Vào FazzyTool Web Interface: `http://127.0.0.1:5000`
2. Click vào tab **"Batch"** → **"Batch Prompts"**
3. Click **"Chọn file"** và upload file `.txt`
4. Click **"Bắt đầu xử lý"**

### Bước 3: Theo dõi tiến trình
- Chrome sẽ tự động mở và bắt đầu tạo ảnh
- Theo dõi progress trong web interface
- Mỗi prompt sẽ tạo **4 ảnh**
- Tất cả ảnh sẽ được tải về thư mục `output/`

## 📊 Thông Số Mặc Định
- **Số ảnh mỗi prompt**: 4 ảnh
- **Tải về**: Tất cả ảnh được tạo
- **Delay giữa prompts**: 5 giây
- **Thư mục lưu**: `output/`
- **Tên file**: `batch_XXX_prompt_name_timestamp.png`

## 💡 Tips Viết Prompts Hiệu Quả

### ✅ Prompt Tốt:
```
A cute kitten playing with yarn, watercolor style, soft lighting, 4k quality
```

### ❌ Prompt Kém:
```
cat
```

### 🎨 Các từ khóa hữu ích:
- **Style**: `watercolor, oil painting, digital art, photorealistic, cartoon`
- **Lighting**: `soft lighting, dramatic lighting, golden hour, neon lights`
- **Quality**: `4k, high resolution, detailed, sharp focus`
- **Mood**: `peaceful, dramatic, mysterious, cheerful, nostalgic`

## 🔧 Xử Lý Sự Cố

### ❌ "Không tìm thấy prompt nào"
- Kiểm tra format file (phải có "Prompt 1", "Prompt 2"...)
- Đảm bảo file có đuôi `.txt`

### ❌ "Có task khác đang chạy"
- Chờ task hiện tại hoàn thành
- Chỉ chạy 1 batch tại một thời điểm

### ❌ Chrome không mở
- Kiểm tra Chrome đã cài đặt
- Đảm bảo không có Chrome instance khác đang chạy Freepik

## 📁 File Mẫu Có Sẵn

1. **`batch_prompts_sample.txt`**
   - 10 prompts đa dạng
   - Các chủ đề: động vật, phong cảnh, sci-fi, nghệ thuật

2. **`batch_prompts_vietnam.txt`**
   - 10 prompts chủ đề Việt Nam
   - Các địa danh: Hạ Long, Hội An, Sapa, Hà Nội

## 🎯 Ví Dụ Hoàn Chình

```txt
Prompt 1
A majestic dragon flying over ancient mountains, fantasy art style, dramatic lighting, detailed scales, mythical atmosphere

Prompt 2
A peaceful Japanese garden with cherry blossoms, zen atmosphere, soft pink petals, traditional architecture, spring season

Prompt 3
A cyberpunk city at night, neon signs, flying cars, rain-soaked streets, futuristic buildings, purple and blue lighting
```

## ⚠️ Lưu Ý Quan Trọng

1. **Chỉ một batch tại một thời điểm** - Hệ thống chỉ xử lý 1 task cùng lúc
2. **Chrome sẽ mở tự động** - KHÔNG tắt Chrome khi đang xử lý
3. **Thời gian xử lý** - Khoảng 30-60 giây mỗi prompt
4. **Cần kết nối Internet** - Để truy cập Freepik AI
5. **Free tier có giới hạn** - Cân nhắc số lượng prompts

---

💡 **Mẹo**: Bắt đầu với file nhỏ (3-5 prompts) để test trước khi chạy batch lớn! 