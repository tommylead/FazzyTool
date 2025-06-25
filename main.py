#!/usr/bin/env python3
"""
FAZZYTOOL - Công cụ tự động sinh ảnh bằng Freepik AI

Tool này tự động hóa việc sinh ảnh trên nền tảng Freepik Pikaso
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
from batch_processor import BatchProcessor

# Global configuration cho AI generation
AI_GENERATION_CONFIG = {
    'num_images': 4,
    'download_count': 2
}

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

    {Colors.GREEN}{Colors.BOLD}Tool tự động sinh ảnh AI từ Freepik Pikaso{Colors.ENDC}
    """
    print(banner)


def validate_environment():
    """Kiểm tra biến môi trường cần thiết"""
    load_dotenv()
    
    # Thử đọc FREEPIK_COOKIE từ .env trước
    freepik_cookie = os.getenv("FREEPIK_COOKIE")
    
    # Nếu không có trong .env hoặc chỉ là placeholder, thử đọc từ cookie_template.txt
    if not freepik_cookie or freepik_cookie == "placeholder_cookie":
        cookies = load_cookie_from_template()
        if cookies:
            print(f"{Colors.GREEN}✅ Đã tìm thấy cookie trong cookie_template.txt{Colors.ENDC}")
            return True
        else:
            print(f"{Colors.FAIL}Lỗi: Cookie không tìm thấy trong .env hoặc cookie_template.txt{Colors.ENDC}")
            print(f"{Colors.WARNING}Vui lòng cập nhật cookie trong cookie_template.txt{Colors.ENDC}")
            return False
    else:
        print(f"{Colors.GREEN}✅ Đã tìm thấy cookie trong .env{Colors.ENDC}")
        
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
            
            print(f"🔍 Debug: start_marker found at {start_idx}, end_marker at {end_idx}")
            
            if start_idx != -1 and end_idx != -1:
                cookie_json = content[start_idx + len(start_marker):end_idx].strip()
                print(f"🔍 Debug: Extracted cookie_json length: {len(cookie_json)}")
                print(f"🔍 Debug: Cookie starts with '[': {cookie_json.startswith('[') if cookie_json else False}")
                
                if cookie_json and cookie_json.startswith('['):
                    cookies = json.loads(cookie_json)
                    print(f"🔍 Debug: Parsed {len(cookies)} cookies from JSON")
                    
                    # Fix sameSite values để tương thích với Playwright
                    for cookie in cookies:
                        if 'sameSite' in cookie:
                            if cookie['sameSite'] == 'no_restriction':
                                cookie['sameSite'] = 'None'
                            elif cookie['sameSite'] not in ['Strict', 'Lax', 'None']:
                                cookie['sameSite'] = 'Lax'  # Default safe value
                        
                        # Remove các fields không cần thiết cho Playwright
                        unwanted_fields = ['firstPartyDomain', 'partitionKey', 'storeId', 'hostOnly']
                        for field in unwanted_fields:
                            cookie.pop(field, None)
                            
                        # Rename expirationDate thành expires nếu có
                        if 'expirationDate' in cookie:
                            cookie['expires'] = cookie.pop('expirationDate')
                    
                    print(f"🔍 Debug: Returning {len(cookies)} processed cookies")
                    return cookies
                else:
                    print(f"🔍 Debug: Cookie JSON invalid or empty")
            else:
                print(f"🔍 Debug: Markers not found in template")
        else:
            print(f"🔍 Debug: cookie_template.txt not found")
        return []
    except Exception as e:
        print(f"⚠️ Lỗi khi load cookie: {e}")
        return []


def process_single_image(prompt_item: Dict, show_browser: bool, cookies: List[Dict]) -> Optional[str]:
    """Xử lý một prompt image đơn lẻ với cải tiến mới"""
    try:
        generator = FreepikImageGenerator(headless=not show_browser)
        
        # Lấy thông tin từ prompt_item
        prompt = prompt_item.get('content', '')
        num_images = prompt_item.get('num_images', 4)  # Mặc định 4 ảnh
        download_count = prompt_item.get('download_count')  # None = tải tất cả
        filename_prefix = prompt_item.get('filename_prefix')
        
        if not prompt:
            print("❌ Prompt rỗng")
            return None
            
        # Convert cookies thành string format cho generator
        cookie_string = json.dumps(cookies) if cookies else None
        
        # Sinh ảnh với các tùy chọn mới
        downloaded_files = generator.generate_image(
            prompt=prompt,
            cookie_string=cookie_string,
            num_images=num_images,
            download_count=download_count,
            filename_prefix=filename_prefix
        )
        
        # Trả về file đầu tiên nếu có (để tương thích với code cũ)
        return downloaded_files[0] if downloaded_files else None
        
    except Exception as e:
        print(f"❌ Lỗi xử lý image: {e}")
        return None


def process_single_image_batch(prompt_item: Dict, show_browser: bool, cookies: List[Dict]) -> List[str]:
    """Xử lý một prompt image và trả về list tất cả ảnh đã tải"""
    try:
        generator = FreepikImageGenerator(headless=not show_browser)
        
        prompt = prompt_item.get('content', '')
        num_images = prompt_item.get('num_images', 4)
        download_count = prompt_item.get('download_count')
        filename_prefix = prompt_item.get('filename_prefix')
        
        if not prompt:
            return []
            
        cookie_string = json.dumps(cookies) if cookies else None
        
        downloaded_files = generator.generate_image(
            prompt=prompt,
            cookie_string=cookie_string,
            num_images=num_images,
            download_count=download_count,
            filename_prefix=filename_prefix
        )
        
        return downloaded_files or []
        
    except Exception as e:
        print(f"❌ Lỗi xử lý image batch: {e}")
        return []



def process_file_prompt(file_path: str, generate_image: bool, show_browser: bool):
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
            print(f"🎨 Bắt đầu sinh 4 ảnh, tải về 4 ảnh")
            print(f"📝 Prompt: {image_prompt}")
            
            # Load cookie từ template
            cookies = load_cookie_from_template()
            
            # Tạo prompt item format mới
            prompt_item = {
                'content': image_prompt,
                'num_images': 4,
                'download_count': 4,
                'filename_prefix': 'sample'
            }
            
            # Sử dụng process_single_image_batch
            downloaded_files = process_single_image_batch(prompt_item, show_browser, cookies)
            
            if downloaded_files:
                results["image_paths"] = downloaded_files
                results["image_path"] = downloaded_files[0]  # Để tương thích code cũ
        

        
        # Hiển thị kết quả
        print(f"\n{Colors.BLUE}{Colors.BOLD}KẾT QUẢ:{Colors.ENDC}")
        if "image_path" in results:
            print(f"{Colors.GREEN}✓ Ảnh được lưu tại: {results['image_path']}{Colors.ENDC}")
        
        if not results:
            print(f"{Colors.WARNING}Không có kết quả nào được tạo ra.{Colors.ENDC}")
            
        return True
        
    except Exception as e:
        print(f"{Colors.FAIL}Lỗi khi xử lý file prompt: {str(e)}{Colors.ENDC}")
        if "--debug" in sys.argv:
            traceback.print_exc()
        return False


def process_ai_prompt(topic: str, generate_image: bool, show_browser: bool, num_images: int, download_count: Optional[int]):
    """Xử lý prompt AI với cải tiến lưu file và fallback options"""
    try:
        # Khởi tạo Gemini generator với thư mục prompts
        print(f"🔮 Đang sinh prompt AI từ chủ đề: {topic}")
        
        # Kiểm tra API key trước
        load_dotenv()
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            print(f"{Colors.FAIL}❌ GEMINI_API_KEY không tìm thấy trong file .env{Colors.ENDC}")
            print(f"{Colors.WARNING}💡 Giải pháp thay thế:{Colors.ENDC}")
            print(f"{Colors.GREEN}1. Lấy API key mới tại: https://makersuite.google.com/app/apikey{Colors.ENDC}")
            print(f"{Colors.GREEN}2. Hoặc sử dụng prompt thủ công:{Colors.ENDC}")
            print(f"   python main.py file --file sample_prompts.json")
            return False
        
        try:
            gemini_generator = GeminiPromptGenerator(output_dir="prompts")
            
            # Sinh prompt với tự động lưu file
            prompt_data = gemini_generator.generate_prompt(topic, save_to_file=True)
            
            if not prompt_data:
                print("❌ Không thể sinh prompt từ AI")
                return False
            
            print(f"✅ Đã sinh prompt AI thành công!")
            print(f"📁 File prompt: {prompt_data.get('file_path', 'Unknown')}")
            print(f"🎨 Image prompt: {prompt_data['image_prompt'][:100]}...")

            
        except Exception as gemini_error:
            error_msg = str(gemini_error)
            print(f"{Colors.FAIL}❌ Lỗi Gemini API: {error_msg}{Colors.ENDC}")
            
            # Xử lý các lỗi phổ biến
            if "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                print(f"\n{Colors.WARNING}🔥 GEMINI API ĐÃ HẾT QUOTA MIỄN PHÍ!{Colors.ENDC}")
                print(f"{Colors.BLUE}💡 CÁC GIẢI PHÁP THAY THẾ:{Colors.ENDC}")
                print(f"{Colors.GREEN}1. 🔑 Tạo API key mới:{Colors.ENDC}")
                print(f"   - Truy cập: https://makersuite.google.com/app/apikey")
                print(f"   - Tạo project mới hoặc dùng Google account khác")
                print(f"   - Copy key mới vào file .env")
                print(f"\n{Colors.GREEN}2. 📝 Sử dụng prompt có sẵn:{Colors.ENDC}")
                print(f"   python main.py file --file sample_prompts.json")
                print(f"\n{Colors.GREEN}3. 📋 Tạo prompt thủ công:{Colors.ENDC}")
                
                # Tạo prompt thủ công ngay lập tức
                manual_prompt = create_manual_prompt(topic)
                if manual_prompt:
                    prompt_data = manual_prompt
                    print(f"{Colors.GREEN}✅ Đã tạo prompt thủ công thành công!{Colors.ENDC}")
                else:
                    return False
                    
            elif "api" in error_msg.lower() and "key" in error_msg.lower():
                print(f"\n{Colors.FAIL}🔑 API Key không hợp lệ!{Colors.ENDC}")
                print(f"{Colors.BLUE}💡 Hướng dẫn fix:{Colors.ENDC}")
                print(f"1. Kiểm tra GEMINI_API_KEY trong file .env")
                print(f"2. Tạo key mới tại: https://makersuite.google.com/app/apikey")
                return False
            else:
                print(f"\n{Colors.FAIL}❌ Lỗi không xác định: {error_msg}{Colors.ENDC}")
                return False
        
        # Load cookies
        cookies = load_cookie_from_template()
        
        success_count = 0
        
        # Xử lý sinh ảnh
        if generate_image:
            try:
                print(f"\n{Colors.BLUE}🎨 Bắt đầu sinh ảnh...{Colors.ENDC}")
                
                # Chuẩn bị prompt item với cấu hình nâng cao
                global AI_GENERATION_CONFIG
                image_prompt_item = {
                    'content': prompt_data['image_prompt'],
                    'num_images': AI_GENERATION_CONFIG['num_images'],
                    'download_count': AI_GENERATION_CONFIG['download_count'],
                    'filename_prefix': f"{prompt_data.get('prompt_id', 'ai_generated')}_img"
                }
                
                downloaded_images = process_single_image_batch(image_prompt_item, show_browser, cookies)
                
                if downloaded_images:
                    success_count += 1
                    print(f"{Colors.GREEN}✅ Đã sinh {len(downloaded_images)} ảnh thành công{Colors.ENDC}")
                    for i, img_path in enumerate(downloaded_images, 1):
                        print(f"  {i}. {os.path.basename(img_path)}")
                else:
                    print(f"{Colors.FAIL}❌ Thất bại sinh ảnh{Colors.ENDC}")
                    
            except Exception as e:
                print(f"{Colors.FAIL}❌ Lỗi sinh ảnh: {e}{Colors.ENDC}")
        

        
        return success_count > 0
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi xử lý AI prompt: {e}{Colors.ENDC}")
        return False

def create_manual_prompt(topic: str) -> Optional[Dict[str, Any]]:
    """Tạo prompt thủ công khi Gemini API không hoạt động"""
    try:
        print(f"\n{Colors.BLUE}🛠️ Đang tạo prompt thủ công cho: {topic}{Colors.ENDC}")
        
        # Template prompt cơ bản dựa trên topic
        prompt_templates = {
            'mèo': 'Cute orange cat sitting by the window, soft natural lighting, photorealistic, high quality, 4K',
            'chó': 'Adorable puppy playing in garden, natural lighting, photorealistic, high quality, 4K',
            'cảnh': 'Beautiful landscape with mountains and sky, golden hour lighting, cinematic, high quality, 4K',
            'poster': 'Modern minimalist poster design, clean layout, professional typography, contemporary style',
            'logo': 'Creative logo design, modern style, clean lines, professional appearance, vector art'
        }
        
        # Tìm template phù hợp
        selected_template = None
        topic_lower = topic.lower()
        
        for key, template in prompt_templates.items():
            if key in topic_lower:
                selected_template = template
                break
        
        # Fallback template nếu không tìm thấy
        if not selected_template:
            selected_template = f'High quality image of {topic}, professional photography, detailed, 4K resolution, natural lighting'
        
        # Tạo prompt data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_data = {
            'image_prompt': selected_template,
            'topic': topic,
            'prompt_id': f'manual_{timestamp}',
            'generated_at': datetime.now().isoformat(),
            'generated_by': 'manual_fallback'
        }
        
        # Lưu vào file
        os.makedirs('prompts', exist_ok=True)
        safe_topic = "".join(c for c in topic[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_topic = safe_topic.replace(' ', '_')
        
        filename = f"manual_{timestamp}_{safe_topic}.json"
        file_path = os.path.join('prompts', filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(prompt_data, f, ensure_ascii=False, indent=2)
        
        prompt_data['file_path'] = file_path
        
        print(f"💾 Đã lưu prompt thủ công: {file_path}")
        return prompt_data
        
    except Exception as e:
        print(f"❌ Lỗi tạo prompt thủ công: {e}")
        return None


@click.group()
def cli():
    """FazzyTool - Công cụ dòng lệnh"""
    pass

@cli.command()
@click.option('--file', '-f', type=str, help='Đường dẫn tới file prompt (.txt, .json, .docx)')
@click.option('--image/--no-image', default=True, help='Sinh ảnh (mặc định: True)')
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
def file(file, image, show_browser):
    """Sinh ảnh từ prompt trong file"""
    if not file:
        print(f"{Colors.FAIL}Lỗi: Cần cung cấp file prompt qua --file.{Colors.ENDC}")
        return
        
    process_file_prompt(file, image, show_browser)

@cli.command()
@click.option('--topic', '-t', type=str, required=True, help='Chủ đề để sinh prompt (tiếng Việt)')
@click.option('--image/--no-image', default=True, help='Sinh ảnh (mặc định: True)')
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
@click.option('--download-count', default=None, type=int, help='Số lượng ảnh tải về (mặc định: tất cả)')
def ai(topic, image, show_browser, download_count):
    """Sinh prompt bằng AI và tùy chọn sinh ảnh/video."""
    if not validate_environment():
        return
    process_ai_prompt(topic, image, show_browser, 4, download_count)

@cli.command()
@click.option('--topics', '-t', multiple=True, help='Danh sách chủ đề (có thể lặp lại nhiều lần)')
@click.option('--file', '-f', type=str, help='File chứa danh sách chủ đề (mỗi dòng một chủ đề)')
@click.option('--start-index', default=1, help='Số thứ tự bắt đầu đánh số prompt')
def ai_batch(topics, file, start_index):
    """Sinh nhiều prompt AI từ danh sách chủ đề và lưu thành file có thứ tự"""
    
    topic_list = list(topics)
    
    # Đọc từ file nếu có
    if file:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                topic_list.extend([line.strip() for line in f if line.strip()])
        except Exception as e:
            print(f"{Colors.FAIL}❌ Lỗi đọc file {file}: {e}{Colors.ENDC}")
            return
    
    if not topic_list:
        print(f"{Colors.FAIL}Lỗi: Không có chủ đề nào để xử lý.{Colors.ENDC}")
        return

    print(f"{Colors.BLUE}Bắt đầu tạo batch {len(topic_list)} prompts...{Colors.ENDC}")
    
    # Tạo thư mục prompts nếu chưa có
    prompts_dir = "prompts"
    os.makedirs(prompts_dir, exist_ok=True)
    
    # Tạo các prompts
    for i, topic in enumerate(topic_list, start=start_index):
        print(f"  {Colors.GREEN}Đang tạo prompt {i} cho chủ đề: '{topic}'...{Colors.ENDC}")
        try:
            create_manual_prompt(topic)
        except Exception as e:
            print(f"  {Colors.FAIL}Lỗi khi tạo prompt cho '{topic}': {e}{Colors.ENDC}")
    
    print(f"\n{Colors.GREEN}✅ Đã tạo thành công {len(topic_list)} file prompt trong thư mục '{prompts_dir}'.{Colors.ENDC}")
    print(f"{Colors.WARNING}Sử dụng 'python main.py batch' để bắt đầu xử lý hàng loạt.{Colors.ENDC}")

@cli.command()
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
@click.option('--dry-run', is_flag=True, help='Chỉ xem thông tin batch mà không thực thi')
def batch(show_browser, dry_run):
    """Xử lý hàng loạt các file prompt trong thư mục 'prompts'."""
    if not validate_environment():
        return
        
    prompts_dir = "prompts"
    if not os.path.exists(prompts_dir) or not os.listdir(prompts_dir):
        print(f"{Colors.FAIL}Lỗi: Thư mục '{prompts_dir}' không tồn tại hoặc rỗng.{Colors.ENDC}")
        print(f"{Colors.WARNING}Sử dụng 'python main.py ai-batch' để tạo các file prompt trước.{Colors.ENDC}")
        return

    # Load cookie
    cookies = load_cookie_from_template()
    if not cookies:
        print(f"{Colors.FAIL}Lỗi: Không thể load cookie. Dừng thực thi.{Colors.ENDC}")
        return
        
    # Khởi tạo BatchProcessor
    processor = BatchProcessor(
        prompts_dir=prompts_dir,
        show_browser=show_browser,
        cookies=cookies
    )
    
    # Lấy thông tin batch
    batch_info = processor.get_batch_info()
    
    print(f"\n{Colors.HEADER}{Colors.BOLD}--- BATCH PROCESSING ---{Colors.ENDC}")
    print(f"{Colors.BLUE}Tìm thấy {batch_info['total_files']} file prompt trong '{prompts_dir}'.{Colors.ENDC}")
    
    if not batch_info['total_files']:
        return
        
    # Hiển thị danh sách file
    for file_info in batch_info['files']:
        status = f"{Colors.GREEN}✓{Colors.ENDC}" if file_info['exists'] else f"{Colors.FAIL}✗{Colors.ENDC}"
        print(f"  [{status}] {file_info['filename']} - Topic: {file_info.get('topic', 'N/A')}")
        
    if dry_run:
        print(f"\n{Colors.WARNING}--dry-run chế độ ON. Kết thúc mà không thực thi.{Colors.ENDC}")
        return
        
    # Xác nhận thực thi
    if not click.confirm(f"\n{Colors.WARNING}Bạn có muốn bắt đầu xử lý {batch_info['total_files']} file không?{Colors.ENDC}", default=True):
        print("Đã hủy.")
        return
        
    # Thực thi batch
    processor.run_batch()
    
    print(f"\n{Colors.GREEN}{Colors.BOLD}--- HOÀN THÀNH BATCH ---{Colors.ENDC}")

@cli.command()
def setup():
    """Hướng dẫn cài đặt và cấu hình môi trường."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}--- HƯỚNG DẪN CÀI ĐẶT FAZZYTOOL ---{Colors.ENDC}")
    print(f"1. {Colors.BLUE}Cập nhật file .env với API key của Gemini và cookie của Freepik Premium{Colors.ENDC}")
    print(f"2. {Colors.BLUE}Sử dụng lệnh 'python main.py ai --topic \"chủ đề của bạn\"' để sinh nội dung bằng AI{Colors.ENDC}")
    print(f"3. {Colors.BLUE}Hoặc, sử dụng lệnh 'python main.py file --file path/to/prompt.json' để sinh từ file sẵn có{Colors.ENDC}")
    print(f"4. {Colors.BLUE}Kết quả sẽ được lưu trong thư mục output/{Colors.ENDC}")
    print(f"5. {Colors.BLUE}Chạy tool:{Colors.ENDC} python main.py --help")

@cli.command()
def test():
    """
    Chạy test nhanh để kiểm tra chức năng sinh ảnh/video.
    Sử dụng prompt mẫu 'sample_prompts.json'.
    """
    if not validate_environment():
        return

    print(f"{Colors.BLUE}Bắt đầu chạy test...{Colors.ENDC}")
    
    # Đường dẫn file test
    test_file = "sample_prompts.json"
    
    if not os.path.exists(test_file):
        print(f"{Colors.FAIL}Lỗi: Không tìm thấy file test '{test_file}'.{Colors.ENDC}")
        return
        
    # Đọc prompt từ file test
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            prompt_data = json.load(f)
    except Exception as e:
        print(f"{Colors.FAIL}Lỗi khi đọc file test: {e}{Colors.ENDC}")
        return
        
    # Load cookie
    cookies = load_cookie_from_template()
    if not cookies:
        print(f"{Colors.FAIL}Không thể load cookie. Dừng test.{Colors.ENDC}")
        return
        
    # --- Test Image Generation ---
    print(f"\n{Colors.HEADER}--- Testing Image Generation ---{Colors.ENDC}")
    image_prompt = prompt_data.get("image_prompt", "")
    if image_prompt:
        print(f"📝 Prompt ảnh: {image_prompt}")
        
        # Tạo prompt item
        image_prompt_item = {
            'content': image_prompt,
            'num_images': 4,
            'download_count': 1,  # Chỉ tải 1 ảnh để test
            'filename_prefix': 'test_image'
        }
        
        # Chạy với browser hiển thị
        downloaded_images = process_single_image_batch(image_prompt_item, True, cookies)
        
        if downloaded_images:
            print(f"{Colors.GREEN}✅ Test ảnh THÀNH CÔNG. Đã tải {len(downloaded_images)} ảnh.{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Test ảnh THẤT BẠI.{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}Không tìm thấy image_prompt trong file test.{Colors.ENDC}")

    print(f"\n{Colors.GREEN}{Colors.BOLD}--- KẾT THÚC TEST ---{Colors.ENDC}")

@cli.command()
@click.option('--prompt', '-p', default='test cookie với prompt debug', help='Prompt để test (mặc định: test cookie với prompt debug)')
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
@click.option('--download-count', default=None, type=int, help='Số lượng ảnh tải về (mặc định: tất cả)')
@click.option('--filename-prefix', type=str, help='Tiền tố tên file ảnh')
def image(file, topic, prompt, num_images, download_count, filename_prefix, show_browser):
    """
    Sinh ảnh từ nhiều nguồn: file, topic (AI), hoặc prompt trực tiếp.
    Đây là lệnh chính để tạo ảnh.
    """
    if not validate_environment():
        return
        
    # Xác định nguồn prompt
    prompt_source_count = sum([1 for var in [file, topic, prompt] if var])
    if prompt_source_count > 1:
        print(f"{Colors.FAIL}Lỗi: Chỉ được chọn một nguồn prompt (--file, --topic, hoặc --prompt).{Colors.ENDC}")
        return
    if prompt_source_count == 0:
        print(f"{Colors.FAIL}Lỗi: Phải cung cấp một nguồn prompt (--file, --topic, hoặc --prompt).{Colors.ENDC}")
        return

    # Load cookie
    cookies = load_cookie_from_template()
    if not cookies:
        print(f"{Colors.FAIL}Lỗi: Không thể load cookie.{Colors.ENDC}")
        return

    final_prompt = ""
    
    # Xử lý prompt từ file
    if file:
        try:
            prompt_data = PromptLoader.load_prompt(file)
            final_prompt = prompt_data.get("image_prompt", "")
            if not filename_prefix:
                filename_prefix = Path(file).stem
        except Exception as e:
            print(f"{Colors.FAIL}Lỗi khi xử lý file prompt: {e}{Colors.ENDC}")
            return
            
    # Xử lý prompt từ topic (AI)
    elif topic:
        try:
            print(f"{Colors.BLUE}Đang sinh prompt từ topic: '{topic}'...{Colors.ENDC}")
            gemini_generator = GeminiPromptGenerator()
            prompt_data = gemini_generator.generate_prompt(topic, save_to_file=False)
            if prompt_data:
                final_prompt = prompt_data.get("image_prompt", "")
                if not filename_prefix:
                    safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
                    filename_prefix = f"ai_{safe_topic[:20]}"
            else:
                raise Exception("Gemini không trả về prompt.")
        except Exception as e:
            print(f"{Colors.FAIL}Lỗi khi sinh prompt bằng AI: {e}{Colors.ENDC}")
            return
    
    # Xử lý prompt trực tiếp
    elif prompt:
        final_prompt = prompt
        if not filename_prefix:
            filename_prefix = "".join(c for c in prompt[:20] if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')

    # Kiểm tra lại prompt cuối cùng
    if not final_prompt:
        print(f"{Colors.FAIL}Lỗi: Không có prompt nào để xử lý.{Colors.ENDC}")
        return
        
    print(f"\n{Colors.HEADER}--- BẮT ĐẦU SINH ẢNH ---{Colors.ENDC}")
    print(f"📝 Prompt: {Colors.BOLD}{final_prompt}{Colors.ENDC}")
    print(f"⚙️  Cấu hình: Sinh {num_images} ảnh, tải về {download_count or 'tất cả'}")
    
    # Tạo prompt item
    prompt_item = {
        'content': final_prompt,
        'num_images': num_images,
        'download_count': download_count,
        'filename_prefix': filename_prefix or 'image'
    }
    
    # Xử lý
    downloaded_files = process_single_image_batch(prompt_item, show_browser, cookies)
    
    if downloaded_files:
        print(f"\n{Colors.GREEN}✅ HOÀN THÀNH! Đã tải {len(downloaded_files)} ảnh:{Colors.ENDC}")
        for f in downloaded_files:
            print(f"  - {f}")
    else:
        print(f"\n{Colors.FAIL}❌ THẤT BẠI! Không có ảnh nào được tạo.{Colors.ENDC}")


if __name__ == "__main__":
    try:
        # Check môi trường trước khi chạy CLI
        # if validate_environment():
        print_banner()
        cli()
    except Exception as e:
        print(f"\n{Colors.FAIL}{Colors.BOLD}Lỗi không xác định:{Colors.ENDC}")
        print(f"Một lỗi nghiêm trọng đã xảy ra: {e}")
        print("\n--- TRACEBACK ---")
        traceback.print_exc()
        sys.exit(1) 