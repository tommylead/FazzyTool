"""
Module xử lý việc đọc prompt từ các định dạng file khác nhau.
Hỗ trợ: .txt, .json, .docx
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from docx import Document


class PromptLoader:
    """Lớp xử lý việc đọc prompt từ nhiều định dạng file khác nhau."""

    @staticmethod
    def load_from_text(file_path: str) -> str:
        """Đọc prompt từ file văn bản (.txt)."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()
            return content
        except Exception as e:
            raise Exception(f"Lỗi khi đọc file text: {str(e)}")

    @staticmethod
    def load_from_json(file_path: str) -> Dict[str, Any]:
        """Đọc prompt từ file JSON (.json)."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            # Kiểm tra xem JSON có đúng định dạng không
            required_keys = ["image_prompt", "video_prompt", "video_duration", "video_ratio"]
            for key in required_keys:
                if key not in data:
                    raise ValueError(f"Thiếu trường '{key}' trong file JSON")
            
            return data
        except json.JSONDecodeError:
            raise Exception("File JSON không hợp lệ")
        except Exception as e:
            raise Exception(f"Lỗi khi đọc file JSON: {str(e)}")

    @staticmethod
    def load_from_docx(file_path: str) -> str:
        """Đọc prompt từ file Word (.docx)."""
        try:
            doc = Document(file_path)
            content = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return content.strip()
        except Exception as e:
            raise Exception(f"Lỗi khi đọc file DOCX: {str(e)}")

    @classmethod
    def load_prompt(cls, file_path: str) -> Dict[str, Any]:
        """
        Đọc prompt từ file và chuyển đổi thành định dạng phù hợp.
        Đầu vào có thể là .txt, .json hoặc .docx
        Đầu ra luôn là dict chứa các thông tin cần thiết.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == ".json":
            return cls.load_from_json(file_path)
        elif file_ext == ".txt":
            prompt_text = cls.load_from_text(file_path)
            # Trả về định dạng mặc định với cùng nội dung cho cả image và video
            return {
                "image_prompt": prompt_text,
                "video_prompt": prompt_text,
                "video_duration": "5s",
                "video_ratio": "1:1"
            }
        elif file_ext == ".docx":
            prompt_text = cls.load_from_docx(file_path)
            # Trả về định dạng mặc định với cùng nội dung cho cả image và video
            return {
                "image_prompt": prompt_text,
                "video_prompt": prompt_text,
                "video_duration": "5s",
                "video_ratio": "1:1"
            }
        else:
            raise ValueError(f"Không hỗ trợ định dạng file: {file_ext}") 