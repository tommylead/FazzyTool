"""
Browser automation cho việc sinh ảnh từ Freepik AI
"""

import os
import time
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from playwright.sync_api import sync_playwright, Page


class FreepikImageGenerator:
    """Lớp xử lý việc sinh ảnh từ Freepik AI bằng browser automation."""

    def __init__(self, headless: bool = True, output_dir: str = "output"):
        self.headless = headless
        self.output_dir = output_dir
        
        # Tạo thư mục output nếu chưa tồn tại
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Thống kê để tracking
        self.generation_stats = {
            "total_generated": 0,
            "successful_downloads": 0,
            "failed_downloads": 0
        }

    def parse_cookies(self, cookie_input: str):
        """
        Parse cookie từ string hoặc JSON
        Hỗ trợ cả Firefox JSON format và string format
        """
        if not cookie_input or not cookie_input.strip():
            return []
            
        # Kiểm tra placeholder cookie
        if cookie_input.strip() == "placeholder_cookie":
            print("⚠️ Cookie placeholder được phát hiện, bỏ qua...")
            return []
            
        cookies = []
        
        try:
            # Thử parse JSON trước
            if cookie_input.strip().startswith('['):
                json_cookies = json.loads(cookie_input)
                
                for cookie in json_cookies:
                    # Chuyển đổi format Firefox sang Playwright
                    playwright_cookie = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': cookie.get('path', '/'),
                        'secure': cookie.get('secure', False),
                        'httpOnly': cookie.get('httpOnly', False)
                    }
                    
                    # Chuyển đổi sameSite
                    if 'sameSite' in cookie:
                        if cookie['sameSite'] == 'lax':
                            playwright_cookie['sameSite'] = 'Lax'
                        elif cookie['sameSite'] == 'strict':
                            playwright_cookie['sameSite'] = 'Strict'
                        elif cookie['sameSite'] == 'none':
                            playwright_cookie['sameSite'] = 'None'
                    
                    # Xử lý expires
                    if 'expires' in cookie and cookie['expires']:
                        try:
                            if isinstance(cookie['expires'], (int, float)):
                                playwright_cookie['expires'] = cookie['expires']
                            else:
                                # Parse string date if needed
                                pass
                        except:
                            pass
                    
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
        except Exception as e:
            print(f"Lỗi parse cookie: {e}")
            
        return cookies

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

    def _setup_browser(self) -> None:
        """Thiết lập browser và context"""
        # Setup trong method generate_image
        pass

    def _close_browser(self) -> None:
        """Đóng browser"""
        # Cleanup trong method generate_image
        pass
        
    def _wait_and_click(self, selector: str, timeout: int = 10000) -> None:
        """Đợi element và click"""
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
        
    def _download_single_image(self, image_index: int = 0, filename_prefix: str = "freepik_image") -> Optional[str]:
        """
        Tải một ảnh cụ thể về máy với tên file có thứ tự.
        
        Args:
            image_index: Chỉ số ảnh cần tải (0-based)
            filename_prefix: Tiền tố tên file
            
        Returns:
            Đường dẫn đến file ảnh đã tải, None nếu không thành công
        """
        try:
            # Tạo timestamp để đảm bảo tên file unique
            timestamp = int(time.time())
            filename = f"{filename_prefix}_{image_index + 1:03d}_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            print(f"💾 Đang tải ảnh {image_index + 1}...")
            
            # Đợi thêm một chút để ảnh load hoàn toàn
            time.sleep(2)
            
            downloaded = False
            
            # Cách 1: Tránh click nhầm vào ảnh bằng cách tìm chính xác download area
            try:
                print(f"🔍 Tìm vùng download cho ảnh {image_index + 1}...")
                
                # Đầu tiên, tìm container của ảnh thứ image_index
                image_containers = [
                    ".result-item", ".generated-item", ".image-result", 
                    "[data-testid*='result-item']", ".grid-item"
                ]
                
                target_container = None
                for container_selector in image_containers:
                    try:
                        containers = self.page.query_selector_all(container_selector)
                        if containers and len(containers) > image_index:
                            target_container = containers[image_index]
                            print(f"🔍 Tìm thấy container ảnh {image_index + 1}: {container_selector}")
                            break
                    except:
                        continue
                
                # Trong container này, tìm menu/download button
                if target_container:
                    menu_selectors = [
                        "button[aria-label*='More']",
                        "button[aria-label*='Download']", 
                        "button[data-testid*='download']",
                        "[title*='Download']",
                        "button[role='button']"
                    ]
                    
                    for menu_selector in menu_selectors:
                        try:
                            menu_button = target_container.query_selector(menu_selector)
                            if menu_button and menu_button.is_visible():
                                print(f"🔍 Tìm thấy menu button trong container: {menu_selector}")
                                menu_button.click()
                                time.sleep(1)  # Chờ menu mở ra
                                break
                        except:
                            continue
                            
            except Exception as e:
                print(f"⚠️ Không thể mở menu dropdown: {e}")
            
            # Cách 2: Tìm nút download của ảnh cụ thể với correct syntax
            # Tìm tất cả download buttons trước
            base_download_selectors = [
                # Selectors mới cho UI Freepik hiện tại
                "button[data-cy='download-button']",  # Download button chính
                "button[aria-label*='Download']",
                "button[title*='Download']", 
                "svg[data-testid='download-icon']",  # Icon download
                "[data-tour*='download']",
                # Menu dropdown (nút ...)
                "button[aria-label*='More']",
                "button[aria-label*='Options']", 
                "[data-testid*='menu']",
                "[data-testid*='more']",
                # Selectors truyền thống
                "button:has-text('Download')",
                "a:has-text('Download')",
                "[data-testid*='download']",
                ".download-btn",
                "a[download]"
            ]
            
            for base_selector in base_download_selectors:
                try:
                    # Tìm tất cả elements với base selector
                    elements = self.page.query_selector_all(base_selector)
                    print(f"🔍 Tìm thấy {len(elements)} download buttons với '{base_selector}'")
                    
                    # Chọn element theo index
                    if elements and len(elements) > image_index:
                        element = elements[image_index]
                        
                        if element and element.is_visible():
                            print(f"🔍 Chọn download button {image_index + 1}/{len(elements)}: {base_selector}")
                        
                        # Scroll đến element
                        element.scroll_into_view_if_needed()
                        time.sleep(1)
                        
                        with self.page.expect_download() as download_info:
                            element.click(timeout=5000)
                        download = download_info.value
                        download.save_as(filepath)
                        downloaded = True
                        print(f"✅ Đã tải ảnh qua nút download: {os.path.basename(filepath)}")
                        break
                            
                except Exception as e:
                    print(f"⚠️ Lỗi với download selector {base_selector}: {e}")
                    continue
                
            if downloaded:
                return filepath
            
            # Cách 2: Thử download ảnh trực tiếp từ URL
            if not downloaded:
                print(f"🔍 Thử download ảnh {image_index + 1} từ URL trực tiếp...")
                try:
                    # Tìm ảnh element
                    img_selectors = [
                        "img[src*='blob:']", "img[src*='generated']", "img[alt*='Generated']",
                        ".result-image img", ".generated-image img", "[data-testid*='result'] img",
                        "img[src*='freepik']", "canvas"
                    ]
                    
                    img_element = None
                    for selector in img_selectors:
                        try:
                            elements = self.page.query_selector_all(selector)
                            if elements and len(elements) > image_index:
                                img_element = elements[image_index]
                                if img_element and img_element.is_visible():
                                    print(f"🔍 Tìm thấy ảnh element: {selector}")
                                    break
                        except:
                            continue
                    
                    if img_element:
                        # Lấy URL ảnh
                        img_url = img_element.get_attribute('src')
                        print(f"🔗 URL ảnh: {img_url[:100]}...")
                        
                        if img_url and img_url.startswith('blob:'):
                            # Với blob URL, cần convert sang base64 hoặc dùng cách khác
                            print("🔄 Blob URL - thử convert...")
                            
                            # Method 1: Right-click và Save As
                            try:
                                img_element.click(button='right')
                                time.sleep(1)
                                
                                # Thử tìm "Save image as" trong context menu
                                save_selectors = [
                                    "text='Save image as'", "text='Save image'", 
                                    "text='Download image'", "[role='menuitem']:has-text('Save')"
                                ]
                                
                                for save_selector in save_selectors:
                                    try:
                                        save_option = self.page.query_selector(save_selector)
                                        if save_option:
                                            save_option.click()
                                            downloaded = True
                                            print(f"✅ Đã download qua right-click menu")
                                            break
                                    except:
                                        continue
                                        
                            except Exception as e:
                                print(f"⚠️ Right-click method failed: {e}")
                            
                            # Method 2: Playwright native download handling
                            if not downloaded:
                                try:
                                    print("🔄 Thử Playwright download...")
                                    
                                    # Setup download handler
                                    download_promise = self.page.wait_for_download()
                                    
                                    # JavaScript để trigger download
                                    js_trigger = f"""
                                    async () => {{
                                        const imgs = document.querySelectorAll('img[src*="blob:"]');
                                        if (imgs.length > {image_index}) {{
                                            const img = imgs[{image_index}];
                                            const response = await fetch(img.src);
                                            const blob = await response.blob();
                                            const url = window.URL.createObjectURL(blob);
                                            const a = document.createElement('a');
                                            a.href = url;
                                            a.download = 'freepik_image.png';
                                            document.body.appendChild(a);
                                            a.click();
                                            document.body.removeChild(a);
                                            window.URL.revokeObjectURL(url);
                                            return true;
                                        }}
                                        return false;
                                    }}
                                    """
                                    
                                    # Trigger download
                                    trigger_result = self.page.evaluate(js_trigger)
                                    
                                    if trigger_result:
                                        # Wait for download and save to correct location
                                        download = download_promise.value
                                        download.save_as(filepath)
                                        downloaded = True
                                        print(f"✅ Đã download qua Playwright: {filename}")
                                    
                                except Exception as e:
                                    print(f"⚠️ Playwright download failed: {e}")
                                    
                                    # Fallback: Base64 conversion method
                                    try:
                                        print("🔄 Thử Base64 conversion...")
                                        js_base64 = f"""
                                        async () => {{
                                            const imgs = document.querySelectorAll('img[src*="blob:"]');
                                            if (imgs.length > {image_index}) {{
                                                const img = imgs[{image_index}];
                                                const response = await fetch(img.src);
                                                const blob = await response.blob();
                                                
                                                return new Promise((resolve) => {{
                                                    const reader = new FileReader();
                                                    reader.onloadend = () => resolve(reader.result);
                                                    reader.readAsDataURL(blob);
                                                }});
                                            }}
                                            return null;
                                        }}
                                        """
                                        
                                        base64_data = self.page.evaluate(js_base64)
                                        
                                        if base64_data and base64_data.startswith('data:image'):
                                            # Remove data:image/png;base64, prefix
                                            base64_data = base64_data.split(',')[1]
                                            
                                            # Decode và save
                                            import base64
                                            image_data = base64.b64decode(base64_data)
                                            
                                            with open(filepath, 'wb') as f:
                                                f.write(image_data)
                                            
                                            downloaded = True
                                            print(f"✅ Đã download qua Base64: {filename}")
                                            
                                    except Exception as e2:
                                        print(f"⚠️ Base64 method failed: {e2}")
                
                except Exception as e:
                    print(f"⚠️ Lỗi download URL: {e}")
            
            # Cách 3: Screenshot ảnh cụ thể (fallback)
            if not downloaded:
                print(f"🔍 Fallback: Screenshot ảnh {image_index + 1} trực tiếp...")
                img_selectors = [
                    f"img[src*='generated']:nth({image_index})",
                    f"img[alt*='Generated']:nth({image_index})", 
                    f".result-image img:nth({image_index})",
                    f".generated-image img:nth({image_index})",
                    f"[data-testid*='result'] img:nth({image_index})",
                    f"img[src*='blob:']:nth({image_index})",
                    f"img[src*='freepik']:nth({image_index})",
                    f"canvas:nth({image_index})",
                    # Fallback không có index
                    "img[src*='generated']",
                    "img[alt*='Generated']", 
                    ".result-image img",
                    ".generated-image img",
                    "[data-testid*='result'] img",
                    "img[src*='blob:']",
                    "img[src*='freepik']",
                    "canvas"
                ]
                
                for selector in img_selectors:
                    try:
                        # Tách selector và index
                        base_selector = selector.split(':nth(')[0]
                        elements = self.page.query_selector_all(base_selector)
                        
                        if elements and len(elements) > image_index:
                            element = elements[image_index]
                        elif not ':nth(' in selector:
                            element = self.page.query_selector(selector)
                        else:
                            continue
                        
                        if element and element.is_visible():
                            print(f"🔍 Tìm thấy ảnh {image_index + 1}: {base_selector}")
                            
                            # Scroll đến ảnh
                            element.scroll_into_view_if_needed()
                            time.sleep(1)
                            
                            # Screenshot ảnh
                            element.screenshot(path=filepath)
                            downloaded = True
                            print(f"✅ Đã screenshot ảnh {image_index + 1}: {filepath}")
                            break
                    except Exception as e:
                        print(f"⚠️ Lỗi với img selector {selector}: {e}")
                        continue
            
            # Cách 3: Screenshot vùng chứa ảnh cụ thể
            if not downloaded:
                print(f"🔍 Thử screenshot vùng kết quả {image_index + 1}...")
                try:
                    result_area_selectors = [
                        f"[data-testid*='result']:nth({image_index})",
                        f".result-container:nth({image_index})",
                        f".generated-content:nth({image_index})",
                        f".output-area:nth({image_index})"
                    ]
                    
                    for selector in result_area_selectors:
                        try:
                            base_selector = selector.split(':nth(')[0]
                            elements = self.page.query_selector_all(base_selector)
                            
                            if elements and len(elements) > image_index:
                                element = elements[image_index]
                                element.screenshot(path=filepath)
                                downloaded = True
                                print(f"✅ Đã screenshot vùng kết quả {image_index + 1}: {filepath}")
                                break
                        except:
                            continue
                            
                except Exception as e:
                    print(f"⚠️ Lỗi screenshot vùng kết quả: {e}")
            
            if downloaded:
                self.generation_stats["successful_downloads"] += 1
                return filepath
            else:
                self.generation_stats["failed_downloads"] += 1
                print(f"❌ Không thể tải ảnh {image_index + 1}")
                return None
                    
        except Exception as e:
            print(f"❌ Lỗi khi tải ảnh {image_index + 1}: {e}")
            self.generation_stats["failed_downloads"] += 1
            return None

    def _download_image_fallback(self, image_index: int, filename_prefix: str = "freepik_image") -> Optional[str]:
        """Method dự phòng để tải ảnh khi method chính thất bại"""
        try:
            timestamp = int(time.time())
            filename = f"{filename_prefix}_{timestamp}_{image_index + 1}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            print(f"🔧 Thử method dự phòng: screenshot toàn màn hình...")
            
            # Method 1: Screenshot toàn bộ viewport và crop
            try:
                # Scroll to ensure images are in view
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
                time.sleep(2)
                
                # Take full page screenshot
                full_screenshot = os.path.join(self.output_dir, f"temp_full_{timestamp}.png")
                self.page.screenshot(path=full_screenshot, full_page=True)
                
                # This is a basic fallback - in reality you'd want to crop specific regions
                # For now, just rename the file to indicate it's a fallback
                fallback_filepath = os.path.join(self.output_dir, f"fallback_{filename}")
                import shutil
                shutil.move(full_screenshot, fallback_filepath)
                
                print(f"✅ Fallback screenshot thành công: {os.path.basename(fallback_filepath)}")
                return fallback_filepath
                
            except Exception as e:
                print(f"❌ Fallback screenshot thất bại: {e}")
                
            # Method 2: Thử các selectors khác
            try:
                print("🔧 Thử tải qua right-click context menu...")
                
                generic_selectors = [
                    f"img:nth-of-type({image_index + 1})",
                    f"canvas:nth-of-type({image_index + 1})",
                    f"[role='img']:nth-of-type({image_index + 1})"
                ]
                
                for selector in generic_selectors:
                    try:
                        element = self.page.query_selector(selector)
                        if element and element.is_visible():
                            element.screenshot(path=filepath)
                            print(f"✅ Fallback selector thành công: {selector}")
                            return filepath
                    except:
                        continue
                        
            except Exception as e:
                print(f"❌ Fallback selectors thất bại: {e}")
            
            return None
            
        except Exception as e:
            print(f"❌ Fallback method hoàn toàn thất bại: {e}")
            return None

    def generate_image(self, prompt: str, cookie_string: str = None, num_images: int = 4, 
                      download_count: int = None, filename_prefix: str = None):
        """
        Sinh ảnh từ prompt sử dụng Freepik AI
        
        Args:
            prompt: Mô tả ảnh cần sinh
            cookie_string: Cookie để đăng nhập (string hoặc JSON)
            num_images: Số lượng ảnh muốn AI sinh ra (mặc định: 4)
            download_count: Số lượng ảnh muốn tải về (None = tải tất cả)
            filename_prefix: Tiền tố tên file (mặc định: từ prompt)
            
        Returns:
            List[str]: Danh sách đường dẫn các file ảnh đã tải về
        """
        
        # Tạo filename_prefix từ prompt nếu không có
        if not filename_prefix:
            safe_prompt = "".join(c for c in prompt[:30] if c.isalnum() or c in (' ', '-', '_')).strip()
            filename_prefix = safe_prompt.replace(' ', '_') or "freepik_image"
        
        if download_count is None:
            download_count = num_images
        elif download_count > num_images:
            print(f"⚠️ download_count ({download_count}) > num_images ({num_images}), điều chỉnh về {num_images}")
            download_count = num_images
        
        print(f"🎨 Bắt đầu sinh {num_images} ảnh, tải về {download_count} ảnh")
        print(f"📝 Prompt: {prompt}")
        
        downloaded_files = []
        
        with sync_playwright() as p:
            # Đọc cấu hình browser từ config (mặc định Chrome để tránh lỗi)
            browser_type = "chrome"
            config_show_browser = False
            
            try:
                if os.path.exists('config_template.txt'):
                    with open('config_template.txt', 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'browser=firefox' in content:
                        browser_type = "firefox"
                    elif 'browser=chrome' in content:
                        browser_type = "chrome"
                    
                    # Đọc show_browser setting
                    if 'show_browser=true' in content:
                        config_show_browser = True
                        print("⚙️ Config: show_browser=true - sử dụng visible mode")
            except:
                pass
            
            # Ưu tiên config setting nếu không có parameter explicit
            final_headless = self.headless and not config_show_browser
            
            print(f"🌐 Sử dụng browser: {browser_type}")
            print(f"👁️ Chế độ: {'Visible' if not final_headless else 'Headless'}")
            
            # Khởi động trình duyệt tùy theo cấu hình
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
            else:  # firefox
                browser = p.firefox.launch(
                    headless=final_headless,
                    args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
                viewport={"width": 1920, "height": 1080},
                ignore_https_errors=True
            )
            
            # Thiết lập timeout mặc định
            context.set_default_timeout(30000)
            
            page = context.new_page()
            self.page = page  # Store for use in other methods
            
            try:
                # Truy cập thẳng vào AI Image Generator trước
                ai_generator_url = "https://www.freepik.com/pikaso/ai-image-generator"
                print(f"🎯 Truy cập trực tiếp AI Image Generator: {ai_generator_url}")
                
                try:
                    page.goto(ai_generator_url, wait_until="domcontentloaded", timeout=30000)
                    time.sleep(2)  # Chờ trang load cơ bản
                    
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
                        
                        if page.query_selector("text=Log in") or page.query_selector("text=Sign up"):
                            print("⚠️ Cookie có thể đã hết hạn hoặc không hợp lệ")
                        else:
                            print("✅ Đã đăng nhập thành công!")
                
                # Kiểm tra trạng thái đăng nhập
                time.sleep(3)
                
                current_cookies = page.context.cookies()
                has_auth_cookies = any(c['name'] in ['GR_TOKEN', 'GRID', 'UID'] for c in current_cookies)
                
                login_indicators = [
                    "text=Sign in", "text=Log in", "text=Sign up for free",
                    "text=Get started", "text=Create account"
                ]
                
                has_login_prompt = False
                for indicator in login_indicators:
                    if page.query_selector(indicator):
                        has_login_prompt = True
                        break
                
                if has_auth_cookies and not has_login_prompt:
                    print("✅ Đã đăng nhập Premium!")
                elif has_auth_cookies:
                    print("⚠️ Có cookie nhưng vẫn thấy prompt đăng nhập")
                    page.reload(wait_until="networkidle")
                    time.sleep(3)
                else:
                    print("ℹ️ Sử dụng free tier (chưa đăng nhập)")
                
                print("✅ Đã truy cập thành công vào AI Image Generator!")
                
                # Chờ trang load hoàn toàn trước khi tìm input
                print("⏳ Chờ trang load hoàn toàn...")
                time.sleep(5)  # Chờ 5 giây để đảm bảo trang load xong
                
                # Debug: Screenshot và URL hiện tại
                print(f"🔍 Debug: Current URL: {page.url}")
                page.screenshot(path=os.path.join(self.output_dir, "debug_main_tool_page.png"))
                print(f"🔍 Debug: Screenshot saved to debug_main_tool_page.png")
                
                # Xử lý popup/modal có thể che mất input
                print("🔍 Kiểm tra và xóa popup/modal...")
                popup_selectors = [
                    # Modal/overlay selectors
                    ".modal", ".popup", ".overlay", ".dialog",
                    "[role='dialog']", "[role='alertdialog']",
                    ".cookie-banner", ".cookie-notice",
                    ".notification", ".toast", ".alert",
                    # Freepik specific
                    ".onboarding", ".tutorial", ".intro",
                    ".welcome", ".guide", ".tooltip",
                    # Generic blocking elements
                    "[data-testid*='modal']", "[data-testid*='popup']",
                    "[aria-modal='true']", ".backdrop"
                ]
                
                for popup_selector in popup_selectors:
                    try:
                        popup_elements = page.query_selector_all(popup_selector)
                        for popup in popup_elements:
                            if popup.is_visible():
                                print(f"🗑️ Tìm thấy và xóa popup: {popup_selector}")
                                popup.evaluate("element => element.remove()")
                    except:
                        continue
                
                # Thêm thời gian chờ sau khi xóa popup
                time.sleep(2)
                
                # Kiểm tra xem có bị redirect không và force navigate nếu cần
                current_url = page.url
                target_url = "https://www.freepik.com/pikaso/ai-image-generator"
                if target_url not in current_url:
                    print(f"🔄 Bị redirect từ {target_url} đến {current_url}, force navigate...")
                    try:
                        page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
                        time.sleep(3)
                        print(f"✅ Đã force navigate về: {page.url}")
                    except Exception as e:
                        print(f"⚠️ Lỗi force navigate: {e}")
                
                # Tìm và nhập prompt
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
                        # Kiểm tra element có tồn tại không
                        element = page.query_selector(selector)
                        if element:
                            print(f"    ✓ Element tồn tại")
                            if element.is_visible():
                                print(f"    ✓ Element visible")
                                if element.is_enabled():
                                    print(f"    ✓ Element enabled")
                                    prompt_selector = selector
                                    print(f"✅ Tìm thấy ô prompt: {selector}")
                                    
                                    # Debug thông tin về element
                                    try:
                                        element_info = page.evaluate("""
                                        (selector) => {
                                            try {
                                                const el = document.querySelector(selector);
                                                if (el) {
                                                    return {
                                                        tagName: el.tagName,
                                                        contentEditable: el.contentEditable,
                                                        placeholder: el.placeholder || '',
                                                        value: el.value || '',
                                                        textContent: el.textContent.substring(0, 50) || '',
                                                        innerHTML: el.innerHTML.substring(0, 50) || '',
                                                        visible: !el.hidden && el.offsetParent !== null,
                                                        rect: el.getBoundingClientRect(),
                                                        className: el.className
                                                    };
                                                }
                                                return null;
                                            } catch(e) {
                                                return { error: e.toString() };
                                            }
                                        }
                                        """, selector)
                                        print(f"🔍 Element debug: {element_info}")
                                    except Exception as e:
                                        print(f"⚠️ Không thể debug element: {e}")
                                    
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
                    # Fallback: Scan tất cả input elements trên trang
                    print("🔍 Fallback: Tìm tất cả input có thể trên trang...")
                    try:
                        all_inputs_info = page.evaluate("""
                        (() => {
                            const inputs = [];
                            
                            // Tìm tất cả input, textarea, contenteditable
                            const allElements = [
                                ...document.querySelectorAll('input'),
                                ...document.querySelectorAll('textarea'),
                                ...document.querySelectorAll('[contenteditable="true"]'),
                                ...document.querySelectorAll('[role="textbox"]')
                            ];
                            
                            allElements.forEach((el, index) => {
                                try {
                                    if (el.offsetParent !== null && !el.disabled && !el.hidden) { // Visible and enabled
                                        const rect = el.getBoundingClientRect();
                                        if (rect.width > 0 && rect.height > 0) {
                                            // Tạo selector đơn giản và an toàn
                                            let simpleSelector = el.tagName.toLowerCase();
                                            if (el.contentEditable === 'true') {
                                                simpleSelector = '[contenteditable="true"]';
                                            } else if (el.getAttribute('role') === 'textbox') {
                                                simpleSelector = '[role="textbox"]';
                                            } else if (el.type) {
                                                simpleSelector += '[type="' + el.type + '"]';
                                            }
                                            
                                            inputs.push({
                                                selector: simpleSelector,
                                                tagName: el.tagName,
                                                type: el.type || '',
                                                placeholder: el.placeholder || '',
                                                value: (el.value || el.textContent || '').substring(0, 20),
                                                className: el.className.substring(0, 50),
                                                contentEditable: el.contentEditable,
                                                width: rect.width,
                                                height: rect.height,
                                                x: rect.x,
                                                y: rect.y,
                                                visible: true
                                            });
                                        }
                                    }
                                } catch(e) {
                                    // Skip element nếu có lỗi
                                }
                            });
                            
                            return inputs;
                        })()
                        """)
                        
                        print(f"🔍 Tìm thấy {len(all_inputs_info)} input elements:")
                        for i, input_info in enumerate(all_inputs_info):
                            print(f"  {i+1}. {input_info}")
                        
                        # Tìm input phù hợp nhất - thường là cái lớn nhất ở phía trên
                        best_input = None
                        best_score = 0
                        
                        for input_info in all_inputs_info:
                            score = 0
                            
                            # Ưu tiên input lớn
                            if input_info['width'] > 200 and input_info['height'] > 30:
                                score += 3
                            
                            # Ưu tiên contenteditable
                            if input_info['contentEditable'] == 'true':
                                score += 2
                            
                            # Ưu tiên textarea
                            if input_info['tagName'] == 'TEXTAREA':
                                score += 2
                            
                            # Ưu tiên vị trí phía trên
                            if input_info['y'] < 500:
                                score += 1
                            
                            # Ưu tiên có placeholder phù hợp
                            placeholder = input_info['placeholder'].lower()
                            if any(word in placeholder for word in ['describe', 'prompt', 'text', 'enter']):
                                score += 2
                            
                            print(f"  Input score: {score} - {input_info['tagName']} {input_info['className'][:20]}")
                            
                            if score > best_score:
                                best_score = score
                                best_input = input_info
                        
                        if best_input:
                            # Tạo selector cho input tốt nhất
                            if best_input['contentEditable'] == 'true':
                                prompt_selector = "[contenteditable='true']"
                            elif best_input['tagName'] == 'TEXTAREA':
                                prompt_selector = "textarea"
                            elif best_input['tagName'] == 'INPUT':
                                prompt_selector = "input[type='text']"
                            else:
                                prompt_selector = "[role='textbox']"
                            
                            print(f"✅ Chọn input tốt nhất: {prompt_selector} (score: {best_score})")
                        
                    except Exception as e:
                        print(f"⚠️ Lỗi fallback scan: {e}")
                
                if not prompt_selector:
                    # Screenshot để debug
                    page.screenshot(path=os.path.join(self.output_dir, "debug_no_input_found.png"))
                    raise Exception("Không tìm thấy ô nhập prompt sau tất cả các method")
                
                # Nhập prompt với nhiều phương pháp fallback
                print("✍️ Đang nhập prompt...")
                
                # Thử nhiều cách nhập prompt với error handling tốt hơn
                prompt_entered = False
                
                def method_1():
                    """Method 1: Click và fill cơ bản"""
                    page.click(prompt_selector, timeout=10000)
                    time.sleep(0.5)
                    page.fill(prompt_selector, prompt, timeout=10000)
                
                def method_2():
                    """Method 2: Focus và clear trước"""
                    page.focus(prompt_selector, timeout=5000)
                    time.sleep(0.3)
                    page.fill(prompt_selector, "", timeout=3000)  # Clear first
                    time.sleep(0.2)
                    page.fill(prompt_selector, prompt, timeout=10000)
                
                def method_3():
                    """Method 3: JavaScript trực tiếp - safe với proper escaping"""
                    # Escape both selector and prompt properly
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
                
                def method_4():
                    """Method 4: Contenteditable specific - click, clear, type"""
                    # Click vào element contenteditable
                    page.click(prompt_selector, timeout=5000)
                    time.sleep(0.5)
                    
                    # Chọn tất cả nội dung hiện tại và xóa
                    page.keyboard.press("Control+A")
                    time.sleep(0.2)
                    page.keyboard.press("Backspace")
                    time.sleep(0.5)
                    
                    # Type từ từ với delay để tránh mất ký tự
                    page.keyboard.type(prompt, delay=50)
                    time.sleep(0.5)
                    
                    # Press Enter hoặc Tab để trigger events
                    page.keyboard.press("Tab")
                    time.sleep(0.2)
                
                def method_5():
                    """Method 5: Force value với multiple events - safely escaped"""
                    try:
                        # Sử dụng page.evaluate với arguments thay vì string formatting
                        page.evaluate("""
                        (args) => {
                            try {
                                const element = document.querySelector(args.selector);
                                if (element) {
                                    // Clear first
                                    if (element.value !== undefined) {
                                        element.value = '';
                                    }
                                    if (element.textContent !== undefined) {
                                        element.textContent = '';
                                    }
                                    
                                    // Set value
                                    if (element.value !== undefined) {
                                        element.value = args.prompt;
                                    }
                                    
                                    // For contenteditable
                                    if (element.contentEditable === 'true') {
                                        element.textContent = args.prompt;
                                        element.innerHTML = args.prompt;
                                    }
                                    
                                    // Trigger events
                                    const events = ['focus', 'input', 'change', 'keyup', 'blur'];
                                    events.forEach(eventType => {
                                        const event = new Event(eventType, { bubbles: true });
                                        element.dispatchEvent(event);
                                    });
                                }
                            } catch(e) {
                                console.log('Method 5 error:', e);
                            }
                        }
                        """, {"selector": prompt_selector, "prompt": prompt})
                    except Exception as e:
                        print(f"Method 5 JavaScript error: {e}")
                
                # ƯU TIÊN METHOD 3 (JavaScript) theo yêu cầu user
                methods = [method_3, method_5, method_1, method_2, method_4]
                
                for i, method in enumerate(methods):
                    try:
                        print(f"  🔄 Thử phương pháp {i+1}...")
                        method()
                        
                        # Chờ lâu hơn để DOM update
                        time.sleep(2)
                        
                        # Kiểm tra xem đã nhập thành công chưa - với nhiều cách
                        current_value = ""
                        
                        # Cách 1: input_value (cho input/textarea)
                        try:
                            current_value = page.input_value(prompt_selector)
                            if current_value:
                                print(f"  📝 Phát hiện qua input_value: '{current_value[:30]}...'")
                        except:
                            pass
                        
                        # Cách 2: JavaScript get content (cho contenteditable)
                        if not current_value:
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
                                if current_value:
                                    print(f"  📝 Phát hiện qua JavaScript: '{current_value[:30]}...'")
                            except Exception as e:
                                print(f"  ⚠️ Lỗi JavaScript check: {e}")
                        
                        # Cách 3: Check visual - nếu có text xuất hiện trên trang
                        if not current_value:
                            try:
                                # Tìm text prompt trong page content
                                if prompt[:10] in page.content():
                                    current_value = prompt  # Assume success
                                    print(f"  📝 Phát hiện qua page content search")
                            except:
                                pass
                        
                        # Đánh giá kết quả
                        prompt_words = prompt.lower().split()[:3]  # 3 từ đầu
                        current_words = current_value.lower().split()[:3] if current_value else []
                        
                        # Thành công nếu có ít nhất 2/3 từ đầu khớp hoặc length > 5
                        success = False
                        if current_value and len(current_value.strip()) > 5:
                            if len(set(prompt_words) & set(current_words)) >= 2:
                                success = True
                            elif len(current_value.strip()) >= len(prompt) * 0.7:  # 70% length
                                success = True
                        
                        if success:
                            print(f"  ✅ THÀNH CÔNG với phương pháp {i+1}! Content: '{current_value[:50]}...'")
                            prompt_entered = True
                            break
                        else:
                            print(f"  ⚠️ Phương pháp {i+1} chưa đủ: '{current_value[:30]}...' (len={len(current_value) if current_value else 0})")
                            
                    except Exception as e:
                        print(f"  ❌ Phương pháp {i+1} lỗi: {e}")
                        continue
                
                if not prompt_entered:
                    print("❌ Không thể nhập prompt bằng bất kỳ phương pháp nào")
                    # Screenshot để debug
                    page.screenshot(path=os.path.join(self.output_dir, "debug_prompt_error.png"))
                    raise Exception("Không thể nhập prompt vào ô input")
                
                print(f"✅ Đã nhập prompt thành công")
                
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
                
                # Chờ ảnh được sinh ra
                print("⏳ Đang chờ ảnh được sinh ra...")
                
                # Đợi kết quả trong 120 giây (tăng thời gian chờ cho nhiều ảnh)
                result_found = False
                for i in range(120):
                    try:
                        # Kiểm tra các thông báo lỗi chi tiết hơn
                        error_messages = [
                            "text=Sign up", "text=Credits required", "text=Credit", 
                            "text=Subscribe", "text=Upgrade", "text=Premium",
                            "text=Limit reached", "text=Daily limit", "text=Free limit"
                        ]
                        
                        found_error = False
                        error_type = ""
                        
                        for error_msg in error_messages:
                            if page.query_selector(error_msg):
                                found_error = True
                                error_type = error_msg
                                break
                        
                        if found_error:
                            print(f"⚠️ Phát hiện thông báo: {error_type}")
                            
                            # Kiểm tra thêm context để xác định chính xác
                            page_content = page.content().lower()
                            
                            # Debug: In ra một phần content để hiểu
                            debug_content = page_content[max(0, page_content.find("credit")-50):page_content.find("credit")+100] if "credit" in page_content else ""
                            if debug_content:
                                print(f"🔍 Debug content: ...{debug_content}...")
                            
                            if "credit" in page_content and ("required" in page_content or "needed" in page_content):
                                print("❌ Xác nhận: Hết credits")
                                break
                            elif "sign up" in page_content or "log in" in page_content:
                                print("❌ Xác nhận: Cần đăng nhập")
                                break
                            else:
                                print("⚠️ Thông báo không rõ ràng, tiếp tục chờ...")
                                # Screenshot để debug
                                if i == 10:  # Screenshot sau 10 giây
                                    page.screenshot(path=os.path.join(self.output_dir, f"debug_generation_{i}s.png"))
                                    print(f"📸 Đã chụp screenshot debug tại {i}s")
                                # Không break, tiếp tục chờ
                        
                        # Tìm ảnh kết quả - tìm tất cả ảnh
                        result_selectors = [
                            "img[src*='generated']", "img[alt*='Generated']", 
                            ".result-image img", ".generated-image", "[data-testid*='result'] img",
                            "img[src*='blob:']", "canvas"
                        ]
                        
                        found_images = 0
                        for selector in result_selectors:
                            try:
                                elements = page.query_selector_all(selector)
                                visible_elements = [e for e in elements if e.is_visible()]
                                found_images = max(found_images, len(visible_elements))
                            except:
                                continue
                        
                        if found_images >= num_images:
                            print(f"✅ Đã sinh ra {found_images} ảnh!")
                            result_found = True
                            break
                        elif found_images > 0:
                            print(f"⏳ Đã có {found_images}/{num_images} ảnh... ({i+1}/120s)")
                            
                        time.sleep(1)
                        
                    except:
                        time.sleep(1)
                
                if not result_found:
                    # Kiểm tra lại lý do timeout chi tiết
                    page_content = page.content().lower()
                    
                    if page.query_selector("text=Sign up") or "sign up" in page_content:
                        raise Exception("Free tier yêu cầu đăng ký - cần tài khoản Premium")
                    elif "credit" in page_content and ("required" in page_content or "needed" in page_content or "insufficient" in page_content):
                        raise Exception("Hết credits - cần tài khoản Premium")
                    elif page.query_selector("text=Error") or "error" in page_content:
                        print("⚠️ Có lỗi xảy ra, thử tải ảnh có sẵn...")
                    else:
                        print("⚠️ Timeout nhưng thử tải ảnh có sẵn...")
                
                # Tải ảnh về theo thứ tự với retry logic
                print(f"💾 Đang tải {download_count} ảnh về theo thứ tự...")
                
                # Đầu tiên kiểm tra có bao nhiêu ảnh thực tế có sẵn
                print("🔍 Kiểm tra số ảnh có sẵn trên trang...")
                available_images = 0
                result_selectors = [
                    "img[src*='generated']", "img[alt*='Generated']", 
                    ".result-image img", ".generated-image img", "[data-testid*='result'] img",
                    "img[src*='blob:']", "img[src*='freepik']", "canvas"
                ]
                
                for selector in result_selectors:
                    try:
                        elements = page.query_selector_all(selector)
                        visible_elements = [e for e in elements if e.is_visible()]
                        available_images = max(available_images, len(visible_elements))
                    except:
                        continue
                
                print(f"📊 Phát hiện {available_images} ảnh có sẵn trên trang")
                actual_download_count = min(download_count, available_images)
                
                if actual_download_count < download_count:
                    print(f"⚠️ Chỉ có thể tải {actual_download_count}/{download_count} ảnh")
                
                # Tải từng ảnh với retry và tránh xung đột
                for i in range(actual_download_count):
                    print(f"\n📥 Tải ảnh {i+1}/{actual_download_count}...")
                    
                    # Scroll lên top để reset vị trí trang, tránh click nhầm
                    page.evaluate("window.scrollTo(0, 0)")
                    time.sleep(1)
                    
                    # Scroll đến vùng kết quả để thấy ảnh cần tải
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.6)")
                    time.sleep(1)
                    
                    # Thử tải với retry logic
                    max_retries = 3
                    filepath = None
                    
                    for retry in range(max_retries):
                        if retry > 0:
                            print(f"🔄 Thử lại lần {retry + 1}/{max_retries}...")
                            time.sleep(3)  # Chờ lâu hơn khi retry
                    
                        filepath = self._download_single_image(
                            image_index=i, 
                            filename_prefix=filename_prefix
                        )
                        
                        if filepath:
                            break  # Thành công thì thoát khỏi retry loop
                        
                    if filepath:
                        downloaded_files.append(filepath)
                        print(f"✅ Thành công: {os.path.basename(filepath)}")
                    else:
                        print(f"❌ Thất bại tải ảnh {i+1} sau {max_retries} lần thử")
                        
                        # Thử các cách khác nếu download thất bại
                        print(f"🔧 Thử method dự phòng cho ảnh {i+1}...")
                        fallback_filepath = self._download_image_fallback(i, filename_prefix)
                        if fallback_filepath:
                            downloaded_files.append(fallback_filepath)
                            print(f"✅ Dự phòng thành công: {os.path.basename(fallback_filepath)}")
                    
                    # Delay dài hơn giữa các lần tải để tránh xung đột
                    if i < actual_download_count - 1:
                        print(f"⏳ Chờ {3} giây trước khi tải ảnh tiếp theo...")
                        time.sleep(3)
                
                self.generation_stats["total_generated"] += len(downloaded_files)
                
                # Tóm tắt kết quả
                print(f"\n🎯 TỔNG KẾT:")
                print(f"✅ Đã tải thành công: {len(downloaded_files)}/{download_count}")
                print(f"📁 Thư mục lưu: {self.output_dir}/")
                
                for i, filepath in enumerate(downloaded_files, 1):
                    print(f"  {i}. {os.path.basename(filepath)}")
                
                return downloaded_files
                    
            except Exception as e:
                print(f"❌ Lỗi khi sinh ảnh: {e}")
                return downloaded_files
                
            finally:
                browser.close() 