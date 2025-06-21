# 📝 Hướng dẫn sử dụng chức năng "Batch từ file prompt"

## 🎯 Mục đích
Tạo ảnh hàng loạt từ file .txt chứa các prompt có sẵn (không sử dụng AI Gemini).

## 📁 Vị trí file mẫu
- **File mẫu**: `sample_batch_prompts.txt` (trong thư mục gốc)
- **File của bạn**: Có thể để bất kỳ đâu, upload qua web interface

## 📋 Format file .txt

### Quy tắc:
1. Mỗi prompt bắt đầu bằng "Prompt" + số thứ tự
2. Nội dung prompt viết tiếng Anh (để kết quả tốt nhất)
3. Dòng trống để phân tách các prompt

### Ví dụ:
```
Prompt 1
A cute orange cat in garden

Prompt 2  
Beautiful sunset over ocean

Prompt 3
Futuristic robot in city
```

## 🚀 Cách sử dụng

### Bước 1: Tạo file .txt
- Copy file `sample_batch_prompts.txt` làm mẫu
- Hoặc tạo file mới theo format trên
- Lưu với encoding UTF-8

### Bước 2: Upload và xử lý
1. Mở **FazzyTool Web Interface**: `python START_WEB.bat`
2. Vào menu **"Batch từ file prompt"**
3. Upload file .txt của bạn
4. Nhấn **"Xem trước"** để kiểm tra
5. Nhấn **"Bắt đầu tạo ảnh"**

### Bước 3: Theo dõi kết quả
- Xem log real-time với màu sắc
- Theo dõi progress bar
- Xem ảnh trong gallery khi hoàn thành

## ⚙️ Cấu hình mặc định
- **Mỗi prompt**: 4 ảnh sinh ra → 4 ảnh tải về
- **Delay**: 5 giây giữa các prompt  
- **Giới hạn**: Tối đa 20 prompt/batch
- **Output**: Lưu vào thư mục `output/`

## 📊 Ước tính thời gian
- **5 prompt** = 20 ảnh = ~15 phút
- **10 prompt** = 40 ảnh = ~30 phút  
- **20 prompt** = 80 ảnh = ~60 phút

## 💡 Tips hay
1. **Test nhỏ trước**: Bắt đầu với 2-3 prompt
2. **Tên file rõ ràng**: Ví dụ `my_prompts_2025.txt`
3. **Kiểm tra cookie**: Đảm bảo đã cấu hình trong Settings
4. **Prompt quality**: Viết tiếng Anh, mô tả chi tiết

---
**🎨 Happy batch creating!** 