"""
Batch Processor cho FAZZYTOOL - Phiên bản tối ưu
Xử lý hàng loạt prompt từ các file template với các tính năng nâng cao
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
            'browser': 'chrome',
            'headless': False,
            'output_folder': 'output',
            # Cấu hình mới cho image generation
            'default_num_images': 4,
            'default_download_count': 2,
            'auto_filename_prefix': True
        }
        
        try:
            if os.path.exists('config_template.txt'):
                with open('config_template.txt', 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Parse simple key=value format
                for line in content.split('\n'):
                    line = line.strip()
                    if '=' in line and not line.startswith('#') and not line.startswith('[') and not line.startswith('==='):
                        key, value = line.split('=', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        # Remove inline comments
                        if '#' in value:
                            value = value.split('#')[0].strip()
                        
                        try:
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
                            elif key == 'default_num_images':
                                config['default_num_images'] = int(value)
                            elif key == 'default_download_count':
                                config['default_download_count'] = int(value)
                            elif key == 'auto_filename_prefix':
                                config['auto_filename_prefix'] = value.lower() == 'true'
                        except ValueError as e:
                            print(f"Lỗi parse {key}={value}: {e}")
                            continue
                            
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
        """Parse prompts từ template file với hỗ trợ cấu hình nâng cao"""
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
            
            for i, idea in enumerate(idea_matches, 1):
                prompts.append({
                    'type': 'ai_idea',
                    'content': idea.strip(),
                    'use_ai': True,
                    'prompt_id': f'ai_idea_{i:03d}',
                    'num_images': self.config['default_num_images'],
                    'download_count': self.config['default_download_count'],
                    'filename_prefix': f'ai_idea_{i:03d}' if self.config['auto_filename_prefix'] else None
                })
                
            # Parse DETAILED_PROMPT (thủ công)
            detail_pattern = r'DETAILED_PROMPT_START\s*(.*?)\s*DETAILED_PROMPT_END'
            detail_matches = re.findall(detail_pattern, content, re.DOTALL)
            
            for i, detail in enumerate(detail_matches, 1):
                prompts.append({
                    'type': 'detailed',
                    'content': detail.strip(),
                    'use_ai': False,
                    'prompt_id': f'detailed_{i:03d}',
                    'num_images': self.config['default_num_images'],
                    'download_count': self.config['default_download_count'],
                    'filename_prefix': f'detailed_{i:03d}' if self.config['auto_filename_prefix'] else None
                })
                
            # Parse JSON_PROMPTS với cấu hình nâng cao
            json_pattern = r'JSON_PROMPTS_START\s*(.*?)\s*JSON_PROMPTS_END'
            json_matches = re.findall(json_pattern, content, re.DOTALL)
            
            for json_content in json_matches:
                try:
                    json_prompts = json.loads(json_content.strip())
                    for i, jp in enumerate(json_prompts, 1):
                        prompt_item = {
                            'type': 'json',
                            'content': jp.get('prompt', ''),
                            'style': jp.get('style', ''),
                            'media_type': jp.get('type', 'image'),
                            'use_ai': False,
                            'prompt_id': f'json_{i:03d}',
                            # Hỗ trợ cấu hình nâng cao từ JSON
                            'num_images': jp.get('num_images', self.config['default_num_images']),
                            'download_count': jp.get('download_count', self.config['default_download_count']),
                            'filename_prefix': jp.get('filename_prefix') or (f'json_{i:03d}' if self.config['auto_filename_prefix'] else None)
                        }
                        prompts.append(prompt_item)
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
        """Tạo batch job từ các template với cấu hình nâng cao"""
        cookies = self.load_cookies_from_template()
        prompts = self.parse_prompts_from_template()
        available_images = self.get_available_images()
        
        if not cookies:
            print("⚠️  Chưa có cookie! Vui lòng cập nhật cookie_template.txt")
            
        if not prompts:
            print("⚠️  Chưa có prompt! Vui lòng cập nhật prompts_template.txt")
            print(f"🔍 Debug: Đã kiểm tra file prompts_template.txt")
            if os.path.exists('prompts_template.txt'):
                print(f"✅ File tồn tại, kích thước: {os.path.getsize('prompts_template.txt')} bytes")
            else:
                print(f"❌ File không tồn tại")
        
        # Phân loại prompts thành image và video với thông tin chi tiết
        image_prompts = []
        video_prompts = []
        
        for prompt in prompts:
            media_type = prompt.get('media_type', 'image')
            if media_type == 'video':
                video_prompts.append(prompt)
            else:
                image_prompts.append(prompt)
        
        # Tính toán thống kê
        total_images_to_generate = sum(p.get('num_images', 4) for p in image_prompts)
        total_images_to_download = sum(p.get('download_count', 2) for p in image_prompts)
        
        batch_job = {
            'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'config': self.config,
            'cookies': cookies,
            'prompts': prompts,
            'image_prompts': image_prompts,
            'video_prompts': video_prompts,
            'available_images': available_images,
            'total_items': len(prompts),
            'total_images_to_generate': total_images_to_generate,
            'total_images_to_download': total_images_to_download,
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
        """Lưu báo cáo batch với thông tin chi tiết hơn"""
        timestamp = job_info['timestamp']
        report_file = f"output/batch_report_{timestamp}.json"
        
        os.makedirs('output', exist_ok=True)
        
        # Tính toán thống kê chi tiết
        total_images_generated = sum(len(r.get('downloaded_files', [])) for r in results if r.get('type') == 'image')
        total_videos_generated = len([r for r in results if r.get('type') == 'video' and r.get('status') == 'success'])
        
        report = {
            'job_info': job_info,
            'results': results,
            'summary': {
                'total_prompts': len(results),
                'success': len([r for r in results if r.get('status') == 'success']),
                'failed': len([r for r in results if r.get('status') == 'failed']),
                'total_images_generated': total_images_generated,
                'total_videos_generated': total_videos_generated,
                'completion_time': datetime.now().isoformat(),
                'estimated_credits_used': total_images_generated * 10 + total_videos_generated * 25  # Ước tính
            },
            'file_mapping': self._create_file_mapping(results)
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        print(f"📊 Báo cáo batch đã lưu: {report_file}")
        
        # Tạo file CSV đơn giản để dễ xem
        self._create_csv_report(results, job_info, timestamp)
        
    def _create_file_mapping(self, results: List[Dict]) -> Dict:
        """Tạo bản đồ file để dễ tracking"""
        mapping = {
            'images': {},
            'videos': {}
        }
        
        for result in results:
            prompt_id = result.get('prompt_id', 'unknown')
            if result.get('type') == 'image' and result.get('downloaded_files'):
                mapping['images'][prompt_id] = {
                    'prompt': result.get('prompt', '')[:50] + '...',
                    'files': result['downloaded_files']
                }
            elif result.get('type') == 'video' and result.get('path'):
                mapping['videos'][prompt_id] = {
                    'prompt': result.get('prompt', '')[:50] + '...',
                    'file': result['path']
                }
        
        return mapping
    
    def _create_csv_report(self, results: List[Dict], job_info: Dict, timestamp: str):
        """Tạo báo cáo CSV đơn giản"""
        csv_file = f"output/batch_report_{timestamp}.csv"
        
        try:
            with open(csv_file, 'w', encoding='utf-8') as f:
                # Header
                f.write("Prompt ID,Type,Status,Prompt,Files Generated\n")
                
                # Data
                for result in results:
                    prompt_id = result.get('prompt_id', 'unknown')
                    prompt_type = result.get('type', 'unknown')
                    status = result.get('status', 'unknown')
                    prompt = result.get('prompt', '').replace(',', ';').replace('\n', ' ')[:100]
                    
                    files = []
                    if prompt_type == 'image' and result.get('downloaded_files'):
                        files = [os.path.basename(f) for f in result['downloaded_files']]
                    elif prompt_type == 'video' and result.get('path'):
                        files = [os.path.basename(result['path'])]
                    
                    files_str = ';'.join(files)
                    
                    f.write(f"{prompt_id},{prompt_type},{status},\"{prompt}\",\"{files_str}\"\n")
                    
            print(f"📈 Báo cáo CSV đã lưu: {csv_file}")
            
        except Exception as e:
            print(f"⚠️ Lỗi tạo CSV report: {e}")
        
    def print_batch_summary(self, job: Dict[str, Any]):
        """In tóm tắt batch job với thông tin chi tiết hơn"""
        print("\n" + "="*60)
        print("🚀 BATCH JOB SUMMARY - PHIÊN BẢN TỐI ỬU")
        print("="*60)
        print(f"📅 Thời gian: {job['timestamp']}")
        print(f"🔧 Cấu hình: {job['config']['browser']} | Concurrent: {job['config']['max_concurrent']}")
        print(f"🍪 Cookie: {'✅ Có' if job['cookies'] else '❌ Không'}")
        print(f"📝 Tổng prompt: {job['total_items']}")
        
        if job['prompts']:
            ai_prompts = len([p for p in job['prompts'] if p.get('use_ai')])
            manual_prompts = job['total_items'] - ai_prompts
            print(f"   ├─ AI tự động: {ai_prompts}")
            print(f"   └─ Thủ công: {manual_prompts}")
        
        # Hiển thị phân loại media với thông tin chi tiết
        image_count = len(job.get('image_prompts', []))
        video_count = len(job.get('video_prompts', []))
        available_images = len(job.get('available_images', []))
        
        print(f"🎨 Ảnh: {image_count} prompt")
        if image_count > 0:
            print(f"   ├─ Tổng ảnh sẽ sinh: {job['total_images_to_generate']}")
            print(f"   └─ Tổng ảnh sẽ tải: {job['total_images_to_download']}")
        
        print(f"🎬 Video: {video_count} prompt")
        print(f"🖼️ Ảnh có sẵn: {available_images} file")
        
        # Hiển thị workflow
        workflow = job.get('workflow', 'unknown')
        workflow_descriptions = {
            'image_then_video': '🔄 Tạo ảnh trước → Dùng ảnh tạo video',
            'image_only': '🎨 Chỉ tạo ảnh với cấu hình nâng cao',
            'video_from_existing_images': '🎬 Tạo video từ ảnh có sẵn',
            'video_text_to_video': '🎬 Tạo video từ text',
            'unknown': '❓ Không xác định'
        }
        
        print(f"📋 Workflow: {workflow_descriptions.get(workflow, workflow)}")
        
        # Thông tin chi tiết cho từng workflow
        if workflow == 'image_only' and image_count > 0:
            print(f"   📸 Chi tiết cấu hình:")
            for i, prompt in enumerate(job['image_prompts'][:3], 1):  # Chỉ hiển thị 3 prompt đầu
                print(f"     {i}. {prompt['prompt_id']}: {prompt['num_images']} ảnh → tải {prompt['download_count']}")
            if image_count > 3:
                print(f"     ... và {image_count - 3} prompt khác")
        
        if workflow == 'video_from_existing_images' and available_images > 0:
            print(f"   📸 Sẽ dùng {min(available_images, video_count)} ảnh để tạo video")
            if video_count > available_images:
                print(f"   ⚠️ Thiếu {video_count - available_images} ảnh cho video prompts")
        
        # Ước tính thời gian và credits
        estimated_time = self._estimate_processing_time(job)
        estimated_credits = self._estimate_credits_usage(job)
        
        print(f"⏱️ Thời gian ước tính: {estimated_time}")
        print(f"💰 Credits ước tính: {estimated_credits}")
        
        print("="*60)
        
        # Kiểm tra các điều kiện cần thiết
        warnings = []
        
        if not job['cookies']:
            warnings.append("⚠️ Chưa có cookie Freepik! Cập nhật cookie_template.txt")
            
        if not job['prompts']:
            warnings.append("⚠️ Chưa có prompt! Cập nhật prompts_template.txt")
        
        if workflow == 'video_from_existing_images' and available_images == 0:
            warnings.append("⚠️ Có video prompt nhưng không có ảnh! Tạo ảnh trước hoặc upload ảnh vào output/")
        
        if job['total_images_to_generate'] > 20:
            warnings.append("⚠️ Số lượng ảnh lớn có thể tiêu tốn nhiều credits Premium!")
            
        for warning in warnings:
            print(warning)
            
        # Chỉ các warning quan trọng mới làm job invalid
        critical_warnings = [w for w in warnings if any(keyword in w for keyword in ["Chưa có cookie", "Chưa có prompt", "Thiếu", "video prompt nhưng không có ảnh"])]
        
        return len(critical_warnings) == 0  # True nếu không có critical warning
    
    def _estimate_processing_time(self, job: Dict) -> str:
        """Ước tính thời gian xử lý"""
        image_time = job['total_images_to_generate'] * 8  # 8s per image
        video_time = len(job.get('video_prompts', [])) * 15  # 15s per video
        delay_time = (job['total_items'] - 1) * job['config']['delay_between_requests']
        
        total_seconds = image_time + video_time + delay_time
        
        if total_seconds < 60:
            return f"~{total_seconds} giây"
        elif total_seconds < 3600:
            return f"~{total_seconds // 60} phút {total_seconds % 60} giây"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"~{hours} giờ {minutes} phút"
    
    def _estimate_credits_usage(self, job: Dict) -> str:
        """Ước tính số credits sử dụng"""
        image_credits = job['total_images_to_generate'] * 10  # 10 credits per image
        video_credits = len(job.get('video_prompts', [])) * 25  # 25 credits per video
        total_credits = image_credits + video_credits
        
        return f"~{total_credits} credits ({image_credits} ảnh + {video_credits} video)" 