# config/constants.py

from dataclasses import dataclass
from typing import List, Dict


LOAI_CUOC = {
    'dd': {'ten': 'Đầu đuôi', 'chu_so': 2},
    'dau': {'ten': 'Đầu', 'chu_so': 2},
    'duoi': {'ten': 'Đuôi', 'chu_so': 2},
    'da': {'ten': 'Đá', 'chu_so': 2},
    'dax': {'ten': 'Đá Xiên', 'chu_so': 2},
    'daxien': {'ten': 'Đá Xiên', 'chu_so': 2},
    'bao': {'ten': 'Bao', 'chu_so': [2,3,4]},
    'xc': {'ten': 'Xỉu chủ', 'chu_so': 3},
    'xcdau': {'ten': 'Xỉu chủ đầu', 'chu_so': 3},
    'xcduoi': {'ten': 'Xỉu chủ đuôi', 'chu_so': 3},
    'xcdao': {'ten': 'Xỉu đảo', 'chu_so': 3},
    'xcdaoduoi': {'ten': 'Xỉu đảo đuôi', 'chu_so': 3},
    'xcdaodau': {'ten': 'Xỉu đảo đầu', 'chu_so': 3},
    'bdao': {'ten': 'Bao đảo', 'chu_so': [3,4]},
}

DAI_XO_SO = {
    # XSMN
    "Tp.Hcm": {"TP", "tp", "tphcm"}, 
    "Đồng Tháp": {"ĐT", "dt", "DThap", "dthap", "dongthap", "dong thap"}, 
    "Cà Mau": {"CM", "cm", "CMau", "cmau", "ca mau"},
    "Bến Tre": {"BT", "bt", "btr", "btre", "bentre", "ben tre"}, 
    "Vũng Tàu": {"VT", "vt", "vungtau", "vung tau", "vtau"}, 
    "Bạc Liêu": {"BLieu", "blieu", "baclieu", "bac lieu", "blu"},
    "Đồng Nai": {"ĐN", "dn", "dongnai", "dong nai", "dnai"}, 
    "Cần Thơ": {"CT", "ct", "cantho", "can tho", "ctho"}, 
    "Sóc Trăng": {"ST", "st", "soctrang", "soc trang", "strang"},  
    "Tây Ninh": {"TN", "tn", "tayninh", "tay ninh", "tninh"}, 
    "An Giang": {"AG", "ag", "angiang", "an giang", "agiang"}, 
    "Bình Thuận": {"BTh", "bth", "binhthuan", "binh thuan", "bthuan"},
    "Vĩnh Long": {"VL", "vl", "vinhlong", "vinh long", "vlong"}, 
    "Bình Dương": {"BD", "bduong", "bdg", "binhduong", "binh duong"}, 
    "Long An": {"LA", "la", "longan", "long an", "lan"}, 
    "Trà Vinh": {"TV", "tv", "travinh", "tra vinh", "tvinh"},
    "Bình Phước": {"BP", "bp", "binhphuoc", "binh phuoc", "bphuoc"}, 
    "Hậu Giang": {"HG", "hg", "haugiang", "hau giang", "hgiang"}, 
    "Tiền Giang": {"TG", "tg", "tiengiang", "tien giang", "tgiang"}, 
    "Kiên Giang": {"KG", "kg", "kiengiang", "kien giang", "kgiang"},
    "Đà Lạt": {"DL", "dlat", "dalat", "da lat", "đà lạt", "dl"},
    
    # XSMT
    "Phú Yên": {"PY", "py", "PYen", "pyen", "phuyen", "phu yen"},
    "Huế": {"hue", "Hue", "tth", "thuatienhue", "thua tien hue"},
    "Đắk Lắk": {"DLK", "dlk", "daklak", "dak lak"},
    "Quảng Nam": {"QN", "qn", "QNam", "qnam", "quangnam", "quang nam"},
    "Đà Nẵng": {"DNang", "dnang", "da nang", "danang", "dng"},
    "Khánh Hòa": {"KH", "kh", "KHoa", "khoa", "khanhhoa", "khanh hoa"},
    "Quảng Bình": {"QB", "qb", "QBinh", "qbinh", "quangbinh", "quang binh"},
    "Bình Định": {"BĐ", "bdinh", "BĐinh", "bđinh", "binhdinh", "binh dinh", "bdh"},
    "Quảng Trị": {"QTri", "qt","qtri", "QT", "quangtri", "quang tri"},
    "Gia Lai": {"GLai", "gl", "GL", "glai", "gialai", "gia lai"},
    "Ninh Thuận": {"NT", "nt", "nthuan", "ninhthuan", "ninh thuan", "nth"},
    "Quảng Ngãi": {"QNg", "qng", "quangngai", "quang ngai", "qngai"},
    "Đắk Nông": {"DNong", "dnong", "daknong", "dak nong", "dkn"},
    "Kon Tum": {"KTum", "ktum", "kontum", "kon tum", "ktm"},

    # Đài gộp
    "2 Đài MN": {"2dmn", "2d mn", "2dai", "2DMN" },
    "2 Đài MT": {"2dmt", "2d mt", "2DMT"},
    "3 Đài MN": {"3dmn", "3d mn", "3dai", "3DMN"},
    "3 Đài MT": {"3dmt", "3d mt", "3DMT"},
    "4 Đài MN": {"4dmn", "4d mn", "4dai", "4DMN"},
    
    # XSMB
    "Miền Bắc": {"MB", "mb", "Mb"},
}

LICH_QUAY_SO = {
    "MN": {
        0: ["Tp.Hcm", "Đồng Tháp", "Cà Mau"],           # Thứ 2
        1: ["Bến Tre", "Vũng Tàu", "Bạc Liêu"],          # Thứ 3
        2: ["Đồng Nai", "Cần Thơ", "Sóc Trăng"],         # Thứ 4
        3: ["Tây Ninh", "An Giang", "Bình Thuận"],       # Thứ 5
        4: ["Vĩnh Long", "Bình Dương", "Trà Vinh"],      # Thứ 6
        5: ["Tp.Hcm", "Long An", "Bình Phước", "Hậu Giang"], # Thứ 7
        6: ["Tiền Giang", "Kiên Giang", "Đà Lạt"]        # Chủ Nhật
    },
    "MT": {
        0: ["Phú Yên", "Huế"],                           # Thứ 2
        1: ["Đắk Lắk", "Quảng Nam"],                     # Thứ 3
        2: ["Đà Nẵng", "Khánh Hòa"],                     # Thứ 4
        3: ["Bình Định", "Quảng Trị", "Quảng Bình"],     # Thứ 5
        4: ["Gia Lai", "Ninh Thuận"],                    # Thứ 6
        5: ["Đà Nẵng", "Quảng Ngãi", "Đắk Nông"],        # Thứ 7
        6: ["Kon Tum", "Khánh Hòa", "Huế"]                 # Chủ Nhật (Lưu ý check lại lịch MT tùy vùng)
    }
}

TIEN_TE = {
    'n': 1000, 'ng': 1000, 'ngan': 1000,
    'k': 1000, 
    'd': 1000, 'đ': 1000, 'vnd': 1,
    'tr': 1000000, 'trieu': 1000000
}

# Quy tắc sửa lỗi & mapping từ viết tắt
AUTO_FIX_RULES = {
    # Loại cược viết tắt
    # - xỉu chủ - xỉu chủ đảo - xỉu chủ đầu - xỉu chủ đuôi
    'xd': 'xcdao', 'xc dao': 'xcdao', 'xdao': 'xcdao',
    'xđ': 'xcdao', 'xc đ': 'xcdao',
    'x': 'xc', 'xe': 'xc',
    'xcd': 'xcdao', 'xc d': 'xcdao',
    'xcdui': 'xcduoi', 'xc dui': 'xcduoi',
    # --- xỉu đảo đầu - xỉu đảo đuôi ---
    'xdaoduoi': 'xcdaoduoi', 
    'xc dao duoi': 'xcdaoduoi',
    'x dao duoi': 'xcdaoduoi',
    'xdaodau': 'xcdaodau',
    'xc dao dau': 'xcdaodau',
    'x dao dau': 'xcdaodau',
    # - Bao - Bao đảo -
    'b': 'bao',
    'bl': 'bao',
    'blo': 'bao',
    'bđao': 'bdao',
    'bđ': 'bdao',
    # - đầu đuôi - đá
    'ddau': 'dd', 'đđ': 'dd', 'dđ': 'dd', 'đd': 'dd',
    'daa': 'da', 'đa': 'da', "đã": 'da', 'đá': 'da',
    'đau': 'dau', 'dui': 'duoi',
     
    
    # Sửa lỗi chính tả đài phổ biến
    'tp hcm': 'tp',
}



# --- CẤU HÌNH NHÓM HIỂN THỊ VÀ TỶ LỆ ---
# ty_le_an: 1 ăn bao nhiêu
# ti_le_xac: Hệ số nhân tiền xác (Ví dụ: 0.8 là 100k chỉ tính 80k)
# Đối với Khách

CAU_HINH_NHOM_CUOC = {
    '2CB': {
        'ten': '2 Con Bao',
        'match_types': ['bao', 'blo', 'b', 'bl'], 
        'match_len': 2,
        'ty_le_an': 80,    # Ví dụ: 1 ăn 80k
        'ti_le_xac': 0.8  # Ví dụ: Cò 20% (nhân 0.8)
    },
    '3CB': {
        'ten': '3 Con Bao',
        'match_types': ['bao', 'blo', 'b', 'bl'],
        'match_len': 3,
        'ty_le_an': 80,
        'ti_le_xac': 0.8
    },
    '4CB': {
        'ten': '4 Con Bao',
        'match_types': ['bao', 'blo', 'b', 'bl'],
        'match_len': 4,
        'ty_le_an': 80,
        'ti_le_xac': 0.8
    },
    'ĐáT': {
        'ten': 'Đá Thẳng',
        'match_types': ['da', 'daa'],
        'match_len': 2,
        'ty_le_an': 80,
        'ti_le_xac': 0.8
    },
    'ĐáX': {
        'ten': 'Đá Xiên 1 Đài',
        'match_types': ['dax', 'daxien'],
        'match_len': 2,
        'ty_le_an': 80,
        'ti_le_xac': 0.8
    },
    '3CXC': {
        'ten': '3 Con Xỉu Chủ',
        'match_types': ['xc', 'xcduoi', 'xcdau', 'x', 'xe'],
        'match_len': 3,
        'ty_le_an': 80,
        'ti_le_xac': 0.8
    },
    '3CXĐ': {
        'ten': '3 Con Xỉu Đảo',
        'match_types': ['xcdao', 'xd', 'xcd', 'xc dao', 'xcdaoduoi', 'xcdaodau'],
        'match_len': 3,
        'ty_le_an': 80,   
        'ti_le_xac': 0.8
    },
    '3CBĐ': {
        'ten': '3 Con Bao Đảo',
        'match_types': ['bd', 'bdao', 'bđ'],
        'match_len': 3,
        'ty_le_an': 80,
        'ti_le_xac': 0.8
    },
    '4CBĐ': {
        'ten': '4 Con Bao Đảo',
        'match_types': ['bd', 'bdao', 'bđ'],
        'match_len': 4,
        'ty_le_an': 80,
        'ti_le_xac': 0.8
    },
    
}