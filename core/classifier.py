# core/classifier.py
from config.constants import CAU_HINH_NHOM_CUOC

def phan_loai_nhom_cuoc(cuoc):
    """
    Hàm xác định nhóm cược dựa trên Loại cược và Độ dài số đánh.
    Trả về dict config của nhóm tìm thấy hoặc None.
    """
    # Lấy độ dài của con số đầu tiên để so sánh (Ví dụ: "54" -> len 2)
    if not cuoc.so_danh:
        return None, None
        
    do_dai_so = len(cuoc.so_danh[0])
    loai_cuoc_raw = cuoc.loai_cuoc.lower()

    for ma_nhom, cfg in CAU_HINH_NHOM_CUOC.items():
        # 1. Kiểm tra xem loại cược có nằm trong danh sách match_types không
        ds_loai_match = [t.lower() for t in cfg['match_types']]
        
        if loai_cuoc_raw in ds_loai_match:
            # 2. Kiểm tra độ dài số (match_len)
            # Nếu config có quy định độ dài thì phải khớp mới nhận
            if 'match_len' in cfg:
                if do_dai_so == cfg['match_len']:
                    return ma_nhom, cfg
            else:
                # Nếu config không quy định độ dài thì nhận luôn (trường hợp hiếm)
                return ma_nhom, cfg

    return None, None