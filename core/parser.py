# core/parser.py
import re
from typing import List, Tuple, Sequence
from config.constants import LOAI_CUOC, DAI_XO_SO, TIEN_TE, AUTO_FIX_RULES, LICH_QUAY_SO
from core.models import Cuoc, KetQuaParse
from datetime import datetime

class SMSParser:

    def __init__(self):
        # Biến này giúp nhớ tên đài của dòng trước đó
        self.last_dai_found = []

    # --- 1. THÊM HÀM CHECK ĐÀI ---
    def _is_dai_token(self, token: str) -> bool:
        """Kiểm tra token có nằm trong danh sách tên đài không (bao gồm cả bd)"""
        t = token.lower().strip('.,-/ ')

        # Check nhanh các đài trong config
        for shorts in DAI_XO_SO.values():
            if t in [s.lower() for s in shorts]:
                return True
        return False
    
    def _resolve_dai_gop(self, token: str, date_obj=None) -> List[str]:
        """
        Bung đài gộp thành danh sách đài lẻ dựa theo ngày.
        Ví dụ: Thứ 2, token='2dmn' -> Trả về ['Tp.Hcm', 'Đồng Tháp']
        """
        t = token.lower()
        
        # Kiểm tra xem có phải đài gộp không
        mn_match = re.match(r'^(\d)(dmn|dai|d)$', t) # 2dmn, 3dmn
        mt_match = re.match(r'^(\d)(dmt|d)$', t) # 2dmt, 3dmt
        
        # Xác định vùng và số lượng đài cần lấy
        # Dùng if/elif/else để type-checker thu hẹp kiểu (mn_match/mt_match không còn None khi gọi .group)
        if mn_match:
            region = "MN"
            count = int(mn_match.group(1))
        elif mt_match:
            region = "MT"
            count = int(mt_match.group(1))
        else:
            return [token] # Không phải đài gộp, trả về nguyên gốc
        
        # Xác định thứ trong tuần (0=Mon, 6=Sun)
        if date_obj is None:
            date_obj = datetime.now()
        weekday = date_obj.weekday()
        
        # Lấy danh sách đài theo lịch
        try:
            todays_stations = LICH_QUAY_SO[region].get(weekday, [])
            
            # Nếu yêu cầu nhiều hơn thực tế (VD: Thứ 2 có 3 đài mà đòi 4dmn) -> Lấy max
            real_count = min(count, len(todays_stations))
            
            if real_count <= 0:
                return [token]
                
            # Lấy n đài đầu tiên
            return todays_stations[:real_count]
            
        except Exception:
            return [token]
        
    # --- 2. CẬP NHẬT LOGIC VALIDATE THEO YÊU CẦU ---
    def _validate_logic(self, loai_key: str, nums: List[str], current_dai: List[str]) -> Tuple[bool, str]:
        """
        Trả về: (Hợp lệ hay không, Lý do lỗi)
        """
        # 1. Kiểm tra trùng số áp dụng cho Đá thường và Đá xiên
        cac_loai_cam_trung = ['da', 'daa', 'dax', 'daxien', 'daX']
    
        if loai_key in cac_loai_cam_trung:
            if len(nums) != len(set(nums)):
                list_co_dau = [f"'{n}'" for n in nums] 
                return False, f"Cược '{loai_key}' không được có số trùng nhau (số: {', '.join(list_co_dau)})"
        
        # Xác định đài MB (Vì MB có luật riêng)
        is_mb = False
        for d in current_dai:
            # Map tên ngắn về tên đầy đủ để check
            if self._map_dai(d) == "Miền Bắc":
                is_mb = True
                break
        
        # 1. Map tên đài ra tên đầy đủ để kiểm tra
        full_names = [self._map_dai(d) for d in current_dai]
    
        # 2. Kiểm tra xem có phải là đài gộp không (2d, 3d)
        is_dai_gop = any(("2 Đài" in name or "3 Đài" or "4 Đài" in name) for name in full_names)
        
        so_luong_dai = len(current_dai)
        
        # --- RULE 0: KIỂM TRA ĐỘ DÀI SỐ CHO ĐÁ (QUAN TRỌNG) ---
        # Bất kể là 'da' hay 'dax', số bắt buộc phải là 2 chữ số
        if loai_key in ['da', 'daa', 'daX', 'dax', 'daxien']:
            for n in nums:
                if len(n) != 2:
                    return False, f"Cược '{loai_key}' CHỈ nhận số 2 chữ số. Bạn đang đánh số '{n}' ({len(n)} chữ số)."

        # --- RULE 1: ĐÁ (da) - Thường là đá chéo 2 đài hoặc đá vòng MB ---
        if loai_key in ['da', 'daa']:
            if len(nums) < 2:
                return False, f"Cược ĐÁ cần ít nhất 2 con số (Bạn nhập {len(nums)} số)."
            if len(nums) > 6:
                return False, f"Cược ĐÁ tối đa chỉ 6 con số (Bạn nhập {len(nums)} số)."
            
            # Logic đài cho Đá thường
            if is_mb or is_dai_gop:
                pass # MB đá 1 đài hoặc 2d/3d thì 1 tên đài vẫn chấp nhận đá
            else:
                # MN/MT đá chéo cần ít nhất 2 đài
                if so_luong_dai < 1: 
                     return False, f"Cược ĐÁ cần có đài."

        # --- RULE 2: ĐÁ XIÊN (dax) - Đá các số trong cùng 1 đài ---
        elif loai_key in ['daX', 'dax', 'daxien']:
            if is_mb:
                # MB không phân biệt dax, dùng da là được. Nhưng nếu khách quen dùng dax thì có thể châm chước (return True)
                # Ở đây ta chặn để chuẩn cú pháp:
                return False, "Đài Miền Bắc (MB) chỉ dùng 'da' (đá vòng), không dùng 'dax'."
            
            # Đá xiên bắt buộc chỉ 1 đài
            if so_luong_dai != 1:
                return False, f"Đá Xiên (dax) chỉ áp dụng cho DUY NHẤT 1 đài. Bạn đang chọn {so_luong_dai} đài ({', '.join(current_dai)})."
            
            if len(nums) < 2:
                return False, f"Đá Xiên cần ít nhất 2 con số."
            if len(nums) > 6:
                return False, f"Đá Xiên tối đa 6 con số."

        # --- RULE 3: CÁC LOẠI 3, 4 SỐ (XC, BAO ĐẢO...) ---
        elif loai_key in ['xc', 'xcdao', 'xcdau', 'xcduoi', 'xcdaoduoi', 'xcdaodau', 'xd', 'bd', 'bdao', 'bao', 'blo', 'dd', 'dau', 'duoi']:
            
            # 1. Xác định độ dài yêu cầu
            yeu_cau_do_dai = []
            if loai_key in LOAI_CUOC:
                cfg = LOAI_CUOC[loai_key]['chu_so']
                if isinstance(cfg, int): yeu_cau_do_dai = [cfg]
                else: yeu_cau_do_dai = cfg
            elif loai_key in ['bd', 'bdao']: 
                yeu_cau_do_dai = [3, 4]
            elif loai_key in ['xc', 'xcdao', 'xcdau', 'xcduoi', 'xcdaoduoi', 'xcdaodau', 'xd']:
                yeu_cau_do_dai = [3]

            # 2. Kiểm tra từng số
            for n in nums:
                if yeu_cau_do_dai and len(n) not in yeu_cau_do_dai:
                    return False, f"Loại cược '{loai_key}' yêu cầu số có {yeu_cau_do_dai} chữ số (Số '{n}' có {len(n)} chữ số)."
                
                check_dao = 'dao' in loai_key or loai_key in ['bd', 'bdao']
                if check_dao:
                    if len(set(n)) == 1: 
                        return False, f"Số '{n}' có các chữ số giống nhau nên không thể đánh Đảo."

        # Nếu chạy hết các if mà không return False -> Hợp lệ
        return True, ""

    def parse(self, text: str, ngay_chay=None) -> KetQuaParse:
        # Nếu không truyền ngày, mặc định là hôm nay
        if ngay_chay is None:
            ngay_chay = datetime.now()
        # 1. Làm sạch cơ bản
        text_clean = self._normalize_text(text)

        # --- 2. LOGIC KIỂM TRA BẮT BUỘC ĐẦU CÂU PHẢI LÀ ĐÀI ---
        # Lấy từ đầu tiên để kiểm tra trước khi xử lý sâu
        first_token = text_clean.split()[0] if text_clean else ""
        
        if not first_token:
             return KetQuaParse(
                nguon=text, da_sua="", dai=[], ten_dai=[], 
                danh_sach_cuoc=[], tong_tien=0, tong_tien_format="0đ", 
                hop_le=False, loi="Tin nhắn rỗng"
            )
        
        # - Nếu token đầu KHÔNG phải đài VÀ KHÔNG có đài cũ -> Mới báo lỗi
        # Nếu đã có đài cũ (self.last_dai_found) thì cho qua để xử lý tiếp
        if not self._is_dai_token(first_token) and not self.last_dai_found:
             return KetQuaParse(
                nguon=text, da_sua=text_clean, dai=[], ten_dai=[], 
                danh_sach_cuoc=[], tong_tien=0, tong_tien_format="0đ", 
                hop_le=False, loi=f"Thiếu Tên Đài (Lỗi tại: '{first_token}')"
            )
        
        # 3. Sửa tiền thông minh (thêm n, sửa 05 -> 0.5)
        text_smart = self._smart_fix_money(text_clean)

        # 4. Xử lý tách dấu chấm cho số thường (55.42 -> 55 42)
        # nhưng GIỮ NGUYÊN cho tiền (0.5n -> 0.5n)
        tokens = text_smart.split()
        final_tokens = []
        for token in tokens:
            # Nếu có dấu chấm mà KHÔNG phải là tiền (không có đuôi n/k/đ...) -> Tách ra
            if '.' in token and not self._is_money_token(token):
                final_tokens.append(token.replace('.', ' '))
            else:
                final_tokens.append(token)
        
        # Ghép lại thành chuỗi hiển thị cuối cùng
        text_final = " ".join(final_tokens)
        
        try:
            # 5. Parse từ chuỗi đã xử lý hoàn chỉnh
            # str(text_final): " ".join(...) bị Pyright suy luận thành LiteralString,
            # khiến .split() trả về list[LiteralString] (không gán được vào List[str] vì list là invariant)
            final_token_list: List[str] = str(text_final).split()
            all_dai_found, cuoc_list = self._parse_tokens(final_token_list, ngay_chay)
            
            unique_dai = list(set([c.ten_dai for c in cuoc_list]))
            tong_tien = sum(c.tien for c in cuoc_list)

            is_ok = True if cuoc_list else False
            return KetQuaParse(
                nguon=text,
                da_sua=text_final,
                dai=all_dai_found,
                ten_dai=unique_dai,
                danh_sach_cuoc=cuoc_list,
                tong_tien=tong_tien,
                tong_tien_format=f"{tong_tien:,}đ".replace(",", "."),
                hop_le=is_ok,
                loi=None if is_ok else "Chỉ có tên Đài thiếu thông tin Số/Tiền/Loại cược."
            )
        except Exception as e:
            return KetQuaParse(
                nguon=text, da_sua=text_final, dai=[], ten_dai=[], 
                danh_sach_cuoc=[], tong_tien=0, tong_tien_format="0đ", 
                hop_le=False, loi=str(e)
            )

    def _normalize_text(self, text: str) -> str:
        """Tách rời mọi thứ dính liền, sau đó ghép lại"""
        t = text.replace('\n', ' ').replace('\r', ' ') 
        t = text.lower()
        

        # --- LOGIC KÉO SỐ (THÊM MỚI) ---
        # Mục đích: Biến "00 kéo 05" thành "00 01 02 03 04 05"
        def expand_range(match):
            start_str = match.group(1)
            end_str = match.group(2)
            try:
                start = int(start_str)
                end = int(end_str)
                
                # Nếu nhập ngược "09 kéo 00" -> tự đảo lại
                if start > end:
                    start, end = end, start
                
                # [MỚI] LOGIC XÁC ĐỊNH BƯỚC NHẢY (STEP)
                # Nếu cùng đuôi (00-90, 15-45) -> Bước nhảy 10
                if start % 10 == end % 10:
                    step = 10
                else:
                    step = 1

                # Giới hạn số lượng (chống spam)
                # Vì có step 10 nên ta nới lỏng giới hạn check khoảng cách một chút nếu cần,
                # nhưng giữ logic cũ > 100 số thì bỏ qua là an toàn.
                if (end - start) // step > 100:
                    return match.group(0) 

                # Xác định độ dài định dạng
                fmt_len = max(len(start_str), len(end_str))
                
                # Tạo danh sách số
                expanded = []
                # [MỚI] Thêm tham số step vào range
                for i in range(start, end + 1, step):
                    # Format thêm số 0 đằng trước
                    expanded.append(f"{i:0{fmt_len}d}")
                
                return " ".join(expanded)
            except Exception:
                return match.group(0)

        # Regex tìm: Số + (khoảng trắng tùy ý) + "kéo" hoặc "keo" + (khoảng trắng tùy ý) + Số
        # Ví dụ khớp: "00kéo09", "00 keo 09", "00 keo 10"
        regex_keo = r'(\d+)[\s\.\-,_]*(?:kéo|keo|kèo)[\s\.\-,_]*(\d+)'
        t = re.sub(regex_keo, expand_range, t)
        
        merge_map = []
        for shorts in DAI_XO_SO.values():
            # 1. Tìm phiên bản đích (liền mạch): ưu tiên từ không có dấu cách
            # Ví dụ: trong {"DL", "dalat", "da lat"} -> chọn "dalat" hoặc "dl"
            # Ta ưu tiên chọn cái dài hơn một chút để dễ đọc (dalat) thay vì (dl) nếu muốn, 
            # hoặc đơn giản là lấy cái đầu tiên không có dấu cách.
            
            target_token = None
            # Tìm từ không có space (vd: dalat)
            candidates = [s.lower() for s in shorts if ' ' not in s]
            if candidates:
                # Ưu tiên lấy từ dài (vd: dalat) để rõ nghĩa hơn từ tắt (dl), hoặc ngược lại tùy bạn.
                # Ở đây mình lấy từ dài nhất không có dấu cách để giống yêu cầu 'dalat' của bạn
                target_token = max(candidates, key=len) 
            
            if target_token:
                # 2. Tìm các từ có dấu cách để thay thế (vd: "da lat", "đà lạt")
                space_vars = [s.lower() for s in shorts if ' ' in s]
                for sv in space_vars:
                    merge_map.append((sv, target_token))
        
        # 3. Sắp xếp thay thế từ dài trước (để tránh lỗi substring, vd: thay "bà rịa vũng tàu" trước "vũng tàu")
        merge_map.sort(key=lambda x: len(x[0]), reverse=True)
        
        # 4. Thực hiện replace
        for original, replacement in merge_map:
            if original in t:
                t = t.replace(original, replacement)

        # Làm sạch phía sau tên đài để tránh dính vào số (ví dụ: "đà lạt11" -> "dalat 11")
        t = re.sub(r'([a-zđ]+)\.', r'\1 ', t)        
        
        # 1. Đổi dấu phẩy thành dấu chấm nếu nằm giữa 2 số (5,5 -> 5.5)
        # Regex: (Số)(,)(Số) -> \1.\2
        t = re.sub(r'(?<=\d),(?=\d)', '.', t)
        
        # Tách số và lệnh cược bị dính bởi ký tự lạ (.-/)
        # Ví dụ: "013.435.xc12" -> "013.435 xc12" (Sau đó dấu chấm giữa số sẽ tự tách ở bước sau)
        # Giữ nguyên tiền: "1.5n" vẫn là "1.5n" do loại trừ n,k,d...
        t = re.sub(r'(\d)[\.\-\/_]+(?!(?:n|k|d|đ|tr|ng|ngan)\b)([a-zđ]+)', r'\1 \2', t)

        # 2. Biến mọi ký tự ngăn cách thành khoảng trắng (bao gồm cả dấu chấm giữa các số)
        # Lưu ý: Với lô đề, số thập phân ít dùng cho số đánh (chỉ dùng cho tiền 1.5tr)
        t = re.sub(r'[-/+,|:]', ' ', t)

        
        # 3. Tách Chữ và Số dính liền (da20k -> da 20 k, x6b1 -> x 6 b 1)
        t = re.sub(r'([^\d\s.]+)(\d)', r'\1 \2', t) # Chữ trước Số
        t = re.sub(r'(\d)(?!(?:n|k|d|đ|tr|ng|ngan)\b)([^\d\s.]+)', r'\1 \2', t) # Số trước Chữ

        # Lúc này: "da20k" -> "da 20 k". "1.5n" -> "1 5 n" (do xóa dấu chấm ở b1)
        # Tuy nhiên, ta cần xử lý lại đơn vị tiền tệ để nó dính vào số cho dễ parse
        # Hoặc ta để tách rời và hàm parse sẽ tự nhận diện token 'n', 'k' đứng sau số.
        # Ở đây tôi chọn cách: Gắn lại các đơn vị tiền tệ phổ biến (n, k, d, tr) vào số đứng trước
        
        # Logic: Quét danh sách đài, nếu đài nào bắt đầu bằng số -> tìm phiên bản bị tách và ghép lại.
        for shorts in DAI_XO_SO.values():
            for s in shorts:
                s_lower = s.lower()
                # Kiểm tra nếu tên đài bắt đầu bằng số (ví dụ: 2dmn, 3dmt) và có độ dài > 1
                if len(s_lower) > 1 and s_lower[0].isdigit():
                    # Tạo pattern: Tìm Số + Space + Phần_Chữ_Còn_Lại (ví dụ: "2" + " " + "dmn")
                    # s_lower[0] là số, s_lower[1:] là phần chữ
                    part_num = s_lower[0]
                    part_text = s_lower[1:]
                    
                    # Regex tìm: "2 dmn"
                    pattern = r'\b' + re.escape(part_num) + r'\s+' + re.escape(part_text) + r'\b'
                    
                    # Thay thế "2 dmn" -> "2dmn"
                    t = re.sub(pattern, s_lower, t)
                    
        # Regex: Tìm Số + Space + (n/k/d/tr...) -> Gộp lại
        t = re.sub(r'(\d+)\s+([nkd]|tr|ng)(?=\s|$)', r'\1\2', t)
        
        # 4. Áp dụng Auto Fix (sửa lỗi chính tả, map từ viết tắt)
        # Sort key dài trước để tránh replace nhầm (ví dụ 'x' vs 'xc')
        sorted_rules = sorted(AUTO_FIX_RULES.keys(), key=len, reverse=True)
        for key in sorted_rules:
            # Chỉ replace khi từ đó đứng độc lập (có space bao quanh) để an toàn
            # Vì ta đã tách space ở bước 2 nên logic này hoạt động tốt
            pattern = r'(?<!\w)' + re.escape(key) + r'(?!\w)'
            if re.search(pattern, t):
                t = re.sub(pattern, AUTO_FIX_RULES[key], t)
                
        # 5. Dọn dẹp khoảng trắng dư thừa
        t = re.sub(r'\s+', ' ', t).strip()
        
        return t


    def _smart_fix_money(self, text: str) -> str:
        tokens = text.split()
        new_tokens = []
        
        # Tạo danh sách keyword chuẩn
        base_bet_keywords = list(LOAI_CUOC.keys()) + ['blo', 'b', 'x', 'da', 'dá', 'bao', 'dd', 'dau', 'duoi', 'bdao']
        if 'bd' in base_bet_keywords: base_bet_keywords.remove('bd')

        i = 0
        while i < len(tokens):
            token = tokens[i]
            token_lower = token.lower()
            
            # [BƯỚC 1: QUAN TRỌNG] Ép buộc Map từ khóa (ví dụ: đđ -> dd, b -> bao)
            # Dù bước normalize có sót thì bước này sẽ bắt lại
            mapped_token = token_lower
            if token_lower in AUTO_FIX_RULES:
                mapped_token = AUTO_FIX_RULES[token_lower]
            
            is_bet_keyword = False
            
            # Kiểm tra xem từ ĐÃ SỬA (mapped_token) có phải là lệnh cược không
            if mapped_token in base_bet_keywords:
                is_bet_keyword = True

            

            # [BƯỚC 2] Lưu token vào danh sách kết quả
            if is_bet_keyword:
                if mapped_token == 'bd':
                    new_tokens.append('bdao')
                else:
                    # Lưu từ đã sửa (đđ -> dd) để các bước sau hiểu
                    new_tokens.append(mapped_token)
            else:
                new_tokens.append(token)

            # [BƯỚC 3: XỬ LÝ TIỀN]
            # Nếu đã xác định là cược -> Bắt buộc xử lý token tiếp theo thành tiền
            if is_bet_keyword and i + 1 < len(tokens):
                next_t = tokens[i+1]
                
                # Regex bắt: Số (nguyên/thập phân) + Đuôi (có thể rỗng)
                # Ví dụ: "20", "20n", "0.5", "10b"
                m = re.match(r'^(\d+(\.\d+)?)([a-zđ]*)$', next_t)
                
                if m:
                    val_str = m.group(1) 
                    unit = m.group(3)
                    
                    # --- BẮT BUỘC: Nếu không có đơn vị (unit rỗng) -> Thêm 'n' ---
                    if not unit:
                        unit = 'n'
                    
                    # Chuẩn hóa các đuôi khác về n
                    if unit in ['k', 'ng', 'ngan']:
                        unit = 'n'
                        
                    # Sửa lỗi 05 -> 0.5 (nếu cần)
                    if val_str.startswith('0') and len(val_str) > 1 and '.' not in val_str:
                        val_str = val_str[0] + '.' + val_str[1:]
                    
                    # Ghép lại thành tiền chuẩn (vd: 20 -> 20n)
                    fixed_money = f"{val_str}{unit}"
                    new_tokens.append(fixed_money)
                    
                    i += 2 # Nhảy qua token tiền gốc vì đã xử lý xong
                    continue

            i += 1
            
        return " ".join(new_tokens)

    def _parse_tokens(self, tokens: List[str], date_obj) -> Tuple[List[str], List[Cuoc]]:
        all_dai_found = [] 
        cuoc_list = []
        
        # State (Trạng thái)
        current_dai_list = list(self.last_dai_found)
        temp_nums = []
        
        # Regex kiểm tra
        re_so_danh = re.compile(r'^\d+$') 

        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            # --- TÁCH DẤU CHẤM CÒN SÓT TRONG SỐ ĐÁNH ---
            # Ví dụ: token là "11.59.19" -> Tách thành 11, 59, 19
            # Trừ khi nó là tiền (có 'n' hoặc 'k' hoặc là số thập phân sau loại cược - đã xử lý ở smart_fix)
            # Ở bước này, nếu token thuần số và có chấm, ta tách nó ra.
            if '.' in token and not self._is_money_token(token):
                # Tách ra và chèn lại vào dòng xử lý
                sub_tokens = token.replace('.', ' ').split()
                if len(sub_tokens) > 1:
                    # Chèn sub_tokens vào vị trí hiện tại của tokens
                    tokens[i:i+1] = sub_tokens
                    token = tokens[i] # Lấy lại token đầu tiên sau khi tách
            
            # --- KIỂM TRA ĐÀI ---
            is_dai = False
            # Logic phân biệt BD (Bình Dương) và BD (Bao Đảo)
            # Nếu gặp chữ 'bd' mà trước đó ĐANG CÓ SỐ (temp_nums > 0) -> Thì nó là Loại cược (Bao đảo), KHÔNG phải Đài
            """ if token == 'bd':
                if len(temp_nums) > 0:
                    is_dai = False # Có số trước mặt -> Là Bao đảo
                else:
                    is_dai = True  # Không có số -> Là đài Bình Dương
            else:
                # Check các đài khác bình thường """
            for shorts in DAI_XO_SO.values():
                if token in [s.lower() for s in shorts]:
                    is_dai = True
                    break
            
            if not is_dai:
                if re.match(r'^\d+dm[nt]$', token.lower()):
                    is_dai = True
            
            if is_dai:
                is_prev_dai = False
                if len(temp_nums) > 0:
                    raise Exception(f"Các số ({', '.join(temp_nums)}) đang bị treo. Bạn chưa nhập Loại cược và Tiền cho chúng.")
                
                # Thay vì add trực tiếp token (vd: 2dmn), ta bung nó ra thành list (vd: TP, DT)
                real_stations = self._resolve_dai_gop(token, date_obj)

                is_prev_dai = False
                # Thay vì đoán từ 'prev' là gì (dễ nhầm với bd/bao đảo), 
                # ta kiểm tra xem 'prev' có phải CHÍNH LÀ ĐÀI vừa được thêm vào danh sách không.
                if i > 0:
                    pre_token = tokens[i-1]
                    
                    # Kiểm tra xem từ đứng trước có phải là Đài hay không?
                    # Nếu từ trước CŨNG LÀ ĐÀI -> Nghĩa là đang liệt kê -> Gộp vào (True)
                    # Nếu từ trước là số hoặc cược -> Nghĩa là chuyển sang đài mới -> Reset (False)
                    
                    is_pre_token_is_station = self._is_dai_token(pre_token)
                    
                    # Kiểm tra thêm trường hợp đài gộp (2dmn, 3dmt...)
                    if not is_pre_token_is_station:
                        if re.match(r'^\d+dm[nt]$', pre_token.lower()):
                            is_pre_token_is_station = True
                            
                    if is_pre_token_is_station:
                        is_prev_dai = True
                    
                
                if not is_prev_dai:
                    current_dai_list = [] 
                
                # --- Thêm danh sách đài đã bung vào current_dai_list
                for st in real_stations:
                    # Map về tên chuẩn (viết hoa đẹp) nếu cần, hoặc giữ nguyên
                    # Lưu ý: LICH_QUAY_SO trả về tên đầy đủ, DAI_XO_SO là tên ngắn
                    # Để an toàn, cứ append vào list
                    if st not in current_dai_list:
                        current_dai_list.append(st)
                    
                    # Thêm vào danh sách tổng các đài xuất hiện trong tin nhắn
                    # (Dùng check uppercase để tránh trùng lặp hiển thị)
                    is_in_all = False
                    for existing in all_dai_found:
                        if existing.lower() == st.lower():
                            is_in_all = True
                            break
                    if not is_in_all:
                        all_dai_found.append(st)
                    
                # Cập nhật bộ nhớ đệm
                self.last_dai_found = list(current_dai_list)

                temp_nums = []
                i += 1
                continue

            # --- KIỂM TRA LOẠI CƯỢC ---
            # - Check thêm daX thủ công nếu nó chưa có trong LOAI_CUOC
            is_bet_token = (token in LOAI_CUOC) or (token in ['dax', 'daxien'])

            if is_bet_token:
                loai_key = token
                if not temp_nums:
                    i += 1; continue
                    
                tien_val = 0
                if i + 1 < len(tokens):
                    next_t = tokens[i+1]
                    if self._is_money_token(next_t):
                        tien_val = self._parse_tien(next_t)
                        i += 1
                
                # Bắt buộc phải có tiền
                if tien_val == 0:
                    raise Exception(f"Sau loại cược '{token}' phải là Số tiền (Ví dụ: {token} 10n).")
                
                if tien_val > 0:
                    # --- GỌI VALIDATE LOGIC ---
                    is_valid, msg = self._validate_logic(loai_key, temp_nums, current_dai_list)
                    if not is_valid:
                        # Ném lỗi để báo ra UI
                        raise Exception(msg)

                    nums_to_bet = list(temp_nums)
                    
                    if current_dai_list:
                        ten_dai_hien_thi = ", ".join([self._map_dai(d) for d in current_dai_list])
                    else:
                        ten_dai_hien_thi = "Chưa rõ đài"
                    
                    # LOGIC TỰ ĐỘNG ĐỔI TÊN ĐÁ THEO SỐ LƯỢNG ĐÀI ---
                    if loai_key in ['da', 'daa', 'dax', 'daxien', 'daX']:
                        # Nếu có nhiều hơn 1 đài -> Gọi là Đá thường
                        if len(current_dai_list) > 1:
                            ten_loai = "Đá thường"
                        # Nếu chỉ có 1 đài -> Gọi là Đá Xiên
                        else:
                            ten_loai = "Đá Xiên"
                            
                    elif loai_key in LOAI_CUOC:
                        ten_loai = LOAI_CUOC[loai_key]['ten']
                    else:
                        ten_loai = loai_key

                    new_cuoc = Cuoc(
                        so_danh=nums_to_bet,
                        loai_cuoc=loai_key,
                        ten_loai=ten_loai,
                        tien=tien_val,
                        tien_format=f"{tien_val:,}đ".replace(",", "."),
                        ten_dai=ten_dai_hien_thi
                    )
                    cuoc_list.append(new_cuoc)
                    
                    # --- BẮT ĐẦU LOGIC QUYẾT ĐỊNH GIỮ SỐ HAY KHÔNG ---
                    should_reset = True
                    
                    # Kiểm tra token tiếp theo
                    if i + 1 < len(tokens):
                        next_peek = tokens[i+1]
                        
                        # Check xem từ tiếp theo có phải từ khóa cược không
                        is_next_bet = (next_peek in LOAI_CUOC) or (next_peek in ['dax', 'daxien'])
                        
                        if is_next_bet:
                            # Mặc định: Nếu là cược thì GIỮ SỐ để đánh tiếp (chaining)
                            should_reset = False
                            
                            # [LOGIC MỚI] Xử lý ngoại lệ cho 'bd' dựa trên độ dài số
                            if next_peek == 'bd':
                                # Rule: Bao đảo (bd) chỉ dành cho 3, 4 chữ số.
                                # Nếu danh sách số vừa đánh (nums_to_bet) chứa số 2 chữ số
                                # -> Thì 'bd' này chắc chắn là ĐÀI BÌNH DƯƠNG -> Phải Reset số
                                if any(len(n) == 2 for n in nums_to_bet):
                                    should_reset = True
                                else:
                                    # Trường hợp số là 3 chữ số (ví dụ: 123 456 da 5n bd...)
                                    # Vẫn cần check thêm xem sau 'bd' có tiền không để chắc chắn
                                    is_bd_with_money = False
                                    if i + 2 < len(tokens):
                                        after_bd = tokens[i+2]
                                        if self._is_money_token(after_bd):
                                            is_bd_with_money = True
                                    
                                    # Nếu không có tiền đi kèm -> Nó là Đài -> Reset
                                    if not is_bd_with_money:
                                        should_reset = True

                    if should_reset: 
                        temp_nums = []
                i += 1
                continue
                    
            
            if self._is_money_token(token):
                goi_y = ""
                # Nếu từ trước đó là số (VD: 20), ghép lại thành 20n để báo lỗi
                if i > 0 and re.match(r'^\d+$', tokens[i-1]):
                    goi_y = f" (có thể ý bạn là '{tokens[i-1]}{token}'?)"
                
                raise Exception(f"Lỗi cú pháp: Số tiền '{token}' bị đặt sai vị trí{goi_y}.")

            # --- KIỂM TRA SỐ ---
            if re.match(r'^\d+$', token):
                temp_nums.append(token)
                i += 1
                continue
            if len(temp_nums) > 0:
                raise Exception(f"Không nhận diện được loại cược '{token}'.")
            else:
                 # Nếu không có số chờ, vẫn báo lỗi để chặt chẽ
                 raise Exception(f"Lỗi cú pháp: Từ '{token}' không hợp lệ.")
            
            # Sau khi kết thúc vòng lặp nếu số chưa được xử lý -> lỗi
        if len(temp_nums) > 0:
             raise Exception(f"Các số ở cuối tin nhắn ({', '.join(temp_nums)}) chưa có Loại cược và Tiền.")   
            
        return all_dai_found, cuoc_list 

    def _map_dai(self, code):
        code_lower = code.lower()
        
        # 1. Kiểm tra xem code có trùng với tên đầy đủ (Key) trong cấu hình không
        # (Xử lý trường hợp đài gộp trả về tên đầy đủ như 'Kon Tum')
        for full in DAI_XO_SO.keys():
            if full.lower() == code_lower:
                return full
        
        # 2. Kiểm tra xem code có nằm trong danh sách viết tắt không
        for full, shorts in DAI_XO_SO.items():
            if code_lower in [s.lower() for s in shorts]: 
                return full
        
        # 3. Nếu không tìm thấy, trả về dạng Viết Hoa Chữ Cái Đầu (thay vì UPPER)
        return code.title()

    def _is_money_token(self, t):
        # Chấp nhận số có 'n', 'k', d, đ, ng, ngan  số thực 0.5 
        return bool(re.search(r'(n|k|tr|ng|d|đ)$', t.lower()))

    def _parse_tien(self, t):
        try:
            # Tách số và chữ (0.5n -> 0.5, n)
            m = re.match(r'^([\d\.]+)([a-zđ]+)$', t)
            if not m: return 0
            val_str, unit = m.groups()
            
            val = float(val_str) # 0.5 -> 0.5
            
            mul = 1000 # Mặc định là nghìn
            for k, v in TIEN_TE.items():
                if unit.startswith(k): mul = v; break
            
            return int(val * mul)
        except: return 0