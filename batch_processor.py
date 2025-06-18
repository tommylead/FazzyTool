"""
Batch Processor cho FAZZYTOOL
Xử lý hàng loạt prompt từ các file template
"""

import asyncio
import json
import re
import os
from datetime import datetime
from typing import List, Dict, Any
import configparser

class BatchProcessor:
    def __init__(self):
        self.config = self.load_config()
        self.prompts = []
        self.cookies = []
        
    def load_config(self) -> Dict[str, Any]:
        """Đọc cấu hình từ config_template.txt"""
        config = {
            'api_key': 'AIzaSyDvEEI2MX3hwh4mrDBRB01hjHcdAiz4a9Q',
            'wait_time': 3,
            'max_retries': 3,
            'max_concurrent': 2,
            'delay_between_requests': 5,
            'browser': 'firefox',
            'headless': False,
            'output_folder': 'output'
        }
        
        try:
            if os.path.exists('config_template.txt'):
                with open('config_template.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse simple key=value format
                for line in content.split('\n'):
                    if '=' in line and not line.startswith('[') and not line.startswith('==='):
                        key, value = line.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == 'api_key':
                            config['api_key'] = value
                        elif key == 'wait_time':
                            config['wait_time'] = int(value)
                        elif key == 'max_retries':
                            config['max_retries'] = int(value)
                        elif key == 'max_concurrent':
                            config['max_concurrent'] = int(value)
                        elif key == 'delay_between_requests':
                            config['delay_between_requests'] = int(value)
                        elif key == 'browser':
                            config['browser'] = value
                        elif key == 'headless':
                            config['headless'] = value.lower() == 'true'
                        elif key == 'output_folder':
                            config['output_folder'] = value
                            
        except Exception as e:
            print(f"Lỗi đọc config: {e}, sử dụng cấu hình mặc định")
            
        return config
        
    def load_cookies_from_template(self) -> List[Dict]:
        """Đọc cookie từ cookie_template.txt"""
        cookies = []
        
        try:
            if os.path.exists('cookie_template.txt'):
                with open('cookie_template.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Tìm phần JSON cookie
                start_marker = "=== PASTE COOKIE JSON VÀO ĐÂY ==="
                end_marker = "=== KẾT THÚC COOKIE ==="
                
                if start_marker in content and end_marker in content:
                    start_idx = content.find(start_marker) + len(start_marker)
                    end_idx = content.find(end_marker)
                    json_content = content[start_idx:end_idx].strip()
                    
                    if json_content and not json_content.startswith('['):
                        # Nếu không phải JSON array, thử parse từng dòng
                        lines = json_content.split('\n')
                        json_content = '\n'.join([line for line in lines if line.strip()])
                    
                    if json_content:
                        cookies = json.loads(json_content)
                        
        except Exception as e:
            print(f"Lỗi đọc cookie template: {e}")
            
        return cookies
        
    def parse_prompts_from_template(self, file_path: str = 'prompts_template.txt') -> List[Dict]:
        """Parse prompts từ template file"""
        prompts = []
        
        try:
            if not os.path.exists(file_path):
                print(f"Không tìm thấy file {file_path}")
                return prompts
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse PROMPT_IDEA (cho AI Gemini)
            idea_pattern = r'PROMPT_IDEA_START\s*(.*?)\s*PROMPT_IDEA_END'
            idea_matches = re.findall(idea_pattern, content, re.DOTALL)
            
            for idea in idea_matches:
                prompts.append({
                    'type': 'ai_idea',
                    'content': idea.strip(),
                    'use_ai': True
                })
                
            # Parse DETAILED_PROMPT (thủ công)
            detail_pattern = r'DETAILED_PROMPT_START\s*(.*?)\s*DETAILED_PROMPT_END'
            detail_matches = re.findall(detail_pattern, content, re.DOTALL)
            
            for detail in detail_matches:
                prompts.append({
                    'type': 'detailed',
                    'content': detail.strip(),
                    'use_ai': False
                })
                
            # Parse JSON_PROMPTS
            json_pattern = r'JSON_PROMPTS_START\s*(.*?)\s*JSON_PROMPTS_END'
            json_matches = re.findall(json_pattern, content, re.DOTALL)
            
            for json_content in json_matches:
                try:
                    json_prompts = json.loads(json_content.strip())
                    for jp in json_prompts:
                        prompts.append({
                            'type': 'json',
                            'content': jp.get('prompt', ''),
                            'style': jp.get('style', ''),
                            'media_type': jp.get('type', 'image'),
                            'use_ai': False
                        })
                except json.JSONDecodeError as e:
                    print(f"Lỗi parse JSON prompt: {e}")
                    
        except Exception as e:
            print(f"Lỗi đọc prompt template: {e}")
            
        return prompts
        
    def get_available_images(self) -> List[str]:
        """Lấy danh sách ảnh có sẵn trong thư mục output để làm image-to-video"""
        image_files = []
        
        if os.path.exists('output'):
            for file in os.listdir('output'):
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.gif')):
                    image_files.append(os.path.join('output', file))
        
        # Sort theo tên file để đảm bảo thứ tự
        image_files.sort()
        return image_files
    
    def create_batch_job(self) -> Dict[str, Any]:
        """Tạo batch job từ các template"""
        cookies = self.load_cookies_from_template()
        prompts = self.parse_prompts_from_template()
        available_images = self.get_available_images()
        
        if not cookies:
            print("⚠️  Chưa có cookie! Vui lòng cập nhật cookie_template.txt")
            
        if not prompts:
            print("⚠️  Chưa có prompt! Vui lòng cập nhật prompts_template.txt")
        
        # Phân loại prompts thành image và video
        image_prompts = []
        video_prompts = []
        
        for prompt in prompts:
            media_type = prompt.get('media_type', 'image')
            if media_type == 'video':
                video_prompts.append(prompt)
            else:
                image_prompts.append(prompt)
        
        batch_job = {
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'config': self.config,
            'cookies': cookies,
            'prompts': prompts,
            'image_prompts': image_prompts,
            'video_prompts': video_prompts,
            'available_images': available_images,
            'total_items': len(prompts),
            'workflow': self._determine_workflow(image_prompts, video_prompts, available_images),
            'status': 'ready'
        }
        
        return batch_job
    
    def _determine_workflow(self, image_prompts: List[Dict], video_prompts: List[Dict], available_images: List[str]) -> str:
        """Xác định workflow dựa trên prompts và ảnh có sẵn"""
        
        if len(image_prompts) > 0 and len(video_prompts) > 0:
            return "image_then_video"  # Tạo ảnh trước, rồi dùng ảnh để tạo video
        elif len(image_prompts) > 0:
            return "image_only"  # Chỉ tạo ảnh
        elif len(video_prompts) > 0 and len(available_images) > 0:
            return "video_from_existing_images"  # Dùng ảnh có sẵn để tạo video
        elif len(video_prompts) > 0:
            return "video_text_to_video"  # Tạo video từ text (nếu không có ảnh)
        else:
            return "unknown"
        
    def save_batch_report(self, results: List[Dict], job_info: Dict):
        """Lưu báo cáo batch"""
        timestamp = job_info['timestamp']
        report_file = f"output/batch_report_{timestamp}.json"
        
        os.makedirs('output', exist_ok=True)
        
        report = {
            'job_info': job_info,
            'results': results,
            'summary': {
                'total': len(results),
                'success': len([r for r in results if r.get('status') == 'success']),
                'failed': len([r for r in results if r.get('status') == 'failed']),
                'completion_time': datetime.now().isoformat()
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"📊 Báo cáo batch đã lưu: {report_file}")
        
    def print_batch_summary(self, job: Dict[str, Any]):
        """In tóm tắt batch job"""
        print("\n" + "="*50)
        print("🚀 BATCH JOB SUMMARY")
        print("="*50)
        print(f"📅 Thời gian: {job['timestamp']}")
        print(f"🔧 Cấu hình: {job['config']['browser']} | Concurrent: {job['config']['max_concurrent']}")
        print(f"🍪 Cookie: {'✅ Có' if job['cookies'] else '❌ Không'}")
        print(f"📝 Tổng prompt: {job['total_items']}")
        
        if job['prompts']:
            ai_prompts = len([p for p in job['prompts'] if p.get('use_ai')])
            manual_prompts = job['total_items'] - ai_prompts
            print(f"   ├─ AI tự động: {ai_prompts}")
            print(f"   └─ Thủ công: {manual_prompts}")
        
        # Hiển thị phân loại media
        image_count = len(job.get('image_prompts', []))
        video_count = len(job.get('video_prompts', []))
        available_images = len(job.get('available_images', []))
        
        print(f"🎨 Ảnh: {image_count} prompt")
        print(f"🎬 Video: {video_count} prompt")
        print(f"🖼️ Ảnh có sẵn: {available_images} file")
        
        # Hiển thị workflow
        workflow = job.get('workflow', 'unknown')
        workflow_descriptions = {
            'image_then_video': '🔄 Tạo ảnh trước → Dùng ảnh tạo video',
            'image_only': '🎨 Chỉ tạo ảnh',
            'video_from_existing_images': '🎬 Tạo video từ ảnh có sẵn',
            'video_text_to_video': '🎬 Tạo video từ text',
            'unknown': '❓ Không xác định'
        }
        
        print(f"📋 Workflow: {workflow_descriptions.get(workflow, workflow)}")
        
        if workflow == 'video_from_existing_images' and available_images > 0:
            print(f"   📸 Sẽ dùng {min(available_images, video_count)} ảnh để tạo video")
            if video_count > available_images:
                print(f"   ⚠️ Thiếu {video_count - available_images} ảnh cho video prompts")
        
        print("="*50)
        
        if not job['cookies']:
            print("⚠️  CẢNH BÁO: Chưa có cookie Freepik!")
            print("   Vui lòng cập nhật file cookie_template.txt")
            return False
            
        if not job['prompts']:
            print("⚠️  CẢNH BÁO: Chưa có prompt!")
            print("   Vui lòng cập nhật file prompts_template.txt")
            return False
        
        if workflow == 'video_from_existing_images' and available_images == 0:
            print("⚠️  CẢNH BÁO: Có video prompt nhưng không có ảnh!")
            print("   Tạo ảnh trước hoặc upload ảnh vào thư mục output/")
            return False
            
        return True 