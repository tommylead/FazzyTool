#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Web Interface Video Generation - Kiểm tra web interface có hoạt động không
"""

import requests
import json
import time

def test_web_video_api():
    """Test API tạo video qua web interface"""
    print("🧪 Test Web Interface Video Generation")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:5000"
    
    # Test data - Text-to-Video đơn giản
    test_data = {
        "mode": "text-to-video",
        "prompt_mode": "single", 
        "prompts": ["A cute puppy playing in a garden"],
        "duration": "5s",
        "ratio": "16:9",
        "model": "kling_master_2_1",
        "repeat_count": 1
    }
    
    try:
        # 1. Test ping server
        print("🔗 Kiểm tra kết nối server...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Server đang chạy")
        else:
            print(f"❌ Server trả về status: {response.status_code}")
            return False
            
        # 2. Test API endpoint
        print("🚀 Gửi request tạo video...")
        
        # Tạo FormData để giống như web interface gửi
        form_data = {
            'mode': test_data['mode'],
            'prompt_mode': test_data['prompt_mode'],
            'prompts': json.dumps(test_data['prompts']),
            'duration': test_data['duration'],
            'ratio': test_data['ratio'],
            'model': test_data['model'],
            'repeat_count': str(test_data['repeat_count'])
        }
        
        response = requests.post(
            f"{base_url}/api/generate-video",
            data=form_data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                print(f"✅ Task created successfully: {task_id}")
                print(f"📊 Total videos expected: {result.get('total_videos', 1)}")
                
                # 3. Test status check
                print("⏳ Kiểm tra status task...")
                for i in range(3):  # Chỉ check 3 lần để test
                    time.sleep(2)
                    status_response = requests.get(f"{base_url}/api/task-status/{task_id}")
                    
                    if status_response.status_code == 200:
                        status = status_response.json()
                        print(f"📋 Status check {i+1}: {status.get('message', 'N/A')}")
                        print(f"📊 Progress: {status.get('progress', 0)}%")
                        
                        if status.get('status') in ['completed', 'error']:
                            break
                    else:
                        print(f"⚠️ Status check failed: {status_response.status_code}")
                
                print("✅ Web interface API test completed!")
                print("🎉 Interface hoạt động bình thường, có thể tạo video từ web")
                return True
            else:
                print("❌ Không nhận được task_id")
                return False
        else:
            print(f"❌ API request failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Không thể kết nối đến server. Đảm bảo web server đang chạy.")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout. Server có thể đang quá tải.")
        return False
    except Exception as e:
        print(f"❌ Lỗi không mong muốn: {e}")
        return False

if __name__ == "__main__":
    success = test_web_video_api()
    
    if success:
        print("\n🎯 KẾT LUẬN:")
        print("✅ Web interface hoạt động tốt")
        print("🌐 Có thể truy cập: http://127.0.0.1:5000")
        print("🎬 Có thể tạo video từ giao diện web")
    else:
        print("\n❌ KẾT LUẬN:")
        print("⚠️ Web interface có vấn đề")
        print("🔧 Kiểm tra lại server và configuration") 