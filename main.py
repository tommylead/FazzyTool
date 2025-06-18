#!/usr/bin/env python3
"""
FAZZYTOOL - Công cụ tự động sinh ảnh và video bằng Freepik AI

Tool này tự động hóa việc sinh ảnh và video trên nền tảng Freepik Pikaso
thông qua trình duyệt tự động, dựa trên prompt do người dùng hoặc Gemini API sinh ra.
"""

import os
import sys
import json
import click
import traceback
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from dotenv import load_dotenv

from prompt_loader import PromptLoader
from gemini_prompt import GeminiPromptGenerator
from browser_image import FreepikImageGenerator
from browser_video import FreepikVideoGenerator
from batch_processor import BatchProcessor


# Màu sắc cho terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """In banner của tool"""
    banner = f"""
    {Colors.BLUE}{Colors.BOLD}
    ███████╗ █████╗ ███████╗███████╗██╗   ██╗████████╗ ██████╗  ██████╗ ██╗     
    ██╔════╝██╔══██╗╚══███╔╝╚══███╔╝╚██╗ ██╔╝╚══██╔══╝██╔═══██╗██╔═══██╗██║     
    █████╗  ███████║  ███╔╝   ███╔╝  ╚████╔╝    ██║   ██║   ██║██║   ██║██║     
    ██╔══╝  ██╔══██║ ███╔╝   ███╔╝    ╚██╔╝     ██║   ██║   ██║██║   ██║██║     
    ██║     ██║  ██║███████╗███████╗   ██║      ██║   ╚██████╔╝╚██████╔╝███████╗
    ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝      ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝
    {Colors.ENDC}                                                                        

    {Colors.GREEN}{Colors.BOLD}Tool tự động sinh ảnh và video AI từ Freepik Pikaso{Colors.ENDC}
    """
    print(banner)


def validate_environment():
    """Kiểm tra biến môi trường cần thiết trong .env"""
    load_dotenv()
    
    # Kiểm tra FREEPIK_COOKIE
    freepik_cookie = os.getenv("FREEPIK_COOKIE")
    if not freepik_cookie:
        print(f"{Colors.FAIL}Lỗi: FREEPIK_COOKIE không tìm thấy trong file .env{Colors.ENDC}")
        print(f"{Colors.WARNING}Vui lòng sao chép cookie từ tài khoản Freepik Premium vào file .env{Colors.ENDC}")
        return False
        
    return True


def create_output_dir():
    """Tạo thư mục output nếu chưa tồn tại"""
    output_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def load_cookie_from_template():
    """Load cookie từ cookie_template.txt"""
    try:
        if os.path.exists("cookie_template.txt"):
            with open("cookie_template.txt", "r", encoding="utf-8") as f:
                content = f.read()
                
            # Tìm phần cookie JSON
            start_marker = "=== PASTE COOKIE JSON VÀO ĐÂY ==="
            end_marker = "=== KẾT THÚC COOKIE ==="
            
            start_idx = content.find(start_marker)
            end_idx = content.find(end_marker)
            
            if start_idx != -1 and end_idx != -1:
                cookie_json = content[start_idx + len(start_marker):end_idx].strip()
                if cookie_json and cookie_json.startswith('['):
                    return cookie_json
        return None
    except Exception as e:
        print(f"⚠️ Lỗi khi load cookie: {e}")
        return None


def process_single_image(prompt_item: Dict, show_browser: bool, cookies: List[Dict]) -> Optional[str]:
    """Xử lý tạo một ảnh từ prompt item"""
    try:
        from browser_image import FreepikImageGenerator
        
        output_dir = create_output_dir()
        image_generator = FreepikImageGenerator(headless=(not show_browser), output_dir=output_dir)
        
        # Chuyển cookies thành string format
        cookie_string = json.dumps(cookies) if cookies else None
        
        image_path = image_generator.generate_image(prompt_item['content'], cookie_string)
        return image_path
        
    except Exception as e:
        print(f"❌ Lỗi tạo ảnh: {e}")
        return None


def process_single_video_from_image(prompt_item: Dict, image_path: str, show_browser: bool, cookies: List[Dict]) -> Optional[str]:
    """Xử lý tạo một video từ ảnh và prompt item"""
    try:
        from browser_video import FreepikVideoGenerator
        
        output_dir = create_output_dir()
        video_generator = FreepikVideoGenerator(headless=(not show_browser), output_dir=output_dir)
        
        # Chuyển cookies thành string format
        cookie_string = json.dumps(cookies) if cookies else None
        
        # Lấy thông tin video từ prompt item
        duration = prompt_item.get('duration', '5s')
        ratio = prompt_item.get('ratio', '1:1')
        
        video_path = video_generator.generate_video_from_image(
            image_path=image_path,
            prompt=prompt_item['content'],
            cookie_string=cookie_string,
            duration=duration,
            ratio=ratio
        )
        return video_path
        
    except Exception as e:
        print(f"❌ Lỗi tạo video: {e}")
        return None


def process_file_prompt(file_path: str, generate_image: bool, generate_video: bool, show_browser: bool):
    """Xử lý prompt từ file"""
    try:
        print(f"{Colors.BLUE}Đang đọc prompt từ file: {file_path}{Colors.ENDC}")
        prompt_data = PromptLoader.load_prompt(file_path)
        
        output_dir = create_output_dir()
        results = {}
        
        # Sinh ảnh nếu được yêu cầu
        if generate_image:
            image_prompt = prompt_data.get("image_prompt", "")
            print(f"{Colors.GREEN}Đang sinh ảnh với prompt: {image_prompt[:50]}...{Colors.ENDC}")
            
            # Load cookie từ template
            cookie_string = load_cookie_from_template()
            
            image_generator = FreepikImageGenerator(headless=(not show_browser), output_dir=output_dir)
            image_path = image_generator.generate_image(image_prompt, cookie_string)
            
            if image_path:
                results["image_path"] = image_path
        
        # Sinh video nếu được yêu cầu
        if generate_video:
            video_prompt = prompt_data.get("video_prompt", "")
            video_duration = prompt_data.get("video_duration", "5s")
            video_ratio = prompt_data.get("video_ratio", "1:1")
            
            print(f"{Colors.GREEN}Đang sinh video với prompt: {video_prompt[:50]}...{Colors.ENDC}")
            print(f"{Colors.GREEN}Thời lượng: {video_duration}, Tỷ lệ: {video_ratio}{Colors.ENDC}")
            
            video_generator = FreepikVideoGenerator(headless=(not show_browser), output_dir=output_dir)
            video_path = video_generator.generate_video(
                video_prompt, 
                duration=video_duration,
                ratio=video_ratio
            )
            
            if video_path:
                results["video_path"] = video_path
        
        # Hiển thị kết quả
        print(f"\n{Colors.BLUE}{Colors.BOLD}KẾT QUẢ:{Colors.ENDC}")
        if "image_path" in results:
            print(f"{Colors.GREEN}✓ Ảnh được lưu tại: {results['image_path']}{Colors.ENDC}")
        if "video_path" in results:
            print(f"{Colors.GREEN}✓ Video được lưu tại: {results['video_path']}{Colors.ENDC}")
        
        if not results:
            print(f"{Colors.WARNING}Không có kết quả nào được tạo.{Colors.ENDC}")
            
        return True
        
    except Exception as e:
        print(f"{Colors.FAIL}Lỗi khi xử lý file prompt: {str(e)}{Colors.ENDC}")
        if "--debug" in sys.argv:
            traceback.print_exc()
        return False


def process_ai_prompt(topic: str, generate_image: bool, generate_video: bool, show_browser: bool):
    """Xử lý prompt từ chủ đề bằng Gemini AI"""
    try:
        print(f"{Colors.BLUE}Đang sử dụng Gemini API để sinh prompt cho chủ đề: {topic}{Colors.ENDC}")
        
        # Kiểm tra GEMINI_API_KEY
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            print(f"{Colors.FAIL}Lỗi: GEMINI_API_KEY không tìm thấy trong file .env{Colors.ENDC}")
            return False
        
        # Sinh prompt từ Gemini
        generator = GeminiPromptGenerator()
        prompt_data = generator.generate_prompt(topic)
        
        # Lưu prompt vào file để tham khảo sau này
        output_dir = create_output_dir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_file = os.path.join(output_dir, f"prompt_{timestamp}.json")
        
        with open(prompt_file, "w", encoding="utf-8") as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        
        print(f"{Colors.GREEN}Đã lưu prompt vào file: {prompt_file}{Colors.ENDC}")
        
        # Hiển thị prompt đã sinh
        print(f"\n{Colors.BLUE}{Colors.BOLD}PROMPT SINH BỞI GEMINI:{Colors.ENDC}")
        print(f"{Colors.GREEN}Image prompt: {prompt_data['image_prompt'][:100]}...{Colors.ENDC}")
        print(f"{Colors.GREEN}Video prompt: {prompt_data['video_prompt'][:100]}...{Colors.ENDC}")
        print(f"{Colors.GREEN}Video duration: {prompt_data['video_duration']}{Colors.ENDC}")
        print(f"{Colors.GREEN}Video ratio: {prompt_data['video_ratio']}{Colors.ENDC}\n")
        
        # Tiến hành sinh ảnh/video với prompt đã có
        results = {}
        
        # Sinh ảnh nếu được yêu cầu
        if generate_image:
            image_prompt = prompt_data.get("image_prompt", "")
            print(f"{Colors.BLUE}Đang sinh ảnh với prompt từ Gemini...{Colors.ENDC}")
            
            # Load cookie từ template
            cookie_string = load_cookie_from_template()
            
            image_generator = FreepikImageGenerator(headless=(not show_browser), output_dir=output_dir)
            image_path = image_generator.generate_image(image_prompt, cookie_string)
            
            if image_path:
                results["image_path"] = image_path
        
        # Sinh video nếu được yêu cầu
        if generate_video:
            video_prompt = prompt_data.get("video_prompt", "")
            video_duration = prompt_data.get("video_duration", "5s")
            video_ratio = prompt_data.get("video_ratio", "1:1")
            
            print(f"{Colors.BLUE}Đang sinh video với prompt từ Gemini...{Colors.ENDC}")
            
            video_generator = FreepikVideoGenerator(headless=(not show_browser), output_dir=output_dir)
            video_path = video_generator.generate_video(
                video_prompt, 
                duration=video_duration,
                ratio=video_ratio
            )
            
            if video_path:
                results["video_path"] = video_path
        
        # Hiển thị kết quả
        print(f"\n{Colors.BLUE}{Colors.BOLD}KẾT QUẢ:{Colors.ENDC}")
        if "image_path" in results:
            print(f"{Colors.GREEN}✓ Ảnh được lưu tại: {results['image_path']}{Colors.ENDC}")
        if "video_path" in results:
            print(f"{Colors.GREEN}✓ Video được lưu tại: {results['video_path']}{Colors.ENDC}")
        
        if not results:
            print(f"{Colors.WARNING}Không có kết quả nào được tạo.{Colors.ENDC}")
            
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"{Colors.FAIL}Lỗi khi xử lý prompt AI: {error_msg}{Colors.ENDC}")
        
        # Hiển thị hướng dẫn khi gặp lỗi quota
        if "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
            print(f"\n{Colors.WARNING}💡 GIẢI PHÁP THAY THẾ:{Colors.ENDC}")
            print(f"{Colors.GREEN}Sử dụng chế độ File với prompt có sẵn:{Colors.ENDC}")
            print(f"{Colors.GREEN}python main.py file --file sample_prompts.json{Colors.ENDC}")
            print(f"{Colors.GREEN}File mẫu 'sample_prompts.json' đã được tạo sẵn cho bạn!{Colors.ENDC}")
        
        if "--debug" in sys.argv:
            traceback.print_exc()
        return False


@click.group()
def cli():
    """FAZZYTOOL - Công cụ tự động sinh ảnh và video AI từ Freepik Pikaso"""
    print_banner()
    
    # Kiểm tra môi trường
    if not validate_environment():
        sys.exit(1)


@cli.command()
@click.option('--file', '-f', type=str, help='Đường dẫn tới file prompt (.txt, .json, .docx)')
@click.option('--image/--no-image', default=True, help='Sinh ảnh (mặc định: True)')
@click.option('--video/--no-video', default=True, help='Sinh video (mặc định: True)')
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
def file(file, image, video, show_browser):
    """Sinh ảnh/video từ prompt trong file"""
    if not file:
        print(f"{Colors.FAIL}Vui lòng cung cấp đường dẫn file với tùy chọn --file{Colors.ENDC}")
        sys.exit(1)
        
    if not os.path.exists(file):
        print(f"{Colors.FAIL}Không tìm thấy file: {file}{Colors.ENDC}")
        sys.exit(1)
        
    success = process_file_prompt(file, image, video, show_browser)
    if not success:
        sys.exit(1)


@cli.command()
@click.option('--topic', '-t', type=str, required=True, help='Chủ đề để sinh prompt (tiếng Việt)')
@click.option('--image/--no-image', default=True, help='Sinh ảnh (mặc định: True)')
@click.option('--video/--no-video', default=True, help='Sinh video (mặc định: True)')
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
def ai(topic, image, video, show_browser):
    """Sinh ảnh/video từ chủ đề bằng Gemini AI"""
    if not topic:
        print(f"{Colors.FAIL}Vui lòng cung cấp chủ đề với tùy chọn --topic{Colors.ENDC}")
        sys.exit(1)
        
    success = process_ai_prompt(topic, image, video, show_browser)
    if not success:
        sys.exit(1)


@cli.command()
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
@click.option('--dry-run', is_flag=True, help='Chỉ xem thông tin batch mà không thực thi')
def batch(show_browser, dry_run):
    """Xử lý hàng loạt từ file template"""
    try:
        processor = BatchProcessor()
        batch_job = processor.create_batch_job()
        
        # Hiển thị tóm tắt batch
        is_valid = processor.print_batch_summary(batch_job)
        
        if not is_valid:
            print(f"\n{Colors.FAIL}❌ Batch job không hợp lệ. Vui lòng kiểm tra các file template.{Colors.ENDC}")
            return
            
        if dry_run:
            print(f"\n{Colors.BLUE}🔍 DRY RUN - Chỉ xem thông tin, không thực thi{Colors.ENDC}")
            return
            
        # Xác nhận từ người dùng
        print(f"\n{Colors.WARNING}Bạn có muốn tiếp tục xử lý batch này? (y/N): {Colors.ENDC}", end="")
        confirm = input().strip().lower()
        
        if confirm not in ['y', 'yes', 'có']:
            print(f"{Colors.BLUE}Đã hủy batch job.{Colors.ENDC}")
            return
            
        # Thực thi batch theo workflow
        print(f"\n{Colors.GREEN}🚀 Bắt đầu xử lý batch...{Colors.ENDC}")
        results = []
        workflow = batch_job.get('workflow', 'unknown')
        
        if workflow == 'image_then_video':
            # Workflow: Tạo ảnh trước, sau đó dùng ảnh để tạo video
            print(f"{Colors.BLUE}📋 Workflow: Tạo ảnh trước → Dùng ảnh tạo video{Colors.ENDC}")
            
            # Bước 1: Tạo tất cả ảnh
            created_images = []
            for i, prompt_item in enumerate(batch_job['image_prompts'], 1):
                print(f"\n{Colors.BLUE}[Ảnh {i}/{len(batch_job['image_prompts'])}] {prompt_item['content'][:50]}...{Colors.ENDC}")
                
                try:
                    image_path = process_single_image(prompt_item, show_browser, batch_job['cookies'])
                    if image_path:
                        created_images.append(image_path)
                        results.append({'prompt': prompt_item['content'], 'type': 'image', 'status': 'success', 'path': image_path})
                    else:
                        results.append({'prompt': prompt_item['content'], 'type': 'image', 'status': 'failed'})
                        
                    # Delay
                    if i < len(batch_job['image_prompts']):
                        delay = batch_job['config']['delay_between_requests']
                        print(f"{Colors.BLUE}Chờ {delay}s...{Colors.ENDC}")
                        import time
                        time.sleep(delay)
                        
                except Exception as e:
                    print(f"{Colors.FAIL}Lỗi tạo ảnh {i}: {str(e)}{Colors.ENDC}")
                    results.append({'prompt': prompt_item['content'], 'type': 'image', 'status': 'failed', 'error': str(e)})
            
            # Bước 2: Dùng ảnh vừa tạo để tạo video
            for i, prompt_item in enumerate(batch_job['video_prompts'], 1):
                print(f"\n{Colors.BLUE}[Video {i}/{len(batch_job['video_prompts'])}] {prompt_item['content'][:50]}...{Colors.ENDC}")
                
                try:
                    if i <= len(created_images):
                        image_path = created_images[i-1]
                        video_path = process_single_video_from_image(prompt_item, image_path, show_browser, batch_job['cookies'])
                        if video_path:
                            results.append({'prompt': prompt_item['content'], 'type': 'video', 'status': 'success', 'path': video_path, 'source_image': image_path})
                        else:
                            results.append({'prompt': prompt_item['content'], 'type': 'video', 'status': 'failed'})
                    else:
                        print(f"{Colors.WARNING}Không có ảnh tương ứng cho video prompt {i}{Colors.ENDC}")
                        results.append({'prompt': prompt_item['content'], 'type': 'video', 'status': 'failed', 'error': 'No corresponding image'})
                        
                    # Delay
                    if i < len(batch_job['video_prompts']):
                        delay = batch_job['config']['delay_between_requests']
                        print(f"{Colors.BLUE}Chờ {delay}s...{Colors.ENDC}")
                        import time
                        time.sleep(delay)
                        
                except Exception as e:
                    print(f"{Colors.FAIL}Lỗi tạo video {i}: {str(e)}{Colors.ENDC}")
                    results.append({'prompt': prompt_item['content'], 'type': 'video', 'status': 'failed', 'error': str(e)})
                    
        elif workflow == 'video_from_existing_images':
            # Workflow: Dùng ảnh có sẵn để tạo video
            print(f"{Colors.BLUE}📋 Workflow: Dùng ảnh có sẵn tạo video{Colors.ENDC}")
            available_images = batch_job['available_images']
            
            for i, prompt_item in enumerate(batch_job['video_prompts'], 1):
                print(f"\n{Colors.BLUE}[Video {i}/{len(batch_job['video_prompts'])}] {prompt_item['content'][:50]}...{Colors.ENDC}")
                
                try:
                    if i <= len(available_images):
                        image_path = available_images[i-1]
                        print(f"📸 Sử dụng ảnh: {os.path.basename(image_path)}")
                        video_path = process_single_video_from_image(prompt_item, image_path, show_browser, batch_job['cookies'])
                        if video_path:
                            results.append({'prompt': prompt_item['content'], 'type': 'video', 'status': 'success', 'path': video_path, 'source_image': image_path})
                        else:
                            results.append({'prompt': prompt_item['content'], 'type': 'video', 'status': 'failed'})
                    else:
                        print(f"{Colors.WARNING}Không có ảnh tương ứng cho video prompt {i}{Colors.ENDC}")
                        results.append({'prompt': prompt_item['content'], 'type': 'video', 'status': 'failed', 'error': 'No corresponding image'})
                        
                    # Delay
                    if i < len(batch_job['video_prompts']):
                        delay = batch_job['config']['delay_between_requests']
                        print(f"{Colors.BLUE}Chờ {delay}s...{Colors.ENDC}")
                        import time
                        time.sleep(delay)
                        
                except Exception as e:
                    print(f"{Colors.FAIL}Lỗi tạo video {i}: {str(e)}{Colors.ENDC}")
                    results.append({'prompt': prompt_item['content'], 'type': 'video', 'status': 'failed', 'error': str(e)})
                    
        else:
            # Workflow cũ: xử lý từng prompt một
            for i, prompt_item in enumerate(batch_job['prompts'], 1):
                print(f"\n{Colors.BLUE}[{i}/{batch_job['total_items']}] Đang xử lý prompt: {prompt_item['content'][:50]}...{Colors.ENDC}")
                
                try:
                    result = {'prompt': prompt_item['content'], 'status': 'processing'}
                    
                    # Xử lý theo loại prompt
                    if prompt_item.get('use_ai', False):
                        # Sử dụng AI để sinh prompt chi tiết
                        success = process_ai_prompt(prompt_item['content'], True, False, show_browser)
                    else:
                        # Sử dụng prompt trực tiếp
                        temp_prompt_file = f"temp_prompt_{i}.json"
                        with open(temp_prompt_file, 'w', encoding='utf-8') as f:
                            json.dump({
                                'image_prompt': prompt_item['content'],
                                'video_prompt': prompt_item['content'],
                                'video_duration': '5s',
                                'video_ratio': '1:1'
                            }, f, ensure_ascii=False, indent=2)
                        
                        success = process_file_prompt(temp_prompt_file, True, False, show_browser)
                        
                        # Xóa file tạm
                        if os.path.exists(temp_prompt_file):
                            os.remove(temp_prompt_file)
                    
                    result['status'] = 'success' if success else 'failed'
                    results.append(result)
                    
                    # Delay giữa các request
                    if i < batch_job['total_items']:
                        delay = batch_job['config']['delay_between_requests']
                        print(f"{Colors.BLUE}Chờ {delay}s trước khi xử lý tiếp...{Colors.ENDC}")
                        import time
                        time.sleep(delay)
                        
                except Exception as e:
                    print(f"{Colors.FAIL}Lỗi xử lý prompt {i}: {str(e)}{Colors.ENDC}")
                    results.append({'prompt': prompt_item['content'], 'status': 'failed', 'error': str(e)})
        
        # Lưu báo cáo
        processor.save_batch_report(results, batch_job)
        
        # Tóm tắt kết quả
        success_count = len([r for r in results if r['status'] == 'success'])
        failed_count = len([r for r in results if r['status'] == 'failed'])
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ BATCH HOÀN THÀNH{Colors.ENDC}")
        print(f"{Colors.GREEN}Thành công: {success_count}/{len(results)}{Colors.ENDC}")
        print(f"{Colors.FAIL}Thất bại: {failed_count}/{len(results)}{Colors.ENDC}")
        
    except Exception as e:
        print(f"{Colors.FAIL}Lỗi batch processing: {str(e)}{Colors.ENDC}")
        if "--debug" in sys.argv:
            traceback.print_exc()


@cli.command()
def setup():
    """Thiết lập file .env và các thư mục cần thiết"""
    # Tạo file .env nếu chưa tồn tại
    env_file = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_file):
        try:
            with open(env_file, "w", encoding="utf-8") as f:
                f.write("# Chứa API key của Gemini và Cookie Freepik\n")
                f.write("GEMINI_API_KEY=your_gemini_api_key_here\n")
                f.write("FREEPIK_COOKIE=your_freepik_cookie_here\n")
                
            print(f"{Colors.GREEN}Đã tạo file .env mẫu tại: {env_file}{Colors.ENDC}")
            print(f"{Colors.GREEN}Vui lòng cập nhật API key và cookie trong file này.{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Lỗi khi tạo file .env: {str(e)}{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}File .env đã tồn tại tại: {env_file}{Colors.ENDC}")
    
    # Tạo thư mục output
    output_dir = os.path.join(os.getcwd(), "output")
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"{Colors.GREEN}Đã tạo thư mục output tại: {output_dir}{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.FAIL}Lỗi khi tạo thư mục output: {str(e)}{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}Thư mục output đã tồn tại tại: {output_dir}{Colors.ENDC}")
    
    print(f"\n{Colors.BLUE}{Colors.BOLD}Hướng dẫn sử dụng:{Colors.ENDC}")
    print(f"{Colors.GREEN}1. Cập nhật file .env với API key của Gemini và cookie của Freepik Premium{Colors.ENDC}")
    print(f"{Colors.GREEN}2. Sử dụng lệnh 'python main.py ai --topic \"chủ đề của bạn\"' để sinh nội dung bằng AI{Colors.ENDC}")
    print(f"{Colors.GREEN}3. Hoặc, sử dụng lệnh 'python main.py file --file path/to/prompt.json' để sinh từ file sẵn có{Colors.ENDC}")
    print(f"{Colors.GREEN}4. Kết quả sẽ được lưu trong thư mục output/{Colors.ENDC}")


if __name__ == "__main__":
    cli() 