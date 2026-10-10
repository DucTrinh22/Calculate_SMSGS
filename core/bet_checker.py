# core/bet_checker.py
import itertools
import re
from config.constants import DAI_XO_SO

class BetChecker:
    def __init__(self, kqxs_data):
        # --- FIX BUG: Chuyển toàn bộ kết quả sang dạng chuỗi (String) ---
        # Để tránh lỗi "int object has no len()" hoặc "no endswith"
        self.kqxs = {}
        if kqxs_data:
            for dai, data in kqxs_data.items():
                # 1. Kiểm tra loại dữ liệu
                if isinstance(data, dict):
                    try:
                        # [QUAN TRỌNG] Sắp xếp theo Key số học (0, 1, 2, 3, 4...)
                        # Dữ liệu gốc: {"4": "ĐB", "0": "G7_1"...} -> Thứ tự lộn xộn
                        # Sau khi sort: [Key 0, Key 1, Key 2, Key 3, Key 4...]
                        sorted_items = sorted(data.items(), key=lambda x: int(x[0]))
                        
                        # Chỉ lấy giá trị (Value) để tạo thành List
                        raw_list = [item[1] for item in sorted_items]
                    except ValueError:
                        # Nếu Key không phải số, lấy values bình thường
                        raw_list = list(data.values())
                else:
                    raw_list = data
                
                # 2. Ép kiểu thành String
                # Đảm bảo số "09" không bị hiểu là int 9, giúp hàm endswith hoạt động
                self.kqxs[dai] = [str(x) for x in raw_list] 

    def get_station_result(self, dai_raw):
        """
        Tìm kết quả của MỘT đài cụ thể.
        Trả về: List số hoặc None
        """
        dai_raw = dai_raw.strip()
        # 1. Tìm trực tiếp
        if dai_raw in self.kqxs:
            return self.kqxs[dai_raw]
        
        # 2. Tìm qua config/viết tắt
        for key_config, synonyms in DAI_XO_SO.items():
            if dai_raw.lower() == key_config.lower() or dai_raw.lower() in [s.lower() for s in synonyms]:
                if key_config in self.kqxs:
                    return self.kqxs[key_config]
        return None
    
    def expand_number_list(self, so_danh_list):
        """
        Xử lý logic 'kéo':
        - 00 keo 09 -> bước nhảy 1 -> 00, 01, 02...
        - 00 keo 90 -> bước nhảy 10 -> 00, 10, 20...
        """
        ket_qua = []
        for item in so_danh_list:
            s = str(item).lower().strip()
            # Nếu phát hiện từ khóa 'keo' hoặc 'kéo'
            if 'keo' in s or 'kéo' in s:
                try:
                    parts = re.split(r'kéo|keo', s)
                    if len(parts) == 2:
                        start_str = parts[0].strip()
                        end_str = parts[1].strip()
                        start = int(start_str)
                        end = int(end_str)
                        
                        # LOGIC QUAN TRỌNG: Kiểm tra đuôi
                        # Nếu đuôi giống nhau (vd 00 - 90) -> Bước nhảy là 10
                        if start % 10 == end % 10:
                            step = 10
                        else:
                            step = 1
                            
                        # Tạo dãy số
                        current = start
                        while current <= end:
                            # Giữ nguyên định dạng số 0 ở đầu (vd: '05')
                            len_format = len(start_str) 
                            ket_qua.append(str(current).zfill(len_format))
                            current += step
                    else:
                        ket_qua.append(s)
                except:
                    ket_qua.append(s) # Lỗi thì trả về gốc
            else:
                ket_qua.append(s)
        return ket_qua

    def check_cuoc(self, cuoc):
        ds_so_chi_tiet = cuoc.so_danh
        list_dai_names = [d.strip() for d in cuoc.ten_dai.split(',')]
        
        # 2. Lấy dữ liệu xổ số
        valid_stations = {} 
        for name in list_dai_names:
            res = self.get_station_result(name)
            if res and len(res) > 0:
                valid_stations[name] = res
        
        # Nếu không có dữ liệu đài nào
        if not valid_stations:
            return {
                "status": "pending", 
                "message": f"Chưa có KQ đài {cuoc.ten_dai}", 
                "win_count": 0, 
                "winning_numbers": []
            }

        win_total = 0
        detail = []
        winning_numbers = set()

        # LOGIC DÒ TÁCH BIỆT TỪNG ĐÀI
        for station_name, results in valid_stations.items():
            # results[0] -> G8, results[-1] -> ĐB

            is_mb = 'miền bắc' in station_name.lower() or 'mb' in station_name.lower() or 'MB' in station_name.upper()
            
            # --- [QUAN TRỌNG] PHÂN LOẠI GIẢI THƯỞNG ---
            list_dau = []   # Chứa các số trúng giải ĐẦU
            list_duoi = []  # Chứa các số trúng giải ĐUÔI (ĐB)
            list_bao = results # Chứa toàn bộ giải để dò Bao Lô
            
            if is_mb:
                # === CẤU HÌNH MIỀN BẮC (Theo JSON của bạn) ===
                # Giải 7 (Đầu) nằm ở 4 vị trí đầu tiên (0, 1, 2, 3)
                if len(results) >= 4:
                    list_dau = results[0:4] 
                
                # Giải ĐB (Đuôi) nằm ở vị trí index 4 -> Lấy 2 số cuối
                if len(results) > 4:
                    giai_db = results[4] 
                    # Lấy 2 số cuối của giải ĐB để dò lô/đề
                    list_duoi = [giai_db[-2:]]
            else:
                # === CẤU HÌNH MN / MT ===
                # Giải 8 (Đầu) thường là phần tử đầu tiên
                if len(results) > 0:
                    list_dau = [results[0]]
                
                # Giải ĐB (Đuôi) là phần tử cuối cùng -> Lấy 2 số cuối
                if len(results) > 0:
                    giai_db = results[-1]
                    list_duoi = [giai_db[-2:]]
            
            # 1. BAO LÔ (18 giải)
            if cuoc.loai_cuoc in ['bao', 'blo', 'b']:
                for so in ds_so_chi_tiet:
                    hits = 0
                    for res in list_bao:
                        if len(res) >= len(so) and res.endswith(so):
                            hits += 1
                    if hits > 0:
                        win_total += hits
                        detail.append(f"Lô {so} ({station_name}: {hits} lần)")
                        winning_numbers.add(so)

            # 2. ĐẦU (G8 - Index 0)
            elif cuoc.loai_cuoc in ['dau', 'ddau']:
                for so in ds_so_chi_tiet:
                    hits = 0
                    for res in list_dau:
                        if res.endswith(so): hits += 1
                    if hits > 0:
                        win_total += hits
                        detail.append(f"Đầu {so} ({station_name}: {hits} lần)")
                        winning_numbers.add(so)

            # 3. ĐUÔI (ĐB - Index cuối)
            elif cuoc.loai_cuoc in ['duoi']:
                for so in ds_so_chi_tiet:
                    if so in list_duoi: # Đuôi thì phải trùng khớp hoàn toàn hoặc endswith đều được
                        win_total += 1
                        detail.append(f"Đuôi {so} ({station_name})")
                        winning_numbers.add(so)

            # 4. ĐẦU ĐUÔI (G8 + ĐB)
            elif cuoc.loai_cuoc in ['dd', 'dauduoi', 'đđ']:
                targets = list_dau + list_duoi
                for so in ds_so_chi_tiet:
                    hits = 0
                    for t in targets:
                        if t.endswith(so): hits += 1
                    if hits > 0:
                        win_total += hits
                        detail.append(f"Đầu Đuôi {so} ({station_name}: {hits} lần)")
                        winning_numbers.add(so)

            # 5. ĐÁ / XIÊN (Cần logic đặc biệt: Xiên có thể ghép cùng 1 đài hoặc khác đài?)
            # Thường Đá thẳng là cùng 1 đài. Đá xiên quay là nhiều đài.
            # Ở đây ta giữ logic đơn giản: Gom tất cả số trúng của mọi đài vào 1 pool rồi tính xiên.
                
            # 6. 3 CON BAO ĐẢO (3CBĐ)
            elif cuoc.loai_cuoc in [ 'baodao', 'bdao']:
                for so in ds_so_chi_tiet:
                    # Bỏ qua nếu số quá ngắn (vd đánh đảo số '1')
                    if len(so) < 2: continue 

                    # 1. Sinh hoán vị (Tự động xử lý 3 số hay 4 số)
                    # Dùng set để loại bỏ số trùng (VD: 112 đảo chỉ ra 112, 121, 211)
                    perms = set([''.join(p) for p in itertools.permutations(so)])
                    
                    hit_total_so = 0 # Tổng số lần trúng của cụm này
                    
                    # 2. Dò từng số hoán vị với bảng kết quả
                    for p_so in perms:
                        hits_p = 0
                        for res in results:
                            # Tự động kiểm tra độ dài:
                            # Nếu đánh 4 con, giải nào có 2,3 số sẽ bị bỏ qua
                            if len(res) >= len(p_so) and res.endswith(p_so):
                                hits_p += 1
                        
                        if hits_p > 0:
                            hit_total_so += hits_p
                            # Chi tiết: Ghi rõ trúng số nào (đảo) từ số gốc nào
                            detail.append(f"Đảo {p_so} (gốc {so}) ({station_name}: {hits_p} lần)")
                    
                    if hit_total_so > 0:
                        win_total += hit_total_so
                        winning_numbers.add(so)

        # --- XỬ LÝ RIÊNG CHO ĐÁ/XIÊN ---
        if cuoc.loai_cuoc in ['da', 'dax', 'daxien']:
            found_counts = {so: 0 for so in ds_so_chi_tiet}
            
            # Tìm tất cả số xuất hiện trong tất cả các đài đã chọn
            for st_name, res_list in valid_stations.items():
                for so in ds_so_chi_tiet:
                    # Đếm số lần số xuất hiện trong đài này
                    count_in_station = 0
                    for r in res_list:
                        if r.endswith(so):
                            count_in_station += 1
                    
                    # Cộng dồn vào tổng số lần xuất hiện (quan trọng cho Đá nhiều đài)
                    found_counts[so] += count_in_station

            # 2. Xét các cặp số đá
            if len(ds_so_chi_tiet) >= 2:
                pairs = list(itertools.combinations(ds_so_chi_tiet, 2))
                for p1, p2 in pairs:
                    # Lấy số lần xuất hiện
                    c1 = found_counts.get(p1, 0)
                    c2 = found_counts.get(p2, 0)
                    
                    # Điều kiện trúng: Cả 2 số đều phải xuất hiện ít nhất 1 lần
                    if c1 > 0 and c2 > 0:
                        win_total += 1
                        
                        # --- FORMAT HIỂN THỊ KẾT QUẢ ---
                        # Nếu trúng > 1 lần (nháy) thì hiển thị số lần
                        # Ví dụ: "52 (2 lần)"
                        p1_msg = f"{p1} ({c1} lần)" if c1 > 1 else p1
                        p2_msg = f"{p2} ({c2} lần)" if c2 > 1 else p2
                        
                        detail.append(f"{cuoc.ten_loai} {p1_msg} - {p2_msg}")
                        winning_numbers.add(p1)
                        winning_numbers.add(p2)

        # === XỬ LÝ XỈU CHỦ ĐẢO (XC ĐẢO) ===
        elif cuoc.loai_cuoc in ['xcdao', 'xcdaoduoi', 'xcdaodau']:
            for station_name, results in valid_stations.items(): 

                # Xác định miền (MB hay MN/MT)
                is_mb = 'miền bắc' in station_name.lower() or 'mb' in station_name.lower() or 'MB' in station_name.upper()

                xc_dau = []
                xc_duoi = []

                # --- 1. LẤY XC ĐẦU ---
                if is_mb:
                    # MB: XC Đầu là các giải có 3 chữ số (Thường là Giải 6: index 24, 25, 26)
                    xc_dau = [r for r in results if len(r) == 3]
                else:
                    # MN/MT: XC Đầu là Giải 7 (nằm ở index 1)
                    # Kiểm tra kỹ: phải có index 1 và độ dài phải là 3
                    if len(results) > 1 and len(results[1]) == 3:
                        xc_dau = [results[1]]

                # --- 2. LẤY XC ĐUÔI ---
                # Lấy giải đặc biệt (phần tử cuối cùng hoặc index 4 với MB tùy cấu trúc)
                giai_db = ""
                if is_mb:
                    # MB: Giải ĐB thường ở index 4 (trong list 27 giải chuẩn) hoặc cuối cùng
                    # Ưu tiên lấy phần tử dài nhất hoặc index 4
                    if len(results) > 4: giai_db = results[4]
                    else: giai_db = results[-1]
                else:
                    # MN/MT: Giải ĐB luôn nằm cuối cùng
                    if results: giai_db = results[-1]
                
                # Chỉ lấy 3 số cuối của giải ĐB
                if len(giai_db) >= 3:
                    xc_duoi = [giai_db[-3:]]

                # --- 3. GỘP TARGET (Xác định vùng dò) ---
                targets = []
                # Nếu chỉ đánh đuôi (xcdaoduoi)
                if 'duoi' in cuoc.loai_cuoc and 'dau' not in cuoc.loai_cuoc: 
                    targets = xc_duoi
                # Nếu chỉ đánh đầu (xcdaodau)
                elif 'dau' in cuoc.loai_cuoc and 'duoi' not in cuoc.loai_cuoc: 
                    targets = xc_dau
                # Mặc định (xcdao) là cả đầu và đuôi
                else:
                    targets = xc_duoi + xc_dau

                # --- 4. DÒ SỐ HOÁN VỊ ---
                for so in ds_so_chi_tiet:
                    if len(so) < 3: continue # XC phải từ 3 số trở lên

                    # Sinh hoán vị (VD: 906 -> 906, 960, 069, 096...)
                    perms = set([''.join(p) for p in itertools.permutations(so)])
                    
                    hit_total_so = 0 
                    
                    for p_so in perms:
                        hits_p = 0
                        for val in targets:
                            # Kiểm tra: Val phải trùng khớp hoàn toàn với số hoán vị
                            if val == p_so or val.endswith(p_so):
                                hits_p += 1
                        
                        if hits_p > 0:
                            hit_total_so += hits_p
                            detail.append(f"XC Đảo {p_so} (gốc {so}) ({station_name}: {hits_p} lần)")
                    
                    if hit_total_so > 0:
                        win_total += hit_total_so
                        winning_numbers.add(so)                   
        
        # --- XỬ LÝ XỈU CHỦ (Tách đài) ---
        elif cuoc.loai_cuoc in ['xc', 'xcdd', 'xcduoi', 'xcdau']:
             for station_name, results in valid_stations.items():
                is_mb = (station_name == 'Miền Bắc')
                targets = []

                # --- BƯỚC 1: XÁC ĐỊNH GIẢI ĐẦU & GIẢI ĐUÔI ---
                
                if is_mb:
                    # MB: XC Đuôi là 3 số cuối giải ĐB (Index 4)
                    xc_duoi = [results[4][-3:]] if len(results) > 4 and len(results[4])>=3 else []
                    # MB: XC Đầu là các giải 6 (có 3 chữ số). Thường nằm sau giải ĐB.
                    xc_dau = [r for r in results if len(r) == 3]
                else:
                    # MN: XC Đuôi (ĐB) - XC Đầu (G7)
                    xc_duoi = [results[-1][-3:]] if len(results) > 0 and len(results[-1])>=3 else []
                    xc_dau = [results[1]] if len(results) > 1 and len(results[1])==3 else []

                # Chọn list dựa theo loại cược
                if cuoc.loai_cuoc == 'xcduoi': targets.extend(xc_duoi)
                elif cuoc.loai_cuoc == 'xcdau': targets.extend(xc_dau)
                else: targets.extend(xc_duoi + xc_dau)

                # --- BƯỚC 3: DÒ SỐ ---
                for so in ds_so_chi_tiet:
                    hits_in_station = 0
                    for val in targets:
                        # Chỉ dò nếu giải có đủ 3 số trở lên
                        if len(val) >= 3 and val.endswith(so):
                            hits_in_station += 1
                    
                    if hits_in_station > 0:
                        win_total += hits_in_station
                        detail.append(f"XC {so} ({station_name}: {hits_in_station} lần)")
                        winning_numbers.add(so)

        if win_total > 0:
            return {"status": "win", "message": ", ".join(detail), "win_count": win_total, "winning_numbers": list(winning_numbers)}
        else:
            return {"status": "lose", "message": "Thua", "win_count": 0, "winning_numbers": []}
        