"""
Module xử lý việc điều khiển trình duyệt tự động để sinh ảnh từ Freepik AI.
"""

import os
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, Page, Browser


class FreepikImageGenerator:
    """Lớp xử lý việc điều khiển trình duyệt để sinh ảnh từ Freepik AI."""

    def __init__(self, headless: bool = True, output_dir: str = "output"):
        """
        Khởi tạo trình điều khiển browser.
        
        Args:
            headless: True để chạy ẩn browser, False để hiển thị UI
            output_dir: Thư mục lưu ảnh đầu ra
        """
        load_dotenv()
        self.freepik_cookie = os.getenv("FREEPIK_COOKIE")
        
        if not self.freepik_cookie:
            raise ValueError("FREEPIK_COOKIE không tìm thấy trong file .env")
            
        self.headless = headless
        self.output_dir = output_dir
        
        # Tạo thư mục output nếu chưa tồn tại
        os.makedirs(self.output_dir, exist_ok=True)
        
        # URL trực tiếp của Freepik AI Image Generator
        self.url = "https://www.freepik.com/pikaso/ai-image-generator#from_element=mainmenu"
        
        # Thiết lập Playwright
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
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
                # Chuyển đổi format cookie cho Playwright
                playwright_cookies = []
                for cookie in cookies:
                    playwright_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', False),
                        'httpOnly': cookie.get('httpOnly', False)
                    }
                    
                    # Thêm sameSite nếu có
                    if 'sameSite' in cookie and cookie['sameSite'] != 'no_restriction':
                        # Chuyển đổi sameSite value cho Playwright
                        if cookie['sameSite'] == 'lax':
                            playwright_cookie['sameSite'] = 'Lax'
                        elif cookie['sameSite'] == 'strict':
                            playwright_cookie['sameSite'] = 'Strict'
                        elif cookie['sameSite'] == 'none':
                            playwright_cookie['sameSite'] = 'None'
                    
                    # Thêm expires nếu có
                    if 'expirationDate' in cookie and cookie['expirationDate']:
                        playwright_cookie['expires'] = cookie['expirationDate']
                    
                    playwright_cookies.append(playwright_cookie)
                
                page.context.add_cookies(playwright_cookies)
                print(f"✓ Đã thiết lập {len(playwright_cookies)} cookie")
                
                # Log các cookie quan trọng
                important_cookies = [c for c in cookies if c['name'] in ['GR_TOKEN', 'GR_REFRESH', 'GRID', 'UID']]
                if important_cookies:
                    print(f"✓ Đã thiết lập {len(important_cookies)} cookie đăng nhập quan trọng")
                
            else:
                print("⚠️ Không có cookie để thiết lập")
        except Exception as e:
            print(f"❌ Lỗi thiết lập cookie: {e}")
            print(f"Debug: {str(e)}")

    def _setup_browser(self) -> None:
        """Khởi tạo và cấu hình trình duyệt."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch(headless=self.headless)
        self.context = self.browser.new_context()
        
        # Thiết lập cookie để đăng nhập
        self.page = self.context.new_page()
        self.page.goto("https://www.freepik.com")
        
        # Thiết lập cookie đăng nhập
        freepik_cookie_parts = self.freepik_cookie.split(";")
        for part in freepik_cookie_parts:
            if "=" in part:
                name, value = part.strip().split("=", 1)
                self.page.context.add_cookies([{
                    "name": name,
                    "value": value,
                    "url": "https://www.freepik.com"
                }])
        
    def _close_browser(self) -> None:
        """Đóng trình duyệt và giải phóng tài nguyên."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def _wait_and_click(self, selector: str, timeout: int = 10000) -> None:
        """Đợi và nhấp vào phần tử."""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            self.page.click(selector)
        except Exception as e:
            print(f"Lỗi khi nhấp vào {selector}: {str(e)}")
            
    def _wait_for_image_generation(self, timeout_seconds: int = 60) -> bool:
        """
        Đợi cho quá trình sinh ảnh hoàn tất.
        
        Args:
            timeout_seconds: Thời gian tối đa đợi (giây)
            
        Returns:
            True nếu sinh ảnh thành công, False nếu timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            # Kiểm tra nếu có thông báo lỗi
            error_message = self.page.query_selector("text=Something went wrong")
            if error_message:
                print("Gặp lỗi khi sinh ảnh!")
                return False
            
            # Kiểm tra nếu ảnh đã sẵn sàng (nút tải xuống đã xuất hiện)
            download_button = self.page.query_selector("button:has-text('Download')")
            if download_button:
                print("Sinh ảnh thành công!")
                return True
            
            time.sleep(1)  # Đợi 1 giây trước khi kiểm tra lại
        
        print(f"Hết thời gian chờ ({timeout_seconds} giây)!")
        return False
        
    def _download_image(self) -> Optional[str]:
        """
        Tải ảnh đã sinh về máy.
        
        Returns:
            Đường dẫn đến file ảnh đã tải, None nếu không thành công
        """
        try:
            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_path = os.path.join(self.output_dir, f"image_{timestamp}.png")
            
            # Nhấn nút Download
            download_button = self.page.query_selector("button:has-text('Download')")
            if not download_button:
                print("Không tìm thấy nút Download!")
                return None
            
            # Thiết lập sự kiện tải file
            with self.page.expect_download() as download_info:
                download_button.click()
                
            download = download_info.value
            # Lưu file tải xuống vào thư mục đích
            download.save_as(image_path)
            
            print(f"Đã tải ảnh về: {image_path}")
            return image_path
        except Exception as e:
            print(f"Lỗi khi tải ảnh: {str(e)}")
            return None
            
    def generate_image(self, prompt: str, cookie_string: str = None):
        """
        Sinh ảnh từ prompt sử dụng Freepik AI
        
        Args:
            prompt: Mô tả ảnh cần sinh
            cookie_string: Cookie để đăng nhập (string hoặc JSON)
            
        Returns:
            str: Đường dẫn file ảnh đã tải về
        """
        print(f"🎨 Bắt đầu sinh ảnh với prompt: {prompt}")
        
        with sync_playwright() as p:
            # Khởi động trình duyệt
            browser = p.firefox.launch(headless=self.headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0"
            )
            page = context.new_page()
            
            try:
                # Thiết lập cookie nếu có
                if cookie_string:
                    cookies = self.parse_cookies(cookie_string)
                    if cookies:
                        # Đi đến trang chính trước để set cookie
                        print("🌐 Đang mở trang Freepik để thiết lập cookie...")
                        page.goto("https://www.freepik.com", wait_until="networkidle", timeout=30000)
                        
                        # Set cookies
                        self.set_cookies(page, cookies)
                        print("✓ Đã thiết lập cookie, chờ 3 giây...")
                        time.sleep(3)
                        
                        # Reload để áp dụng cookie
                        page.reload(wait_until="networkidle")
                        time.sleep(2)
                        
                        # Kiểm tra đăng nhập
                        if page.query_selector("text=Log in") or page.query_selector("text=Sign up"):
                            print("⚠️ Cookie có thể đã hết hạn hoặc không hợp lệ")
                        else:
                            print("✅ Đã đăng nhập thành công!")
                
                # Đi đến trang Pikaso
                print("🌐 Đang chuyển đến trang AI Image Generator...")
                page.goto("https://www.freepik.com/pikaso/ai-image-generator", 
                         wait_until="networkidle", timeout=30000)
                
                # Kiểm tra trạng thái đăng nhập
                time.sleep(3)  # Đợi trang load hoàn toàn
                
                # Kiểm tra cookie
                current_cookies = page.context.cookies()
                has_auth_cookies = any(c['name'] in ['GR_TOKEN', 'GRID', 'UID'] for c in current_cookies)
                
                # Kiểm tra các dấu hiệu đăng nhập
                login_indicators = [
                    "text=Sign in",
                    "text=Log in", 
                    "text=Sign up for free",
                    "text=Get started",
                    "text=Create account"
                ]
                
                has_login_prompt = False
                for indicator in login_indicators:
                    if page.query_selector(indicator):
                        has_login_prompt = True
                        break
                
                if has_auth_cookies and not has_login_prompt:
                    print("✅ Đã đăng nhập Premium!")
                    print("✓ Có thể sử dụng model Flux Kontext [Pro]")
                elif has_auth_cookies:
                    print("⚠️ Có cookie nhưng vẫn thấy prompt đăng nhập")
                    print("💡 Cookie có thể đã hết hạn, thử refresh...")
                    page.reload(wait_until="networkidle")
                    time.sleep(3)
                else:
                    print("ℹ️ Sử dụng free tier (chưa đăng nhập)")
                    print("⚠️ Free tier có giới hạn về số lượng và chất lượng")
                    print("💡 Để sử dụng đầy đủ tính năng, cần đăng nhập Premium")
                
                print("✅ Đã truy cập thành công vào AI Image Generator!")
                
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
                
                # Chọn model Flux Kontext[Pro]
                print("⚙️ Đang chọn model Flux Kontext[Pro]...")
                try:
                    # Chờ trang load hoàn toàn
                    time.sleep(3)
                    
                    # Theo giao diện mới, model được hiển thị ở bên phải
                    # Tìm model Flux Kontext [Pro] trực tiếp
                    flux_pro_selectors = [
                        # Selector chính xác cho Flux Kontext [Pro] với biểu tượng NEW
                        "div:has-text('Flux Kontext [Pro]'):has-text('NEW')",
                        "button:has-text('Flux Kontext [Pro]')",
                        "[data-testid*='flux-kontext-pro']",
                        "[data-model*='flux-kontext-pro']",
                        # Selector dựa trên structure DOM
                        "div:has-text('Flux Kontext [Pro]'):has-text('Great for daily use')",
                        "div:has-text('100'):has-text('Flux Kontext [Pro]')",  # Có text "100" credits
                        # Fallback selectors
                        "div:has-text('Flux Kontext'):has-text('Pro')",
                        "div:has-text('Great for daily use')",  # Description text
                        ".model-card:has-text('Flux Kontext')",
                        "*[class*='model']:has-text('Flux Kontext [Pro]')",
                        # Thử với các selector khác
                        "div[role='button']:has-text('Flux Kontext')",
                        "button[aria-label*='Flux Kontext']",
                        # Selector theo vị trí (model đầu tiên bên phải)
                        "div:has-text('Flux Kontext') >> nth=0",
                        "*:has-text('Flux Kontext [Pro]') >> nth=0"
                    ]
                    
                    flux_selected = False
                    for flux_selector in flux_pro_selectors:
                        try:
                            # Kiểm tra xem element có tồn tại không
                            element = page.query_selector(flux_selector)
                            if element:
                                # Scroll đến element nếu cần
                                element.scroll_into_view_if_needed()
                                time.sleep(1)
                                
                                # Click vào model
                                element.click(timeout=3000)
                                print("✅ Đã chọn model Flux Kontext [Pro]")
                                flux_selected = True
                                time.sleep(2)  # Chờ model được apply
                                break
                        except Exception as e:
                            print(f"⚠️ Lỗi với selector {flux_selector}: {e}")
                            continue
                    
                    # Nếu không tìm thấy, thử cách khác
                    if not flux_selected:
                        print("🔍 Tìm kiếm model bằng cách khác...")
                        try:
                            # Tìm tất cả elements có chứa text "Flux"
                            all_flux_elements = page.query_selector_all("*:has-text('Flux')")
                            print(f"Tìm thấy {len(all_flux_elements)} elements chứa 'Flux'")
                            
                            for i, element in enumerate(all_flux_elements[:5]):  # Chỉ thử 5 cái đầu
                                try:
                                    text_content = element.text_content()
                                    if "Kontext" in text_content and ("Pro" in text_content or "[Pro]" in text_content):
                                        print(f"Tìm thấy model: {text_content}")
                                        element.scroll_into_view_if_needed()
                                        time.sleep(1)
                                        element.click()
                                        print("✅ Đã chọn model Flux Kontext [Pro]")
                                        flux_selected = True
                                        time.sleep(2)
                                        break
                                except:
                                    continue
                        except Exception as e:
                            print(f"Lỗi khi tìm kiếm: {e}")
                    
                    if not flux_selected:
                        print("⚠️ Không tìm thấy model Flux Kontext [Pro], sử dụng model mặc định")
                        print("💡 Model mặc định có thể vẫn hoạt động tốt")
                            
                except Exception as e:
                    print(f"⚠️ Lỗi khi chọn model: {e}")
                    print("📝 Tiếp tục với model mặc định")
                
                # Tìm và click nút Generate
                print("🚀 Đang bắt đầu sinh ảnh...")
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
                        print("✓ Đã click nút sinh ảnh")
                        generated = True
                        break
                    except:
                        continue
                
                if not generated:
                    raise Exception("Không tìm thấy nút Generate")
                
                # Chờ ảnh được sinh ra
                print("⏳ Đang chờ ảnh được sinh ra...")
                
                # Đợi kết quả trong 60 giây
                result_found = False
                for i in range(60):
                    try:
                        # Kiểm tra thông báo lỗi hoặc yêu cầu đăng nhập
                        if page.query_selector("text=Sign up") or page.query_selector("text=Credits required"):
                            print("⚠️ Free tier đã hết quota hoặc cần đăng nhập")
                            print("💡 Vui lòng:")
                            print("   1. Đăng nhập tài khoản Premium")
                            print("   2. Hoặc chờ quota reset")
                            print("   3. Hoặc cập nhật cookie Premium vào cookie_template.txt")
                            break
                        
                        # Tìm ảnh kết quả
                        result_selectors = [
                            "img[src*='generated']",
                            "img[alt*='Generated']", 
                            ".result-image img",
                            ".generated-image",
                            "[data-testid*='result'] img",
                            "img[src*='blob:']",  # Ảnh tạm thời
                            "canvas"  # Canvas element
                        ]
                        
                        for selector in result_selectors:
                            try:
                                element = page.query_selector(selector)
                                if element and element.is_visible():
                                    print("✅ Ảnh đã được sinh ra!")
                                    result_found = True
                                    break
                            except:
                                continue
                        
                        if result_found:
                            break
                            
                        time.sleep(1)
                        print(f"⏳ Đang chờ... ({i+1}/60s)")
                        
                    except:
                        time.sleep(1)
                
                if not result_found:
                    # Kiểm tra lý do thất bại
                    if page.query_selector("text=Sign up"):
                        raise Exception("Free tier yêu cầu đăng ký - cần tài khoản Premium")
                    elif page.query_selector("text=Credits"):
                        raise Exception("Hết credits - cần tài khoản Premium")
                    else:
                        raise Exception("Timeout: Ảnh không được sinh ra sau 60 giây")
                
                # Tải ảnh về
                print("💾 Đang tải ảnh về...")
                timestamp = int(time.time())
                filename = f"freepik_image_{timestamp}.png"
                filepath = os.path.join(self.output_dir, filename)
                
                # Đợi thêm một chút để ảnh load hoàn toàn
                time.sleep(2)
                
                # Tìm tất cả các cách có thể tải ảnh
                downloaded = False
                
                # Cách 1: Tìm nút download
                download_selectors = [
                    "button:has-text('Download')",
                    "a:has-text('Download')",
                    "[data-testid*='download']",
                    ".download-btn",
                    "a[download]",
                    "button[aria-label*='Download']",
                    "button[title*='Download']"
                ]
                
                for selector in download_selectors:
                    try:
                        element = page.query_selector(selector)
                        if element and element.is_visible():
                            print(f"🔍 Tìm thấy nút download: {selector}")
                            with page.expect_download() as download_info:
                                element.click(timeout=5000)
                            download = download_info.value
                            download.save_as(filepath)
                            downloaded = True
                            print(f"✅ Đã tải ảnh qua nút download: {filepath}")
                            break
                    except Exception as e:
                        print(f"⚠️ Lỗi với download selector {selector}: {e}")
                        continue
                
                # Cách 2: Screenshot ảnh trực tiếp
                if not downloaded:
                    print("🔍 Thử screenshot ảnh trực tiếp...")
                    img_selectors = [
                        "img[src*='generated']",
                        "img[alt*='Generated']", 
                        ".result-image img",
                        ".generated-image img",
                        "[data-testid*='result'] img",
                        "img[src*='blob:']",
                        "img[src*='freepik']",
                        "canvas",
                        # Tìm ảnh lớn nhất
                        "img:not([width='1']):not([height='1'])"
                    ]
                    
                    for selector in img_selectors:
                        try:
                            element = page.query_selector(selector)
                            if element and element.is_visible():
                                print(f"🔍 Tìm thấy ảnh: {selector}")
                                
                                # Scroll đến ảnh
                                element.scroll_into_view_if_needed()
                                time.sleep(1)
                                
                                # Screenshot ảnh
                                element.screenshot(path=filepath)
                                downloaded = True
                                print(f"✅ Đã screenshot ảnh: {filepath}")
                                break
                        except Exception as e:
                            print(f"⚠️ Lỗi với img selector {selector}: {e}")
                            continue
                
                # Cách 3: Screenshot toàn bộ vùng kết quả
                if not downloaded:
                    print("🔍 Thử screenshot vùng kết quả...")
                    try:
                        # Tìm vùng chứa kết quả
                        result_area_selectors = [
                            "[data-testid*='result']",
                            ".result-container",
                            ".generated-content",
                            ".output-area"
                        ]
                        
                        for selector in result_area_selectors:
                            try:
                                element = page.query_selector(selector)
                                if element and element.is_visible():
                                    element.screenshot(path=filepath)
                                    downloaded = True
                                    print(f"✅ Đã screenshot vùng kết quả: {filepath}")
                                    break
                            except:
                                continue
                                
                    except Exception as e:
                        print(f"⚠️ Lỗi screenshot vùng kết quả: {e}")
                
                # Cách 4: Screenshot toàn trang (fallback cuối cùng)
                if not downloaded:
                    print("🔍 Screenshot toàn trang làm fallback...")
                    try:
                        page.screenshot(path=filepath, full_page=True)
                        downloaded = True
                        print(f"✅ Đã screenshot toàn trang: {filepath}")
                    except Exception as e:
                        print(f"⚠️ Lỗi screenshot toàn trang: {e}")
                
                if downloaded:
                    print(f"✅ Đã lưu ảnh: {filepath}")
                    return filepath
                else:
                    raise Exception("Không thể tải ảnh về bằng mọi cách")
                    
            except Exception as e:
                print(f"❌ Lỗi khi sinh ảnh: {e}")
                return None
                
            finally:
                browser.close() 