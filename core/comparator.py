# core/comparator.py
import re
from datetime import datetime
from difflib import SequenceMatcher
from core.models import KetQuaSoSanh
from core.parser import SMSParser

class SMSComparator:
    def __init__(self):
        self.parser = SMSParser()

    def compare(self, tin_nhan: str) -> KetQuaSoSanh:
        ket_qua_parse = self.parser.parse(tin_nhan)
        thoi_gian = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not ket_qua_parse.hop_le:
            return KetQuaSoSanh(
                tin_nhan_goc=tin_nhan,
                tin_nhan_sau_sua=ket_qua_parse.da_sua,
                hop_le=False,
                cac_loi=[ket_qua_parse.loi] if ket_qua_parse.loi else ["Không tìm thấy cược hợp lệ"],
                thoi_gian=thoi_gian
            )

        # --- THAY ĐỔI Ở ĐÂY ---
        # Trước đây: tin_nhan_chuan = self._reconstruct_message(ket_qua_parse)
        # Bây giờ: Lấy trực tiếp chuỗi đã normalize từ parser để giữ nguyên dạng raw
        tin_nhan_chuan = ket_qua_parse.da_sua
        # ----------------------

        similarity = SequenceMatcher(None, tin_nhan, tin_nhan_chuan).ratio()

        return KetQuaSoSanh(
            tin_nhan_goc=tin_nhan,
            tin_nhan_sau_sua=tin_nhan_chuan,
            hop_le=True,
            danh_sach_cuoc=ket_qua_parse.danh_sach_cuoc,
            do_tuong_dong=similarity,
            thoi_gian=thoi_gian
        )

"""     # Hàm này không còn dùng để tạo output chính nữa, 
    # nhưng có thể giữ lại nếu sau này muốn debug hiển thị đẹp
    def _reconstruct_message(self, kq) -> str:
        lines = []
        for c in kq.danh_sach_cuoc:
            so_str = " ".join(c.so_danh)
            line = f"[{c.ten_dai}] {so_str} {c.loai_cuoc} {c.tien_format}"
            lines.append(line)
        return " | ".join(lines) """