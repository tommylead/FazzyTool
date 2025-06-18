"""
Module xử lý việc điều khiển trình duyệt tự động để sinh video từ Freepik AI.
"""

import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser


class FreepikVideoGenerator:
    """Lớp xử lý việc điều khiển trình duyệt để sinh video từ Freepik AI."""

    def __init__(self, headless: bool = True, output_dir: str = "output"):
        """
        Khởi tạo trình điều khiển browser.
        
        Args:
            headless: True để chạy ẩn browser, False để hiển thị UI
            output_dir: Thư mục lưu video đầu ra
        """
        self.headless = headless
        self.output_dir = output_dir
        
        # Tạo thư mục output nếu chưa tồn tại
        os.makedirs(self.output_dir, exist_ok=True)
    
    def parse_cookies(self, cookie_input: str):
        """
        Parse cookie từ nhiều định dạng khác nhau
        
        Args:
            cookie_input: Cookie dưới dạng string hoặc JSON
            
        Returns:
            list: Danh sách cookie đã được parse
        """
        try:
            # Thử parse JSON trước
            if cookie_input.strip().startswith('['):
                cookies_json = json.loads(cookie_input)
                
                # Lọc các cookie quan trọng cho Freepik
                important_cookies = []
                important_names = [
                    'GR_TOKEN',      # Token xác thực chính
                    'GR_REFRESH',    # Refresh token
                    'GRID',          # User ID
                    'UID',           # User ID backup
                    '_ga',           # Google Analytics
                    '_ga_QWX66025LC',# Google Analytics specific
                    'OptanonConsent',# Cookie consent
                    'ab.storage.userId.8086d9ee-1f81-4508-ba9f-3a661635ac90',  # User session
                    'ph_phc_Rc6y1yvZwwwR09Pl9NtKBo5gzpxr1Ei4Bdbg3kC1Ihz_posthog'  # Analytics
                ]
                
                for cookie in cookies_json:
                    if cookie['name'] in important_names:
                        important_cookies.append({
                            'name': cookie['name'],
                            'value': cookie['value'],
                            'domain': cookie['domain'],
                            'path': cookie.get('path', '/'),
                            'secure': cookie.get('secure', False),
                            'httpOnly': cookie.get('httpOnly', False)
                        })
                
                print(f"✓ Đã parse {len(important_cookies)} cookie quan trọng từ {len(cookies_json)} cookie")
                return important_cookies
                
            else:
                # Parse cookie string dạng "name=value; name2=value2"
                cookies = []
                cookie_pairs = cookie_input.split(';')
                
                for pair in cookie_pairs:
                    if '=' in pair:
                        name, value = pair.strip().split('=', 1)
                        cookies.append({
                            'name': name.strip(),
                            'value': value.strip(),
                            'domain': '.freepik.com',
                            'path': '/',
                            'secure': False,
                            'httpOnly': False
                        })
                
                print(f"✓ Đã parse {len(cookies)} cookie từ cookie string")
                return cookies
                
        except Exception as e:
            print(f"❌ Lỗi parse cookie: {e}")
            return []
    
    def set_cookies(self, page: Page, cookies):
        """
        Thiết lập cookie cho trang web
        
        Args:
            page: Playwright page object
            cookies: Danh sách cookie
        """
        try:
            if cookies:
                page.context.add_cookies(cookies)
                print(f"✓ Đã thiết lập {len(cookies)} cookie")
            else:
                print("⚠️ Không có cookie để thiết lập")
        except Exception as e:
            print(f"❌ Lỗi thiết lập cookie: {e}")

    def generate_video_from_image(self, image_path: str, prompt: str, cookie_string: str = None, duration: str = "5s", ratio: str = "1:1"):
        """
        Sinh video từ ảnh sử dụng Freepik AI Image-to-Video với Kling 2.1 Master
        
        Args:
            image_path: Đường dẫn tới ảnh đầu vào
            prompt: Mô tả video cần sinh
            cookie_string: Cookie để đăng nhập (string hoặc JSON)
            duration: Thời lượng video ("5s" hoặc "10s")
            ratio: Tỷ lệ khung hình ("1:1", "16:9", "9:16")
            
        Returns:
            str: Đường dẫn file video đã tải về
        """
        print(f"🎬 Bắt đầu sinh video từ ảnh: {image_path}")
        print(f"📝 Prompt: {prompt}")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Không tìm thấy file ảnh: {image_path}")
        
        with sync_playwright() as p:
            # Khởi động trình duyệt
            browser = p.firefox.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            try:
                # Thiết lập cookie nếu có
                if cookie_string:
                    cookies = self.parse_cookies(cookie_string)
                    self.set_cookies(page, cookies)
                
                # Đi đến trang Pikaso Video
                print("🌐 Đang mở trang Freepik Pikaso Video...")
                page.goto("https://www.freepik.com/pikaso/ai-video-generator", 
                         wait_until="networkidle", timeout=30000)
                
                # Chờ trang load
                time.sleep(5)
                
                # Chọn chế độ Image-to-Video
                print("🖼️ Chọn chế độ Image-to-Video...")
                try:
                    img_to_video_selectors = [
                        "button:has-text('Image to Video')",
                        "button:has-text('image to video')",
                        "[data-testid*='image-to-video']",
                        ".image-to-video",
                        "tab:has-text('Image')",
                        "button[aria-label*='Image']"
                    ]
                    
                    for selector in img_to_video_selectors:
                        try:
                            if page.query_selector(selector):
                                page.click(selector, timeout=3000)
                                print("✅ Đã chọn chế độ Image-to-Video")
                                time.sleep(2)
                                break
                        except:
                            continue
                    else:
                        print("⚠️ Không tìm thấy chế độ Image-to-Video, tiếp tục...")
                        
                except Exception as e:
                    print(f"⚠️ Lỗi khi chọn chế độ Image-to-Video: {e}")
                
                # Upload ảnh
                print("📤 Đang upload ảnh...")
                try:
                    upload_selectors = [
                        "input[type='file']",
                        "[data-testid*='upload']",
                        ".upload-input",
                        "input[accept*='image']"
                    ]
                    
                    uploaded = False
                    for selector in upload_selectors:
                        try:
                            upload_input = page.query_selector(selector)
                            if upload_input:
                                upload_input.set_input_files(image_path)
                                print("✅ Đã upload ảnh thành công")
                                uploaded = True
                                time.sleep(3)
                                break
                        except:
                            continue
                    
                    if not uploaded:
                        # Thử tìm button upload và click
                        upload_button_selectors = [
                            "button:has-text('Upload')",
                            "button:has-text('Choose')",
                            ".upload-button",
                            "[data-testid*='upload-button']"
                        ]
                        
                        for selector in upload_button_selectors:
                            try:
                                if page.query_selector(selector):
                                    page.click(selector)
                                    time.sleep(1)
                                    
                                    # Tìm input file sau khi click
                                    file_input = page.query_selector("input[type='file']")
                                    if file_input:
                                        file_input.set_input_files(image_path)
                                        print("✅ Đã upload ảnh thành công")
                                        uploaded = True
                                        time.sleep(3)
                                        break
                            except:
                                continue
                    
                    if not uploaded:
                        raise Exception("Không thể upload ảnh")
                        
                except Exception as e:
                    print(f"❌ Lỗi upload ảnh: {e}")
                    raise
                
                # Chọn model Kling 2.1 Master
                print("⚙️ Đang chọn model Kling 2.1 Master...")
                try:
                    time.sleep(3)
                    
                    # Tìm dropdown model
                    model_selectors = [
                        "button:has-text('Model')",
                        "[data-testid*='model']",
                        "button[aria-label*='model']",
                        ".model-selector",
                        ".model-dropdown",
                        "select",
                        "[role='combobox']"
                    ]
                    
                    model_clicked = False
                    for selector in model_selectors:
                        try:
                            if page.query_selector(selector):
                                page.click(selector, timeout=3000)
                                time.sleep(2)
                                model_clicked = True
                                print(f"✓ Đã click model selector: {selector}")
                                break
                        except:
                            continue
                    
                    if model_clicked:
                        # Tìm và chọn Kling 2.1 Master
                        kling_selectors = [
                            "text=Kling 2.1 Master",
                            "text=kling 2.1 master",
                            "text=Kling 2.1",
                            "text=kling 2.1",
                            "[data-value*='kling']",
                            "option[value*='kling']",
                            "li:has-text('Kling')",
                            "div:has-text('Kling 2.1')"
                        ]
                        
                        kling_selected = False
                        for kling_selector in kling_selectors:
                            try:
                                if page.query_selector(kling_selector):
                                    page.click(kling_selector, timeout=2000)
                                    print("✅ Đã chọn model Kling 2.1 Master")
                                    kling_selected = True
                                    break
                            except:
                                continue
                        
                        if not kling_selected:
                            print("⚠️ Không tìm thấy model Kling 2.1 Master, sử dụng model mặc định")
                    else:
                        print("⚠️ Không tìm thấy model selector, sử dụng model mặc định")
                        
                except Exception as e:
                    print(f"⚠️ Lỗi khi chọn model: {e}")
                    print("📝 Tiếp tục với model mặc định")
                
                # Nhập prompt (nếu có)
                if prompt:
                    print("✍️ Đang nhập prompt...")
                    try:
                        prompt_selectors = [
                            "textarea[placeholder*='Describe']",
                            "textarea[placeholder*='describe']", 
                            "textarea[placeholder*='prompt']",
                            "textarea[placeholder*='Prompt']",
                            "textarea[data-testid*='prompt']",
                            "textarea",
                            "[contenteditable='true']",
                            "[role='textbox']"
                        ]
                        
                        prompt_entered = False
                        for selector in prompt_selectors:
                            try:
                                element = page.query_selector(selector)
                                if element and element.is_enabled() and element.is_visible():
                                    page.click(selector)
                                    page.fill(selector, prompt)
                                    print("✅ Đã nhập prompt")
                                    prompt_entered = True
                                    break
                            except:
                                continue
                        
                        if not prompt_entered:
                            print("⚠️ Không thể nhập prompt, tiếp tục...")
                            
                    except Exception as e:
                        print(f"⚠️ Lỗi nhập prompt: {e}")
                
                # Thiết lập duration và ratio
                print(f"⚙️ Thiết lập duration: {duration}, ratio: {ratio}")
                try:
                    # Thiết lập duration
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
                    
                    # Thiết lập ratio
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
                            
                except Exception as e:
                    print(f"⚠️ Lỗi thiết lập duration/ratio: {e}")
                
                # Tìm và click nút Generate
                print("🚀 Đang bắt đầu sinh video...")
                generate_selectors = [
                    "button[data-testid*='generate']",
                    "button:has-text('Generate')",
                    "button:has-text('Create')", 
                    ".generate-btn",
                    "input[type='submit']"
                ]
                
                generated = False
                for selector in generate_selectors:
                    try:
                        if page.query_selector(selector):
                            page.click(selector, timeout=3000)
                            print("✓ Đã click nút sinh video")
                            generated = True
                            break
                    except:
                        continue
                
                if not generated:
                    raise Exception("Không tìm thấy nút Generate")
                
                # Đợi video được sinh
                print("⏳ Đang chờ video được sinh...")
                success = self._wait_for_video_generation(timeout_seconds=180)  # 3 phút
                
                if not success:
                    raise Exception("Sinh video thất bại hoặc timeout")
                
                # Tải video về
                print("💾 Đang tải video...")
                video_path = self._download_video()
                
                if video_path:
                    print(f"✅ Đã tải video thành công: {video_path}")
                    return video_path
                else:
                    raise Exception("Không thể tải video")
                    
            except Exception as e:
                print(f"❌ Lỗi sinh video: {e}")
                return None
            finally:
                browser.close()

    def generate_video(self, prompt: str, cookie_string: str = None, duration: str = "5s", ratio: str = "1:1"):
        """
        Sinh video từ prompt sử dụng Freepik AI
        
        Args:
            prompt: Mô tả video cần sinh
            cookie_string: Cookie để đăng nhập (string hoặc JSON)
            duration: Thời lượng video ("5s" hoặc "10s")
            ratio: Tỷ lệ khung hình ("1:1", "16:9", "9:16")
            
        Returns:
            str: Đường dẫn file video đã tải về
        """
        print(f"🎬 Bắt đầu sinh video với prompt: {prompt}")
        
        with sync_playwright() as p:
            # Khởi động trình duyệt
            browser = p.firefox.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = context.new_page()
            
            try:
                # Thiết lập cookie nếu có
                if cookie_string:
                    cookies = self.parse_cookies(cookie_string)
                    self.set_cookies(page, cookies)
                
                # Đi đến trang Pikaso Video
                print("🌐 Đang mở trang Freepik Pikaso Video...")
                page.goto("https://www.freepik.com/pikaso/ai-video-generator", 
                         wait_until="networkidle", timeout=30000)
                
                # Chờ và tìm ô nhập prompt
                print("🔍 Tìm ô nhập prompt...")
                
                # Danh sách các selector có thể có
                potential_selectors = [
                    "textarea[placeholder*='Describe']",
                    "textarea[placeholder*='describe']", 
                    "textarea[placeholder*='prompt']",
                    "textarea[placeholder*='Prompt']",
                    "textarea[data-testid*='prompt']",
                    "textarea[data-testid*='input']",
                    "[contenteditable='true']",
                    "textarea",
                    "input[type='text']",
                    "[role='textbox']",
                    ".prompt-input",
                    "#prompt",
                    "#prompt-input",
                    ".text-input",
                    "[name='prompt']",
                    "[placeholder*='Enter']",
                    "[placeholder*='Type']"
                ]
                
                prompt_selector = None
                found = False
                
                # Thử từng selector
                for selector in potential_selectors:
                    try:
                        page.wait_for_selector(selector, timeout=2000)
                        
                        # Kiểm tra xem element có thể nhập được không
                        element = page.query_selector(selector)
                        if element and element.is_enabled() and element.is_visible():
                            prompt_selector = selector
                            found = True
                            print(f"✓ Tìm thấy ô prompt với selector: {selector}")
                            break
                    except:
                        continue
                
                if not found:
                    # Debug: In ra tất cả các element có thể là input
                    print("🔍 Debug: Tìm tất cả input elements...")
                    try:
                        all_inputs = page.query_selector_all("input, textarea, [contenteditable], [role='textbox']")
                        print(f"Tìm thấy {len(all_inputs)} input elements:")
                        for i, inp in enumerate(all_inputs[:5]):  # Chỉ in 5 cái đầu
                            tag = inp.evaluate("el => el.tagName")
                            placeholder = inp.get_attribute("placeholder") or ""
                            data_testid = inp.get_attribute("data-testid") or ""
                            role = inp.get_attribute("role") or ""
                            print(f"  {i+1}. <{tag}> placeholder='{placeholder}' data-testid='{data_testid}' role='{role}'")
                    except Exception as e:
                        print(f"Debug error: {e}")
                    
                    raise Exception("Không tìm thấy ô nhập prompt")
                
                # Nhập prompt
                print("✍️ Đang nhập prompt...")
                
                # Thử nhiều cách nhập text
                try:
                    # Cách 1: Clear và fill
                    page.click(prompt_selector)
                    page.fill(prompt_selector, "")  # Clear trước
                    page.fill(prompt_selector, prompt)
                    
                    # Kiểm tra xem text đã được nhập chưa
                    current_value = page.input_value(prompt_selector) if page.query_selector(prompt_selector).get_attribute("value") is not None else page.text_content(prompt_selector)
                    
                    if not current_value or len(current_value.strip()) == 0:
                        print("⚠️ Cách 1 không thành công, thử cách 2...")
                        # Cách 2: Type từng ký tự
                        page.click(prompt_selector)
                        page.keyboard.press("Control+A")  # Select all
                        page.keyboard.press("Delete")     # Delete
                        page.type(prompt_selector, prompt, delay=50)
                        
                        current_value = page.input_value(prompt_selector) if page.query_selector(prompt_selector).get_attribute("value") is not None else page.text_content(prompt_selector)
                        
                        if not current_value or len(current_value.strip()) == 0:
                            print("⚠️ Cách 2 không thành công, thử cách 3...")
                            # Cách 3: Sử dụng JavaScript
                            page.evaluate(f"""
                                const element = document.querySelector('{prompt_selector}');
                                if (element) {{
                                    element.value = `{prompt}`;
                                    element.textContent = `{prompt}`;
                                    element.innerHTML = `{prompt}`;
                                    
                                    // Trigger events
                                    element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                    element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                }}
                            """)
                            
                            # Kiểm tra lại
                            current_value = page.input_value(prompt_selector) if page.query_selector(prompt_selector).get_attribute("value") is not None else page.text_content(prompt_selector)
                            
                            if not current_value or len(current_value.strip()) == 0:
                                print("❌ Không thể nhập prompt bằng mọi cách!")
                                raise Exception("Không thể nhập prompt vào ô input")
                    
                    print(f"✅ Đã nhập prompt thành công: {current_value[:50]}...")
                    
                except Exception as e:
                    print(f"❌ Lỗi khi nhập prompt: {e}")
                    raise
                
                # Chọn model Kling Master 2.1
                print("⚙️ Đang chọn model Kling Master 2.1...")
                try:
                    # Tìm và click vào dropdown model
                    model_selectors = [
                        "[data-testid*='model']",
                        "button[aria-label*='model']",
                        ".model-selector",
                        "select"
                    ]
                    
                    for selector in model_selectors:
                        try:
                            page.click(selector, timeout=3000)
                            time.sleep(1)
                            
                            # Tìm và chọn Kling Master 2.1
                            kling_selectors = [
                                "text=Kling Master 2.1",
                                "[data-value*='kling']",
                                "option[value*='kling']"
                            ]
                            
                            for kling_selector in kling_selectors:
                                try:
                                    page.click(kling_selector, timeout=2000)
                                    print("✓ Đã chọn model Kling Master 2.1")
                                    break
                                except:
                                    continue
                            break
                        except:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ Không thể chọn model: {e}")
                    print("📝 Sử dụng model mặc định")
                
                # Chọn thời lượng video
                print(f"⏱️ Đang chọn thời lượng: {duration}")
                try:
                    duration_selectors = [
                        f"button:has-text('{duration}')",
                        f"[data-value='{duration}']",
                        f".duration-{duration}"
                    ]
                    
                    for selector in duration_selectors:
                        try:
                            page.click(selector, timeout=3000)
                            print(f"✓ Đã chọn thời lượng {duration}")
                            break
                        except:
                            continue
                except Exception as e:
                    print(f"⚠️ Không thể chọn thời lượng: {e}")
                
                # Chọn tỷ lệ khung hình
                print(f"📏 Đang chọn tỷ lệ: {ratio}")
                try:
                    ratio_selectors = [
                        f"button:has-text('{ratio}')",
                        f"[data-value='{ratio}']",
                        f".ratio-{ratio.replace(':', 'x')}"
                    ]
                    
                    for selector in ratio_selectors:
                        try:
                            page.click(selector, timeout=3000)
                            print(f"✓ Đã chọn tỷ lệ {ratio}")
                            break
                        except:
                            continue
                except Exception as e:
                    print(f"⚠️ Không thể chọn tỷ lệ: {e}")
                
                # Tìm và click nút Generate
                print("🚀 Đang bắt đầu sinh video...")
                generate_selectors = [
                    "button[data-testid*='generate']",
                    "button:has-text('Generate')",
                    "button:has-text('Create')", 
                    ".generate-btn",
                    "input[type='submit']"
                ]
                
                generated = False
                for selector in generate_selectors:
                    try:
                        page.click(selector, timeout=3000)
                        print("✓ Đã click nút sinh video")
                        generated = True
                        break
                    except:
                        continue
                
                if not generated:
                    raise Exception("Không tìm thấy nút Generate")
                
                # Chờ video được sinh ra
                print("⏳ Đang chờ video được sinh ra...")
                
                # Đợi kết quả trong 180 giây (video mất nhiều thời gian hơn ảnh)
                result_found = False
                for i in range(180):
                    try:
                        # Tìm video kết quả hoặc nút download
                        result_selectors = [
                            "video[src*='generated']",
                            "button:has-text('Download')",
                            ".result-video",
                            ".generated-video",
                            "[data-testid*='result'] video",
                            ".download-btn"
                        ]
                        
                        for selector in result_selectors:
                            try:
                                page.wait_for_selector(selector, timeout=2000)
                                print("✅ Video đã được sinh ra!")
                                result_found = True
                                break
                            except:
                                continue
                        
                        if result_found:
                            break
                            
                        time.sleep(1)
                        print(f"⏳ Đang chờ... ({i+1}/180s)")
                        
                    except:
                        time.sleep(1)
                
                if not result_found:
                    raise Exception("Timeout: Video không được sinh ra sau 180 giây")
                
                # Tải video về
                print("💾 Đang tải video về...")
                timestamp = int(time.time())
                filename = f"freepik_video_{timestamp}.mp4"
                filepath = os.path.join(self.output_dir, filename)
                
                # Tìm link download
                download_selectors = [
                    "a[download]",
                    "button:has-text('Download')",
                    ".download-btn"
                ]
                
                downloaded = False
                for selector in download_selectors:
                    try:
                        with page.expect_download() as download_info:
                            page.click(selector, timeout=5000)
                        download = download_info.value
                        download.save_as(filepath)
                        downloaded = True
                        break
                    except:
                        continue
                
                if downloaded:
                    print(f"✅ Đã lưu video: {filepath}")
                    return filepath
                else:
                    raise Exception("Không thể tải video về")
                    
            except Exception as e:
                print(f"❌ Lỗi khi sinh video: {e}")
                return None
                
            finally:
                browser.close() 