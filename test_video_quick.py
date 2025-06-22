#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test nhanh video generation với logic cải thiện
"""

import os
import sys
import time
from browser_video import FreepikVideoGenerator

def test_quick_video():
    """Test nhanh video generation"""
    print("🎬 Test nhanh Text-to-Video")
    print("=" * 50)
    
    # Load cookie từ template
    cookie_file = "cookie_template.txt"
    cookie_string = ""
    
    if os.path.exists(cookie_file):
        with open(cookie_file, 'r', encoding='utf-8') as f:
            cookie_string = f.read().strip()
        print(f"✅ Load được cookie từ {cookie_file}")
    else:
        print(f"⚠️ Không tìm thấy file cookie: {cookie_file}")
        return False
    
    # Khởi tạo generator với browser visible
    generator = FreepikVideoGenerator(headless=False, output_dir="output")
    
    # Test prompt ngắn
    prompt = "A cat playing with a ball"
    
    try:
        print(f"📝 Prompt: {prompt}")
        print("🚀 Bắt đầu test...")
        
        video_path = generator.generate_video(
            prompt=prompt,
            cookie_string=cookie_string,
            duration="5s",
            ratio="1:1",
            model="kling_master_2_1"
        )
        
        if video_path and os.path.exists(video_path):
            print(f"✅ Thành công! Video đã được tạo: {video_path}")
            return True
        else:
            print("❌ Video không được tạo")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

if __name__ == "__main__":
    success = test_quick_video()
    if success:
        print("\n🎉 Test thành công!")
    else:
        print("\n�� Test thất bại!") 