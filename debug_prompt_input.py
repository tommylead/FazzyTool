#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script debug để test việc nhập prompt với cookie Chrome
"""

import json
import time
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

def debug_prompt_input():
    """Debug chi tiết việc nhập prompt"""
    
    # Đọc cookie từ file hoặc nhập trực tiếp
    try:
        with open("cookie.txt", "r", encoding="utf-8") as f:
            cookie_content = f.read().strip()
        print("✅ Đã đọc cookie từ file cookie.txt")
    except:
        print("❌ Không tìm thấy file cookie.txt")
        cookie_content = input("Paste cookie Chrome vào đây: ").strip()
    
    if not cookie_content:
        print("❌ Không có cookie!")
        return
    
    test_prompt = "test cookie với prompt debug"
    print(f"🧪 Test prompt: {test_prompt}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Hiển thị browser để debug
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # Parse và set cookies
            print("🍪 Đang set cookies...")
            if cookie_content.startswith('['):
                # JSON format
                cookies = json.loads(cookie_content)
            else:
                # String format
                cookies = []
                for item in cookie_content.split(';'):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        cookies.append({
                            'name': key.strip(),
                            'value': value.strip(),
                            'domain': '.freepik.com',
                            'path': '/'
                        })
            
            context.add_cookies(cookies)
            print(f"✅ Đã set {len(cookies)} cookies")
            
            # Vào trang Freepik AI
            print("🌐 Đang vào trang Freepik AI...")
            page.goto("https://www.freepik.com/pikaso", wait_until="networkidle")
            
            # Chờ và screenshot trang ban đầu
            time.sleep(3)
            page.screenshot(path="debug_step1_initial.png")
            print("📸 Screenshot step 1: debug_step1_initial.png")
            
            # Tìm và phân tích ô input
            print("\n🔍 Tìm ô nhập prompt...")
            
            prompt_selectors = [
                "textarea[placeholder*='prompt']",
                "textarea[placeholder*='describe']", 
                "input[placeholder*='prompt']",
                "input[placeholder*='describe']",
                "[data-testid*='prompt']",
                "[data-testid*='input']",
                ".prompt-input",
                "textarea",
                "input[type='text']"
            ]
            
            found_selector = None
            for selector in prompt_selectors:
                try:
                    element = page.query_selector(selector)
                    if element and element.is_visible():
                        print(f"✅ Tìm thấy ô input: {selector}")
                        found_selector = selector
                        
                        # Phân tích element
                        info = page.evaluate(f"""
                        (selector) => {{
                            const el = document.querySelector(selector);
                            return {{
                                tagName: el.tagName,
                                type: el.type,
                                placeholder: el.placeholder,
                                id: el.id,
                                className: el.className,
                                value: el.value,
                                contentEditable: el.contentEditable,
                                disabled: el.disabled,
                                readOnly: el.readOnly
                            }};
                        }}
                        """, selector)
                        
                        print(f"📋 Thông tin element:")
                        for key, value in info.items():
                            print(f"   {key}: {value}")
                        break
                        
                except Exception as e:
                    print(f"❌ Lỗi với selector {selector}: {e}")
                    continue
            
            if not found_selector:
                print("❌ Không tìm thấy ô input nào!")
                page.screenshot(path="debug_step2_no_input.png")
                return
            
            # Screenshot trước khi nhập
            page.screenshot(path="debug_step2_before_input.png")
            print("📸 Screenshot step 2: debug_step2_before_input.png")
            
            # Test 5 phương pháp nhập
            print(f"\n📝 Test nhập prompt: '{test_prompt}'")
            
            methods = [
                ("Method 1: Click + Fill", lambda: (
                    page.click(found_selector, timeout=10000),
                    time.sleep(0.5),
                    page.fill(found_selector, test_prompt)
                )),
                
                ("Method 2: Focus + Clear + Fill", lambda: (
                    page.focus(found_selector),
                    time.sleep(0.3),
                    page.fill(found_selector, ""),
                    time.sleep(0.2),
                    page.fill(found_selector, test_prompt)
                )),
                
                ("Method 3: JavaScript Direct", lambda: page.evaluate(f"""
                    try {{
                        const element = document.querySelector('{found_selector}');
                        if (element) {{
                            element.focus();
                            element.value = '{test_prompt}';
                            element.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            element.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        }}
                    }} catch(e) {{
                        console.log('JS error:', e);
                    }}
                """)),
                
                ("Method 4: Keyboard Type", lambda: (
                    page.click(found_selector),
                    time.sleep(0.3),
                    page.keyboard.press("Control+A"),
                    time.sleep(0.2),
                    page.keyboard.press("Backspace"),
                    time.sleep(0.3),
                    page.keyboard.type(test_prompt, delay=50)
                )),
                
                ("Method 5: Force Value", lambda: page.evaluate(f"""
                    try {{
                        const element = document.querySelector('{found_selector}');
                        if (element) {{
                            element.value = '';
                            element.textContent = '';
                            element.value = {json.dumps(test_prompt)};
                            
                            if (element.contentEditable === 'true') {{
                                element.textContent = {json.dumps(test_prompt)};
                            }}
                            
                            const events = ['focus', 'input', 'change', 'keyup'];
                            events.forEach(eventType => {{
                                const event = new Event(eventType, {{ bubbles: true }});
                                element.dispatchEvent(event);
                            }});
                        }}
                    }} catch(e) {{
                        console.log('JS force error:', e);
                    }}
                """))
            ]
            
            success_method = None
            
            for i, (method_name, method_func) in enumerate(methods):
                print(f"\n🔄 {method_name}...")
                
                try:
                    # Thực hiện method
                    method_func()
                    time.sleep(1)
                    
                    # Kiểm tra kết quả
                    try:
                        current_value = page.input_value(found_selector)
                    except:
                        current_value = page.evaluate(f"document.querySelector('{found_selector}').value")
                    
                    print(f"   📋 Giá trị hiện tại: '{current_value}'")
                    
                    if current_value and test_prompt.lower() in current_value.lower():
                        print(f"   ✅ THÀNH CÔNG!")
                        success_method = method_name
                        break
                    else:
                        print(f"   ❌ Thất bại")
                        
                except Exception as e:
                    print(f"   ❌ Lỗi: {e}")
                
                # Screenshot sau mỗi method
                page.screenshot(path=f"debug_step3_method_{i+1}.png")
                print(f"   📸 Screenshot: debug_step3_method_{i+1}.png")
            
            # Screenshot cuối cùng
            page.screenshot(path="debug_step4_final.png")
            print("📸 Screenshot final: debug_step4_final.png")
            
            # Tìm nút Generate để test
            print("\n🔍 Tìm nút Generate...")
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
                        print(f"✅ Tìm thấy nút generate: {selector}")
                        generate_found = True
                        
                        # Không click, chỉ highlight để xem
                        page.evaluate(f"""
                            document.querySelector('{selector}').style.border = '3px solid red';
                        """)
                        break
                except:
                    continue
            
            if not generate_found:
                print("❌ Không tìm thấy nút Generate")
            
            # Screenshot với highlight
            page.screenshot(path="debug_step5_generate_highlighted.png")
            print("📸 Screenshot với highlight: debug_step5_generate_highlighted.png")
            
            # Tổng kết
            print(f"\n🎯 TỔNG KẾT DEBUG:")
            print(f"✅ Selector tìm thấy: {found_selector}")
            print(f"✅ Method thành công: {success_method or 'KHÔNG CÓ'}")
            print(f"✅ Nút Generate: {'Có' if generate_found else 'Không'}")
            print(f"📁 Screenshots được lưu trong thư mục hiện tại")
            
            # Chờ user xem kết quả
            input("\n⏸️ Nhấn Enter để đóng browser...")
            
        except Exception as e:
            print(f"❌ Lỗi tổng quát: {e}")
            page.screenshot(path="debug_error.png")
            
        finally:
            browser.close()

if __name__ == "__main__":
    debug_prompt_input() 