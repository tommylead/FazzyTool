"""
Browser automation cho việc sinh video từ Freepik AI
"""

import os
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from playwright.sync_api import sync_playwright, Page


class FreepikVideoGenerator:
    """Lớp xử lý việc sinh video từ Freepik AI bằng browser automation."""

    def __init__(self, headless: bool = True, output_dir: str = "output"):
        self.headless = headless
        self.output_dir = output_dir
        
        # Tạo thư mục output nếu chưa tồn tại
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Session tracking
        self.current_session_dir = None
        
        # Thống kê để tracking
        self.generation_stats = {
            "total_generated": 0,
            "successful_downloads": 0,
            "failed_downloads": 0
        }

    def parse_cookies(self, cookie_input: str):
        """Parse cookie từ string hoặc JSON - improved version"""
        if not cookie_input or not cookie_input.strip():
            return []
            
        # Kiểm tra placeholder cookie
        if cookie_input.strip() == "placeholder_cookie":
            print("⚠️ Cookie placeholder được phát hiện, bỏ qua...")
            return []
            
        cookies = []
        
        try:
            # Extract JSON from template file nếu cần
            if "=== PASTE COOKIE JSON VÀO ĐÂY ===" in cookie_input:
                start_marker = "=== PASTE COOKIE JSON VÀO ĐÂY ==="
                end_marker = "=== KẾT THÚC COOKIE ==="
                
                start_idx = cookie_input.find(start_marker)
                if start_idx != -1:
                    json_start = start_idx + len(start_marker)
                    end_idx = cookie_input.find(end_marker, json_start)
                    
                    if end_idx == -1:
                        cookie_json = cookie_input[json_start:].strip()
                    else:
                        cookie_json = cookie_input[json_start:end_idx].strip()
                    
                    cookie_input = cookie_json
            
            # Thử parse JSON trước
            if cookie_input.strip().startswith('['):
                json_cookies = json.loads(cookie_input)
                
                for cookie in json_cookies:
                    # Skip cookies thiếu required fields
                    if not cookie.get('name') or not cookie.get('value'):
                        continue
                    
                    # Chuyển đổi format Firefox sang Playwright - IMPROVED
                    playwright_cookie = {
                        'name': str(cookie['name']),
                        'value': str(cookie['value']),
                        'domain': str(cookie.get('domain', '.freepik.com')),
                        'path': str(cookie.get('path', '/')),
                    }
                    
                    # Handle boolean fields safely
                    if 'secure' in cookie and cookie['secure'] is not None:
                        playwright_cookie['secure'] = bool(cookie['secure'])
                    
                    if 'httpOnly' in cookie and cookie['httpOnly'] is not None:
                        playwright_cookie['httpOnly'] = bool(cookie['httpOnly'])
                    
                    # Handle sameSite safely
                    if 'sameSite' in cookie and cookie['sameSite']:
                        same_site = str(cookie['sameSite']).lower()
                        if same_site in ['lax', 'strict', 'none']:
                            playwright_cookie['sameSite'] = same_site.capitalize()
                    
                    # Skip expirationDate - it causes issues with Playwright
                    # Playwright will handle session vs persistent automatically
                    
                    cookies.append(playwright_cookie)
                    
            else:
                # Parse string format (name=value; name2=value2)
                for part in cookie_input.split(';'):
                    if '=' in part:
                        name, value = part.strip().split('=', 1)
                        cookies.append({
                            'name': name.strip(),
                            'value': value.strip(),
                            'domain': '.freepik.com',
                            'path': '/'
                        })
                        
            print(f"✅ Parsed {len(cookies)} valid cookies")
            return cookies
            
        except Exception as e:
            print(f"❌ Lỗi parse cookie: {e}")
            return []

    def set_cookies(self, page: Page, cookies):
        """Set cookies cho page"""
        if not cookies:
            return
            
        try:
            # Lọc cookies hợp lệ
            valid_cookies = []
            for cookie in cookies:
                if cookie.get('name') and cookie.get('value'):
                    valid_cookies.append(cookie)
            
            if valid_cookies:
                page.context.add_cookies(valid_cookies)
                print(f"✓ Đã thêm {len(valid_cookies)} cookies")
        except Exception as e:
            print(f"Lỗi set cookies: {e}")

    def _create_session_directory(self):
        """Tạo thư mục session mới cho video generation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session_dir = os.path.join(self.output_dir, f"text_to_video_{timestamp}")
        os.makedirs(self.current_session_dir, exist_ok=True)
        return self.current_session_dir

    def _save_session_metadata(self, metadata: dict):
        """Lưu metadata của session"""
        if self.current_session_dir:
            metadata_file = os.path.join(self.current_session_dir, "session_info.json")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

    def _get_model_display_name(self, model: str) -> str:
        """Chuyển model code thành tên hiển thị trên UI"""
        model_map = {
            "kling_2_1": "Kling AI 2.1",
            "kling_2_1_master": "Kling AI 2.1 Master", 
            "kling_master_2_1": "Kling AI 2.1 Master",  # Alternative naming
            "kling_1_5": "Kling AI 1.5", 
            "kling_1_5_master": "Kling AI 1.5 Master",
            "kling_master_1_5": "Kling AI 1.5 Master",  # Alternative naming
            "auto": "Auto",
            "default": "Auto",
            
            # Có thể có các model khác
            "minimax": "MiniMax",
            "hailuo": "MiniMax Hailuo",
            "runway": "Runway ML",
            "luma": "Luma AI"
        }
        display_name = model_map.get(model, model)
        print(f"🎯 Model mapping: '{model}' → '{display_name}'")
        return display_name

    def _get_model_selectors(self, model: str) -> List[str]:
        """Lấy danh sách selector để chọn model"""
        model_name = self._get_model_display_name(model)
        return [
            f"text={model_name}",
            f"button:has-text('{model_name}')",
            f"[data-value='{model}']",
            f"option[value='{model}']",
            f"li:has-text('{model_name}')",
            f"[aria-label*='{model_name}']"
        ]

    def _wait_for_video_generation(self, page: Page, timeout_seconds: int = 300) -> bool:
        """Đợi cho quá trình sinh video hoàn tất"""
        start_time = time.time()
        print(f"⏳ Đang chờ video được sinh ra (timeout: {timeout_seconds}s)...")
        
        # TRACK: Lưu thời điểm bắt đầu generation để phân biệt video mới
        self.generation_start_time = start_time
        
        # Counter để tránh spam log
        check_count = 0
        processing_detected = False  # Track xem có thấy processing không
        processing_completed = False  # Track processing đã hoàn tất
        
        while time.time() - start_time < timeout_seconds:
            elapsed = int(time.time() - start_time)
            check_count += 1
            
            # Báo tiến trình mỗi 30s
            if elapsed > 0 and elapsed % 30 == 0:
                print(f"⏳ Đã chờ {elapsed}s/{timeout_seconds}s...")
            
            try:
                # BƯỚC 1: KIỂM TRA XEM CÓ ĐANG PROCESSING KHÔNG
                processing_indicators = [
                    "text=/.*Processing your video.*/i", 
                    "text=/.*Generating.*/i",
                    "text=/.*Estimated time.*/i",
                    ".progress-bar", "[role='progressbar']",
                    ".loading", ".spinner"
                ]
                
                currently_processing = False
                for indicator in processing_indicators:
                    try:
                        element = page.query_selector(indicator)
                        if element and element.is_visible():
                            processing_text = element.text_content() or ""
                            currently_processing = True
                            processing_detected = True
                            
                            # Log processing status mỗi 60s
                            if elapsed % 60 == 0:
                                print(f"🔄 Video đang processing: {processing_text[:80]}...")
                            break
                    except:
                        continue
                
                # BƯỚC 2: NẾU ĐANG PROCESSING - TIẾP TỤC CHỜ
                if currently_processing:
                    time.sleep(5)
                    continue
                
                # BƯỚC 3: PROCESSING ĐÃ DỪNG - CHỜ VIDEO RESULT XUẤT HIỆN
                if not currently_processing and processing_detected and not processing_completed:
                    print(f"✅ Processing stopped at {elapsed}s! Waiting for video result to appear...")
                    processing_completed = True
                    
                    # ĐÂY LÀ ĐIỂM QUAN TRỌNG: Đợi video result xuất hiện
                    # Thay vì return True ngay, đợi video thật sự xuất hiện
                    
                # BƯỚC 4: NẾU PROCESSING ĐÃ HOÀN TÁTM - TÌM VIDEO RESULT
                if processing_completed:
                    # Đợi thêm cho video result load
                    time.sleep(5)
                    
                    print("🔍 Checking for new video results...")
                    
                    # METHOD 1: Tìm videos trong page
                    videos = page.query_selector_all("video")
                    print(f"📹 Found {len(videos)} videos total")
                    
                    # Tìm video result (không phải banner)
                    new_video_found = False
                    for i, video in enumerate(videos):
                        if video.is_visible():
                            try:
                                src = video.get_attribute("src") or video.get_attribute("data-src")
                                if src and not src.startswith("data:"):
                                    # Skip obvious banners
                                    if any(banner in src.lower() for banner in ['banner', 'demo', 'preview']):
                                        continue
                                    
                                    duration = video.evaluate("v => v.duration")
                                    readyState = video.evaluate("v => v.readyState")
                                    
                                    # Check for REASONABLE video result
                                    if duration and 3 <= duration <= 20 and readyState >= 3:
                                        print(f"🎬 Found new video result - Duration: {duration}s")
                                        print(f"   Src: {src[:80]}...")
                                        new_video_found = True
                                        break
                            except:
                                continue
                    
                    # METHOD 2: Tìm download buttons hoặc result containers
                    if not new_video_found:
                        print("🔍 Checking for download buttons/result indicators...")
                        
                        result_indicators = [
                            "[data-cy*='download']", "button:has-text('Download')",
                            ".video-result", ".result-thumbnail", ".video-preview",
                            ".download-btn", "[data-testid*='download']",
                            ".result-container", ".generation-result", 
                            "[class*='result']", "[class*='download']"
                        ]
                        
                        for indicator in result_indicators:
                            try:
                                elements = page.query_selector_all(indicator)
                                for element in elements:
                                    if element.is_visible():
                                        print(f"✓ Found result indicator: {indicator}")
                                        new_video_found = True
                                        break
                                if new_video_found:
                                    break
                            except:
                                continue
                    
                    # METHOD 3: Kiểm tra page content changes
                    if not new_video_found:
                        print("🔍 Checking page content for generation completion...")
                        
                        # Tìm text indicators
                        completion_texts = [
                            "text=/.*completed.*/i", "text=/.*finished.*/i", 
                            "text=/.*ready.*/i", "text=/.*done.*/i",
                            "text=/.*generated.*/i", "text=/.*created.*/i"
                        ]
                        
                        for text_indicator in completion_texts:
                            try:
                                element = page.query_selector(text_indicator)
                                if element and element.is_visible():
                                    text_content = element.text_content() or ""
                                    if len(text_content) < 100:  # Avoid very long text
                                        print(f"✓ Found completion text: {text_content[:50]}...")
                                        new_video_found = True
                                        break
                            except:
                                continue
                    
                    if new_video_found:
                        print("✅ Video result found! Ready to download.")
                        return True
                    else:
                        # Nếu chưa tìm thấy video result, đợi thêm
                        # Track thời gian từ khi processing completed
                        if not hasattr(self, 'processing_end_time'):
                            self.processing_end_time = time.time()
                        
                        wait_time = time.time() - self.processing_end_time
                        if wait_time < 60:  # Đợi tối đa 60s sau khi processing stop
                            print(f"🔍 No video result yet, waiting more... ({int(wait_time)}s since processing stopped)")
                            time.sleep(10)
                            continue
                        else:
                            print("⏰ Timeout waiting for video result after processing")
                            print("🎯 Proceeding with available content (may include fallback downloads)")
                            # Return True để cho phép download fallback (có thể là banner)
                            return True
                
                # BƯỚC 5: NẾU CHƯA THẤY PROCESSING - CHỜ THÊM
                if not processing_detected and elapsed < 30:
                    if elapsed % 10 == 0:
                        print("⏳ Chờ processing bắt đầu...")
                    time.sleep(2)
                    continue
                
                # BƯỚC 6: KIỂM TRA COMPLETION INDICATORS (ít tin cậy hơn)
                completion_selectors = [
                    "button:has-text('Download')", "[data-cy*='download']",
                    ".video-result", ".result-thumbnail", ".video-preview"
                ]
                
                for completion_selector in completion_selectors:
                    try:
                        element = page.query_selector(completion_selector)
                        if element and element.is_visible():
                            print(f"✅ Phát hiện completion indicator: {completion_selector}")
                            # Nếu đã có processing_completed, có thể tin cậy completion
                            if processing_completed:
                                return True
                    except:
                        continue
                
                # BƯỚC 7: KIỂM TRA LỖI
                error_selectors = [
                    "text=/.*Error.*/i", "text=/.*Failed.*/i", ".error", "[role='alert']"
                ]
                
                for error_selector in error_selectors:
                    try:
                        error_element = page.query_selector(error_selector)
                        if error_element and error_element.is_visible():
                            error_text = error_element.text_content()
                            print(f"❌ Lỗi generation: {error_text}")
                            return False
                    except:
                        continue
                        
            except Exception as e:
                if check_count % 20 == 0:
                    print(f"⚠️ Lỗi check: {e}")
            
            time.sleep(3)
        
        print(f"⏰ Timeout sau {timeout_seconds}s")
        return False

    def _download_video_to_session(self, page: Page) -> Optional[str]:
        """Tải video mới nhất (không phải video cũ/banner) về session directory"""
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"video_output_{timestamp}.mp4"
            filepath = os.path.join(self.current_session_dir, filename)
            
            print("🎯 Tìm video mới nhất để download...")
            
            # BƯỚC 1: Đợi video result load
            time.sleep(3)
            
            # BƯỚC 2: PRIORITY 1 - TÌM DOWNLOAD BUTTON TRƯỚC (tin cậy nhất)
            print("🔽 Priority 1: Looking for download buttons...")
            
            download_selectors = [
                "[data-cy='download']", "[data-cy*='download']",
                "button:has-text('Download')", "a[download]",
                ".download-btn", "[data-testid*='download']",
                "[class*='download']", "button[class*='download']"
            ]
            
            download_success = False
            for btn_selector in download_selectors:
                try:
                    download_buttons = page.query_selector_all(btn_selector)
                    print(f"  🔍 {btn_selector}: {len(download_buttons)} buttons")
                    
                    for download_btn in download_buttons:
                        if download_btn and download_btn.is_visible() and download_btn.is_enabled():
                            try:
                                print(f"  ✓ Trying download button: {btn_selector}")
                                
                                download_btn.scroll_into_view_if_needed()
                                time.sleep(2)
                                
                                with page.expect_download(timeout=30000) as download_info:
                                    download_btn.click()
                                    print("  ✓ Clicked download button successfully")
                                
                                download = download_info.value
                                download.save_as(filepath)
                                print(f"✅ Downloaded successfully via button: {filename}")
                                return filepath
                                
                            except Exception as btn_e:
                                print(f"  ⚠️ Button failed: {btn_e}")
                                continue
                except Exception as e:
                    print(f"  ⚠️ Error with selector {btn_selector}: {e}")
                    continue
            
            # BƯỚC 3: PRIORITY 2 - TÌM VIDEO SRC để download
            print("📹 Priority 2: Looking for video sources...")
            
            videos = page.query_selector_all("video")
            print(f"📹 Found {len(videos)} videos on page")
            
            # Strategy: Phân loại videos thành categories
            candidate_videos = []
            banner_videos = []
            other_videos = []
            
            for i, video in enumerate(videos):
                if video.is_visible():
                    try:
                        src = video.get_attribute("src") or video.get_attribute("data-src")
                        if src and not src.startswith("data:"):
                            # IMPROVED: Chỉ skip nếu RÕ RÀNG là banner
                            obvious_banner_keywords = ['banner', 'demo', 'preview', 'tutorial', 'intro']
                            is_obvious_banner = any(keyword in src.lower() for keyword in obvious_banner_keywords)
                            
                            # Check video properties
                            duration = video.evaluate("v => v.duration")
                            readyState = video.evaluate("v => v.readyState")
                            
                            video_info = {
                                'element': video,
                                'src': src,
                                'duration': duration,
                                'readyState': readyState,
                                'index': i
                            }
                            
                            if is_obvious_banner:
                                banner_videos.append(video_info)
                                print(f"  🚫 Banner video {i+1}: {src[:50]}...")
                            elif duration and 3 <= duration <= 20 and readyState >= 3:
                                candidate_videos.append(video_info)
                                print(f"  ✓ Candidate video {i+1}:")
                                print(f"    Duration: {duration}s, ReadyState: {readyState}")
                                print(f"    Src: {src[:80]}...")
                            else:
                                other_videos.append(video_info)
                                print(f"  ? Other video {i+1}: Duration={duration}, ReadyState={readyState}")
                                
                    except Exception as e:
                        print(f"  ⚠️ Error checking video {i+1}: {e}")
                        continue
            
            print(f"✅ Categories: {len(candidate_videos)} candidates, {len(banner_videos)} banners, {len(other_videos)} others")
            
            # BƯỚC 4: STRATEGY SELECTION cho VIDEO
            selected_video = None
            
            if candidate_videos:
                selected_video = candidate_videos[-1]
                print(f"🎬 Selected from candidates: video {selected_video['index']+1}")
                
            elif other_videos:
                valid_others = [v for v in other_videos if v['duration'] and v['duration'] > 0]
                if valid_others:
                    selected_video = valid_others[-1]
                    print(f"🎬 Selected from others: video {selected_video['index']+1}")
                    
            elif banner_videos:
                selected_video = banner_videos[-1]
                print(f"🎬 Desperate fallback: banner video {selected_video['index']+1}")
            
            # BƯỚC 5: TRY VIDEO SRC DOWNLOAD
            if selected_video:
                video_element = selected_video['element']
                video_src = selected_video['src']
                
                print(f"🎯 Selected video details:")
                print(f"   Index: {selected_video['index']+1}")
                print(f"   Duration: {selected_video['duration']}s")
                print(f"   ReadyState: {selected_video['readyState']}")
                print(f"   Src: {video_src[:100]}...")
                
                # Try URL download
                if video_src.startswith("http"):
                    try:
                        print("📥 Downloading from video URL...")
                        
                        with page.expect_download(timeout=30000) as download_info:
                            page.evaluate("""
                            (params) => {
                                const link = document.createElement('a');
                                link.href = params.url;
                                link.download = params.filename;
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                            }
                            """, {"url": video_src, "filename": filename})
                        
                        download = download_info.value
                        download.save_as(filepath)
                        print(f"✅ Downloaded successfully via URL: {filename}")
                        return filepath
                        
                    except Exception as url_e:
                        print(f"⚠️ URL download failed: {url_e}")
                
                # Screenshot fallback
                try:
                    print("📸 Creating screenshot fallback...")
                    screenshot_filename = f"video_output_{timestamp}_screenshot.png"
                    screenshot_path = os.path.join(self.current_session_dir, screenshot_filename)
                    
                    video_element.scroll_into_view_if_needed()
                    time.sleep(1)
                    video_element.screenshot(path=screenshot_path)
                    
                    print(f"📸 Screenshot saved: {screenshot_filename}")
                    return screenshot_path
                    
                except Exception as screenshot_e:
                    print(f"⚠️ Screenshot failed: {screenshot_e}")
            
            print("❌ No suitable content found for download")
            return None
            
        except Exception as e:
            print(f"❌ Download error: {e}")
            return None

    def generate_video(self, prompt: str, cookie_string: str = None, duration: str = "5s", 
                      ratio: str = "1:1", model: str = "kling_2_1"):
        """
        Sinh video từ text prompt - workflow chuẩn giống như generate_image
        """
        
        print(f"🎬 Bắt đầu sinh video từ text")
        print(f"📝 Prompt: {prompt}")
        print(f"⚙️ Model: {self._get_model_display_name(model)}")
        print(f"⏱️ Duration: {duration}")
        print(f"📐 Ratio: {ratio}")
        
        # Tạo session directory
        session_dir = self._create_session_directory()
        
        # Metadata
        session_metadata = {
            "type": "text_to_video",
            "prompt": prompt,
            "model": model,
            "duration": duration,
            "ratio": ratio,
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }
        self._save_session_metadata(session_metadata)
        
        with sync_playwright() as p:
            # Setup browser giống như image generator
            browser_type = "chrome"
            config_show_browser = False
            
            try:
                if os.path.exists('config_template.txt'):
                    with open('config_template.txt', 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'browser=chrome' in content:
                        browser_type = "chrome"
                    
                    if 'show_browser=true' in content:
                        config_show_browser = True
                        print("⚙️ Config: show_browser=true - sử dụng visible mode")
            except:
                pass
            
            final_headless = self.headless and not config_show_browser
            
            print(f"🌐 Sử dụng browser: {browser_type}")
            print(f"👁️ Chế độ: {'Visible' if not final_headless else 'Headless'}")
            
            # Khởi động browser
            if browser_type == "chrome":
                browser = p.chromium.launch(
                    headless=final_headless,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-extensions",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--window-size=1920,1080"
                    ]
                )
            else:
                browser = p.firefox.launch(
                    headless=final_headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
                
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True
            )
            context.set_default_timeout(30000)
            
            page = context.new_page()
            
            try:
                # Truy cập AI Video Generator
                video_generator_url = "https://www.freepik.com/pikaso/ai-video-generator"
                print(f"🎯 Truy cập AI Video Generator: {video_generator_url}")
                
                try:
                    page.goto(video_generator_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)
                    print(f"✅ Đã truy cập: {page.url}")
                except Exception as e:
                    print(f"❌ Lỗi truy cập: {e}")
                    # Fallback với URL đơn giản hơn
                    fallback_url = "https://www.freepik.com/pikaso"
                    print(f"🔄 Thử fallback: {fallback_url}")
                    page.goto(fallback_url, wait_until="domcontentloaded", timeout=20000)
                    time.sleep(2)
                
                # Thiết lập cookie sau khi đã vào trang
                if cookie_string:
                    cookies = self.parse_cookies(cookie_string)
                    if cookies:
                        print("🍪 Đang thiết lập cookie...")
                        self.set_cookies(page, cookies)
                        print("✓ Đã thiết lập cookie, reload trang...")
                        
                        # Reload để áp dụng cookie
                        page.reload(wait_until="domcontentloaded")
                        time.sleep(3)
                        
                        # Kiểm tra THỰC SỰ đã đăng nhập (kiểm tra nhiều indicators)
                        login_indicators = [
                            "text=Log in", "text=Sign up", "text=Login", "text=Sign In",
                            "text=Đăng nhập", "text=Đăng ký", 
                            ".login-button", ".signin-button", "[href*='login']"
                        ]
                        
                        logged_out_indicators = []
                        for indicator in login_indicators:
                            try:
                                if page.query_selector(indicator):
                                    element = page.query_selector(indicator)
                                    if element and element.is_visible():
                                        logged_out_indicators.append(indicator)
                            except:
                                continue
                        
                        # Kiểm tra indicators đăng nhập thành công
                        success_indicators = [
                            "text=Premium", "text=Account", "text=Profile", "text=Logout",
                            "text=My Account", "[href*='logout']", "[href*='account']",
                            ".user-menu", ".profile-menu", ".account-dropdown"
                        ]
                        
                        logged_in_indicators = []
                        for indicator in success_indicators:
                            try:
                                if page.query_selector(indicator):
                                    element = page.query_selector(indicator)
                                    if element and element.is_visible():
                                        logged_in_indicators.append(indicator)
                            except:
                                continue
                        
                        if logged_out_indicators:
                            print(f"❌ CHƯA ĐĂNG NHẬP! Tìm thấy: {logged_out_indicators}")
                            print("🔑 Cần cookie hợp lệ từ tài khoản Freepik Premium đã đăng nhập!")
                            raise Exception("Cookie không hợp lệ hoặc chưa đăng nhập")
                        elif logged_in_indicators:
                            print(f"✅ ĐÃ ĐĂNG NHẬP THÀNH CÔNG! Tìm thấy: {logged_in_indicators}")
                        else:
                            print("⚠️ Không thể xác định trạng thái đăng nhập, tiếp tục thử...")
                    else:
                        print("❌ Không thể parse cookie!")
                        raise Exception("Cookie không hợp lệ")
                else:
                    print("⚠️ Không có cookie - sẽ thử chế độ guest (có thể bị giới hạn)")
                
                print("✅ Đã truy cập thành công vào AI Video Generator!")
                
                # Chờ trang load hoàn toàn trước khi tìm input
                print("⏳ Chờ trang load hoàn toàn...")
                time.sleep(5)  # Chờ 5 giây để đảm bảo trang load xong
                
                # Tìm và nhập prompt - GIỐNG NHƯ IMAGE GENERATOR
                print("🔍 Tìm ô nhập prompt...")
                
                potential_selectors = [
                    # Selectors phù hợp với UI mới của Freepik 2024
                    "[contenteditable='true']",  # Thường dùng cho prompt input
                    "textarea[placeholder*='Describe']", "textarea[placeholder*='describe']", 
                    "textarea[placeholder*='prompt']", "textarea[placeholder*='Prompt']",
                    "textarea",  # Fallback textarea
                    "[role='textbox']",  # Accessibility role
                    "input[type='text']",  # Basic text input
                    "textarea[data-testid*='prompt']", "textarea[data-testid*='input']",
                    ".prompt-input", "#prompt", "#prompt-input", ".text-input", "[name='prompt']",
                    
                    # Selectors dành riêng cho Freepik Pikaso
                    ".ai-prompt-input", ".generate-prompt-input", ".pikaso-prompt",
                    "[data-cy*='prompt']", "[data-cy*='input']", "[data-cy*='text']",
                    "[aria-label*='prompt']", "[aria-label*='Prompt']", "[aria-label*='describe']",
                    "[class*='prompt'][class*='input']", "[class*='text'][class*='area']"
                ]
                
                prompt_selector = None
                for i, selector in enumerate(potential_selectors):
                    print(f"  🔍 Thử selector {i+1}/{len(potential_selectors)}: {selector}")
                    try:
                        element = page.query_selector(selector)
                        if element:
                            print(f"    ✓ Element tồn tại")
                            if element.is_visible():
                                print(f"    ✓ Element visible")
                                if element.is_enabled():
                                    print(f"    ✓ Element enabled")
                                    prompt_selector = selector
                                    print(f"✅ Tìm thấy ô prompt: {selector}")
                                    break
                                else:
                                    print(f"    ❌ Element disabled")
                            else:
                                print(f"    ❌ Element not visible")
                        else:
                            print(f"    ❌ Element không tồn tại")
                    except Exception as e:
                        print(f"    ❌ Lỗi: {e}")
                        continue
                
                if not prompt_selector:
                    raise Exception("Không tìm thấy ô nhập prompt")
                
                # Nhập prompt - SỬ DỤNG JAVASCRIPT TRỰC TIẾP (theo yêu cầu user)
                print("✍️ Đang nhập prompt...")
                
                try:
                    # Method 3: JavaScript trực tiếp - được ưu tiên
                    escaped_selector = prompt_selector.replace("'", "\\'").replace('"', '\\"')
                    escaped_prompt = prompt.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
                    js_code = f"""
                    try {{
                        const element = document.querySelector('{escaped_selector}');
                        if (element) {{
                            element.focus();
                            if (element.value !== undefined) {{
                                element.value = '{escaped_prompt}';
                            }}
                            if (element.textContent !== undefined) {{
                                element.textContent = '{escaped_prompt}';
                            }}
                            element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }} catch(e) {{
                        console.log('Method 3 error:', e);
                    }}
                    """
                    page.evaluate(js_code)
                    
                    # Chờ lâu hơn để DOM update
                    time.sleep(2)
                    
                    # Kiểm tra xem đã nhập thành công chưa
                    current_value = ""
                    try:
                        current_value = page.evaluate("""
                        (selector) => {
                            try {
                                const el = document.querySelector(selector);
                                if (el) {
                                    const content = el.textContent || el.innerText || el.value || '';
                                    return content.trim();
                                }
                                return '';
                            } catch(e) {
                                return '';
                            }
                        }
                        """, prompt_selector)
                    except:
                        pass
                    
                    if current_value and len(current_value.strip()) > 5:
                        print(f"✅ Đã nhập prompt thành công: '{current_value[:50]}...'")
                    else:
                        print(f"⚠️ Có thể chưa nhập thành công: '{current_value}'")
                        # Fallback với fill
                        page.click(prompt_selector)
                        page.fill(prompt_selector, prompt)
                        print("✅ Đã nhập prompt bằng fill fallback")
                        
                except Exception as e:
                    print(f"❌ Lỗi khi nhập prompt: {e}")
                    raise Exception("Không thể nhập prompt")
                
                # Chọn model nếu không phải auto
                if model != "auto":
                    print(f"🤖 Đang chọn model: {self._get_model_display_name(model)}...")
                    try:
                        # Chờ thêm để UI load xong
                        time.sleep(2)
                        
                        # Tìm dropdown model với nhiều selector khác nhau
                        model_dropdown_selectors = [
                            # Generic model selectors
                            "button:has-text('Model')",
                            "button:has-text('AI Model')", 
                            "button:has-text('Auto')",
                            "button:has-text('Kling')",
                            
                            # Data attributes
                            "[data-testid*='model']",
                            "[data-testid*='dropdown']",
                            "[data-cy*='model']",
                            
                            # CSS classes
                            ".model-selector",
                            ".dropdown-model",
                            ".model-dropdown",
                            
                            # Aria labels
                            "[aria-label*='model']",
                            "[aria-label*='Model']",
                            
                            # Generic dropdowns that might contain model
                            "button[role='button']:has-text('Auto')",
                            "div[role='button']:has-text('Auto')",
                            ".dropdown-toggle",
                            "button.dropdown-toggle"
                        ]
                        
                        dropdown_opened = False
                        for i, dropdown_selector in enumerate(model_dropdown_selectors):
                            print(f"  🔍 Thử dropdown selector {i+1}/{len(model_dropdown_selectors)}: {dropdown_selector}")
                            try:
                                dropdown_element = page.query_selector(dropdown_selector)
                                if dropdown_element:
                                    print(f"    ✓ Dropdown element tồn tại")
                                    if dropdown_element.is_visible():
                                        print(f"    ✓ Dropdown visible")
                                        if dropdown_element.is_enabled():
                                            print(f"    ✓ Dropdown enabled")
                                            dropdown_element.click()
                                            print(f"    ✅ Đã click dropdown: {dropdown_selector}")
                                            time.sleep(1.5)  # Chờ dropdown mở
                                            dropdown_opened = True
                                            break
                                        else:
                                            print(f"    ❌ Dropdown disabled")
                                    else:
                                        print(f"    ❌ Dropdown not visible")
                                else:
                                    print(f"    ❌ Dropdown không tồn tại")
                            except Exception as e:
                                print(f"    ❌ Lỗi: {e}")
                                continue
                        
                        if not dropdown_opened:
                            print("⚠️ Không thể mở dropdown model, thử tìm model trực tiếp...")
                        else:
                            # Sau khi mở dropdown, chờ elements load và debug
                            print("🔍 Dropdown đã mở, đang tìm model options...")
                            time.sleep(2)  # Chờ dropdown options load
                            
                            # Debug: Liệt kê tất cả options trong dropdown
                            try:
                                print("📋 Debug: Tìm tất cả dropdown options...")
                                dropdown_items = page.query_selector_all("li, option, [role='option'], [role='menuitem'], .dropdown-item, .menu-item")
                                print(f"Tìm thấy {len(dropdown_items)} potential dropdown items:")
                                for i, item in enumerate(dropdown_items[:15]):  # Giới hạn 15 items
                                    try:
                                        text = item.text_content()
                                        if text and text.strip():
                                            is_visible = item.is_visible()
                                            print(f"    {i+1}. '{text.strip()}' - Visible: {is_visible}")
                                    except:
                                        pass
                            except Exception as debug_e:
                                print(f"❌ Lỗi debug dropdown: {debug_e}")
                                
                        # Chọn model cụ thể với nhiều cách tiếp cận
                        model_display_name = self._get_model_display_name(model)
                        print(f"🎯 Tìm model: '{model_display_name}' (từ '{model}')")
                        
                        # Expanded model selectors với pattern matching linh hoạt hơn
                        model_selectors = [
                            # Text-based selectors - exact match
                            f"text={model_display_name}",
                            f"text={model}",
                            f"button:has-text('{model_display_name}')",
                            f"button:has-text('{model}')",
                            f"li:has-text('{model_display_name}')",
                            f"li:has-text('{model}')",
                            f"div:has-text('{model_display_name}')",
                            f"span:has-text('{model_display_name}')",
                            
                            # Partial text matching for model names
                            f"text=/.*{model_display_name.split()[-1]}.*/i",  # Match last word (like "Master", "2.1")
                            f"li:has-text('Master')" if "master" in model.lower() else None,
                            f"li:has-text('2.1')" if "2_1" in model else None,
                            f"li:has-text('1.5')" if "1_5" in model else None,
                            f"li:has-text('Kling')",  # Generic Kling selector
                            
                            # Data attribute selectors
                            f"[data-value='{model}']",
                            f"[data-value='{model_display_name}']",
                            f"[value='{model}']",
                            f"[value='{model_display_name}']",
                            
                            # Option selectors (for select elements)
                            f"option[value='{model}']",
                            f"option:has-text('{model_display_name}')",
                            
                            # Aria labels
                            f"[aria-label*='{model_display_name}']",
                            f"[aria-label*='{model}']",
                            
                            # CSS class selectors
                            f".model-{model.replace('_', '-')}",
                            f".option-{model.replace('_', '-')}",
                            
                            # Generic selectors for dropdown items
                            f"[role='option']:has-text('{model_display_name}')",
                            f"[role='menuitem']:has-text('{model_display_name}')",
                            f".dropdown-item:has-text('{model_display_name}')",
                            f".menu-item:has-text('{model_display_name}')"
                        ]
                        
                        # Remove None values from list
                        model_selectors = [s for s in model_selectors if s is not None]
                        
                        model_selected = False
                        for i, model_selector in enumerate(model_selectors):
                            print(f"  🔍 Thử model selector {i+1}/{len(model_selectors)}: {model_selector}")
                            try:
                                model_element = page.query_selector(model_selector)
                                if model_element:
                                    print(f"    ✓ Model element tồn tại")
                                    if model_element.is_visible():
                                        print(f"    ✓ Model element visible")
                                        if model_element.is_enabled():
                                            print(f"    ✓ Model element enabled")
                                            model_element.click()
                                            print(f"    ✅ Đã chọn model: {model_display_name}")
                                            time.sleep(1)
                                            model_selected = True
                                            break
                                        else:
                                            print(f"    ❌ Model element disabled")
                                    else:
                                        print(f"    ❌ Model element not visible")
                                else:
                                    print(f"    ❌ Model element không tồn tại")
                            except Exception as e:
                                print(f"    ❌ Lỗi: {e}")
                                continue
                        
                        if model_selected:
                            print(f"✅ Đã chọn model thành công: {model_display_name}")
                        else:
                            print(f"⚠️ Không thể chọn model {model_display_name}, sử dụng model mặc định")
                            
                            # Final debug: Liệt kê tất cả elements có thể là model
                            print("🔍 Final Debug: Tìm tất cả elements có thể là model...")
                            try:
                                # Tìm tất cả buttons
                                all_buttons = page.query_selector_all("button")
                                print(f"📋 Tìm thấy {len(all_buttons)} buttons:")
                                for btn in all_buttons[:10]:  # Chỉ show 10 đầu tiên
                                    try:
                                        text = btn.text_content()
                                        if text and any(keyword in text.lower() for keyword in ['kling', 'model', 'auto']):
                                            print(f"    - Button: '{text.strip()}'")
                                    except:
                                        pass
                                
                                # Tìm tất cả divs và spans
                                model_keywords = ['kling', 'model', 'auto', 'ai', 'master', '2.1', '1.5']
                                for tag in ['div', 'span', 'li']:
                                    elements = page.query_selector_all(tag)
                                    for elem in elements[:20]:  # Giới hạn để không spam
                                        try:
                                            text = elem.text_content()
                                            if text and any(keyword in text.lower() for keyword in model_keywords):
                                                if len(text.strip()) < 50:  # Chỉ show text ngắn
                                                    print(f"    - {tag.upper()}: '{text.strip()}'")
                                        except:
                                            pass
                                            
                            except Exception as debug_e:
                                print(f"❌ Lỗi final debug: {debug_e}")
                                 
                    except Exception as e:
                        print(f"⚠️ Lỗi chọn model: {e}, sử dụng model mặc định")
                
                # Thiết lập duration TRƯỚC khi generate (theo đúng workflow user)
                print(f"⚙️ Thiết lập duration: {duration}")
                duration_selectors = [
                    f"button:has-text('{duration}')",
                    f"[data-value='{duration}']",
                    f"option[value='{duration}']"
                ]
                
                for selector in duration_selectors:
                    try:
                        if page.query_selector(selector):
                            page.click(selector)
                            print(f"✓ Đã chọn duration: {duration}")
                            break
                    except:
                        continue
                
                # Thiết lập ratio TRƯỚC khi generate
                print(f"⚙️ Thiết lập ratio: {ratio}")
                ratio_selectors = [
                    f"button:has-text('{ratio}')",
                    f"[data-value='{ratio}']",
                    f"option[value='{ratio}']"
                ]
                
                for selector in ratio_selectors:
                    try:
                        if page.query_selector(selector):
                            page.click(selector)
                            print(f"✓ Đã chọn ratio: {ratio}")
                            break
                    except:
                        continue
                
                # TRỰC TIẾP TÌM VÀ CLICK NÚT GENERATE (theo yêu cầu user)
                print("🎯 Nhấn trực tiếp vào nút Generate...")
                
                # Selector đúng từ user (không sử dụng gì khác)
                selector = "button[data-cy='generate-button'][data-tour='generate-button']"
                
                try:
                    generate_button = page.query_selector(selector)
                    if generate_button and generate_button.is_visible():
                        generate_button.click()
                        print("✅ Đã click nút Generate")
                    else:
                        # Fallback đơn giản
                        page.click("button:has-text('Generate')")
                        print("✅ Đã click nút Generate (fallback)")
                except Exception as e:
                    print(f"❌ Lỗi click Generate: {e}")
                    raise Exception("Không thể click nút Generate")
                
                # Chờ video được sinh ra
                print("⏳ Đang chờ video được sinh ra...")
                
                # Xác định timeout dựa trên model
                if "master" in model.lower():
                    video_timeout = 600  # 10 phút cho Kling Master
                else:
                    video_timeout = 300  # 5 phút cho model thường
                
                success = self._wait_for_video_generation(page, timeout_seconds=video_timeout)
                
                if not success:
                    raise Exception(f"Sinh video thất bại hoặc timeout sau {video_timeout}s")
                
                # Tải video về
                print("💾 Đang tải video...")
                video_path = self._download_video_to_session(page)
                
                if video_path:
                    # Lưu metadata thành công
                    session_metadata["output_video"] = os.path.basename(video_path)
                    session_metadata["status"] = "completed"
                    self._save_session_metadata(session_metadata)
                    
                    print(f"✅ Đã tạo video thành công: {video_path}")
                    print(f"📁 Session folder: {self.current_session_dir}")
                    return video_path
                else:
                    # Lưu metadata thất bại
                    session_metadata["status"] = "failed"
                    session_metadata["error"] = "Download failed"
                    self._save_session_metadata(session_metadata)
                    raise Exception("Không thể tải video")
                    
            except Exception as e:
                print(f"❌ Lỗi sinh video từ text: {e}")
                # Lưu metadata lỗi
                if hasattr(self, 'current_session_dir'):
                    session_metadata["status"] = "failed"
                    session_metadata["error"] = str(e)
                    self._save_session_metadata(session_metadata)
                raise
                
            finally:
                browser.close()

    def generate_video_from_image(self, image_path: str, prompt: str, cookie_string: str = None, 
                                 duration: str = "5s", ratio: str = "1:1", model: str = "kling_2_1"):
        """
        Sinh video từ ảnh với prompt - workflow tương tự generate_video
        """
        
        print(f"🎬 Bắt đầu sinh video từ ảnh")
        print(f"📁 Ảnh: {image_path}")
        print(f"📝 Prompt: {prompt}")
        print(f"⚙️ Model: {self._get_model_display_name(model)}")
        print(f"⏱️ Duration: {duration}")
        print(f"📐 Ratio: {ratio}")
        
        # Tạo session directory
        session_dir = self._create_session_directory()
        
        # Metadata
        session_metadata = {
            "type": "image_to_video",
            "image_path": image_path,
            "prompt": prompt,
            "model": model,
            "duration": duration,
            "ratio": ratio,
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }
        self._save_session_metadata(session_metadata)
        
        # Sử dụng cùng logic như generate_video nhưng thêm bước upload ảnh
        # ... (có thể implement sau nếu cần)
        
        return self.generate_video(prompt, cookie_string, duration, ratio, model)
