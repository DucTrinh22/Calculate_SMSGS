# utils/helpers.py
import re
from config.constants import AUTO_FIX_RULES

def normalize_basic(text: str) -> str:
    text = re.sub(r'[,.:;!?@#$%^&*()\[\]{}|\\/<>"\']', ' ', text)
    text = re.sub(r'\s+', ' ', text.strip())
    return text

def auto_fix(text: str):
    logs = []
    # Không dùng original = text ở đây mà dùng text trực tiếp
    for wrong, correct in AUTO_FIX_RULES.items():
        # Dùng re.sub với cờ IGNORECASE để thay thế mà không cần lower toàn bộ chuỗi
        if re.search(re.escape(wrong), text, re.IGNORECASE):
            # Tạo pattern không phân biệt hoa thường
            pattern = re.compile(re.escape(wrong), re.IGNORECASE)
            text = pattern.sub(correct, text)
            logs.append(f"Sửa '{wrong}' → '{correct}'")
            
    return text, logs  # Trả về text nguyên bản sau khi sửa (không .title())