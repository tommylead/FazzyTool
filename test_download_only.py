"""
Script test chỉ download video đã được tạo (không tạo mới)
"""

from browser_video import FreepikVideoGenerator
import json
import os
from playwright.sync_api import sync_playwright

def load_cookies_from_template():
    """Load cookies từ cookie_template.txt"""
    try:
        if not os.path.exists("cookie_template.txt"):
            return None
            
        with open("cookie_template.txt", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Tìm phần JSON cookie
        start_marker = "=== PASTE COOKIE JSON VÀO ĐÂY ==="
        end_marker = "=== KẾT THÚC COOKIE ==="
        
        start_idx = content.find(start_marker)
        end_idx = content.find(end_marker)
        
        if start_idx == -1 or end_idx == -1:
            return None
        
        # Lấy phần JSON
        json_part = content[start_idx + len(start_marker):end_idx].strip()
        
        # Thử parse JSON
        try:
            cookies = json.loads(json_part)
            if isinstance(cookies, list) and len(cookies) > 0:
                print(f"✅ Đã load {len(cookies)} cookies từ cookie_template.txt")
                return cookies
        except:
            pass
            
    except:
        pass
    return None

def test_download_existing_video():
    """Test download video đã có sẵn trên trang"""
    
    cookies = load_cookies_from_template()
    if not cookies:
        print("⚠️ Không có cookie, chạy không đăng nhập")
    
    print("🔍 Mở trang Freepik để test download...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Hiển thị browser
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Set cookies nếu có
            if cookies:
                # Convert cookies format
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
                    if 'expirationDate' in cookie:
                        playwright_cookie['expires'] = cookie['expirationDate']
                    playwright_cookies.append(playwright_cookie)
                
                context.add_cookies(playwright_cookies)
                print(f"✓ Đã thiết lập {len(playwright_cookies)} cookies")
            
            # Đi đến trang video generator
            print("🌐 Đang mở trang Freepik Pikaso Video...")
            page.goto("https://www.freepik.com/pikaso/ai-video-generator", 
                     wait_until="networkidle", timeout=30000)
            
            print("📋 Trang đã load. Hãy:")
            print("1. Kiểm tra xem có video nào trong History không")
            print("2. Click vào video để mở")
            print("3. Nhấn Enter trong terminal này để test download")
            
            input("Nhấn Enter khi đã sẵn sàng...")
            
            # Test các cách download
            print("🔍 Bắt đầu test download...")
            
            # Tìm video element
            video_found = False
            video_selectors = [
                "video",
                ".result-video video", 
                ".generated-video video",
                "[data-testid*='result'] video"
            ]
            
            for selector in video_selectors:
                try:
                    page.wait_for_selector(selector, timeout=3000)
                    print(f"✓ Tìm thấy video với selector: {selector}")
                    video_found = True
                    
                    # Lấy thông tin video
                    video_element = page.query_selector(selector)
                    if video_element:
                        video_src = video_element.get_attribute("src")
                        print(f"🔗 Video src: {video_src[:100] if video_src else 'Không có src'}...")
                    
                    break
                except:
                    continue
            
            if not video_found:
                print("❌ Không tìm thấy video element")
                return
            
            # Test các nút download
            download_selectors = [
                "button:has-text('Download')",
                "a[download]", 
                ".download-btn",
                "[data-testid*='download']",
                "button[aria-label*='download']"
            ]
            
            print("\n🔍 Tìm nút download...")
            for selector in download_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"✓ Tìm thấy {len(elements)} element với selector: {selector}")
                        for i, elem in enumerate(elements):
                            text = elem.text_content() or ""
                            visible = elem.is_visible()
                            enabled = elem.is_enabled()
                            print(f"  - Element {i+1}: text='{text}', visible={visible}, enabled={enabled}")
                except Exception as e:
                    print(f"⚠️ Lỗi với selector {selector}: {e}")
            
            print("\n📸 Test chụp màn hình video...")
            try:
                video_element = page.query_selector("video")
                if video_element:
                    screenshot_path = "test_video_screenshot.png"
                    video_element.screenshot(path=screenshot_path)
                    print(f"✅ Đã chụp màn hình: {screenshot_path}")
                else:
                    print("❌ Không thể chụp màn hình")
            except Exception as e:
                print(f"❌ Lỗi chụp màn hình: {e}")
            
            print("\n✅ Test hoàn thành. Nhấn Enter để đóng browser...")
            input()
            
        except Exception as e:
            print(f"❌ Lỗi: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_download_existing_video() 