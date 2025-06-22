#!/usr/bin/env python3
"""
Script test video với browser visible và timeout ngắn
"""

import os
import sys
import json
import traceback
import time
from browser_video import FreepikVideoGenerator

def load_cookie_from_template():
    """Load cookies từ cookie_template.txt"""
    try:
        if not os.path.exists("cookie_template.txt"):
            print("❌ Không tìm thấy file cookie_template.txt")
            return None
            
        with open("cookie_template.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Tìm JSON trong markers
        start_marker = "=== PASTE COOKIE JSON VÀO ĐÂY ==="
        end_marker = "=== KẾT THÚC COOKIE ==="
        
        start_pos = content.find(start_marker)
        end_pos = content.find(end_marker)
        
        if start_pos == -1 or end_pos == -1:
            print("❌ Không tìm thấy markers trong cookie_template.txt")
            return None
        
        json_content = content[start_pos + len(start_marker):end_pos].strip()
        
        if not json_content:
            print("❌ Không có cookie JSON trong template")
            return None
        
        cookies = json.loads(json_content)
        print(f"✅ Load được {len(cookies)} cookies từ template")
        return cookies
        
    except Exception as e:
        print(f"❌ Lỗi load cookie: {e}")
        return None

def test_text_to_video_with_timeout():
    """Test Text-to-Video với timeout ngắn"""
    print("🎬 TEST TEXT-TO-VIDEO với TIMEOUT NGẮN")
    print("=" * 60)
    
    # Load cookies
    cookies = load_cookie_from_template()
    if not cookies:
        print("❌ Không thể load cookies, dừng test")
        return
    
    cookie_string = json.dumps(cookies)
    
    # Khởi tạo generator với browser visible
    print("🌐 Khởi tạo video generator (browser VISIBLE)...")
    generator = FreepikVideoGenerator(headless=False)  # Browser visible
    
    # Test prompt ngắn
    prompt = "A cute cat playing in the garden"
    print(f"📝 Prompt: {prompt}")
    
    try:
        print("🚀 Bắt đầu tạo video...")
        start_time = time.time()
        
        # Gọi function generate_video
        video_path = generator.generate_video(
            prompt=prompt,
            cookie_string=cookie_string,
            duration="5s",
            ratio="16:9",
            model="kling_master_2_1"
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ Thời gian thực hiện: {duration:.1f} giây")
        
        if video_path and os.path.exists(video_path):
            print(f"✅ Thành công! Video được lưu tại: {video_path}")
            file_size = os.path.getsize(video_path) / (1024 * 1024)  # MB
            print(f"📁 Kích thước file: {file_size:.2f} MB")
        else:
            print("❌ Không thể tạo video hoặc video không tồn tại")
            print(f"📁 Video path trả về: {video_path}")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        traceback.print_exc()
    
    print("\n🔍 Kiểm tra session folders:")
    try:
        output_dirs = [d for d in os.listdir("output") if d.startswith("text_to_video_")]
        if output_dirs:
            latest_dir = sorted(output_dirs)[-1]
            print(f"📁 Session folder mới nhất: output/{latest_dir}")
            
            session_path = os.path.join("output", latest_dir)
            if os.path.exists(session_path):
                files = os.listdir(session_path)
                print(f"📄 Files trong session: {files}")
            else:
                print("❌ Session folder không tồn tại")
        else:
            print("❌ Không có session folder nào")
    except Exception as e:
        print(f"❌ Lỗi kiểm tra session: {e}")

if __name__ == "__main__":
    test_text_to_video_with_timeout() 