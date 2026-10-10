# core/models.py
from dataclasses import dataclass, asdict, field
from typing import List, Optional

@dataclass
class Cuoc:
    so_danh: List[str]
    loai_cuoc: str
    ten_loai: str
    tien: int
    tien_format: str
    ten_dai: str = ""  # Lưu tên đài cụ thể cho cược này

    def to_dict(self):
        return asdict(self)

@dataclass
class KetQuaParse:
    nguon: str
    da_sua: str
    dai: List[str]
    ten_dai: List[str]
    danh_sach_cuoc: List[Cuoc]
    tong_tien: int
    tong_tien_format: str
    hop_le: bool
    loi: Optional[str] = None

    def to_dict(self):
        return asdict(self)

@dataclass
class KetQuaSoSanh:
    tin_nhan_goc: str
    tin_nhan_sau_sua: str
    hop_le: bool
    thoi_gian: str
    
    cu_phap_khop: Optional[str] = "Auto Parse"
    ten_cu_phap: Optional[str] = "Phân tích tự động"
    do_tuong_dong: float = 0.0
    cac_loi: List[str] = field(default_factory=list)
    goi_y_sua: List[str] = field(default_factory=list)
    danh_sach_cuoc: List[Cuoc] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)