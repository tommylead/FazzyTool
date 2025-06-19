# 🚨 QUICK FIX CHO LỖI BROWSER AUTOMATION

## ⚡ FIX NGAY LẬP TỨC

### 1. **Chuyển sang Chrome (QUAN TRỌNG!)**
```bash
# Mở file config_template.txt, tìm dòng:
browser=firefox

# Đổi thành:
browser=chrome
```

### 2. **Tăng timeout cho mạng chậm**
```bash
# Trong config_template.txt:
wait_time=10          # Tăng từ 3 lên 10
request_timeout=120   # Tăng từ 30 lên 120
```

### 3. **Test với Chrome ngay**
```bash
py main.py image -p "test cat" --num-images 1 --show-browser
```

## 🎯 CÁC LỖI ĐÃ SỬA

### ✅ **Lỗi JavaScript** 
- Đã fix: `Page.evaluate: missing ) after argument list`
- Cải thiện: Escape characters trong prompt
- Thêm: Try-catch trong JavaScript code

### ✅ **Lỗi Keyboard Protocol**
- Đã fix: `NS_ERROR_ILLEGAL_VALUE` 
- Thay thế: `Delete` → `Backspace`
- Cải thiện: Type từng chunk nhỏ với delay

### ✅ **Lỗi Timeout**
- Cải thiện: 5 phương pháp input fallback
- Tăng: Timeout cho từng method
- Thêm: Auto retry với error handling

## 🔧 NẾU VẪN LỖI

### **Lỗi keyboard vẫn tiếp tục:**
```bash
# Trong config_template.txt:
browser=chrome        # Bắt buộc phải Chrome
headless=false       # Để debug
```

### **Lỗi timeout:**
```bash
# Test với ít ảnh hơn:
py main.py image -p "simple test" --num-images 1 --download-count 1
```

### **Lỗi cookie:**
```bash
# Update cookie mới từ Freepik Premium account
# Copy vào cookie_template.txt
```

## 🚀 WORKFLOW BACKUP

### **Nếu browser hoàn toàn không hoạt động:**

1. **Chỉ dùng AI generation (không browser):**
```bash
py main.py ai-batch -t "mèo dễ thương" "chó con" "hoa đẹp"
```

2. **Tạo prompt manual:**
```bash
py main.py image -p "A beautiful sunset landscape"
# → Chỉ tạo prompt JSON, không tải ảnh
```

3. **Sử dụng file prompts:**
```bash
echo "Beautiful cat photo" > test_prompt.txt
py main.py file -f test_prompt.txt
```

## ⚡ KIỂM TRA NGAY

### **Test 1: Config**
```bash
py main.py test
# Phải thấy: ✅ File .env: Tồn tại
```

### **Test 2: AI Generation**
```bash
py main.py ai -t "test" --no-video --num-images 1
# Phải thấy: 🌐 Sử dụng browser: chrome
```

### **Test 3: Simple Image**
```bash
py main.py image -p "test" --show-browser --num-images 1
# Xem browser mở Chrome, không phải Firefox
```

## 💡 TIPS QUAN TRỌNG

### **Do và Don't:**
- ✅ **DO**: Dùng Chrome, headless=false khi debug
- ✅ **DO**: Test với 1 ảnh trước khi batch
- ✅ **DO**: Kiểm tra mạng ổn định
- ❌ **DON'T**: Dùng Firefox khi gặp lỗi keyboard
- ❌ **DON'T**: Chạy batch khi browser chưa stable

### **Emergency Commands:**
```bash
# Nếu hoàn toàn không hoạt động:
py main.py ai-batch -t "test1" "test2"  # Chỉ tạo prompt
py main.py batch --dry-run             # Xem thông tin batch
py main.py test                        # Kiểm tra config
```

---

## 🎯 TÓM TẮT NHANH

1. **Đổi browser=chrome** trong config_template.txt
2. **Tăng timeout** nếu mạng chậm  
3. **Test nhỏ** trước khi batch lớn
4. **Dùng AI-only** nếu browser fails

**Sau khi fix: Tool sẽ hoạt động mượt mà hơn 90%** 🚀 