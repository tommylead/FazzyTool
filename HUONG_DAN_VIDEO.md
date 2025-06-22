# 🎬 HƯỚNG DẪN VIDEO GENERATION - FAZZYTOOL

## ✅ HOÀN TOÀN CHUẨN BỊ SẴN SÀNG!

### 🚀 Test nhanh nhất
```bash
py main.py test-video
```

### 🎯 Tạo video đơn giản
```bash
py main.py video --prompt "A cute cat playing with a ball"
```

### 🛠️ Commands chính

| Command | Mô tả | Ví dụ |
|---------|-------|-------|
| `test-video` | Test nhanh | `py main.py test-video` |
| `video --prompt` | Tạo video từ text | `py main.py video --prompt "Dancing robot"` |
| `video --topic` | Tạo video từ chủ đề AI | `py main.py video --topic "Mèo dễ thương"` |
| `video --image` | Video từ ảnh | `py main.py video --prompt "Dancing" --image cat.jpg` |
| `sessions` | Xem video đã tạo | `py main.py sessions` |
| `debug-cookie` | Test cookie | `py main.py debug-cookie` |

### ⚙️ Tùy chọn nâng cao

```bash
# Video 10 giây, tỷ lệ 16:9, model master
py main.py video --prompt "Beautiful landscape" --duration 10s --ratio 16:9 --model kling_master_2_1

# Hiển thị browser để debug
py main.py video --prompt "Test video" --show-browser
```

### 🎛️ Settings

- **Duration**: `5s` (nhanh) hoặc `10s` (chất lượng)
- **Ratio**: `1:1` (social), `16:9` (YouTube), `9:16` (TikTok) 
- **Model**: `kling_master_2_1` (tốt nhất) hoặc `kling_2_1`

### 📁 Output

Videos được lưu trong: `output/text_to_video_YYYYMMDD_HHMMSS/`

### 🔧 Troubleshooting

1. **Cookie lỗi**: `py main.py debug-cookie`
2. **Video không tạo**: `py main.py test-video --show-browser`
3. **Cần help**: `py main.py video --help`

---
**🎉 Video Generation đã hoàn chỉnh 100%! Enjoy! 🎬** 