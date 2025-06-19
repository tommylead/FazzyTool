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

    {Colors.GREEN}{Colors.BOLD}Tool tự động sinh ảnh và video AI từ Freepik Pikaso{Colors.ENDC}
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
        
        # Sinh video nếu được yêu cầu
        if generate_video:
            video_prompt = prompt_data.get("video_prompt", "")
            video_duration = prompt_data.get("video_duration", "5s")
            video_ratio = prompt_data.get("video_ratio", "1:1")
            
            print(f"{Colors.GREEN}Đang sinh video với prompt: {video_prompt[:50]}...{Colors.ENDC}")
            print(f"{Colors.GREEN}Thời lượng: {video_duration}, Tỷ lệ: {video_ratio}{Colors.ENDC}")
            
            # Load cookies
            cookies = load_cookie_from_template()
            cookie_string = json.dumps(cookies) if cookies else None
            
            video_generator = FreepikVideoGenerator(headless=(not show_browser), output_dir=output_dir)
            video_path = video_generator.generate_video(
                video_prompt, 
                duration=video_duration,
                ratio=video_ratio,
                cookie_string=cookie_string
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
            print(f"🎬 Video prompt: {prompt_data['video_prompt'][:100]}...")
            
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
        
        # Xử lý sinh video (giữ nguyên logic cũ)
        if generate_video:
            try:
                print(f"\n{Colors.BLUE}🎬 Bắt đầu sinh video...{Colors.ENDC}")
                
                video_generator = FreepikVideoGenerator(headless=not show_browser)
                cookie_string = json.dumps(cookies) if cookies else None
                
                video_path = video_generator.generate_video(
                    prompt=prompt_data['video_prompt'],
                    duration=prompt_data.get('video_duration', '5s'),
                    ratio=prompt_data.get('video_ratio', '1:1'),
                    cookie_string=cookie_string
                )
                
                if video_path:
                    success_count += 1
                    print(f"{Colors.GREEN}✅ Đã sinh video: {os.path.basename(video_path)}{Colors.ENDC}")
                else:
                    print(f"{Colors.FAIL}❌ Thất bại sinh video{Colors.ENDC}")
                    
            except Exception as e:
                print(f"{Colors.FAIL}❌ Lỗi sinh video: {e}{Colors.ENDC}")
        
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
            'mèo': {
                'image': 'Cute orange cat sitting by the window, soft natural lighting, photorealistic, high quality, 4K',
                'video': 'Cat moving gracefully, gentle camera movement, warm lighting, cozy atmosphere'
            },
            'chó': {
                'image': 'Adorable puppy playing in garden, natural lighting, photorealistic, high quality, 4K',
                'video': 'Puppy running and playing, dynamic camera movement, outdoor setting, cheerful mood'
            },
            'cảnh': {
                'image': 'Beautiful landscape with mountains and sky, golden hour lighting, cinematic, high quality, 4K',
                'video': 'Slow camera pan across landscape, peaceful atmosphere, natural lighting'
            },
            'poster': {
                'image': 'Modern minimalist poster design, clean layout, professional typography, contemporary style',
                'video': 'Logo animation with smooth transitions, professional presentation, modern style'
            },
            'logo': {
                'image': 'Creative logo design, modern style, clean lines, professional appearance, vector art',
                'video': 'Logo reveal animation, smooth transitions, professional presentation'
            }
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
            selected_template = {
                'image': f'High quality image of {topic}, professional photography, detailed, 4K resolution, natural lighting',
                'video': f'Cinematic video about {topic}, smooth camera movement, professional cinematography, high quality'
            }
        
        # Tạo prompt data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        prompt_data = {
            'image_prompt': selected_template['image'],
            'video_prompt': selected_template['video'],
            'video_duration': '5s',
            'video_ratio': '1:1',
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
@click.option('--num-images', default=4, help='Số lượng ảnh sinh ra (mặc định: 4)')
@click.option('--download-count', default=None, type=int, help='Số lượng ảnh tải về (mặc định: tất cả)')
def ai(topic, image, video, show_browser, num_images, download_count):
    """Sinh ảnh/video từ chủ đề bằng Gemini AI với tùy chọn nâng cao"""
    if not topic:
        print(f"{Colors.FAIL}Vui lòng cung cấp chủ đề với tùy chọn --topic{Colors.ENDC}")
        sys.exit(1)
    
    # Cập nhật global config cho AI generation
    global AI_GENERATION_CONFIG
    AI_GENERATION_CONFIG = {
        'num_images': num_images,
        'download_count': download_count if download_count is not None else num_images
    }
        
    success = process_ai_prompt(topic, image, video, show_browser)
    if not success:
        sys.exit(1)


@cli.command()
@click.option('--topics', '-t', multiple=True, help='Danh sách chủ đề (có thể lặp lại nhiều lần)')
@click.option('--file', '-f', type=str, help='File chứa danh sách chủ đề (mỗi dòng một chủ đề)')
@click.option('--start-index', default=1, help='Số thứ tự bắt đầu đánh số prompt')
def ai_batch(topics, file, start_index):
    """Sinh nhiều prompt AI từ danh sách chủ đề và lưu thành file có thứ tự"""
    
    topic_list = list(topics) if topics else []
    
    # Đọc từ file nếu có
    if file:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                file_topics = [line.strip() for line in f if line.strip()]
                topic_list.extend(file_topics)
        except Exception as e:
            print(f"{Colors.FAIL}❌ Lỗi đọc file {file}: {e}{Colors.ENDC}")
            return
    
    if not topic_list:
        print(f"{Colors.FAIL}Vui lòng cung cấp chủ đề qua --topics hoặc --file{Colors.ENDC}")
        print("Ví dụ:")
        print("  python main.py ai-batch -t 'Mèo dễ thương' -t 'Chó nhỏ' -t 'Hoa đẹp'")
        print("  python main.py ai-batch -f topics.txt")
        return
    
    try:
        print(f"{Colors.BLUE}🚀 Bắt đầu sinh {len(topic_list)} prompt AI...{Colors.ENDC}")
        
        gemini_generator = GeminiPromptGenerator(output_dir="prompts")
        results = gemini_generator.generate_batch_prompts(topic_list, start_index)
        
        # Thống kê kết quả
        successful = len([r for r in results if "error" not in r])
        failed = len([r for r in results if "error" in r])
        
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ HOÀN THÀNH BATCH AI GENERATION{Colors.ENDC}")
        print(f"{Colors.GREEN}Thành công: {successful}/{len(topic_list)}{Colors.ENDC}")
        print(f"{Colors.FAIL}Thất bại: {failed}/{len(topic_list)}{Colors.ENDC}")
        print(f"{Colors.BLUE}📁 Tất cả file đã lưu trong thư mục: prompts/{Colors.ENDC}")
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi batch AI generation: {e}{Colors.ENDC}")


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


@cli.command()
def test():
    """Test các tính năng cơ bản của FazzyTool"""
    print_banner()
    print(f"{Colors.BLUE}🧪 Đang test các tính năng cơ bản...{Colors.ENDC}")
    
    # Test 1: Kiểm tra file cấu hình
    print(f"\n{Colors.BLUE}1. Kiểm tra file cấu hình:{Colors.ENDC}")
    
    # Check .env
    load_dotenv()
    if os.path.exists('.env'):
        print(f"  ✅ File .env: Tồn tại")
        gemini_key = os.getenv('GEMINI_API_KEY')
        freepik_cookie = os.getenv('FREEPIK_COOKIE')
        print(f"  {'✅' if gemini_key else '❌'} GEMINI_API_KEY: {'Có' if gemini_key else 'Thiếu'}")
        print(f"  {'✅' if freepik_cookie else '❌'} FREEPIK_COOKIE: {'Có' if freepik_cookie else 'Thiếu'}")
    else:
        print(f"  ❌ File .env: Không tồn tại")
    
    # Check cookie template
    cookies = load_cookie_from_template()
    print(f"  {'✅' if cookies else '❌'} Cookie template: {'OK' if cookies else 'Lỗi'}")
    
    # Test 2: Kiểm tra thư mục
    print(f"\n{Colors.BLUE}2. Kiểm tra thư mục:{Colors.ENDC}")
    for folder in ['prompts', 'output']:
        if os.path.exists(folder):
            print(f"  ✅ Thư mục {folder}: Tồn tại")
        else:
            os.makedirs(folder, exist_ok=True)
            print(f"  🔧 Thư mục {folder}: Đã tạo")
    
    # Test 3: Test manual prompt generation
    print(f"\n{Colors.BLUE}3. Test tạo prompt thủ công:{Colors.ENDC}")
    try:
        test_prompt = create_manual_prompt("test mèo dễ thương")
        if test_prompt:
            print(f"  ✅ Tạo prompt thủ công: Thành công")
            print(f"  📁 File: {test_prompt.get('file_path', 'N/A')}")
        else:
            print(f"  ❌ Tạo prompt thủ công: Thất bại")
    except Exception as e:
        print(f"  ❌ Lỗi: {e}")
    
    # Test 4: Kiểm tra imports
    print(f"\n{Colors.BLUE}4. Kiểm tra modules:{Colors.ENDC}")
    modules_to_check = [
        ('selenium', 'Selenium WebDriver'),
        ('requests', 'HTTP Requests'),
        ('click', 'CLI Interface'),
        ('json', 'JSON Processing'),
        ('pathlib', 'Path Management')
    ]
    
    for module_name, description in modules_to_check:
        try:
            __import__(module_name)
            print(f"  ✅ {description}: OK")
        except ImportError:
            print(f"  ❌ {description}: Thiếu")
    
    print(f"\n{Colors.GREEN}🏁 Test hoàn thành!{Colors.ENDC}")
    print(f"\n{Colors.BLUE}💡 Hướng dẫn sử dụng:{Colors.ENDC}")
    print(f"  • Test với prompt có sẵn: python main.py file --file sample_prompts.json")
    print(f"  • Tạo prompt từ AI: python main.py ai --topic 'mèo dễ thương'")
    print(f"  • Xử lý batch: python main.py batch")
    print(f"  • Xem help: python main.py --help")


@cli.command()
def sessions():
    """Hiển thị thống kê các session video đã tạo"""
    print(f"{Colors.BLUE}📊 THỐNG KÊ VIDEO SESSIONS{Colors.ENDC}")
    
    try:
        from browser_video import FreepikVideoGenerator
        
        # Tạo generator để access methods
        generator = FreepikVideoGenerator()
        generator.print_session_summary()
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi khi lấy thống kê sessions: {e}{Colors.ENDC}")


@cli.command()
@click.option('--prompt', '-p', default='test cookie với prompt debug', help='Prompt để test (mặc định: test cookie với prompt debug)')
@click.option('--show-browser/--headless', default=True, help='Hiển thị trình duyệt để debug (mặc định: True)')
def debug_cookie(prompt, show_browser):
    """Debug chi tiết việc sử dụng cookie Chrome để nhập prompt"""
    print(f"{Colors.BLUE}🔧 Bắt đầu debug cookie Chrome...{Colors.ENDC}")
    
    try:
        # Load cookies
        cookies = load_cookie_from_template()
        if not cookies:
            print(f"{Colors.FAIL}❌ Không có cookie trong cookie_template.txt{Colors.ENDC}")
            print(f"{Colors.WARNING}Vui lòng dán cookie vào file cookie_template.txt theo hướng dẫn{Colors.ENDC}")
            return
        
        print(f"{Colors.GREEN}✅ Đã load {len(cookies)} cookies từ template{Colors.ENDC}")
        
        # Tạo generator với browser hiển thị để debug
        from browser_image import FreepikImageGenerator
        generator = FreepikImageGenerator(headless=not show_browser, output_dir="output")
        
        # Debug bằng cách chỉ test phần nhập prompt
        print(f"{Colors.BLUE}🧪 Test prompt: '{prompt}'{Colors.ENDC}")
        
        # Sử dụng playwright manual để debug
        from playwright.sync_api import sync_playwright
        import time
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=not show_browser)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            
            try:
                # Set cookies
                context.add_cookies(cookies)
                print(f"{Colors.GREEN}🍪 Đã set cookies{Colors.ENDC}")
                
                # Thử các URL Freepik khác nhau
                urls_to_try = [
                    "https://www.freepik.com/pikaso/ai-image-generator",
                    "https://www.freepik.com/pikaso",
                    "https://www.freepik.com/ai/image-generator",
                    "https://www.freepik.com/generate/image"
                ]
                
                current_url = None
                for url in urls_to_try:
                    try:
                        print(f"{Colors.BLUE}🌐 Thử URL: {url}...{Colors.ENDC}")
                        page.goto(url, wait_until="networkidle")
                        current_url = url
                        break
                    except Exception as e:
                        print(f"{Colors.WARNING}⚠️ URL {url} thất bại: {e}{Colors.ENDC}")
                        continue
                
                if not current_url:
                    print(f"{Colors.FAIL}❌ Không thể vào bất kỳ URL nào!{Colors.ENDC}")
                    return
                
                # Chờ trang load
                time.sleep(3)
                final_url = page.url
                print(f"{Colors.GREEN}📄 Trang đã load xong: {final_url}{Colors.ENDC}")
                
                # Debug: Show page title và một số thông tin
                try:
                    title = page.title()
                    print(f"{Colors.BLUE}🏷️ Tiêu đề trang: {title}{Colors.ENDC}")
                    
                    # Check nếu có thông báo đăng nhập
                    login_indicators = ["Sign up", "Log in", "Login", "Register"]
                    for indicator in login_indicators:
                        if page.query_selector(f"text={indicator}"):
                            print(f"{Colors.WARNING}⚠️ Phát hiện: {indicator} - Có thể cần đăng nhập{Colors.ENDC}")
                    
                    # List tất cả input/textarea elements để debug
                    all_inputs = page.query_selector_all("input, textarea, [contenteditable='true']")
                    print(f"{Colors.BLUE}🔍 Tìm thấy {len(all_inputs)} input elements:{Colors.ENDC}")
                    
                    for i, input_el in enumerate(all_inputs[:10]):  # Chỉ show 10 cái đầu
                        try:
                            tag = input_el.evaluate("el => el.tagName")
                            placeholder = input_el.evaluate("el => el.placeholder || ''")
                            el_type = input_el.evaluate("el => el.type || ''")
                            visible = input_el.is_visible()
                            print(f"  {i+1}. {tag} type='{el_type}' placeholder='{placeholder}' visible={visible}")
                        except:
                            print(f"  {i+1}. [Error getting info]")
                            
                except Exception as e:
                    print(f"{Colors.WARNING}⚠️ Lỗi khi debug page info: {e}{Colors.ENDC}")
                
                print(f"{Colors.GREEN}📄 Hoàn thành debug page info{Colors.ENDC}")
                
                # Tìm ô input với nhiều selector hơn
                print(f"{Colors.BLUE}🔍 Tìm ô nhập prompt...{Colors.ENDC}")
                prompt_selectors = [
                    # Specific Freepik selectors
                    "textarea[placeholder*='Describe what you want to generate']",
                    "textarea[placeholder*='prompt']",
                    "textarea[placeholder*='describe']", 
                    "input[placeholder*='prompt']",
                    "input[placeholder*='describe']",
                    "input[placeholder*='Describe what you want']",
                    
                    # Data attributes
                    "[data-testid*='prompt']",
                    "[data-testid*='input']",
                    "[data-testid*='textarea']",
                    "[data-cy*='prompt']",
                    "[data-cy*='input']",
                    
                    # Class names
                    ".prompt-input",
                    ".input-prompt",
                    ".ai-prompt",
                    ".generate-input",
                    
                    # Generic selectors
                    "textarea",
                    "input[type='text']",
                    "[role='textbox']",
                    "[contenteditable='true']",
                    
                    # Form elements
                    "form textarea",
                    "form input[type='text']"
                ]
                
                found_selector = None
                for selector in prompt_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element and element.is_visible():
                            print(f"{Colors.GREEN}✅ Tìm thấy ô input: {selector}{Colors.ENDC}")
                            found_selector = selector
                            break
                    except:
                        continue
                
                if not found_selector:
                    print(f"{Colors.FAIL}❌ KHÔNG TÌM THẤY Ô INPUT!{Colors.ENDC}")
                    page.screenshot(path="debug_no_input.png")
                    print(f"{Colors.WARNING}📸 Screenshot đã lưu: debug_no_input.png{Colors.ENDC}")
                    return
                
                # Test nhập prompt bằng nhiều cách
                print(f"{Colors.BLUE}📝 Test nhập prompt: '{prompt}'...{Colors.ENDC}")
                
                # Method 1: Click + Fill
                try:
                    page.click(found_selector, timeout=10000)
                    time.sleep(0.5)
                    page.fill(found_selector, prompt)
                    current_value = page.input_value(found_selector)
                    print(f"{Colors.GREEN}✅ Method 1 thành công: '{current_value}'{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.FAIL}❌ Method 1 thất bại: {e}{Colors.ENDC}")
                    
                    # Method 2: JavaScript force
                    try:
                        js_code = f"""
                        const element = document.querySelector('{found_selector}');
                        if (element) {{
                            element.focus();
                            element.value = '{prompt}';
                            element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                        """
                        page.evaluate(js_code)
                        current_value = page.evaluate(f"document.querySelector('{found_selector}').value")
                        print(f"{Colors.GREEN}✅ Method 2 (JS) thành công: '{current_value}'{Colors.ENDC}")
                    except Exception as e2:
                        print(f"{Colors.FAIL}❌ Method 2 (JS) cũng thất bại: {e2}{Colors.ENDC}")
                
                # Screenshot sau khi nhập
                page.screenshot(path="debug_after_input.png")
                print(f"{Colors.GREEN}📸 Screenshot sau khi nhập: debug_after_input.png{Colors.ENDC}")
                
                # Tìm nút generate
                print(f"{Colors.BLUE}🔍 Tìm nút Generate...{Colors.ENDC}")
                generate_selectors = [
                    "button[data-testid*='generate']",
                    "button:has-text('Generate')",
                    "button:has-text('Create')",
                    ".generate-btn",
                    "input[type='submit']"
                ]
                
                generate_found = False
                for selector in generate_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element and element.is_visible():
                            print(f"{Colors.GREEN}✅ Tìm thấy nút generate: {selector}{Colors.ENDC}")
                            generate_found = True
                            
                            # Highlight nút để xem
                            page.evaluate(f"""
                                document.querySelector('{selector}').style.border = '3px solid red';
                            """)
                            break
                    except:
                        continue
                
                if not generate_found:
                    print(f"{Colors.FAIL}❌ KHÔNG TÌM THẤY NÚT GENERATE!{Colors.ENDC}")
                
                # Screenshot cuối
                page.screenshot(path="debug_final.png")
                print(f"{Colors.GREEN}📸 Screenshot cuối: debug_final.png{Colors.ENDC}")
                
                print(f"\n{Colors.BOLD}🎯 TỔNG KẾT DEBUG:{Colors.ENDC}")
                print(f"  ✅ Cookies: {len(cookies)} cookies đã set")
                print(f"  ✅ Input field: {'Tìm thấy' if found_selector else 'KHÔNG TÌM THẤY'}")
                print(f"  ✅ Generate button: {'Tìm thấy' if generate_found else 'KHÔNG TÌM THẤY'}")
                print(f"  📁 Screenshots: debug_*.png")
                
                if show_browser:
                    input(f"\n{Colors.WARNING}⏸️ Nhấn Enter để đóng browser...{Colors.ENDC}")
                
            except Exception as e:
                print(f"{Colors.FAIL}❌ Lỗi debug: {e}{Colors.ENDC}")
                page.screenshot(path="debug_error.png")
                
            finally:
                browser.close()
                
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi tổng quát: {e}{Colors.ENDC}")
        traceback.print_exc()


# ========================================================================================
# COMMANDS RIÊNG BIỆT CHO TẠO ẢNH VÀ VIDEO
# ========================================================================================

@cli.command()
@click.option('--file', '-f', type=str, help='Đường dẫn tới file prompt (.txt, .json, .docx)')
@click.option('--topic', '-t', type=str, help='Chủ đề để sinh prompt bằng AI (tiếng Việt)')
@click.option('--prompt', '-p', type=str, help='Prompt trực tiếp (tiếng Anh)')
@click.option('--num-images', default=4, help='Số lượng ảnh sinh ra (mặc định: 4)')
@click.option('--download-count', default=None, type=int, help='Số lượng ảnh tải về (mặc định: tất cả)')
@click.option('--filename-prefix', type=str, help='Tiền tố tên file ảnh')
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
def image(file, topic, prompt, num_images, download_count, filename_prefix, show_browser):
    """CHỈ TẠO ẢNH - Sinh ảnh từ prompt, file hoặc AI"""
    print(f"{Colors.GREEN}{Colors.BOLD}🎨 CHẾ ĐỘ TẠO ẢNH{Colors.ENDC}")
    
    # Kiểm tra input
    input_count = sum([bool(file), bool(topic), bool(prompt)])
    if input_count == 0:
        print(f"{Colors.FAIL}❌ Vui lòng cung cấp một trong các tùy chọn:{Colors.ENDC}")
        print(f"   --file: Đường dẫn file prompt")
        print(f"   --topic: Chủ đề tiếng Việt (dùng AI)")
        print(f"   --prompt: Prompt trực tiếp tiếng Anh")
        sys.exit(1)
        
    if input_count > 1:
        print(f"{Colors.FAIL}❌ Chỉ được chọn một tùy chọn input duy nhất{Colors.ENDC}")
        sys.exit(1)
    
    try:
        cookies = load_cookie_from_template()
        if not cookies:
            print(f"{Colors.FAIL}❌ Không thể load cookie. Vui lòng cập nhật cookie_template.txt{Colors.ENDC}")
            sys.exit(1)
        
        # Chuẩn bị prompt data
        prompt_item = {
            'num_images': num_images,
            'download_count': download_count if download_count is not None else num_images,
            'filename_prefix': filename_prefix
        }
        
        if file:
            # Từ file
            print(f"{Colors.BLUE}📁 Đang đọc prompt từ file: {file}{Colors.ENDC}")
            if not os.path.exists(file):
                print(f"{Colors.FAIL}❌ Không tìm thấy file: {file}{Colors.ENDC}")
                sys.exit(1)
                
            loader = PromptLoader()
            file_data = loader.load_prompt(file)
            prompt_item['content'] = file_data.get('image_prompt', file_data.get('prompt', ''))
            
        elif topic:
            # Từ AI
            print(f"{Colors.BLUE}🤖 Đang sinh prompt AI từ chủ đề: {topic}{Colors.ENDC}")
            
            try:
                gemini_generator = GeminiPromptGenerator()
                ai_result = gemini_generator.generate_prompt(topic, save_to_file=True)
                prompt_item['content'] = ai_result['image_prompt']
                print(f"{Colors.GREEN}✅ Đã sinh prompt AI thành công!{Colors.ENDC}")
                print(f"📁 File prompt: {ai_result.get('file_path', 'N/A')}")
                print(f"🎨 Image prompt: {ai_result['image_prompt'][:100]}...")
            except Exception as e:
                print(f"{Colors.FAIL}❌ Lỗi sinh prompt AI: {e}{Colors.ENDC}")
                print(f"{Colors.WARNING}🔧 Đang chuyển sang chế độ tạo prompt thủ công...{Colors.ENDC}")
                
                manual_prompt = create_manual_prompt(topic)
                if manual_prompt:
                    prompt_item['content'] = manual_prompt['image_prompt']
                else:
                    print(f"{Colors.FAIL}❌ Không thể tạo prompt thủ công{Colors.ENDC}")
                    sys.exit(1)
                    
        else:
            # Prompt trực tiếp
            print(f"{Colors.BLUE}✍️ Sử dụng prompt trực tiếp{Colors.ENDC}")
            prompt_item['content'] = prompt
        
        if not prompt_item['content']:
            print(f"{Colors.FAIL}❌ Prompt rỗng{Colors.ENDC}")
            sys.exit(1)
        
        # Tạo ảnh
        print(f"{Colors.GREEN}🎨 Bắt đầu sinh ảnh...{Colors.ENDC}")
        print(f"🎨 Sinh {num_images} ảnh, tải về {prompt_item['download_count']} ảnh")
        print(f"📝 Prompt: {prompt_item['content'][:100]}...")
        
        downloaded_files = process_single_image_batch(prompt_item, show_browser, cookies)
        
        if downloaded_files:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ TẠO ẢNH THÀNH CÔNG!{Colors.ENDC}")
            print(f"{Colors.GREEN}📸 Đã tải về {len(downloaded_files)} ảnh:{Colors.ENDC}")
            for i, file_path in enumerate(downloaded_files, 1):
                print(f"   {i}. {os.path.basename(file_path)}")
            print(f"{Colors.BLUE}📁 Vị trí: thư mục output/{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Thất bại sinh ảnh{Colors.ENDC}")
            sys.exit(1)
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi: {str(e)}{Colors.ENDC}")
        sys.exit(1)


@cli.command()
@click.option('--file', '-f', type=str, help='Đường dẫn tới file prompt (.txt, .json, .docx)')
@click.option('--topic', '-t', type=str, help='Chủ đề để sinh prompt bằng AI (tiếng Việt)')
@click.option('--prompt', '-p', type=str, help='Prompt trực tiếp (tiếng Anh)')
@click.option('--image', '-i', type=str, help='Đường dẫn ảnh để tạo video (image-to-video)')
@click.option('--duration', default='5s', type=click.Choice(['5s', '10s']), help='Thời lượng video (mặc định: 5s)')
@click.option('--ratio', default='16:9', type=click.Choice(['1:1', '16:9', '9:16']), help='Tỉ lệ khung hình (mặc định: 16:9)')
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
def video(file, topic, prompt, image, duration, ratio, show_browser):
    """CHỈ TẠO VIDEO - Sinh video từ prompt hoặc ảnh"""
    print(f"{Colors.GREEN}{Colors.BOLD}🎬 CHẾ ĐỘ TẠO VIDEO{Colors.ENDC}")
    
    # Kiểm tra input
    input_count = sum([bool(file), bool(topic), bool(prompt)])
    if input_count == 0 and not image:
        print(f"{Colors.FAIL}❌ Vui lòng cung cấp một trong các tùy chọn:{Colors.ENDC}")
        print(f"   --file: Đường dẫn file prompt")
        print(f"   --topic: Chủ đề tiếng Việt (dùng AI)")
        print(f"   --prompt: Prompt trực tiếp tiếng Anh")
        print(f"   --image: Đường dẫn ảnh (image-to-video)")
        sys.exit(1)
        
    if input_count > 1:
        print(f"{Colors.FAIL}❌ Chỉ được chọn một tùy chọn input duy nhất{Colors.ENDC}")
        sys.exit(1)
    
    try:
        cookies = load_cookie_from_template()
        if not cookies:
            print(f"{Colors.FAIL}❌ Không thể load cookie. Vui lòng cập nhật cookie_template.txt{Colors.ENDC}")
            sys.exit(1)
        
        # Chuẩn bị prompt data
        prompt_item = {
            'duration': duration,
            'ratio': ratio
        }
        
        # Xử lý prompt
        if file:
            # Từ file
            print(f"{Colors.BLUE}📁 Đang đọc prompt từ file: {file}{Colors.ENDC}")
            if not os.path.exists(file):
                print(f"{Colors.FAIL}❌ Không tìm thấy file: {file}{Colors.ENDC}")
                sys.exit(1)
                
            loader = PromptLoader()
            file_data = loader.load_prompt(file)
            prompt_item['content'] = file_data.get('video_prompt', file_data.get('prompt', ''))
            
            # Lấy duration và ratio từ file nếu có
            prompt_item['duration'] = file_data.get('video_duration', duration)
            prompt_item['ratio'] = file_data.get('video_ratio', ratio)
            
        elif topic:
            # Từ AI
            print(f"{Colors.BLUE}🤖 Đang sinh prompt AI từ chủ đề: {topic}{Colors.ENDC}")
            
            try:
                gemini_generator = GeminiPromptGenerator()
                ai_result = gemini_generator.generate_prompt(topic, save_to_file=True)
                prompt_item['content'] = ai_result['video_prompt']
                prompt_item['duration'] = ai_result.get('video_duration', duration)
                prompt_item['ratio'] = ai_result.get('video_ratio', ratio)
                print(f"{Colors.GREEN}✅ Đã sinh prompt AI thành công!{Colors.ENDC}")
                print(f"📁 File prompt: {ai_result.get('file_path', 'N/A')}")
                print(f"🎬 Video prompt: {ai_result['video_prompt'][:100]}...")
            except Exception as e:
                print(f"{Colors.FAIL}❌ Lỗi sinh prompt AI: {e}{Colors.ENDC}")
                print(f"{Colors.WARNING}🔧 Đang chuyển sang chế độ tạo prompt thủ công...{Colors.ENDC}")
                
                manual_prompt = create_manual_prompt(topic)
                if manual_prompt:
                    prompt_item['content'] = manual_prompt['video_prompt']
                else:
                    print(f"{Colors.FAIL}❌ Không thể tạo prompt thủ công{Colors.ENDC}")
                    sys.exit(1)
                    
        elif prompt:
            # Prompt trực tiếp
            print(f"{Colors.BLUE}✍️ Sử dụng prompt trực tiếp{Colors.ENDC}")
            prompt_item['content'] = prompt
            
        elif image:
            # Image-to-video
            print(f"{Colors.BLUE}🖼️ Tạo video từ ảnh: {image}{Colors.ENDC}")
            if not os.path.exists(image):
                print(f"{Colors.FAIL}❌ Không tìm thấy ảnh: {image}{Colors.ENDC}")
                sys.exit(1)
            
            # Sử dụng tên file làm prompt mặc định
            prompt_item['content'] = f'Video from image: {os.path.basename(image)}'
        
        # Tạo video
        output_dir = create_output_dir()
        
        print(f"{Colors.GREEN}🎬 Bắt đầu sinh video...{Colors.ENDC}")
        print(f"⏱️ Thời lượng: {prompt_item['duration']}")
        print(f"📐 Tỉ lệ: {prompt_item['ratio']}")
        
        if image:
            print(f"🖼️ Từ ảnh: {os.path.basename(image)}")
            video_path = process_single_video_from_image(prompt_item, image, show_browser, cookies)
        else:
            print(f"📝 Prompt: {prompt_item['content'][:100]}...")
            # Tạo video từ text prompt - fallback tạo ảnh trước
            print(f"{Colors.WARNING}⚠️ Text-to-video: Tạo ảnh trước rồi chuyển thành video...{Colors.ENDC}")
            
            # Tạo ảnh trước
            temp_prompt_item = {
                'content': prompt_item['content'],
                'num_images': 1,
                'download_count': 1,
                'filename_prefix': 'temp_for_video'
            }
            
            downloaded_files = process_single_image_batch(temp_prompt_item, show_browser, cookies)
            if downloaded_files:
                temp_image = downloaded_files[0]
                print(f"{Colors.GREEN}✅ Đã tạo ảnh tạm: {os.path.basename(temp_image)}{Colors.ENDC}")
                video_path = process_single_video_from_image(prompt_item, temp_image, show_browser, cookies)
            else:
                video_path = None
        
        if video_path:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ TẠO VIDEO THÀNH CÔNG!{Colors.ENDC}")
            print(f"{Colors.GREEN}🎬 Video: {os.path.basename(video_path)}{Colors.ENDC}")
            print(f"{Colors.BLUE}📁 Vị trí: thư mục output/{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}❌ Thất bại sinh video{Colors.ENDC}")
            sys.exit(1)
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi: {str(e)}{Colors.ENDC}")
        sys.exit(1)


@cli.command()
@click.option('--images-dir', type=str, default='output', help='Thư mục chứa ảnh để tạo video (mặc định: output)')
@click.option('--prompts-file', type=str, help='File chứa prompts cho video (mỗi dòng một prompt)')
@click.option('--duration', default='5s', type=click.Choice(['5s', '10s']), help='Thời lượng video (mặc định: 5s)')
@click.option('--ratio', default='16:9', type=click.Choice(['1:1', '16:9', '9:16']), help='Tỉ lệ khung hình (mặc định: 16:9)')
@click.option('--show-browser/--headless', default=False, help='Hiển thị trình duyệt (mặc định: False)')
def images_to_videos(images_dir, prompts_file, duration, ratio, show_browser):
    """TẠO VIDEO TỪ NHIỀU ẢNH - Chuyển đổi hàng loạt ảnh thành video"""
    print(f"{Colors.GREEN}{Colors.BOLD}🎬 CHẾ ĐỘ TẠO VIDEO TỪ ẢNH{Colors.ENDC}")
    
    try:
        # Kiểm tra thư mục ảnh
        if not os.path.exists(images_dir):
            print(f"{Colors.FAIL}❌ Không tìm thấy thư mục ảnh: {images_dir}{Colors.ENDC}")
            sys.exit(1)
        
        # Tìm tất cả ảnh
        image_extensions = ['.png', '.jpg', '.jpeg', '.webp']
        image_files = []
        for ext in image_extensions:
            image_files.extend(Path(images_dir).glob(f'*{ext}'))
            image_files.extend(Path(images_dir).glob(f'*{ext.upper()}'))
        
        if not image_files:
            print(f"{Colors.FAIL}❌ Không tìm thấy ảnh nào trong thư mục: {images_dir}{Colors.ENDC}")
            sys.exit(1)
        
        print(f"{Colors.BLUE}📸 Tìm thấy {len(image_files)} ảnh{Colors.ENDC}")
        
        # Load prompts nếu có
        prompts = []
        if prompts_file and os.path.exists(prompts_file):
            print(f"{Colors.BLUE}📝 Đang đọc prompts từ: {prompts_file}{Colors.ENDC}")
            with open(prompts_file, 'r', encoding='utf-8') as f:
                prompts = [line.strip() for line in f if line.strip()]
        
        # Load cookies
        cookies = load_cookie_from_template()
        if not cookies:
            print(f"{Colors.FAIL}❌ Không thể load cookie. Vui lòng cập nhật cookie_template.txt{Colors.ENDC}")
            sys.exit(1)
        
        # Xử lý từng ảnh
        successful_videos = []
        failed_videos = []
        
        for i, image_path in enumerate(image_files, 1):
            print(f"{Colors.BLUE}\n[{i}/{len(image_files)}] Đang tạo video từ: {image_path.name}{Colors.ENDC}")
            
            try:
                # Chuẩn bị prompt
                prompt_item = {
                    'duration': duration,
                    'ratio': ratio
                }
                
                if i <= len(prompts):
                    prompt_item['content'] = prompts[i-1]
                    print(f"📝 Prompt: {prompts[i-1][:50]}...")
                else:
                    prompt_item['content'] = f'Video animation from image: {image_path.stem}'
                    print(f"📝 Prompt tự động: {prompt_item['content']}")
                
                # Tạo video
                video_path = process_single_video_from_image(prompt_item, str(image_path), show_browser, cookies)
                
                if video_path:
                    successful_videos.append(video_path)
                    print(f"{Colors.GREEN}✅ Thành công: {os.path.basename(video_path)}{Colors.ENDC}")
                else:
                    failed_videos.append(str(image_path))
                    print(f"{Colors.FAIL}❌ Thất bại: {image_path.name}{Colors.ENDC}")
                
                # Delay giữa các request
                if i < len(image_files):
                    print(f"{Colors.BLUE}Chờ 5s...{Colors.ENDC}")
                    import time
                    time.sleep(5)
                    
            except Exception as e:
                failed_videos.append(str(image_path))
                print(f"{Colors.FAIL}❌ Lỗi tạo video từ {image_path.name}: {str(e)}{Colors.ENDC}")
        
        # Tóm tắt kết quả
        print(f"{Colors.GREEN}{Colors.BOLD}\n🏁 HOÀN THÀNH TẠO VIDEO TỪ ẢNH{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Thành công: {len(successful_videos)}/{len(image_files)}{Colors.ENDC}")
        print(f"{Colors.FAIL}❌ Thất bại: {len(failed_videos)}/{len(image_files)}{Colors.ENDC}")
        
        if successful_videos:
            print(f"{Colors.BLUE}\n📹 Video đã tạo:{Colors.ENDC}")
            for video in successful_videos:
                print(f"   {os.path.basename(video)}")
        
        if failed_videos:
            print(f"{Colors.FAIL}\n💥 Ảnh tạo video thất bại:{Colors.ENDC}")
            for img in failed_videos:
                print(f"   {os.path.basename(img)}")
                
    except Exception as e:
        print(f"{Colors.FAIL}❌ Lỗi: {str(e)}{Colors.ENDC}")
        sys.exit(1)


if __name__ == "__main__":
    cli() 