# core/lottery_fetcher.py
import requests
from bs4 import BeautifulSoup
import re

class MinhNgocFetcher:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def fetch_data(self, date_str, region_slug='mien-nam'):
        """
        Phiên bản Fix 4.0:
        1. Chiến thuật 'Right-Align' (Căn phải) để lấy đúng cột đài.
        2. Bộ lọc 'Smart Filter' loại bỏ các dòng mã vé (XSVL - ...) 
           chứa ký tự lạ hoặc chữ cái.
        """
        url = f"https://www.minhngoc.net.vn/ket-qua-xo-so/{region_slug}/{date_str}.html"
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            if response.status_code != 200:
                print(f"Lỗi HTTP: {response.status_code}")
                return {}

            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Tìm bảng kết quả
            tables = soup.find_all('table', class_='bkqt')
            if not tables:
                content_div = soup.find('div', class_='box_kqxs')
                if content_div:
                    tables = content_div.find_all('table')

            final_results = {}

            for table in tables:
                # 1. HEADER: Xác định tên các đài
                tinh_cells = table.find_all(class_='tinh')
                
                provinces = []

                if not tinh_cells and 'mien-bac' in region_slug:
                    provinces = ['Miền Bắc']
                # Nếu không phải Miền Bắc mà không có header thì bỏ qua (Logic cũ)
                elif not tinh_cells: 
                    continue
                else:
                    # Logic lấy tên đài cho MN/MT
                    for node in tinh_cells:
                        raw = node.get_text(strip=True)
                        norm_name = self._normalize_station_name(raw)
                        provinces.append(norm_name)
                
                num_provinces = len(provinces)
                if num_provinces == 0: continue
                
                # Init storage
                if any(p in final_results for p in provinces):
                    current_results = final_results
                else:
                    current_results = {p: [] for p in provinces}

                # 2. Duyệt từng dòng 
                rows = table.find_all('tr')
                for row in rows:
                    if row.find(class_='tinh'): continue # Bỏ qua header

                    cells = row.find_all('td')
                    if not cells: continue

                    # Lọc lấy các ô dữ liệu (Bỏ ô tên giải)
                    data_cells = []
                    for cell in cells:
                        txt = cell.get_text(strip=True)
                        # Bỏ qua ô tên giải
                        if "Giải" in txt or "Đặc" in txt or "biệt" in txt:
                            continue
                        data_cells.append(cell)
                    
                    if len(data_cells) < num_provinces: continue
                        
                    # Lấy đúng N ô cuối cùng (Căn phải)
                    target_cells = data_cells[-num_provinces:]
                    
                    for i, cell in enumerate(target_cells):
                        target_prov = provinces[i]
                        txt = cell.get_text(separator=' ', strip=True)

                        # === [MỚI] BỘ LỌC RÁC (JUNK FILTER) ===
                        # Loại bỏ dòng mã vé như: "XSVL - 47VL03", "XSBD - MB"
                        # Logic: Nếu chuỗi chứa "XS" (Xổ Số) hoặc chứa ký tự "-" kèm chữ cái
                        if "XS" in txt.upper() or "UV" in txt.upper() or ("-" in txt and any(c.isalpha() for c in txt)):
                            continue
                        
                        
                        # Trích xuất số
                        found_nums = re.findall(r'\d{2,6}', txt.replace('.', ''))
                        
                        for num in found_nums:
                            if len(num) > 6: continue
                            current_results[target_prov].append(num)
                
                final_results.update(current_results)

            # 3. CLEANUP: Cắt đuôi thừa
            cleaned_results = {}
            for prov, nums in final_results.items():
                expected = 27 if 'Miền Bắc' in prov else 18
                if len(nums) > expected:
                    cleaned_results[prov] = nums[:expected]
                elif len(nums) > 0:
                    cleaned_results[prov] = nums
            
            return cleaned_results

        except Exception as e:
            print(f"Lỗi fetcher: {e}")
            return {}

    def _normalize_station_name(self, name):
        name_lower = name.lower()
        if 'hà nội' in name_lower or 'truyền thống' in name_lower or 'miền bắc' in name_lower:
            return 'Miền Bắc'

        mapping = {
            'tp.hcm': 'Tp.Hcm', 'thành phố': 'Tp.Hcm', 'sài gòn': 'Tp.Hcm', 'tp. hcm': 'Tp.Hcm',
            'kiên giang': 'Kiên Giang', 'lâm đồng': 'Đà Lạt', 'đà lạt': 'Đà Lạt',
            'tiền giang': 'Tiền Giang', 'cà mau': 'Cà Mau', 'đồng tháp': 'Đồng Tháp',
            'bạc liêu': 'Bạc Liêu', 'bến tre': 'Bến Tre', 'vũng tàu': 'Vũng Tàu',
            'cần thơ': 'Cần Thơ', 'đồng nai': 'Đồng Nai', 'sóc trăng': 'Sóc Trăng',
            'an giang': 'An Giang', 'tây ninh': 'Tây Ninh', 'bình thuận': 'Bình Thuận',
            'bình dương': 'Bình Dương', 'trà vinh': 'Trà Vinh', 'vĩnh long': 'Vĩnh Long',
            'long an': 'Long An', 'hậu giang': 'Hậu Giang', 'bình phước': 'Bình Phước',
            'bình định': 'Bình Định', 'gia lai': 'Gia Lai', 'ninh thuận': 'Ninh Thuận',
            'đà nẵng': 'Đà Nẵng', 'quảng nam': 'Quảng Nam', 'đắk lắk': 'Đắk Lắk',
            'quảng ngãi': 'Quảng Ngãi', 'thừa thiên huế': 'Thừa Thiên Huế',
            'phú yên': 'Phú Yên', 'khánh hòa': 'Khánh Hòa', 'kon tum': 'Kon Tum',
            'đắk nông': 'Đắk Nông', 'quảng trị': 'Quảng Trị', 'quảng bình': 'Quảng Bình'
        }
        for k, v in mapping.items():
            if k in name_lower:
                return v
        return name.title()