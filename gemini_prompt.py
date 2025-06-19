"""
Module xử lý việc gọi API Gemini để sinh prompt tự động.
"""

import os
import json
from typing import Dict, Any, Optional
from datetime import datetime

import google.generativeai as genai
from dotenv import load_dotenv


class GeminiPromptGenerator:
    """Lớp xử lý việc gọi API Gemini để sinh prompt tự động."""
    
    def __init__(self, output_dir: str = "prompts"):
        """Khởi tạo API key từ biến môi trường."""
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.output_dir = output_dir
        
        # Tạo thư mục prompts nếu chưa có
        os.makedirs(self.output_dir, exist_ok=True)
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY không tìm thấy trong file .env")
            
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def generate_prompt(self, topic: str, prompt_id: Optional[str] = None, save_to_file: bool = True) -> Dict[str, Any]:
        """
        Sinh prompt từ Gemini dựa trên chủ đề đầu vào.
        
        Args:
            topic: Chủ đề tiếng Việt làm đầu vào
            prompt_id: ID/số thứ tự cho prompt (tự động tạo nếu None)
            save_to_file: Có lưu vào file hay không
            
        Returns:
            Dict chứa các prompt cho ảnh và video + thông tin file
        """
        try:
            # Tạo prompt_id nếu không có
            if not prompt_id:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                prompt_id = f"prompt_{timestamp}"
            
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
            
            # Thêm metadata
            result_data.update({
                "topic": topic,
                "prompt_id": prompt_id,
                "generated_at": datetime.now().isoformat(),
                "generated_by": "gemini-1.5-flash"
            })
            
            # Lưu vào file nếu được yêu cầu
            if save_to_file:
                file_path = self.save_prompt_to_file(result_data, prompt_id)
                result_data["file_path"] = file_path
                print(f"💾 Đã lưu prompt: {file_path}")
            
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
            
    def save_prompt_to_file(self, prompt_data: Dict[str, Any], prompt_id: str) -> str:
        """Lưu prompt vào file JSON với tên có thứ tự rõ ràng."""
        try:
            # Tạo tên file với format: prompt_001_topic.json
            topic_safe = prompt_data.get('topic', 'unknown')[:30]  # Giới hạn độ dài
            topic_safe = "".join(c for c in topic_safe if c.isalnum() or c in (' ', '-', '_')).strip()
            topic_safe = topic_safe.replace(' ', '_')
            
            filename = f"{prompt_id}_{topic_safe}.json"
            file_path = os.path.join(self.output_dir, filename)
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
                
            return file_path
        except Exception as e:
            raise Exception(f"Lỗi khi lưu prompt: {str(e)}")
    
    def generate_batch_prompts(self, topics: list, start_index: int = 1) -> list:
        """
        Sinh nhiều prompt từ danh sách topic và lưu thành file có thứ tự.
        
        Args:
            topics: Danh sách các chủ đề
            start_index: Số bắt đầu đánh số (mặc định: 1)
            
        Returns:
            List các prompt data với thông tin file
        """
        results = []
        
        for i, topic in enumerate(topics, start_index):
            try:
                # Tạo prompt_id có thứ tự
                prompt_id = f"prompt_{i:03d}"  # 001, 002, 003...
                
                print(f"🔮 [{i}/{len(topics) + start_index - 1}] Đang sinh prompt cho: {topic}")
                
                prompt_data = self.generate_prompt(topic, prompt_id, save_to_file=True)
                results.append(prompt_data)
                
                print(f"✅ Hoàn thành prompt {prompt_id}")
                
            except Exception as e:
                print(f"❌ Lỗi sinh prompt {i}: {e}")
                results.append({
                    "topic": topic,
                    "prompt_id": f"prompt_{i:03d}",
                    "error": str(e),
                    "status": "failed"
                })
        
        # Tạo file summary
        self._create_batch_summary(results)
        
        return results
    
    def _create_batch_summary(self, results: list):
        """Tạo file tóm tắt batch generation."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = os.path.join(self.output_dir, f"batch_summary_{timestamp}.json")
        
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_prompts": len(results),
            "successful": len([r for r in results if "error" not in r]),
            "failed": len([r for r in results if "error" in r]),
            "prompts": results
        }
        
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
            
        print(f"📊 Đã tạo file tóm tắt: {summary_file}") 