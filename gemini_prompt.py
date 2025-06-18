"""
Module xử lý việc gọi API Gemini để sinh prompt tự động.
"""

import os
import json
from typing import Dict, Any, Optional

import google.generativeai as genai
from dotenv import load_dotenv


class GeminiPromptGenerator:
    """Lớp xử lý việc gọi API Gemini để sinh prompt tự động."""
    
    def __init__(self):
        """Khởi tạo API key từ biến môi trường."""
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY không tìm thấy trong file .env")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
    def generate_prompt(self, topic: str) -> Dict[str, Any]:
        """
        Sinh prompt từ Gemini dựa trên chủ đề đầu vào.
        
        Args:
            topic: Chủ đề tiếng Việt làm đầu vào
            
        Returns:
            Dict chứa các prompt cho ảnh và video
        """
        try:
            system_prompt = """
            Bạn là trợ lý AI chuyên tạo prompt để sinh ảnh và video AI.
            Từ chủ đề người dùng cung cấp, hãy tạo ra các prompt phù hợp.
            
            Luôn trả về kết quả chính xác theo định dạng JSON sau:
            {
              "image_prompt": "Chi tiết prompt cho AI sinh ảnh (tiếng Anh)",
              "video_prompt": "Chi tiết prompt cho AI sinh video (tiếng Anh)",
              "video_duration": "5s hoặc 10s",
              "video_ratio": "1:1, 16:9, hoặc 9:16 tùy thuộc vào nội dung"
            }
            
            Hướng dẫn:
            1. Prompt phải bằng tiếng Anh để AI tạo nội dung tốt nhất
            2. Mô tả chi tiết về visual style, màu sắc, góc nhìn, chủ thể
            3. Cho video: thêm chuyển động, transitions, camera movement
            4. Chọn thời lượng hợp lý: 5s cho nội dung đơn giản, 10s cho phức tạp
            5. Chọn tỷ lệ khung hình phù hợp với nội dung (1:1 vuông, 16:9 ngang, 9:16 dọc)
            
            Chỉ trả về JSON, không thêm bất kỳ chú thích nào khác.
            """
            
            prompt = f"Chủ đề: {topic}\n\nTạo prompt sinh ảnh và video AI từ chủ đề trên."
            
            response = self.model.generate_content(
                [system_prompt, prompt],
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "response_mime_type": "application/json",
                }
            )
            
            # Xử lý phản hồi
            result_text = response.text
            
            # Đôi khi Gemini có thể thêm các markdown code block, loại bỏ chúng
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            
            # Parse JSON
            result_data = json.loads(result_text)
            
            # Kiểm tra định dạng
            required_keys = ["image_prompt", "video_prompt", "video_duration", "video_ratio"]
            for key in required_keys:
                if key not in result_data:
                    raise ValueError(f"Thiếu trường '{key}' trong kết quả từ Gemini")
            
            return result_data
            
        except Exception as e:
            error_msg = str(e)
            
            # Xử lý các lỗi phổ biến
            if "quota" in error_msg.lower() or "exceeded" in error_msg.lower():
                raise Exception(
                    f"❌ Gemini API đã vượt quá quota miễn phí!\n"
                    f"💡 Giải pháp:\n"
                    f"1. Tạo API key mới tại: https://makersuite.google.com/app/apikey\n"
                    f"2. Hoặc sử dụng chế độ File với prompt có sẵn\n"
                    f"3. Chờ đến tháng sau để quota reset\n"
                    f"Chi tiết lỗi: {error_msg}"
                )
            elif "api" in error_msg.lower() and "key" in error_msg.lower():
                raise Exception(
                    f"❌ API Key không hợp lệ!\n"
                    f"💡 Kiểm tra lại GEMINI_API_KEY trong file .env\n"
                    f"Lấy API key mới tại: https://makersuite.google.com/app/apikey\n"
                    f"Chi tiết lỗi: {error_msg}"
                )
            else:
                raise Exception(f"❌ Lỗi khi gọi Gemini API: {error_msg}")
            
    def save_prompt_to_json(self, prompt_data: Dict[str, Any], output_path: str) -> None:
        """Lưu prompt vào file JSON."""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            print(f"Đã lưu prompt vào: {output_path}")
        except Exception as e:
            raise Exception(f"Lỗi khi lưu prompt: {str(e)}") 