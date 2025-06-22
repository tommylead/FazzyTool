#!/usr/bin/env python3
"""
FAZZYTOOL WEB INTERFACE - Giao diện web cho FazzyTool

Giao diện web hiện đại để tương tác với FazzyTool thông qua trình duyệt
"""

import os
import json
import asyncio
import threading
import shutil
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
from pathlib import Path
import uuid
import time

# Import các module của FazzyTool
from prompt_loader import PromptLoader
from gemini_prompt import GeminiPromptGenerator
from browser_image import FreepikImageGenerator
from browser_video import FreepikVideoGenerator
from batch_processor import BatchProcessor

app = Flask(__name__)
app.secret_key = 'fazzytool_secret_key_2024'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Tạo các thư mục cần thiết
os.makedirs('uploads', exist_ok=True)
os.makedirs('output', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Store cho các task đang chạy
running_tasks = {}

def load_cookie_from_template():
    """Load cookie từ cookie_template.txt"""
    try:
        if os.path.exists("cookie_template.txt"):
            with open("cookie_template.txt", "r", encoding="utf-8") as f:
                content = f.read()
                
            start_marker = "=== PASTE COOKIE JSON VÀO ĐÂY ==="
            end_marker = "=== KẾT THÚC COOKIE ==="
            
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)
            
            if start_idx != -1 and end_idx != -1:
                cookie_json = content[start_idx + len(start_marker):end_idx].strip()
                
                if cookie_json and cookie_json.startswith('['):
                    cookies = json.loads(cookie_json)
                    
                    # Fix sameSite values để tương thích với Playwright
                    for cookie in cookies:
                        if 'sameSite' in cookie:
                            if cookie['sameSite'] == 'no_restriction':
                                cookie['sameSite'] = 'None'
                            elif cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                                cookie['sameSite'] = 'Lax'
                        
                        # Remove các fields không cần thiết
                        unwanted_fields = ['firstPartyDomain', 'partitionKey', 'storeId', 'hostOnly']
                        for field in unwanted_fields:
                            cookie.pop(field, None)
                            
                        # Rename expirationDate thành expires nếu có
                        if 'expirationDate' in cookie:
                            cookie['expires'] = cookie.pop('expirationDate')
                    
                    return cookies
        return []
    except Exception as e:
        print(f"⚠️ Lỗi khi load cookie: {e}")
        return []

def run_image_generation_task(task_id, prompt, num_images, download_count, filename_prefix):
    """Chạy task tạo ảnh trong background"""
    try:
        running_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Đang khởi tạo...',
            'results': []
        }
        
        generator = FreepikImageGenerator(headless=False)  # Luôn visible
        cookies = load_cookie_from_template()
        cookie_string = json.dumps(cookies) if cookies else None
        
        running_tasks[task_id]['progress'] = 20
        running_tasks[task_id]['message'] = 'Đang tạo ảnh...'
        
        downloaded_files = generator.generate_image(
            prompt=prompt,
            cookie_string=cookie_string,
            num_images=num_images,
            download_count=download_count,
            filename_prefix=filename_prefix
        )
        
        running_tasks[task_id]['status'] = 'completed'
        running_tasks[task_id]['progress'] = 100
        running_tasks[task_id]['message'] = f'Hoàn thành! Đã tạo {len(downloaded_files)} ảnh'
        running_tasks[task_id]['results'] = downloaded_files
        
    except Exception as e:
        running_tasks[task_id]['status'] = 'error'
        running_tasks[task_id]['message'] = f'Lỗi: {str(e)}'

def run_ai_prompt_task(task_id, topic):
    """Chạy task tạo prompt AI trong background"""
    try:
        running_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Đang khởi tạo AI...',
            'results': []
        }
        
        gemini_generator = GeminiPromptGenerator()
        
        running_tasks[task_id]['progress'] = 30
        running_tasks[task_id]['message'] = 'Đang tạo prompt...'
        
        prompt_data = gemini_generator.generate_prompt(topic)
        
        if prompt_data:
            # Lưu prompt vào file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_topic = safe_topic.replace(' ', '_')
            
            prompt_filename = f"prompts/prompt_{timestamp}_{safe_topic}.json"
            
            os.makedirs("prompts", exist_ok=True)
            with open(prompt_filename, "w", encoding="utf-8") as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            
            running_tasks[task_id]['status'] = 'completed'
            running_tasks[task_id]['progress'] = 100
            running_tasks[task_id]['message'] = 'Hoàn thành! Prompt đã được tạo'
            running_tasks[task_id]['results'] = [prompt_data]
            running_tasks[task_id]['filename'] = prompt_filename
        else:
            running_tasks[task_id]['status'] = 'error'
            running_tasks[task_id]['message'] = 'Không thể tạo prompt'
        
    except Exception as e:
        running_tasks[task_id]['status'] = 'error'
        running_tasks[task_id]['message'] = f'Lỗi: {str(e)}'

def run_video_generation_task(task_id, mode, prompt_mode, prompts, duration, ratio, model, image_path=None, image_paths=None, repeat_count=1):
    """Chạy task tạo video trong background"""
    import signal
    import threading
    
    def timeout_handler():
        """Handler để timeout task sau 8 phút"""
        time.sleep(480)  # 8 phút (ngắn hơn để tránh stuck)
        if task_id in running_tasks and running_tasks[task_id]['status'] == 'running':
            print(f"⏰ [Task {task_id}] TIMEOUT sau 8 phút - force stop")
            running_tasks[task_id]['status'] = 'error'
            running_tasks[task_id]['message'] = 'Timeout: Video generation quá lâu (>8 phút), tự động dừng'
    
    # Khởi tạo timeout thread
    timeout_thread = threading.Thread(target=timeout_handler, daemon=True)
    timeout_thread.start()
    
    try:
        # Khởi tạo task status
        total_videos = len(prompts) * repeat_count
        running_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Đang khởi tạo...',
            'results': [],
            'current_video': 0,
            'total_videos': total_videos,
            'current_prompt': '',
            'current_prompt_index': 0,
            'total_prompts': len(prompts)
        }
        
        print(f"🎬 [Task {task_id}] Bắt đầu tạo video - Mode: {mode}, Prompt mode: {prompt_mode}")
        print(f"📝 [Task {task_id}] Prompts: {prompts}")
        print(f"⚙️ [Task {task_id}] Settings: {duration}, {ratio}, {model}, browser=visible")
        
        # Khởi tạo video generator
        running_tasks[task_id]['message'] = 'Đang khởi tạo video generator...'
        print(f"🔧 [Task {task_id}] Khởi tạo FreepikVideoGenerator (luôn visible mode)")
        
        video_generator = FreepikVideoGenerator(headless=False)  # Luôn visible
        print(f"✅ [Task {task_id}] Video generator đã khởi tạo thành công")
        
        # Load cookies
        running_tasks[task_id]['message'] = 'Đang load cookies...'
        print(f"🍪 [Task {task_id}] Đang load cookies từ template...")
        
        cookies = load_cookie_from_template()
        cookie_string = json.dumps(cookies) if cookies else None
        
        if cookies:
            print(f"✅ [Task {task_id}] Load được {len(cookies)} cookies")
        else:
            print(f"⚠️ [Task {task_id}] Không có cookies - có thể bị lỗi đăng nhập")
        
        running_tasks[task_id]['progress'] = 5
        running_tasks[task_id]['message'] = 'Đang mở trình duyệt...'
        
        # Tạo video cho từng prompt
        results = []
        video_counter = 0
        
        for prompt_index, prompt in enumerate(prompts):
            running_tasks[task_id]['current_prompt_index'] = prompt_index + 1
            running_tasks[task_id]['current_prompt'] = prompt[:50] + "..." if len(prompt) > 50 else prompt
            
            # Determine current image path for this prompt
            current_image_path = None
            if prompt_mode == 'batch-multi-images' and image_paths:
                # Case 3: Each prompt has its own image
                current_image_path = image_paths[prompt_index] if prompt_index < len(image_paths) else None
            elif image_path:
                # Case 1 & 2: Same image for all prompts
                current_image_path = image_path
            
            # Tạo video theo repeat_count cho mỗi prompt
            for repeat_index in range(repeat_count):
                video_counter += 1
                running_tasks[task_id]['current_video'] = video_counter
                
                progress = 5 + (video_counter * 90 // total_videos)
                running_tasks[task_id]['progress'] = progress
                
                # Update message based on mode
                if prompt_mode == 'batch-multi-images':
                    image_name = os.path.basename(current_image_path) if current_image_path else 'N/A'
                    running_tasks[task_id]['message'] = f'Prompt {prompt_index + 1}/{len(prompts)} + {image_name}: {prompt[:30]}...'
                else:
                    running_tasks[task_id]['message'] = f'Prompt {prompt_index + 1}/{len(prompts)}, Video {repeat_index + 1}/{repeat_count}: {prompt[:30]}...'
                
                try:
                    print(f"🎬 [Task {task_id}] Bắt đầu tạo video {video_counter}/{total_videos}")
                    
                    # Thêm timeout cho từng video (5 phút)
                    video_start_time = time.time()
                    video_timeout = 300  # 5 phút
                    
                    if current_image_path and os.path.exists(current_image_path):
                        # Tạo video từ ảnh (Case 1, 2, 3)
                        print(f"🖼️ [Task {task_id}] Tạo video từ ảnh: {os.path.basename(current_image_path)}")
                        video_path = video_generator.generate_video_from_image(
                            image_path=current_image_path,
                            prompt=prompt,
                            cookie_string=cookie_string,
                            duration=duration,
                            ratio=ratio,
                            model=model
                        )
                    else:
                        # Tạo video từ text (Case 4)
                        print(f"📝 [Task {task_id}] Tạo video từ text prompt")
                        video_path = video_generator.generate_video(
                            prompt=prompt,
                            cookie_string=cookie_string,
                            duration=duration,
                            ratio=ratio,
                            model=model
                        )
                    
                    video_end_time = time.time()
                    video_duration = video_end_time - video_start_time
                    print(f"⏱️ [Task {task_id}] Video {video_counter} hoàn thành sau {video_duration:.1f}s")
                    
                    if video_path:
                        if os.path.exists(video_path):
                            # Video file tồn tại - copy vào output
                            base_name = os.path.splitext(os.path.basename(video_path))[0]
                            extension = os.path.splitext(video_path)[1]
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            
                            # Tạo safe prompt name
                            safe_prompt = "".join(c for c in prompt[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
                            safe_prompt = safe_prompt.replace(' ', '_')
                            
                            # Create filename based on mode
                            if prompt_mode == 'batch-multi-images':
                                image_name = os.path.splitext(os.path.basename(current_image_path))[0] if current_image_path else 'noimg'
                                filename = f"{base_name}_p{prompt_index + 1:02d}_{image_name}_{safe_prompt}_{timestamp}{extension}"
                            else:
                                filename = f"{base_name}_p{prompt_index + 1:02d}_v{repeat_index + 1}_{safe_prompt}_{timestamp}{extension}"
                            
                            # Copy file vào thư mục output chính
                            output_path = os.path.join("output", filename)
                            
                            if not os.path.exists("output"):
                                os.makedirs("output")
                            
                            shutil.copy2(video_path, output_path)
                            results.append(filename)
                            
                            running_tasks[task_id]['results'] = results.copy()
                            print(f"✅ [Task {task_id}] Đã tạo video {video_counter}/{total_videos}: {filename}")
                            
                        elif os.path.isdir(video_path):
                            # Trả về session folder - có thể có screenshot hoặc partial result
                            print(f"📁 [Task {task_id}] Session folder: {video_path}")
                            session_files = os.listdir(video_path) if os.path.exists(video_path) else []
                            
                            # Tìm file screenshot hoặc video trong session
                            valid_files = [f for f in session_files if f.endswith(('.mp4', '.png', '.jpg', '.jpeg'))]
                            
                            if valid_files:
                                # Copy files từ session vào output chính
                                for file in valid_files:
                                    src_path = os.path.join(video_path, file)
                                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    safe_prompt = "".join(c for c in prompt[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
                                    safe_prompt = safe_prompt.replace(' ', '_')
                                    
                                    # Tạo tên file mới
                                    file_ext = os.path.splitext(file)[1]
                                    new_filename = f"partial_p{prompt_index + 1:02d}_v{repeat_index + 1}_{safe_prompt}_{timestamp}{file_ext}"
                                    
                                    output_path = os.path.join("output", new_filename)
                                    if not os.path.exists("output"):
                                        os.makedirs("output")
                                    
                                    shutil.copy2(src_path, output_path)
                                    results.append(new_filename)
                                    
                                    print(f"📸 [Task {task_id}] Đã lưu partial result {video_counter}/{total_videos}: {new_filename}")
                                
                                running_tasks[task_id]['results'] = results.copy()
                            else:
                                print(f"⚠️ [Task {task_id}] Session folder trống: {video_path}")
                        else:
                            print(f"❌ [Task {task_id}] Video path không hợp lệ: {video_path}")
                    else:
                        print(f"❌ [Task {task_id}] Không thể tạo video {video_counter}/{total_videos}")
                        
                except Exception as video_error:
                    print(f"❌ Lỗi tạo video {video_counter}/{total_videos}: {video_error}")
                    continue
        
        # Cập nhật trạng thái cuối
        if results:
            # Đếm video thực tế và partial results
            video_count = len([f for f in results if f.endswith('.mp4')])
            screenshot_count = len([f for f in results if f.endswith(('.png', '.jpg', '.jpeg'))])
            
            running_tasks[task_id]['status'] = 'completed'
            running_tasks[task_id]['progress'] = 100
            running_tasks[task_id]['current_video'] = total_videos
            
            if video_count > 0 and screenshot_count > 0:
                running_tasks[task_id]['message'] = f'Hoàn thành! {video_count} video + {screenshot_count} screenshot từ {len(prompts)} prompt'
            elif video_count > 0:
                running_tasks[task_id]['message'] = f'Hoàn thành! Đã tạo {video_count}/{total_videos} video từ {len(prompts)} prompt'
            else:
                running_tasks[task_id]['message'] = f'Hoàn thành! Đã tạo {screenshot_count} screenshot từ {len(prompts)} prompt (video download lỗi)'
                
            running_tasks[task_id]['results'] = results
            print(f"🎉 [Task {task_id}] {running_tasks[task_id]['message']}")
        else:
            running_tasks[task_id]['status'] = 'error'
            running_tasks[task_id]['message'] = 'Không thể tạo video hoặc screenshot nào'
            print(f"❌ [Task {task_id}] Task thất bại hoàn toàn")
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"❌ [Task {task_id}] LỖI NGHIÊM TRỌNG trong run_video_generation_task:")
        print(f"❌ [Task {task_id}] Exception: {str(e)}")
        print(f"❌ [Task {task_id}] Traceback:\n{error_details}")
        
        running_tasks[task_id]['status'] = 'error'
        running_tasks[task_id]['message'] = f'Lỗi: {str(e)}'
        running_tasks[task_id]['error_details'] = error_details

def parse_prompts_from_file(file_content):
    """Parse các prompt từ nội dung file txt"""
    prompts = []
    lines = file_content.split('\n')
    
    current_prompt = None
    current_content = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Kiểm tra nếu là dòng đầu prompt (Prompt 1, Prompt 2, ...)
        if line.lower().startswith('prompt ') and any(char.isdigit() for char in line):
            # Lưu prompt trước đó nếu có
            if current_prompt and current_content:
                prompts.append({
                    'name': current_prompt,
                    'content': ' '.join(current_content).strip()
                })
            
            # Bắt đầu prompt mới
            current_prompt = line
            current_content = []
        else:
            # Thêm nội dung vào prompt hiện tại
            if current_prompt:
                current_content.append(line)
    
    # Lưu prompt cuối cùng
    if current_prompt and current_content:
        prompts.append({
            'name': current_prompt,
            'content': ' '.join(current_content).strip()
        })
    
    return prompts

def run_batch_prompts_task(task_id, prompts_list):
    """Chạy task tạo ảnh hàng loạt từ danh sách prompts trong background"""
    try:
        total_prompts = len(prompts_list)
        running_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Đang khởi tạo...',
            'results': [],
            'current_prompt': '',
            'completed_prompts': 0,
            'total_prompts': total_prompts,
            'logs': []
        }
        
        def add_log(message):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            running_tasks[task_id]['logs'].append(log_entry)
            running_tasks[task_id]['message'] = message
            print(log_entry)  # Also print to console
        
        add_log("🚀 Bắt đầu tạo ảnh hàng loạt từ file prompt...")
        
        # Khởi tạo image generator
        image_generator = FreepikImageGenerator(headless=False)  # Luôn visible
        cookies = load_cookie_from_template()
        cookie_string = json.dumps(cookies) if cookies else None
        
        add_log(f"📋 Tổng cộng: {total_prompts} prompt")
        add_log(f"🎨 Mỗi prompt: 4 ảnh sinh ra, 4 ảnh tải về")
        
        for i, prompt_item in enumerate(prompts_list, 1):
            try:
                prompt_name = prompt_item['name']
                prompt_content = prompt_item['content']
                
                running_tasks[task_id]['current_prompt'] = f"{prompt_name}: {prompt_content[:50]}..."
                add_log(f"\n🔄 [{i}/{total_prompts}] Xử lý {prompt_name}")
                add_log(f"📝 Prompt: {prompt_content}")
                
                # Tạo filename prefix từ prompt name
                safe_name = "".join(c for c in prompt_name if c.isalnum() or c in (' ', '-', '_')).strip()
                safe_name = safe_name.lower().replace(' ', '_').replace('prompt_', 'p')[:20]
                filename_prefix = f"batch_{i:03d}_{safe_name}"
                
                add_log(f"🎨 Đang tạo 4 ảnh từ prompt...")
                
                downloaded_files = image_generator.generate_image(
                    prompt=prompt_content,
                    cookie_string=cookie_string,
                    num_images=4,
                    download_count=4,  # Tải tất cả 4 ảnh
                    filename_prefix=filename_prefix
                )
                
                if downloaded_files:
                    add_log(f"✅ Đã tạo {len(downloaded_files)} ảnh cho {prompt_name}")
                    running_tasks[task_id]['results'].append({
                        'prompt_name': prompt_name,
                        'prompt_content': prompt_content,
                        'files': downloaded_files,
                        'index': i
                    })
                else:
                    add_log(f"❌ Không thể tạo ảnh cho {prompt_name}")
                
                # Cập nhật progress
                running_tasks[task_id]['completed_prompts'] = i
                progress = int((i / total_prompts) * 100)
                running_tasks[task_id]['progress'] = progress
                
                # Delay giữa các prompts để tránh spam
                if i < total_prompts:
                    add_log(f"⏳ Chờ 5 giây trước khi xử lý prompt tiếp theo...")
                    time.sleep(5)
                
            except Exception as e:
                add_log(f"❌ Lỗi xử lý {prompt_name}: {str(e)}")
                continue
        
        # Hoàn thành
        running_tasks[task_id]['status'] = 'completed'
        running_tasks[task_id]['progress'] = 100
        total_images = sum(len(r['files']) for r in running_tasks[task_id]['results'])
        add_log(f"🎉 HOÀN THÀNH! Đã tạo tổng cộng {total_images} ảnh từ {len(running_tasks[task_id]['results'])} prompt")
        
    except Exception as e:
        running_tasks[task_id]['status'] = 'error'
        running_tasks[task_id]['message'] = f'Lỗi hệ thống: {str(e)}'
        running_tasks[task_id]['logs'].append(f"❌ LỖI HỆ THỐNG: {str(e)}")

def run_batch_video_task(task_id, prompts_list, duration, ratio, model, delay_between):
    """Chạy task tạo video hàng loạt trong background"""
    try:
        total_prompts = len(prompts_list)
        running_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Đang khởi tạo...',
            'results': [],
            'current_prompt': '',
            'completed_prompts': 0,
            'total_prompts': total_prompts,
            'logs': []
        }
        
        def add_log(message):
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}"
            running_tasks[task_id]['logs'].append(log_entry)
            running_tasks[task_id]['message'] = message
            print(log_entry)  # Also print to console
        
        add_log("🎬 Bắt đầu tạo video hàng loạt...")
        
        # Khởi tạo video generator
        video_generator = FreepikVideoGenerator(headless=False)  # Luôn visible
        cookies = load_cookie_from_template()
        cookie_string = json.dumps(cookies) if cookies else None
        
        add_log(f"📋 Tổng cộng: {total_prompts} prompts")
        add_log(f"🎥 Thời lượng: {duration}, Tỷ lệ: {ratio}, Model: {model}")
        
        for i, prompt_item in enumerate(prompts_list, 1):
            try:
                prompt_name = prompt_item['name']
                prompt_content = prompt_item['content']
                
                running_tasks[task_id]['current_prompt'] = f"{prompt_name}: {prompt_content[:50]}..."
                add_log(f"\n🔄 [{i}/{total_prompts}] Xử lý {prompt_name}")
                add_log(f"📝 Prompt: {prompt_content}")
                
                add_log(f"🎬 Đang tạo video từ prompt...")
                
                # Tạo video từ text prompt
                video_path = video_generator.generate_video(
                    prompt=prompt_content,
                    cookie_string=cookie_string,
                    duration=duration,
                    ratio=ratio,
                    model=model
                )
                
                if video_path:
                    add_log(f"✅ Đã tạo video cho {prompt_name}: {os.path.basename(video_path)}")
                    running_tasks[task_id]['results'].append({
                        'prompt_name': prompt_name,
                        'prompt_content': prompt_content,
                        'files': [os.path.basename(video_path)],
                        'index': i
                    })
                else:
                    add_log(f"❌ Không thể tạo video cho {prompt_name}")
                
                # Cập nhật progress
                running_tasks[task_id]['completed_prompts'] = i
                progress = int((i / total_prompts) * 100)
                running_tasks[task_id]['progress'] = progress
                
                # Delay giữa các prompts để tránh spam
                if i < total_prompts:
                    add_log(f"⏳ Chờ {delay_between} giây trước khi xử lý prompt tiếp theo...")
                    time.sleep(delay_between)
                
            except Exception as e:
                add_log(f"❌ Lỗi xử lý {prompt_name}: {str(e)}")
                continue
        
        # Hoàn thành
        running_tasks[task_id]['status'] = 'completed'
        running_tasks[task_id]['progress'] = 100
        total_videos = sum(len(r['files']) for r in running_tasks[task_id]['results'])
        add_log(f"🎉 HOÀN THÀNH! Đã tạo tổng cộng {total_videos} video từ {len(running_tasks[task_id]['results'])} prompt")
        
    except Exception as e:
        running_tasks[task_id]['status'] = 'error'
        running_tasks[task_id]['message'] = f'Lỗi hệ thống: {str(e)}'
        running_tasks[task_id]['logs'].append(f"❌ LỖI HỆ THỐNG: {str(e)}")

@app.route('/')
def index():
    """Trang chủ"""
    return render_template('index.html')

@app.route('/generate-image')
def generate_image_page():
    """Trang tạo ảnh"""
    return render_template('generate_image.html')

@app.route('/generate-prompt')
def generate_prompt_page():
    """Trang tạo prompt AI"""
    return render_template('generate_prompt.html')

@app.route('/batch-process')
def batch_process_page():
    """Trang xử lý batch"""
    return render_template('batch_process.html')

@app.route('/generate-video')
def generate_video_page():
    """Trang tạo video AI"""
    return render_template('generate_video.html')


@app.route('/settings')
def settings_page():
    """Trang cài đặt"""
    # Kiểm tra cookie và config
    has_cookie = bool(load_cookie_from_template())
    
    config_status = False
    api_key = ""
    try:
        if os.path.exists("config_template.txt"):
            with open("config_template.txt", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("api_key="):
                        api_key = line.split("=", 1)[1].strip()
                        config_status = bool(api_key and api_key != "YOUR_API_KEY_HERE")
                        break
    except:
        pass
    
    return render_template('settings.html', 
                         has_cookie=has_cookie, 
                         config_status=config_status,
                         api_key=api_key)

@app.route('/api/generate-image', methods=['POST'])
def api_generate_image():
    """API endpoint tạo ảnh"""
    try:
        data = request.json
        prompt = data.get('prompt', '').strip()
        num_images = data.get('num_images', 4)
        download_count = data.get('download_count')
        filename_prefix = data.get('filename_prefix', '')
        # Browser luôn visible nên không cần show_browser parameter
        
        if not prompt:
            return jsonify({'error': 'Prompt không được để trống'}), 400
        
        # Tạo task ID
        task_id = str(uuid.uuid4())
        
        # Chạy task trong background
        thread = threading.Thread(
            target=run_image_generation_task,
            args=(task_id, prompt, num_images, download_count, filename_prefix)
        )
        thread.start()
        
        return jsonify({'task_id': task_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-prompt', methods=['POST'])
def api_generate_prompt():
    """API endpoint tạo prompt AI"""
    try:
        data = request.json
        topic = data.get('topic', '').strip()
        
        if not topic:
            return jsonify({'error': 'Chủ đề không được để trống'}), 400
        
        # Tạo task ID
        task_id = str(uuid.uuid4())
        
        # Chạy task trong background
        thread = threading.Thread(
            target=run_ai_prompt_task,
            args=(task_id, topic)
        )
        thread.start()
        
        return jsonify({'task_id': task_id})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-video', methods=['POST'])
def api_generate_video():
    """API endpoint tạo video AI"""
    try:
        mode = request.form.get('mode', 'text-to-video')
        prompt_mode = request.form.get('prompt_mode', 'single')
        duration = request.form.get('duration', '5s')
        ratio = request.form.get('ratio', '16:9')
        model = request.form.get('model', 'kling_master_2_1')
        # Browser luôn visible nên không cần show_browser parameter
        repeat_count = int(request.form.get('repeat_count', '1'))
        
        # Parse prompts
        prompts_json = request.form.get('prompts', '[]')
        try:
            prompts = json.loads(prompts_json)
        except:
            return jsonify({'error': 'Format prompts không hợp lệ'}), 400
        
        if not prompts or len(prompts) == 0:
            return jsonify({'error': 'Danh sách prompts không được để trống'}), 400
        
        if len(prompts) > 10:
            return jsonify({'error': 'Tối đa 10 prompts mỗi lần'}), 400
        
        # Parse images for multi-images mode
        images = []
        if prompt_mode == 'batch-multi-images':
            images_json = request.form.get('images', '[]')
            try:
                images = json.loads(images_json)
            except:
                return jsonify({'error': 'Format images không hợp lệ'}), 400
            
            if len(images) != len(prompts):
                return jsonify({'error': 'Số lượng prompts và images phải bằng nhau'}), 400
        
        if repeat_count < 1 or repeat_count > 5:
            return jsonify({'error': 'Số lần lặp phải từ 1 đến 5'}), 400
        
        image_path = None
        image_paths = []
        
        if mode == 'image-to-video' and prompt_mode in ['single', 'batch-one-image']:
            # Single image upload for Case 1 & 2
            if 'image' not in request.files:
                return jsonify({'error': 'Vui lòng upload ảnh'}), 400
            
            image_file = request.files['image']
            if image_file.filename == '':
                return jsonify({'error': 'Chưa chọn file ảnh'}), 400
            
            # Lưu ảnh upload
            filename = secure_filename(image_file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"upload_{timestamp}_{filename}"
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            
        elif prompt_mode == 'batch-multi-images':
            # Multiple images from uploads folder for Case 3
            for image_name in images:
                image_file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
                if not os.path.exists(image_file_path):
                    return jsonify({'error': f'Không tìm thấy file ảnh: {image_name}'}), 400
                image_paths.append(image_file_path)
        
        # Tạo task ID
        task_id = str(uuid.uuid4())
        
        # Chạy task trong background
        thread = threading.Thread(
            target=run_video_generation_task,
            args=(task_id, mode, prompt_mode, prompts, duration, ratio, model, image_path, image_paths, repeat_count)
        )
        thread.start()
        
        total_videos = len(prompts) * repeat_count
        return jsonify({'task_id': task_id, 'total_videos': total_videos})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/task-status/<task_id>')
def api_task_status(task_id):
    """API endpoint kiểm tra trạng thái task"""
    if task_id in running_tasks:
        return jsonify(running_tasks[task_id])
    else:
        return jsonify({'error': 'Task không tồn tại'}), 404

@app.route('/api/prompts')
def api_list_prompts():
    """API endpoint liệt kê các prompt đã tạo"""
    try:
        prompts_dir = Path('prompts')
        if not prompts_dir.exists():
            return jsonify([])
        
        prompts = []
        for file_path in prompts_dir.glob('*.json'):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    prompts.append({
                        'filename': file_path.name,
                        'content': data.get('image_prompt', ''),  # Lấy image_prompt thay vì content
                        'video_prompt': data.get('video_prompt', ''),  # Thêm video_prompt
                        'video_duration': data.get('video_duration', ''),
                        'video_ratio': data.get('video_ratio', ''),
                        'topic': data.get('topic', ''),
                        'created': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    })
            except:
                continue
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        prompts.sort(key=lambda x: x['created'], reverse=True)
        return jsonify(prompts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/images')
def api_list_images():
    """API endpoint liệt kê ảnh đã tạo"""
    try:
        output_dir = Path('output')
        if not output_dir.exists():
            return jsonify([])
        
        images = []
        for file_path in output_dir.glob('*.{jpg,jpeg,png,gif,webp}'):
            images.append({
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'created': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        images.sort(key=lambda x: x['created'], reverse=True)
        return jsonify(images)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos')
def api_list_videos():
    """API endpoint liệt kê video đã tạo"""
    try:
        output_dir = Path('output')
        if not output_dir.exists():
            return jsonify([])
        
        videos = []
        for file_path in output_dir.glob('*.{mp4,avi,mov,mkv,webm}'):
            videos.append({
                'filename': file_path.name,
                'size': file_path.stat().st_size,
                'created': datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        videos.sort(key=lambda x: x['created'], reverse=True)
        return jsonify(videos)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/output/<filename>')
def serve_output_file(filename):
    """Serve file từ thư mục output"""
    return send_from_directory('output', filename)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API endpoint quản lý cấu hình"""
    if request.method == 'GET':
        # Đọc cấu hình hiện tại
        config = {}
        try:
            if os.path.exists("config_template.txt"):
                with open("config_template.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if "=" in line and not line.strip().startswith("#"):
                            key, value = line.split("=", 1)
                            config[key.strip()] = value.strip()
        except:
            pass
        
        return jsonify(config)
    
    elif request.method == 'POST':
        # Cập nhật cấu hình
        try:
            data = request.json
            api_key = data.get('api_key', '').strip()
            
            if not api_key:
                return jsonify({'error': 'API key không được để trống'}), 400
            
            # Cập nhật config_template.txt
            if os.path.exists("config_template.txt"):
                with open("config_template.txt", "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # Tìm và thay thế dòng api_key
                for i, line in enumerate(lines):
                    if line.startswith("api_key="):
                        lines[i] = f"api_key={api_key}\n"
                        break
                
                with open("config_template.txt", "w", encoding="utf-8") as f:
                    f.writelines(lines)
                
                return jsonify({'success': True, 'message': 'Cấu hình đã được cập nhật'})
            else:
                return jsonify({'error': 'File config_template.txt không tồn tại'}), 400
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/batch-prompts')
def batch_prompts_page():
    """Trang tạo ảnh hàng loạt từ file prompt"""
    return render_template('batch_prompts.html')

@app.route('/batch-video')
def batch_video_page():
    """Trang tạo video hàng loạt"""
    return render_template('batch_video.html')

@app.route('/api/batch-prompts', methods=['POST'])
def api_batch_prompts():
    """API endpoint tạo ảnh hàng loạt từ file prompt"""
    try:
        data = request.json
        file_content = data.get('file_content', '').strip()
        # Browser luôn visible nên không cần show_browser parameter
        
        if not file_content:
            return jsonify({'error': 'Nội dung file không được để trống'}), 400
        
        # Parse prompts từ file content
        prompts_list = parse_prompts_from_file(file_content)
        
        if not prompts_list:
            return jsonify({'error': 'Không tìm thấy prompt nào hợp lệ trong file'}), 400
        
        if len(prompts_list) > 20:  # Giới hạn số lượng để tránh spam
            return jsonify({'error': 'Tối đa 20 prompt mỗi lần'}), 400
        
        # Tạo task ID
        task_id = str(uuid.uuid4())
        
        # Chạy task trong background
        thread = threading.Thread(
            target=run_batch_prompts_task,
            args=(task_id, prompts_list)
        )
        thread.start()
        
        return jsonify({'task_id': task_id, 'total_prompts': len(prompts_list), 'parsed_prompts': prompts_list})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/batch-video', methods=['POST'])
def api_batch_video():
    """API endpoint tạo video hàng loạt"""
    try:
        data = request.json
        prompts = data.get('prompts', [])
        duration = data.get('duration', '5s')
        ratio = data.get('ratio', '16:9')
        model = data.get('model', 'kling_master_2_1')
        # Browser luôn visible nên không cần show_browser parameter
        delay_between = data.get('delay_between', 10)
        
        if not prompts:
            return jsonify({'error': 'Danh sách prompts không được để trống'}), 400
        
        if len(prompts) > 10:  # Giới hạn số lượng để tránh spam
            return jsonify({'error': 'Tối đa 10 prompts mỗi lần'}), 400
        
        # Tạo task ID
        task_id = str(uuid.uuid4())
        
        # Chạy task trong background
        thread = threading.Thread(
            target=run_batch_video_task,
            args=(task_id, prompts, duration, ratio, model, delay_between)
        )
        thread.start()
        
        return jsonify({'task_id': task_id, 'total_prompts': len(prompts)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-prompt-file', methods=['POST'])
def api_upload_prompt_file():
    """API endpoint upload file prompt"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Không tìm thấy file'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Chưa chọn file'}), 400
        
        if not file.filename.lower().endswith('.txt'):
            return jsonify({'error': 'Chỉ chấp nhận file .txt'}), 400
        
        # Đọc nội dung file
        file_content = file.read().decode('utf-8')
        
        # Parse prompts để kiểm tra
        prompts_list = parse_prompts_from_file(file_content)
        
        return jsonify({
            'success': True,
            'file_content': file_content,
            'total_prompts': len(prompts_list),
            'parsed_prompts': prompts_list
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-gemini', methods=['POST'])
def api_test_gemini():
    """API endpoint test Gemini API key"""
    try:
        data = request.json
        api_key = data.get('api_key', '').strip()
        
        if not api_key:
            return jsonify({'error': 'API key không được để trống'}), 400
        
        # Test trực tiếp với Google Generative AI
        import google.generativeai as genai
        
        try:
            # Configure API key để test
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # Test với một prompt đơn giản
            response = model.generate_content(
                "Hello, this is a test message. Please respond with 'API connection successful'.",
                generation_config={
                    "temperature": 0.1,
                    "max_output_tokens": 50,
                }
            )
            
            if response and response.text:
                return jsonify({'success': True, 'message': 'Kết nối Gemini API thành công!'})
            else:
                return jsonify({'error': 'API key không phản hồi đúng cách'}), 400
                
        except Exception as e:
            error_msg = str(e)
            print(f"Gemini test error: {error_msg}")  # Log để debug
            
            if "API_KEY" in error_msg or "invalid" in error_msg.lower() or "authentication" in error_msg.lower():
                return jsonify({'error': 'API key không hợp lệ'}), 400
            elif "quota" in error_msg.lower() or "exceeded" in error_msg.lower() or "limit" in error_msg.lower():
                return jsonify({'error': 'API key đã hết quota hoặc bị giới hạn'}), 400
            elif "permission" in error_msg.lower() or "denied" in error_msg.lower():
                return jsonify({'error': 'API key không có quyền truy cập'}), 400
            else:
                return jsonify({'error': f'Lỗi kết nối: {error_msg}'}), 400
        
    except Exception as e:
        print(f"Test API error: {str(e)}")  # Log để debug
        return jsonify({'error': str(e)}), 500

@app.route('/api/update-prompt', methods=['POST'])
def api_update_prompt():
    """API endpoint cập nhật prompt đã chỉnh sửa"""
    try:
        data = request.json
        filename = data.get('filename', '')
        prompt_data = data.get('data', {})
        
        if not filename:
            return jsonify({'error': 'Filename không được để trống'}), 400
        
        if not prompt_data:
            return jsonify({'error': 'Dữ liệu prompt không được để trống'}), 400
        
        # Kiểm tra file có tồn tại không
        file_path = os.path.join('prompts', filename)
        if not os.path.exists(file_path):
            return jsonify({'error': 'File prompt không tồn tại'}), 404
        
        # Cập nhật timestamp
        prompt_data['updated_at'] = datetime.now().isoformat()
        prompt_data['updated_by'] = 'user_edit'
        
        # Lưu file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': 'Prompt đã được cập nhật'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import webbrowser
    import threading
    import time
    
    print("🚀 Khởi động FazzyTool Web Interface...")
    print("📝 Giao diện web sẽ chạy tại: http://127.0.0.1:5000")
    print("🔧 Đảm bảo đã cấu hình cookie và API key trong Settings")
    
    # Hàm tự động mở Chrome sau 2 giây
    def auto_open_browser():
        time.sleep(2)  # Đợi web server khởi động
        try:
            # Thử mở Chrome trước
            import subprocess
            import os
            
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
            ]
            
            chrome_opened = False
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    try:
                        subprocess.Popen([chrome_path, "http://127.0.0.1:5000"])
                        print("🌐 Đã mở Chrome tự động!")
                        chrome_opened = True
                        break
                    except:
                        continue
            
            # Nếu không tìm thấy Chrome, dùng browser mặc định
            if not chrome_opened:
                webbrowser.open('http://127.0.0.1:5000')
                print("🌐 Đã mở browser mặc định (không tìm thấy Chrome)!")
                
        except Exception as e:
            print(f"⚠️ Không thể mở browser tự động: {e}")
            print("👉 Vui lòng mở browser và vào: http://127.0.0.1:5000")
    
    # Chạy auto-open browser trong background thread
    # browser_thread = threading.Thread(target=auto_open_browser) # DISABLED
    # browser_thread.daemon = True # DISABLED
    # browser_thread.start() # DISABLED
    
    # Khởi động Flask app
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)
