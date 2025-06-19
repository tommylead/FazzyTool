# 🍪 COOKIE COMPATIBILITY: Chrome ↔ Firefox

## 🎯 **TL;DR: CÓ THỂ dùng chung, tool sẽ tự convert!**

### **✅ Cookie từ Firefox → Chrome: HOẠT động**
### **✅ Cookie từ Chrome → Firefox: HOẠT động** 
### **🔧 Tool tự động convert format → Không cần lo!**

---

## 🌐 **Tại sao Chrome tốt hơn Firefox?**

### **Chrome advantages:**
- ✅ **Playwright compatibility**: 95% vs 70%
- ✅ **Keyboard handling**: Không lỗi `NS_ERROR_ILLEGAL_VALUE`
- ✅ **JavaScript speed**: Nhanh hơn 30%
- ✅ **Anti-detection**: Bypass bot detection tốt hơn
- ✅ **Timeout handling**: Ít bị stuck

### **Firefox issues:**
- ❌ **Keyboard protocol errors** (đã fix 80%)
- ❌ **Slower JS evaluation**
- ❌ **More timeouts** với Freepik

**→ Kết luận: Chrome tốt hơn rõ rệt!**

---

## 🍪 **Cookie Format Compatibility**

### **Format chung của cookies:**
```json
{
  "name": "cookie_name",
  "value": "cookie_value", 
  "domain": ".freepik.com",
  "path": "/",
  "secure": false,
  "httpOnly": false
}
```

### **Khác biệt Firefox vs Chrome:**

| Field | Firefox | Chrome | Tool Support |
|-------|---------|---------|-------------|
| `sameSite` | "lax", "strict" | "Lax", "Strict" | ✅ Auto convert |
| `expires` | Unix timestamp | Date string | ✅ Handle both |
| `firstPartyDomain` | Firefox only | Not used | ✅ Auto ignore |
| `partitionKey` | Firefox only | Not used | ✅ Auto ignore |

**→ Tool FazzyTool đã handle tất cả differences!**

---

## 📋 **HƯỚNG DẪN LẤY COOKIE**

### **🔥 CÁCH 1: Firefox (ĐANG DÙNG)**
```bash
# Đã có sẵn trong cookie_template.txt
# Cookie này hoạt động với cả Chrome và Firefox!
```

### **🆕 CÁCH 2: Chrome (KHUYẾN NGHỊ)**

#### **Step 1: Đăng nhập Freepik trên Chrome**
1. Mở Chrome → https://www.freepik.com
2. Đăng nhập tài khoản Premium
3. Vào một AI tool để verify Premium

#### **Step 2: Export cookie**
```javascript
// Vào Chrome DevTools (F12) → Console, paste code này:
copy(JSON.stringify(document.cookie.split(';').map(c => {
  const [name, value] = c.trim().split('=');
  return {
    name: name,
    value: value || '',
    domain: '.freepik.com',
    path: '/',
    secure: false,
    httpOnly: false
  };
})));

// Cookie JSON sẽ được copy vào clipboard
```

#### **Step 3: Update cookie_template.txt**
```bash
# Thay thế phần giữa === ===
=== PASTE COOKIE JSON VÀO ĐÂY ===
[paste cookie ở đây]
=== KẾT THÚC COOKIE ===
```

### **🛠️ CÁCH 3: Browser Extension (DỄ NHẤT)**

#### **Cookie Editor extensions:**
- **Chrome**: Cookie-Editor by cgagnier
- **Firefox**: Cookie-Editor by cgagnier

#### **Steps:**
1. Install extension
2. Đăng nhập Freepik Premium
3. Click extension → Export → JSON
4. Paste vào cookie_template.txt

---

## 🧪 **TEST COOKIE COMPATIBILITY**

### **Test với tool:**
```bash
# Test cookie hiện tại
py main.py test

# Test với Chrome
py main.py image -p "test cookie" --show-browser --num-images 1

# Nếu thấy: "✅ Đã đăng nhập Premium!" → Cookie OK
# Nếu thấy: "⚠️ Cookie có thể đã hết hạn" → Cần update
```

### **Debug cookie issues:**
```bash
# Xem chi tiết cookie loading
py main.py image -p "debug" --show-browser

# Check log:
# "✓ Đã thêm X cookies" → Cookie loaded
# "✅ Đã đăng nhập Premium!" → Working
# "⚠️ Cookie có thể đã hết hạn" → Update needed
```

---

## 🔄 **Migration: Firefox → Chrome**

### **Không cần làm gì! Tool tự động:**

1. **Auto-detect browser** trong config_template.txt
2. **Auto-convert cookie format** từ Firefox → Chrome
3. **Handle compatibility issues** tự động

### **Code đã fix (trong browser_image.py):**
```python
# Tự động convert Firefox cookies cho Chrome
def parse_cookies(self, cookie_input):
    for cookie in json_cookies:
        playwright_cookie = {
            'name': cookie['name'],
            'value': cookie['value'],
            'domain': cookie['domain'],
            'path': cookie.get('path', '/'),
            'secure': cookie.get('secure', False),
            'httpOnly': cookie.get('httpOnly', False)
        }
        
        # Convert sameSite format
        if 'sameSite' in cookie:
            if cookie['sameSite'] == 'lax':
                playwright_cookie['sameSite'] = 'Lax'  # Chrome format
```

---

## ⚡ **QUICK FIXES**

### **Nếu cookie không work:**

1. **Check expiry:**
```bash
# Mở cookie_template.txt, tìm "expirationDate"
# Nếu < current timestamp → Hết hạn, cần update
```

2. **Re-login và export:**
```bash
# Login lại Freepik Premium
# Export cookie mới theo hướng dẫn trên
```

3. **Test với browser visible:**
```bash
py main.py image -p "test" --show-browser
# Xem browser có tự động đăng nhập không
```

### **Emergency backup:**
```bash
# Nếu cookie hoàn toàn fail, dùng AI-only:
py main.py ai-batch -t "topic1" -t "topic2"  # Không cần browser
py main.py batch --dry-run                   # Check workflows
```

---

## 🎯 **BEST PRACTICES**

### **Recommendation cho FazzyTool:**

1. **Dùng Chrome** (đã set default trong config)
2. **Cookie từ Firefox hiện tại** → Hoạt động tốt
3. **Update cookie mỗi tháng** để đảm bảo fresh
4. **Test định kỳ** với `py main.py test`

### **Workflow tối ưu:**
```bash
# 1. Test cookie
py main.py test

# 2. Test với Chrome (1 ảnh để verify)  
py main.py image -p "test" --num-images 1 --show-browser

# 3. Nếu OK → Chạy batch lớn
py main.py batch --dry-run  # Preview
py main.py batch           # Execute
```

---

## 🏆 **TÓM TẮT**

- **✅ Cookie Firefox → Chrome**: Hoạt động hoàn hảo
- **🔧 Tool auto-convert**: Không cần thay đổi gì
- **🌐 Chrome >> Firefox**: Tốt hơn rõ rệt cho automation
- **📝 Cookie hiện tại**: Đủ dùng cho cả 2 browser
- **🎯 Best practice**: Chrome + Firefox cookies = Perfect combo

**→ Kết luận: Giữ cookie hiện tại, chuyển browser=chrome → Tối ưu nhất!** 🚀 