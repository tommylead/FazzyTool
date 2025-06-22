"""
Test logic download mới với URL video cụ thể
"""

from playwright.sync_api import sync_playwright
import os
from datetime import datetime

def test_video_download():
    """Test download video với URL cụ thể"""
    
    # URL video từ element bạn cung cấp
    video_url = "https://pikaso.cdnpk.net/private/production/2025121484/729ce297-37d4-4b15-86b8-5976b974e688-0.mp4?token=exp=1763769600~hmac=0d9ad472cfe6934dc8d4397c6128bc462fa3f4be5e50be43341eb6a515b95a28"
    
    # Tạo tên file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_video_{timestamp}.mp4"
    filepath = os.path.join("output", filename)
    
    # Tạo thư mục output nếu chưa có
    os.makedirs("output", exist_ok=True)
    
    print(f"🎬 Test download video: {filename}")
    print(f"🔗 URL: {video_url[:100]}...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Đi đến trang bất kỳ để có context
            page.goto("https://www.freepik.com")
            
            print("🔍 Thử method 1: Fetch API...")
            try:
                download_script = f"""
                    (async () => {{
                        try {{
                            console.log('Bắt đầu fetch...');
                            const response = await fetch('{video_url}');
                            console.log('Response status:', response.status);
                            
                            if (!response.ok) {{
                                throw new Error('Response not ok: ' + response.status);
                            }}
                            
                            const blob = await response.blob();
                            console.log('Blob size:', blob.size);
                            
                            const url = window.URL.createObjectURL(blob);
                            const link = document.createElement('a');
                            link.href = url;
                            link.download = '{filename}';
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                            window.URL.revokeObjectURL(url);
                            
                            console.log('Download triggered');
                            return true;
                        }} catch (e) {{
                            console.error('Download error:', e);
                            return false;
                        }}
                    }})()
                """
                
                with page.expect_download(timeout=30000) as download_info:
                    result = page.evaluate(download_script)
                    print(f"Script result: {result}")
                
                download = download_info.value
                download.save_as(filepath)
                print(f"✅ Method 1 thành công! File lưu tại: {filepath}")
                return
                
            except Exception as e:
                print(f"❌ Method 1 thất bại: {e}")
            
            print("🔍 Thử method 2: Link đơn giản...")
            try:
                simple_script = f"""
                    const link = document.createElement('a');
                    link.href = '{video_url}';
                    link.download = '{filename}';
                    link.target = '_blank';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                """
                
                with page.expect_download(timeout=15000) as download_info:
                    page.evaluate(simple_script)
                
                download = download_info.value
                download.save_as(filepath)
                print(f"✅ Method 2 thành công! File lưu tại: {filepath}")
                return
                
            except Exception as e:
                print(f"❌ Method 2 thất bại: {e}")
            
            print("🔍 Thử method 3: Navigate trực tiếp...")
            try:
                # Navigate trực tiếp đến URL video
                with page.expect_download(timeout=20000) as download_info:
                    page.goto(video_url)
                
                download = download_info.value
                download.save_as(filepath)
                print(f"✅ Method 3 thành công! File lưu tại: {filepath}")
                return
                
            except Exception as e:
                print(f"❌ Method 3 thất bại: {e}")
            
            print("❌ Tất cả methods đều thất bại")
            
        except Exception as e:
            print(f"❌ Lỗi chung: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_video_download() 