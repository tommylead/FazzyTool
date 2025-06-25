#!/usr/bin/env python3
"""
FAZZYTOOL WEB INTERFACE - Giao diện web cho FazzyTool

Giao diện web hiện đại để tương tác với FazzyTool thông qua trình duyệt
Chỉ chức năng tạo ảnh - Video đã được loại bỏ
"""

import os
import json
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
# Prevent concurrent image generation
image_generation_lock = threading.Lock()
currently_generating = False

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
    global currently_generating
    
    # Kiểm tra có task đang chạy không
    with image_generation_lock:
        if currently_generating:
            print(f"⚠️ [Task {task_id}] Đã có task đang chạy, hủy task này")
            running_tasks[task_id] = {
                'status': 'error',
                'message': 'Đã có task tạo ảnh khác đang chạy. Vui lòng chờ hoàn thành.'
            }
            return
        currently_generating = True
        print(f"🔒 [Task {task_id}] Đã lock generation process")
    
    try:
        running_tasks[task_id] = {
            'status': 'running',
            'progress': 0,
            'message': 'Đang khởi tạo...',
            'results': []
        }
        
        print(f"🎨 [Task {task_id}] Khởi tạo FreepikImageGenerator...")
        generator = FreepikImageGenerator(headless=False)  # Luôn visible
        
        print(f"🍪 [Task {task_id}] Load cookie...")
        cookies = load_cookie_from_template()
        cookie_string = json.dumps(cookies) if cookies else None
        print(f"🍪 [Task {task_id}] Cookie loaded: {'Có' if cookie_string else 'Không'}")
        
        running_tasks[task_id]['progress'] = 20
        running_tasks[task_id]['message'] = 'Đang tạo ảnh...'
        
        print(f"🚀 [Task {task_id}] Bắt đầu tạo ảnh với prompt: {prompt}")
        print(f"📊 [Task {task_id}] Cấu hình: {num_images} ảnh, tải {download_count}")
        
        downloaded_files = generator.generate_image(
            prompt=prompt,
            cookie_string=cookie_string,
            num_images=num_images,
            download_count=download_count,
            filename_prefix=filename_prefix
        )
        
        print(f"✅ [Task {task_id}] Generate_image hoàn thành: {len(downloaded_files) if downloaded_files else 0} files")
        
        if downloaded_files:
            running_tasks[task_id]['status'] = 'completed'
            running_tasks[task_id]['progress'] = 100
            running_tasks[task_id]['message'] = f'Hoàn thành! Đã tạo {len(downloaded_files)} ảnh'
            running_tasks[task_id]['results'] = downloaded_files
        else:
            running_tasks[task_id]['status'] = 'error'
            running_tasks[task_id]['message'] = 'Không tạo được ảnh nào'
        
    except Exception as e:
        print(f"❌ [Task {task_id}] Lỗi chi tiết: {str(e)}")
        import traceback
        traceback.print_exc()
        running_tasks[task_id]['status'] = 'error'
        running_tasks[task_id]['message'] = f'Lỗi: {str(e)}'
    finally:
        # Luôn unlock khi hoàn thành
        with image_generation_lock:
            currently_generating = False
            print(f"🔓 [Task {task_id}] Đã unlock generation process")

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
    global currently_generating
    
    # Kiểm tra có task đang chạy không
    with image_generation_lock:
        if currently_generating:
            print(f"⚠️ [Batch Task {task_id}] Đã có task đang chạy, hủy batch này")
            running_tasks[task_id] = {
                'status': 'error',
                'message': 'Đã có task tạo ảnh khác đang chạy. Vui lòng chờ hoàn thành.'
            }
            return
        currently_generating = True
        print(f"🔒 [Batch Task {task_id}] Đã lock generation process")
    
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
        add_log("🔧 Đang khởi tạo FreepikImageGenerator...")
        try:
            image_generator = FreepikImageGenerator(headless=False)  # Luôn visible
            add_log("✅ FreepikImageGenerator khởi tạo thành công")
        except Exception as e:
            add_log(f"❌ Lỗi khởi tạo FreepikImageGenerator: {str(e)}")
            raise e
        
        add_log("🍪 Đang load cookie...")
        cookies = load_cookie_from_template()
        cookie_string = json.dumps(cookies) if cookies else None
        add_log(f"🍪 Cookie loaded: {'Có' if cookie_string else 'Không'}")
        
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
        print(f"❌ [Batch Task {task_id}] Lỗi hệ thống: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if task_id in running_tasks:
            running_tasks[task_id]['status'] = 'error'
            running_tasks[task_id]['message'] = f'Lỗi hệ thống: {str(e)}'
            running_tasks[task_id]['logs'].append(f"❌ LỖI HỆ THỐNG: {str(e)}")
        else:
            # Task không tồn tại trong running_tasks, tạo mới
            running_tasks[task_id] = {
                'status': 'error',
                'message': f'Lỗi hệ thống: {str(e)}',
                'logs': [f"❌ LỖI HỆ THỐNG: {str(e)}"],
                'progress': 0,
                'results': [],
                'current_prompt': '',
                'completed_prompts': 0,
                'total_prompts': 0
            }
    finally:
        # Luôn unlock khi hoàn thành batch
        with image_generation_lock:
            currently_generating = False
            print(f"🔓 [Batch Task {task_id}] Đã unlock generation process")

# ========================================================================================
# ROUTES - CHỈ CHO IMAGE GENERATION
# ========================================================================================

@app.route('/')
def index():
    """Trang chủ - chỉ hiển thị chức năng image"""
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
    """Trang batch process"""
    return render_template('batch_process.html')

@app.route('/batch-prompts')
def batch_prompts_page():
    """Trang batch prompts"""
    return render_template('batch_prompts.html')

@app.route('/settings')
def settings_page():
    """Trang cài đặt"""
    return render_template('settings.html')

# ========================================================================================
# API ENDPOINTS
# ========================================================================================

@app.route('/api/generate-image', methods=['POST'])
def api_generate_image():
    """API tạo ảnh với thread safety protection"""
    try:
        # Kiểm tra thread safety NGAY LẬP TỨC
        with image_generation_lock:
            global currently_generating
            if currently_generating:
                print(f"❌ API: Có task khác đang chạy, từ chối request mới")
                return jsonify({
                    'success': False, 
                    'message': '⚠️ Có task tạo ảnh khác đang chạy. Vui lòng chờ hoàn thành.',
                    'error_code': 'TASK_RUNNING'
                })
        
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        num_images = int(data.get('num_images', 4))
        download_count = data.get('download_count')
        filename_prefix = data.get('filename_prefix')
        
        if not prompt:
            return jsonify({'success': False, 'message': 'Prompt không được để trống'})
        
        # Tạo task ID unique
        task_id = str(uuid.uuid4())
        print(f"✅ API: Chấp nhận request mới, Task ID: {task_id}")
        
        # Chạy task trong background thread
        thread = threading.Thread(
            target=run_image_generation_task,
            args=(task_id, prompt, num_images, download_count, filename_prefix)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/generate-prompt', methods=['POST'])
def api_generate_prompt():
    """API tạo prompt AI"""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        
        if not topic:
            return jsonify({'success': False, 'message': 'Topic không được để trống'})
        
        # Tạo task ID unique
        task_id = str(uuid.uuid4())
        
        # Chạy task trong background thread
        thread = threading.Thread(
            target=run_ai_prompt_task,
            args=(task_id, topic)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({'success': True, 'task_id': task_id})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/task-status/<task_id>')
def api_task_status(task_id):
    """API lấy status của task"""
    if task_id in running_tasks:
        return jsonify(running_tasks[task_id])
    else:
        return jsonify({'status': 'not_found', 'message': 'Task không tìm thấy'})

@app.route('/api/prompts')
def api_list_prompts():
    """API liệt kê các prompt đã tạo"""
    try:
        prompts_dir = 'prompts'
        if not os.path.exists(prompts_dir):
            return jsonify([])
        
        prompts = []
        for filename in os.listdir(prompts_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(prompts_dir, filename)
            try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        prompt_data = json.load(f)
                    prompts.append({
                            'filename': filename,
                            'topic': prompt_data.get('topic', 'Unknown'),
                            'image_prompt': prompt_data.get('image_prompt', '')[:100] + '...',
                            'generated_at': prompt_data.get('generated_at', ''),
                            'filepath': filepath
                    })
            except:
                continue
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        prompts.sort(key=lambda x: x['generated_at'], reverse=True)
        return jsonify(prompts)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/images')
def api_list_images():
    """API liệt kê các ảnh đã tạo"""
    try:
        output_dir = 'output'
        if not os.path.exists(output_dir):
            return jsonify([])
        
        images = []
        for filename in os.listdir(output_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                filepath = os.path.join(output_dir, filename)
                stat = os.stat(filepath)
            images.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'url': f'/output/{filename}'
            })
        
        # Sắp xếp theo thời gian tạo (mới nhất trước)
        images.sort(key=lambda x: x['created_at'], reverse=True)
        return jsonify(images)
        
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/output/<filename>')
def serve_output_file(filename):
    """Serve file từ thư mục output"""
    return send_from_directory('output', filename)

@app.route('/api/config', methods=['GET', 'POST'])
def api_config():
    """API cấu hình hệ thống"""
    if request.method == 'GET':
        # Đọc config hiện tại
        config = {
            'cookie_status': 'loaded' if load_cookie_from_template() else 'empty',
            'gemini_api_key': bool(os.getenv('GEMINI_API_KEY')),
            'output_dir': 'output',
            'prompts_dir': 'prompts'
        }
        return jsonify(config)
    
    elif request.method == 'POST':
        # Cập nhật config
        try:
            data = request.get_json()
            # Xử lý cập nhật config ở đây
            return jsonify({'success': True, 'message': 'Cấu hình đã được cập nhật'})
        except Exception as e:
            return jsonify({'success': False, 'message': f'Lỗi: {str(e)}'})

@app.route('/api/batch-prompts', methods=['POST'])
def api_batch_prompts():
    """API xử lý batch prompts từ file content"""
    try:
        # Nhận JSON data với file_content
        data = request.get_json()
        if not data or 'file_content' not in data:
            return jsonify({'message': 'Thiếu file_content trong request'}), 400
        
        file_content = data['file_content']
        if not file_content:
            return jsonify({'message': 'File content rỗng'}), 400
        
        # Parse prompts từ file content
        prompts_list = parse_prompts_from_file(file_content)
        
        if not prompts_list:
            return jsonify({'message': 'Không tìm thấy prompt nào trong file'}), 400
        
        # Tạo task ID unique
        task_id = str(uuid.uuid4())
        
        # Chạy batch task trong background
        thread = threading.Thread(
            target=run_batch_prompts_task,
            args=(task_id, prompts_list)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'task_id': task_id,
            'total_prompts': len(prompts_list),
            'message': f'Đã bắt đầu xử lý {len(prompts_list)} prompts'
        })
        
    except Exception as e:
        return jsonify({'message': f'Lỗi: {str(e)}'}), 500

@app.route('/api/upload-prompt-file', methods=['POST'])
def api_upload_prompt_file():
    """API upload file prompt và parse prompts"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'Không có file'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Chưa chọn file'})
        
        # Kiểm tra extension
        if not file.filename.lower().endswith(('.txt', '.json')):
            return jsonify({'success': False, 'message': 'Chỉ hỗ trợ file .txt và .json'})
        
        # Đọc nội dung file
        file_content = file.read().decode('utf-8')
        
        # Parse prompts từ file content
        parsed_prompts = parse_prompts_from_file(file_content)
        
        if not parsed_prompts:
            return jsonify({'success': False, 'message': 'Không tìm thấy prompt nào trong file'})
        
        # Reset file pointer để save
        file.seek(0)
        
        # Lưu file (optional)
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename, 
            'filepath': filepath,
            'file_content': file_content,
            'parsed_prompts': parsed_prompts,
            'total_prompts': len(parsed_prompts)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/test-gemini', methods=['POST'])
def api_test_gemini():
    """API test Gemini connection"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return jsonify({
                'success': False, 
                'message': 'GEMINI_API_KEY không tìm thấy trong file .env'
            })
        
        # Test tạo prompt đơn giản
        try:
            gemini_generator = GeminiPromptGenerator()
            test_result = gemini_generator.generate_prompt("test connection", save_to_file=False)
            
            if test_result:
                return jsonify({
                    'success': True,
                    'message': 'Kết nối Gemini thành công!',
                    'test_prompt': test_result.get('image_prompt', '')[:100] + '...'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': 'Gemini trả về kết quả rỗng'
                })
                
        except Exception as e:
            error_msg = str(e)
            if 'quota' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'message': 'Gemini API đã hết quota. Hãy tạo API key mới hoặc chờ đến tháng sau.'
                })
            elif 'api' in error_msg.lower() and 'key' in error_msg.lower():
                return jsonify({
                    'success': False,
                    'message': 'API key không hợp lệ. Hãy kiểm tra lại GEMINI_API_KEY trong file .env'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Lỗi Gemini: {error_msg}'
                })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Lỗi hệ thống: {str(e)}'})

@app.route('/api/update-prompt', methods=['POST'])
def api_update_prompt():
    """API cập nhật prompt file"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        updated_data = data.get('data')
        
        if not filename or not updated_data:
            return jsonify({'success': False, 'message': 'Thiếu dữ liệu'})
        
        filepath = os.path.join('prompts', filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'message': 'File không tồn tại'})
        
        # Lưu data đã cập nhật
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': 'Cập nhật thành công'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

# ========================================================================================
# RUN APP
# ========================================================================================

if __name__ == '__main__':
    import webbrowser
    import threading
    
    def auto_open_browser():
        """Tự động mở Chrome sau 2 giây"""
        time.sleep(2)
        try:
            # Ưu tiên mở Chrome
            import subprocess
            import platform
            
            url = 'http://127.0.0.1:5000'
            system = platform.system()
            
            if system == "Windows":
                # Thử mở Chrome trên Windows
                chrome_paths = [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                    r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(os.environ.get('USERNAME', ''))
                ]
            
                chrome_opened = False
                for chrome_path in chrome_paths:
                    if os.path.exists(chrome_path):
                        try:
                            subprocess.Popen([chrome_path, url])
                            chrome_opened = True
                            print("🌐 Đã mở Chrome cho web interface")
                            break
                        except:
                            continue
            
            if not chrome_opened:
                # Fallback về browser mặc định
                webbrowser.open(url)
                print("🌐 Đã mở browser mặc định cho web interface")
        except Exception as e:
            print(f"⚠️ Không thể tự động mở browser: {e}")
            print("📱 Truy cập thủ công: http://127.0.0.1:5000")
    
    # Tạm thời disable auto-open để tránh conflict với FreepikImageGenerator
    # browser_thread = threading.Thread(target=auto_open_browser)
    # browser_thread.daemon = True
    # browser_thread.start()
    
    print("🌐 FazzyTool Web Interface đang khởi động...")
    print("🎨 Chỉ chức năng Image Generation")
    print("📱 Mở trình duyệt tại: http://127.0.0.1:5000")
    
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
