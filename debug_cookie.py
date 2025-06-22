#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug cookie parsing để tìm lỗi
"""

import json

def debug_cookie_file():
    """Debug cookie từ file"""
    print("🔍 Debug Cookie Parsing")
    print("=" * 50)
    
    try:
        with open('cookie_template.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Tìm JSON part
        start_marker = "=== PASTE COOKIE JSON VÀO ĐÂY ==="
        end_marker = "=== KẾT THÚC COOKIE ==="
        
        print(f"🔍 Tìm kiếm markers...")
        print(f"  Start marker: '{start_marker}'")
        print(f"  End marker: '{end_marker}'")
        
        start_idx = content.find(start_marker)
        if start_idx == -1:
            print("❌ Không tìm thấy start marker")
            return False
            
        json_start = start_idx + len(start_marker)
        end_idx = content.find(end_marker, json_start)
        
        if end_idx == -1:
            # Không có end marker, lấy đến cuối file
            cookie_json = content[json_start:].strip()
        else:
            cookie_json = content[json_start:end_idx].strip()
        
        print(f"📋 Cookie JSON length: {len(cookie_json)} chars")
        print(f"🔤 First 200 chars: {cookie_json[:200]}...")
        
        # Thử parse JSON
        try:
            cookies = json.loads(cookie_json)
            print(f"✅ Parse JSON thành công: {len(cookies)} cookies")
            
            # Debug từng cookie
            invalid_cookies = []
            for i, cookie in enumerate(cookies):
                print(f"\n🍪 Cookie {i+1}: {cookie.get('name', 'NO_NAME')}")
                
                # Kiểm tra required fields
                required_fields = ['name', 'value', 'domain']
                missing_fields = []
                for field in required_fields:
                    if field not in cookie:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"  ❌ Thiếu fields: {missing_fields}")
                    invalid_cookies.append(i+1)
                else:
                    print(f"  ✅ Required fields OK")
                
                # Kiểm tra field types
                problematic_fields = []
                for key, value in cookie.items():
                    if key in ['expirationDate'] and value is not None:
                        if not isinstance(value, (int, float)):
                            problematic_fields.append(f"{key}={type(value)}")
                    elif key in ['secure', 'httpOnly', 'hostOnly', 'session'] and value is not None:
                        if not isinstance(value, bool):
                            problematic_fields.append(f"{key}={type(value)}")
                
                if problematic_fields:
                    print(f"  ⚠️ Problematic fields: {problematic_fields}")
                
                # Show key fields
                key_fields = ['name', 'domain', 'path', 'secure', 'sameSite']
                for field in key_fields:
                    if field in cookie:
                        print(f"    {field}: {cookie[field]} ({type(cookie[field])})")
            
            print(f"\n📊 Summary:")
            print(f"  - Total cookies: {len(cookies)}")
            print(f"  - Invalid cookies: {len(invalid_cookies)}")
            if invalid_cookies:
                print(f"  - Invalid cookie numbers: {invalid_cookies}")
            
            return len(invalid_cookies) == 0
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"📍 Error position: {e.pos}")
            if e.pos < len(cookie_json):
                error_context = cookie_json[max(0, e.pos-50):e.pos+50]
                print(f"🔍 Error context: ...{error_context}...")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def create_fixed_cookie_parser():
    """Tạo cookie parser cải thiện"""
    print("\n🔧 Tạo cookie parser cải thiện...")
    
    fixed_parser = '''
def parse_cookies_improved(self, cookie_input: str):
    """Parse cookie từ string hoặc JSON - version cải thiện"""
    if not cookie_input or not cookie_input.strip():
        return []
        
    # Kiểm tra placeholder cookie
    if cookie_input.strip() == "placeholder_cookie":
        print("⚠️ Cookie placeholder được phát hiện, bỏ qua...")
        return []
        
    cookies = []
    
    try:
        # Extract JSON from template file
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
        
        # Thử parse JSON
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
                
                # Skip expirationDate - it causes issues
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
'''
    
    print("💾 Fixed parser được tạo!")
    return fixed_parser

if __name__ == "__main__":
    success = debug_cookie_file()
    if not success:
        create_fixed_cookie_parser() 