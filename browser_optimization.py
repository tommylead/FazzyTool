"""
Browser Optimization Utilities for FazzyTool
Cải thiện browser automation và xử lý timeout
"""

import time
import json
from typing import Optional, List, Dict
from playwright.sync_api import Page


class BrowserOptimizer:
    """Lớp tối ưu browser automation với các phương pháp fallback"""
    
    def __init__(self, page: Page):
        self.page = page
        
    def smart_input_prompt(self, prompt: str, selectors: List[str] = None) -> bool:
        """
        Nhập prompt thông minh với nhiều phương pháp fallback
        
        Args:
            prompt: Text cần nhập
            selectors: List các selector để thử (optional)
            
        Returns:
            True nếu thành công, False nếu thất bại
        """
        if not selectors:
            selectors = [
                "textarea[placeholder*='Describe']",
                "textarea[placeholder*='prompt']", 
                "input[name='queryInput']",
                "textarea[data-testid*='prompt']",
                "[contenteditable='true']",
                "textarea",
                "input[type='text']",
                ".prompt-input",
                "#prompt-input"
            ]
        
        for i, selector in enumerate(selectors, 1):
            print(f"  🔄 Thử selector {i}: {selector}...")
            
            if self._try_input_with_selector(prompt, selector):
                print(f"  ✅ Thành công với selector {i}")
                return True
                
        return False
    
    def _try_input_with_selector(self, prompt: str, selector: str) -> bool:
        """Thử nhập prompt với một selector cụ thể"""
        try:
            # Kiểm tra element tồn tại và visible
            if not self._wait_for_element(selector, timeout=3000):
                return False
                
            if not self.page.is_visible(selector) or not self.page.is_enabled(selector):
                return False
            
            # Thử các phương pháp nhập - ƯU TIÊN PHƯƠNG PHÁP 3 (JavaScript)
            methods = [
                lambda: self._method_javascript_set(selector, prompt),  # Phương pháp 3 - ƯU TIÊN
                lambda: self._method_force_input(selector, prompt),     # Phương pháp 5
                lambda: self._method_click_and_fill(selector, prompt),  # Phương pháp 1
                lambda: self._method_focus_and_type(selector, prompt),  # Phương pháp 2
                lambda: self._method_clear_and_type(selector, prompt)   # Phương pháp 4
            ]
            
            for j, method in enumerate(methods, 1):
                try:
                    print(f"    🔄 Phương pháp {j}...")
                    method()
                    
                    # Verify input worked
                    if self._verify_input(selector, prompt):
                        print(f"    ✅ Thành công phương pháp {j}")
                        return True
                        
                except Exception as e:
                    print(f"    ❌ Phương pháp {j} lỗi: {str(e)[:50]}...")
                    continue
                    
        except Exception as e:
            print(f"    ❌ Selector lỗi: {str(e)[:50]}...")
            
        return False
    
    def _wait_for_element(self, selector: str, timeout: int = 5000) -> bool:
        """Đợi element xuất hiện"""
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    def _method_click_and_fill(self, selector: str, text: str):
        """Phương pháp 1: Click và fill cơ bản"""
        self.page.click(selector, timeout=5000)
        time.sleep(0.2)
        self.page.fill(selector, text, timeout=10000)
    
    def _method_focus_and_type(self, selector: str, text: str):
        """Phương pháp 2: Focus và type từng ký tự"""
        self.page.focus(selector, timeout=5000)
        time.sleep(0.2)
        self.page.keyboard.press("Control+A")
        time.sleep(0.1)
        self.page.keyboard.press("Delete")
        time.sleep(0.1)
        
        # Type theo chunks để tránh timeout
        chunk_size = 50
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            self.page.keyboard.type(chunk, delay=10)
            time.sleep(0.05)
    
    def _method_javascript_set(self, selector: str, text: str):
        """Phương pháp 3: Sử dụng JavaScript trực tiếp - CẢI TIẾN THEO YÊU CẦU USER"""
        # Sử dụng page.evaluate với arguments để tránh escaping issues
        js_code = """
        (args) => {
            try {
                const element = document.querySelector(args.selector);
                if (element) {
                    // Focus và scroll element vào view
                    element.focus();
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    
                    // Clear content trước
                    if (element.value !== undefined) {
                        element.value = '';
                    }
                    if (element.textContent !== undefined) {
                        element.textContent = '';
                    }
                    if (element.innerHTML !== undefined) {
                        element.innerHTML = '';
                    }
                    
                    // Set new value
                    if (element.value !== undefined) {
                        element.value = args.text;
                    }
                    
                    // For contenteditable elements
                    if (element.contentEditable === 'true') {
                        element.textContent = args.text;
                        element.innerHTML = args.text;
                    }
                    
                    // Trigger comprehensive events để đảm bảo framework updates
                    const events = [
                        'focus', 'click', 'input', 'change', 'keyup', 'keydown', 
                        'paste', 'blur', 'textInput'
                    ];
                    
                    events.forEach(eventType => {
                        try {
                            let event;
                            if (eventType === 'keyup' || eventType === 'keydown') {
                                event = new KeyboardEvent(eventType, { 
                                    bubbles: true, 
                                    cancelable: true,
                                    key: 'Enter'
                                });
                            } else {
                                event = new Event(eventType, { 
                                    bubbles: true, 
                                    cancelable: true 
                                });
                            }
                            element.dispatchEvent(event);
                        } catch(e) {
                            console.log('Event error:', e);
                        }
                    });
                    
                    // Force React/Vue/Angular framework updates
                    try {
                        const reactKey = Object.keys(element).find(key => 
                            key.startsWith('__react') || key.startsWith('_vue') || key.startsWith('ng-')
                        );
                        if (reactKey && element[reactKey]?.memoizedProps?.onChange) {
                            element[reactKey].memoizedProps.onChange({
                                target: element,
                                type: 'change'
                            });
                        }
                    } catch(e) {
                        console.log('Framework update error:', e);
                    }
                    
                    // Trigger custom events for modern apps
                    try {
                        element.dispatchEvent(new CustomEvent('forceUpdate', { 
                            bubbles: true,
                            detail: { source: 'fazzy-tool' }
                        }));
                    } catch(e) {}
                    
                    return true;
                }
                return false;
            } catch(e) {
                console.log('JavaScript method error:', e);
                return false;
            }
        }
        """
        
        return self.page.evaluate(js_code, {"selector": selector, "text": text})
    
    def _method_clear_and_type(self, selector: str, text: str):
        """Phương pháp 4: Clear rồi type chậm"""
        self.page.click(selector, timeout=5000)
        time.sleep(0.1)
        
        # Clear multiple ways
        self.page.keyboard.press("Control+A")
        time.sleep(0.1)
        self.page.keyboard.press("Backspace")
        time.sleep(0.1)
        self.page.keyboard.press("Delete")
        time.sleep(0.1)
        
        # Type slower
        self.page.keyboard.type(text, delay=25)
    
    def _method_force_input(self, selector: str, text: str):
        """Phương pháp 5: Force input với nhiều events"""
        js_code = f"""
        const element = document.querySelector('{selector}');
        if (element) {{
            // Focus first
            element.focus();
            element.click();
            
            // Clear content
            element.value = '';
            element.textContent = '';
            
            // Set value
            element.value = {json.dumps(text)};
            
            // For contenteditable
            if (element.contentEditable === 'true') {{
                element.innerHTML = {json.dumps(text)};
                element.textContent = {json.dumps(text)};
            }}
            
            // Trigger all possible events
            ['focus', 'click', 'input', 'change', 'keyup', 'keydown', 'paste'].forEach(eventType => {{
                element.dispatchEvent(new Event(eventType, {{ bubbles: true }}));
            }});
            
            // Force React/Vue updates
            const reactKey = Object.keys(element).find(key => key.startsWith('__react'));
            if (reactKey) {{
                element[reactKey].memoizedProps.onChange({{target: element}});
            }}
        }}
        """
        self.page.evaluate(js_code)
    
    def _verify_input(self, selector: str, expected_text: str) -> bool:
        """Verify rằng input đã được nhập thành công"""
        try:
            time.sleep(0.3)  # Wait for input to register
            
            # Try multiple ways to get value
            try:
                current_value = self.page.input_value(selector)
            except:
                try:
                    current_value = self.page.evaluate(f"document.querySelector('{selector}').value")
                except:
                    current_value = self.page.evaluate(f"document.querySelector('{selector}').textContent")
            
            if current_value and len(current_value.strip()) >= len(expected_text) * 0.8:
                return True
                
        except Exception as e:
            print(f"      ⚠️ Verify error: {e}")
            
        return False
    
    def smart_click_button(self, button_texts: List[str]) -> bool:
        """
        Click button thông minh với nhiều text options
        
        Args:
            button_texts: List các text có thể có của button
            
        Returns:
            True nếu thành công click
        """
        selectors = []
        
        # Generate selectors for each text
        for text in button_texts:
            selectors.extend([
                f"button:has-text('{text}')",
                f"a:has-text('{text}')",
                f"[role='button']:has-text('{text}')",
                f"input[value='{text}']",
                f"button[aria-label*='{text}']",
                f"[data-testid*='{text.lower()}']"
            ])
        
        # NEW SPECIFIC GENERATE BUTTON SELECTORS (từ user feedback)
        selectors.extend([
            # Selector cụ thể cho Generate button mới
            "[data-cy='generate-button']",
            "[data-tour='generate-button']",
            "button[class*='bg-blue-500'][class*='hover:bg-blue-600']",
            "button[class*='w-full'][class*='text-white']:has-text('Generate')",
            # Generic selectors
            "button[type='submit']",
            "input[type='submit']", 
            ".btn-primary",
            ".generate-btn",
            "[data-testid*='generate']",
            "[data-testid*='submit']",
            "button:has-text('Generate')",
            "button:has-text('generate')"
        ])
        
        for i, selector in enumerate(selectors, 1):
            try:
                print(f"  🔄 Thử click {i}: {selector}...")
                
                if self._wait_for_element(selector, 2000):
                    if self.page.is_visible(selector) and self.page.is_enabled(selector):
                        self.page.click(selector, timeout=5000)
                        print(f"  ✅ Clicked thành công: {selector}")
                        return True
                        
            except Exception as e:
                print(f"  ❌ Click {i} lỗi: {str(e)[:50]}...")
                continue
                
        return False
    
    def wait_for_generation(self, timeout_seconds: int = 120) -> bool:
        """
        Đợi quá trình generation hoàn thành với nhiều indicator
        
        Args:
            timeout_seconds: Thời gian đợi tối đa
            
        Returns:
            True nếu generation thành công
        """
        start_time = time.time()
        
        # Các indicator cho generation đang chạy
        loading_indicators = [
            "[data-testid*='loading']",
            ".loading",
            ".spinner", 
            "text=Generating",
            "text=Loading",
            "[aria-label*='loading']"
        ]
        
        # Các indicator cho generation hoàn thành
        success_indicators = [
            "button:has-text('Download')",
            "a:has-text('Download')",
            "[data-testid*='download']",
            ".download-btn",
            "img[src*='generated']",
            "[data-testid*='result']"
        ]
        
        # Các indicator lỗi
        error_indicators = [
            "text=Error",
            "text=Failed",
            "text=Something went wrong",
            ".error-message",
            "[data-testid*='error']"
        ]
        
        print(f"⏳ Đợi generation trong {timeout_seconds}s...")
        
        while time.time() - start_time < timeout_seconds:
            # Check for errors first
            for error_selector in error_indicators:
                if self.page.query_selector(error_selector):
                    print(f"❌ Phát hiện lỗi: {error_selector}")
                    return False
            
            # Check for success
            for success_selector in success_indicators:
                if self.page.query_selector(success_selector):
                    print(f"✅ Generation hoàn thành: {success_selector}")
                    return True
            
            # Show progress if loading indicators present
            for loading_selector in loading_indicators:
                if self.page.query_selector(loading_selector):
                    elapsed = int(time.time() - start_time)
                    print(f"  ⏳ Đang generate... ({elapsed}s/{timeout_seconds}s)")
                    break
            
            time.sleep(2)
        
        print(f"⏰ Timeout sau {timeout_seconds}s")
        return False


def create_optimized_browser_context(playwright, browser_type: str = "firefox"):
    """
    Tạo browser context được tối ưu cho automation
    
    Args:
        playwright: Playwright instance
        browser_type: "firefox" hoặc "chrome"
        
    Returns:
        Browser context đã được tối ưu
    """
    if browser_type.lower() == "chrome":
        browser = playwright.chromium.launch(
            headless=False,
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
        browser = playwright.firefox.launch(
            headless=False,
            firefox_user_prefs={
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False,
                "general.platform.override": "Win32"
            }
        )
    
    # Create optimized context
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        java_script_enabled=True,
        permissions=["notifications"],
        color_scheme="light"
    )
    
    # Set optimized timeouts
    context.set_default_timeout(30000)
    context.set_default_navigation_timeout(45000)
    
    return context 