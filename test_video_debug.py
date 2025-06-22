"""
Script debug để test text-to-video với browser visible
"""

from browser_video import FreepikVideoGenerator
import json
import os

def load_cookies_from_template():
    """Load cookies từ cookie_template.txt"""
    try:
        if not os.path.exists("cookie_template.txt"):
            return None
            
        with open("cookie_template.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Tìm phần JSON cookie
        start_marker = "=== PASTE COOKIE JSON VÀO ĐÂY ==="
        end_marker = "=== KẾT THÚC COOKIE ==="
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            print("⚠️ Không tìm thấy marker cookie trong file")
            return None
        
        # Lấy phần JSON
        json_part = content[start_idx + len(start_marker):end_idx].strip()
        
        # Thử parse JSON
        try:
            cookies = json.loads(json_part)
            if isinstance(cookies, list) and len(cookies) > 0:
                print(f"✅ Đã load {len(cookies)} cookies từ cookie_template.txt")
                return json.dumps(cookies)
            else:
                print("⚠️ Cookie JSON không hợp lệ")
                return None
        except json.JSONDecodeError as e:
            print(f"⚠️ Lỗi parse JSON cookie: {e}")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi đọc cookie file: {e}")
        return None

def test_text_to_video():
    """Test text-to-video với browser visible để debug"""
    
    # Đọc cookie từ cookie_template.txt
    cookie_string = load_cookies_from_template()
    
    if not cookie_string:
        print("⚠️ Không tìm thấy cookie, sẽ chạy không đăng nhập")
    
    # Tạo video generator với browser visible
    generator = FreepikVideoGenerator(headless=False)  # headless=False để hiển thị browser
    
    # Test prompt đơn giản
    test_prompt = "A cute cat playing in a sunny garden"
    
    print(f"🎬 Testing text-to-video với prompt: {test_prompt}")
    print("🔍 Browser sẽ mở để bạn có thể quan sát...")
    
    try:
        result = generator.generate_video(
            prompt=test_prompt,
            cookie_string=cookie_string,
            duration="5s",
            ratio="16:9",
            model="kling_master_2_1"
        )
        
        if result:
            print(f"✅ Thành công! Video đã được tạo: {result}")
        else:
            print("❌ Thất bại! Không thể tạo video")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    test_text_to_video() 