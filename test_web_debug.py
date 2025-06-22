#!/usr/bin/env python3
"""
Script test để debug web interface
"""

import requests
import json
import time

def test_web_api():
    """Test API generate-video trực tiếp"""
    print("🧪 TEST WEB API - Text-to-Video")
    print("=" * 50)
    
    # Prepare data giống như web interface gửi - PROMPT NGẮN
    data = {
        'mode': 'text-to-video',
        'prompt_mode': 'single', 
        'prompts': json.dumps(['A cute cat playing in the garden']),  # Prompt ngắn
        'duration': '5s',
        'ratio': '16:9',
        'model': 'kling_master_2_1',
        'show_browser': 'true',  # String vì từ form
        'repeat_count': '1'
    }
    
    print("📝 Data gửi:")
    for key, value in data.items():
        print(f"  {key}: {value}")
    
    try:
        print("\n🚀 Gửi request đến /api/generate-video...")
        response = requests.post('http://127.0.0.1:5000/api/generate-video', data=data)
        
        print(f"📡 Status code: {response.status_code}")
        print(f"📄 Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ Task ID: {task_id}")
            
            # Check task status continuously
            if task_id:
                print(f"\n🔍 Theo dõi task status...")
                for i in range(60):  # Theo dõi 5 phút (60 * 5s)
                    try:
                        status_response = requests.get(f'http://127.0.0.1:5000/api/task-status/{task_id}')
                        if status_response.status_code == 200:
                            status = status_response.json()
                            progress = status.get('progress', 0)
                            message = status.get('message', '')
                            task_status = status.get('status', 'unknown')
                            
                            print(f"[{i*5:03d}s] {progress:3d}% - {task_status} - {message}")
                            
                            if task_status == 'completed':
                                results = status.get('results', [])
                                print(f"🎉 THÀNH CÔNG! Đã tạo {len(results)} video: {results}")
                                break
                            elif task_status == 'error':
                                error_msg = status.get('message', 'Unknown error')
                                print(f"❌ LỖI: {error_msg}")
                                break
                        else:
                            print(f"❌ Status check failed: {status_response.status_code}")
                            
                    except Exception as e:
                        print(f"❌ Status check error: {e}")
                    
                    time.sleep(5)  # Chờ 5 giây
                    
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_web_api() 