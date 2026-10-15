from datetime import date
import pandas as pd
import streamlit as st
from config.constants import DAI_XO_SO
from core.bet_checker import BetChecker
from core.classifier import phan_loai_nhom_cuoc
from core.lottery_fetcher import MinhNgocFetcher
from core.parser import SMSParser
from gsheet_handler import read_sheet_range, write_sheet_range



@st.cache_data(show_spinner=False, ttl=3600)
def lay_kqxs_theo_ngay(ngay):
    """Lấy toàn bộ kết quả xổ số (MB + MT + MN) của một ngày và gộp thành dict
    {tên_đài: [danh sách số]} để đưa vào BetChecker."""
    date_str = ngay.strftime("%d-%m-%Y")
    fetcher = MinhNgocFetcher()

    ket_qua = {}
    for region_slug in ("mien-bac", "mien-trung", "mien-nam"):
        try:
            data = fetcher.fetch_data(date_str, region_slug=region_slug)
        except Exception:
            data = {}
        if data:
            for ten_dai, ds_so in data.items():
                ten_chuan = _chuan_hoa_ten_dai(ten_dai)
                if ten_chuan:
                    ket_qua[ten_chuan] = ds_so

    return ket_qua


_TEN_DAI_TUONG_DUONG = {
    "Thừa Thiên Huế": "Huế",
    "Huế": "Huế",
    "TP.HCM": "Tp.Hcm",
    "Tp. HCM": "Tp.Hcm",
    "Thành phố Hồ Chí Minh": "Tp.Hcm",
}


def _chuan_hoa_ten_dai(ten_dai):
    if not ten_dai:
        return None
    ten = str(ten_dai).strip()
    if ten in DAI_XO_SO:
        return ten
    if ten in _TEN_DAI_TUONG_DUONG:
        return _TEN_DAI_TUONG_DUONG[ten]
    ten_lower = ten.lower()
    for key_chuan, ds_viet_tat in DAI_XO_SO.items():
        if ten_lower == key_chuan.lower():
            return key_chuan
        if ten_lower in [s.lower() for s in ds_viet_tat]:
            return key_chuan
    return None


def _is_mien_bac(ten_dai: str) -> bool:
    """Nhận diện chính xác đài Miền Bắc."""
    if not ten_dai:
        return False
    td = ten_dai.lower()
    mb_keywords = [
        "mb", "bắc", "bac", "hà nội", "ha noi", "hn",
        "thủ đô", "thu do", "quảng ninh", "qn", "hải phòng",
        "hp", "nam định", "nd", "thái bình", "tb"
    ]
    return any(kw in td for kw in mb_keywords)


# ==============================================================================
# 🟢 ZONE 1: HÀM XỬ LÝ GỌI PARSER & TÍNH TOÁN TIỀN XÁC
# ==============================================================================

def tinh_tien_xac_tung_cuoc(cuoc):
    """
    Tính tiền xác và phân loại mã nhóm chuẩn cho từng cược:
    - Nhóm 2S: 2CB (bao lô 2 con, đầu, đuôi, đầu đuôi), ĐáT (đá thẳng), ĐáX (đá xiên).
    - Nhóm 3S: 3CB, 3CXC (xỉu chủ), 3CXĐ, 3CBĐ, 4CB, 4CBĐ.
    """
    loai_cuoc = (cuoc.loai_cuoc or "").lower().strip()
    ten_loai = (cuoc.ten_loai or "").lower().strip()
    so_danh = cuoc.so_danh or []
    len_so = len(so_danh[0]) if so_danh else 2
    tl = f"{ten_loai} {loai_cuoc}".lower()

    # 1. Thử lấy mã nhóm từ phan_loai_nhom_cuoc
    ma_nhom = None
    try:
        ma_nhom, _ = phan_loai_nhom_cuoc(cuoc)
    except Exception:
        ma_nhom = None

    VALID_GROUPS = {"2CB", "3CB", "4CB", "3CXC", "3CXĐ", "3CBĐ", "4CBĐ", "ĐáT", "ĐáX"}

    # 2. Chuẩn hóa phân nhóm nếu classifier chưa trả về mã hợp lệ
    if ma_nhom not in VALID_GROUPS:
        if loai_cuoc in ["da", "daa", "dax", "daxien", "dax"] or "đá" in tl:
            ma_nhom = "Đá"  # Sẽ phân ĐáT/ĐáX theo số lượng đài ở dưới
        elif loai_cuoc in ["xcdao", "xcdaoduoi", "xcdaodau"] or ("dao" in loai_cuoc and "xc" in loai_cuoc) or ("đảo" in tl and "xc" in tl):
            ma_nhom = "3CXĐ"
        elif loai_cuoc in ["xc", "xcdd", "xcduoi", "xcdau"] or "xc" in loai_cuoc or "xỉu" in tl:
            ma_nhom = "3CXC"
        elif loai_cuoc in ["baodao", "bdao", "bd"] or "đảo" in tl or "dao" in tl:
            ma_nhom = "4CBĐ" if len_so == 4 else "3CBĐ"
        elif loai_cuoc in ["dau", "ddau", "duoi", "dd", "dauduoi", "đđ"] or any(x in tl for x in ["đầu", "đuôi", "dd"]):
            # NẾU ĐÁNH 3 CON ĐẦU/ĐUÔI THÌ ĐÂY LÀ XỈU CHỦ (3S), KHÔNG PHẢI 2CB (2S)
            ma_nhom = "3CXC" if len_so == 3 else "2CB"
        elif loai_cuoc in ["bao", "blo", "b"] or "bao" in tl:
            if len_so == 2:
                ma_nhom = "2CB"
            elif len_so == 3:
                ma_nhom = "3CB"
            elif len_so == 4:
                ma_nhom = "4CB"

    if not ma_nhom:
        return 0, None

    so_luong_so = len(so_danh)
    is_mb = _is_mien_bac(cuoc.ten_dai)

    # 3. Xác định số lượng đài
    so_luong_dai = 1
    if cuoc.ten_dai:
        td = cuoc.ten_dai.lower()
        dais = [d.strip() for d in cuoc.ten_dai.split(",") if d.strip()]
        if dais:
            so_luong_dai = len(dais)
        if "2dmn" in td or "2 đài" in td:
            so_luong_dai = max(so_luong_dai, 2)
        elif "3dmn" in td or "3 đài" in td:
            so_luong_dai = max(so_luong_dai, 3)
        elif "4dmn" in td or "4 đài" in td:
            so_luong_dai = max(so_luong_dai, 4)

    gia_tri_xac = 0

    # -------------------------------------------------------------
    # 1. ĐÁ (Đá thẳng ĐáT, Đá xiên ĐáX) -> Nhóm 2S
    # -------------------------------------------------------------
    if ma_nhom in ["Đá", "ĐáX", "ĐáT"] or "đá" in tl:
        n = so_luong_so
        so_cap = n * (n - 1) // 2 if n >= 2 else 0
        if is_mb:
            he_so = 54  # 1 cặp đá MB = 2 con x 27 giải = 54
            key_nhom = "ĐáT"
        else:
            if so_luong_dai == 1:
                # 1 đài là ĐÁ THẲNG (ĐáT): 2 con x 18 giải = 36
                he_so = 36
                key_nhom = "ĐáT"
            else:
                # Từ 2 đài trở lên là ĐÁ XIÊN (ĐáX):
                # 2 đài = 2 con x 18 giải x 2 đài = 72 giải/cặp
                so_cap_dai = so_luong_dai * (so_luong_dai - 1) // 2
                he_so = 72 * so_cap_dai
                key_nhom = "ĐáX"

        gia_tri_xac = cuoc.tien * he_so * so_cap
        return gia_tri_xac, key_nhom

    # -------------------------------------------------------------
    # 2. 2CB (Đầu, Đuôi, Đầu Đuôi, Bao lô 2 con) -> Nhóm 2S
    # -------------------------------------------------------------
    elif ma_nhom == "2CB":
        is_dau_duoi = any(x in tl for x in ["đầu đuôi", "dauduoi", "dd", "đđ"])
        is_dau = ("đầu" in tl or "dau" in tl) and not is_dau_duoi
        is_duoi = ("đuôi" in tl or "duoi" in tl) and not is_dau_duoi

        if is_mb:
            if is_dau_duoi:
                he_so = 5   # 4 giải G7 + 1 giải ĐB
            elif is_dau:
                he_so = 4   # 4 giải G7
            elif is_duoi:
                he_so = 1   # 1 giải ĐB
            else:
                he_so = 27  # Bao lô MB = 27 giải
        else:
            if is_dau_duoi:
                he_so = 2   # G8 (1) + ĐB (1)
            elif is_dau or is_duoi:
                he_so = 1   # G8 hoặc ĐB
            else:
                he_so = 18  # Bao lô MN/MT = 18 giải

        gia_tri_xac = so_luong_so * cuoc.tien * he_so * so_luong_dai
        return gia_tri_xac, "2CB"

    # -------------------------------------------------------------
    # 3. 3CB (Bao lô 3 con) -> Nhóm 3S
    # -------------------------------------------------------------
    elif ma_nhom == "3CB":
        he_so = 23 if is_mb else 17
        gia_tri_xac = so_luong_so * cuoc.tien * he_so * so_luong_dai
        return gia_tri_xac, "3CB"

    # -------------------------------------------------------------
    # 4. 3CXC (Xỉu chủ / 3 càng) -> Nhóm 3S
    # -------------------------------------------------------------
    elif ma_nhom in ["3CXC", "3CXCDau", "3CXCDuoi"]:
        is_dau_duoi = any(x in tl for x in ["đầu đuôi", "dauduoi", "dd", "đđ", "xcdd"]) or (loai_cuoc == "xc")
        is_dau = ("đầu" in tl or "dau" in tl or "xcdau" in loai_cuoc) and not is_dau_duoi
        is_duoi = ("đuôi" in tl or "duoi" in tl or "xcduoi" in loai_cuoc) and not is_dau_duoi

        if is_mb:
            if is_dau_duoi:
                he_so = 4   # 3 giải G6 + 1 giải ĐB
            elif is_dau:
                he_so = 3   # 3 giải G6
            else:
                he_so = 1   # 1 giải ĐB
        else:
            if is_dau_duoi:
                he_so = 2   # G7 (1) + ĐB (1)
            else:
                he_so = 1   # G7 hoặc ĐB

        gia_tri_xac = so_luong_so * cuoc.tien * he_so * so_luong_dai
        return gia_tri_xac, "3CXC"

    # -------------------------------------------------------------
    # 5. 3CXĐ & 3CBĐ (Xỉu chủ đảo & 3 con bao đảo) -> Nhóm 3S
    # -------------------------------------------------------------
    elif ma_nhom in ["3CXĐ", "3CBĐ"]:
        tong_hv = sum(
            6 if len(set(s)) == 3 else (3 if len(set(s)) == 2 else 1)
            for s in so_danh
            if len(s) == 3
        )
        if ma_nhom == "3CXĐ":
            is_dau_duoi = any(x in tl for x in ["đầu đuôi", "dauduoi", "dd", "đđ"]) or (loai_cuoc == "xcdao")
            is_dau = ("đầu" in tl or "dau" in tl) and not is_dau_duoi
            is_duoi = ("đuôi" in tl or "duoi" in tl) and not is_dau_duoi

            if is_mb:
                he_so = 4 if is_dau_duoi else (3 if is_dau else 1)
            else:
                he_so = 2 if is_dau_duoi else 1
            gia_tri_xac = tong_hv * cuoc.tien * he_so * so_luong_dai
            return gia_tri_xac, "3CXĐ"
        else:  # 3CBĐ
            he_so = 23 if is_mb else 17
            gia_tri_xac = tong_hv * cuoc.tien * he_so * so_luong_dai
            return gia_tri_xac, "3CBĐ"

    # -------------------------------------------------------------
    # 6. 4CB (Bao lô 4 con) -> Nhóm 3S
    # -------------------------------------------------------------
    elif ma_nhom == "4CB":
        he_so = 20 if is_mb else 16
        gia_tri_xac = so_luong_so * cuoc.tien * he_so * so_luong_dai
        return gia_tri_xac, "4CB"

    # -------------------------------------------------------------
    # 7. 4CBĐ (Bao đảo 4 con) -> Nhóm 3S
    # -------------------------------------------------------------
    elif ma_nhom == "4CBĐ":
        tong_hv = 0
        for s in so_danh:
            c = sorted([s.count(char) for char in set(s)])
            tong_hv += (
                24 if c == [1, 1, 1, 1]
                else (12 if c == [1, 1, 2]
                else (6 if c == [2, 2]
                else (4 if c == [1, 3] else 1)))
            )
        he_so = 20 if is_mb else 16
        gia_tri_xac = tong_hv * cuoc.tien * he_so * so_luong_dai
        return gia_tri_xac, "4CBĐ"

    return gia_tri_xac, ma_nhom



def process_xoso_sms(
    text: str,
    parser_instance: SMSParser,
    check_results_list=None,
    bet_checker=None,
    ngay_chay=None,
    he_so_2s: float = 1.0,
    he_so_3s: float = 1.0,
    chia_nghin: bool = False,
):
    clean_text = str(text).strip()
    if not clean_text:
        return None

    try:
        res = parser_instance.parse(clean_text, ngay_chay=ngay_chay)
    except Exception as e:
        return {
            "2S": 0,
            "3S": 0,
            "TienXac": 0,
            "Sotrung": "",
            "TenDai": "",
            "TrangThai": "Lỗi",
            "GhiChu": f"Lỗi parse: {str(e)}",
        }

    group_totals = {
        "2CB": 0, "3CB": 0, "4CB": 0,
        "3CXC": 0, "3CBĐ": 0, "3CXĐ": 0,
        "4CBĐ": 0, "ĐáT": 0, "ĐáX": 0,
    }
    danh_sach_trung = []

    if res.hop_le and res.danh_sach_cuoc:
        for idx, cuoc in enumerate(res.danh_sach_cuoc):
            try:
                xac, nhom = tinh_tien_xac_tung_cuoc(cuoc)
                if nhom and nhom in group_totals:
                    group_totals[nhom] += xac
            except Exception:
                pass

            ck = None
            if check_results_list and idx < len(check_results_list):
                ck = check_results_list[idx]
            elif bet_checker is not None:
                try:
                    ck = bet_checker.check_cuoc(cuoc)
                except Exception:
                    ck = None

            if ck and ck.get("status") == "win":
                thong_bao = str(ck.get("message", "")).strip()
                # 1. Lấy tiền cược từ cuoc.tien
                tien_cuoc = getattr(cuoc, "tien", 0) or 0

                # 2. Xử lý trường hợp tiền lưu là điểm/k (vd 50) hoặc số tiền thật (vd 50000)
                tien_hien_thi = tien_cuoc
                str_tien = f"{tien_hien_thi:,.0f} đ".replace(",", ".")

                # 3. Nối số tiền vào nội dung trúng
                if thong_bao:
                    danh_sach_trung.append(f"{thong_bao}: {str_tien}")
                else:
                    danh_sach_trung.append(f"Trúng: {str_tien}")

    

    def format_bo_so_khong_thua(val) -> str:
        """Loại bỏ các số 0 thừa sau dấu phẩy (vd: 150.0 -> 150; 150.50 -> 150.5)."""
        if val is None or pd.isna(val):
            return "0"
        num = float(val)
        if num.is_integer():
            return str(int(num))
        # Sử dụng format g để tự động cắt các số 0 không có nghĩa ở phần thập phân
        return f"{num:.4f}".rstrip("0").rstrip(".")

    # 1. Tính tổng gốc
    raw_2s = sum(group_totals.get(k, 0) for k in ["2CB", "ĐáX", "ĐáT"])
    raw_3s = sum(group_totals.get(k, 0) for k in ["3CB", "3CXC", "3CXĐ", "3CBĐ", "4CBĐ", "4CB"])

    # 2. Áp dụng hệ số tùy chỉnh
    total_2s = (raw_2s * he_so_2s) / 1000
    total_3s = (raw_3s * he_so_3s) / 1000
    tong_xac = total_2s + total_3s

    def clean_number(val):
        if val is None or pd.isna(val):
            return 0
        num = float(val)
        return int(num) if num.is_integer() else round(num, 2)


    return {
        "2S": total_2s,
        "3S": total_3s,
        "TienXac": tong_xac,
        "Sotrung": ", ".join(danh_sach_trung) if danh_sach_trung else "",
        "TenDai": ", ".join(res.ten_dai) if res.ten_dai else "",
        "TrangThai": "Hợp lệ" if res.hop_le else "Lỗi",
        "GhiChu": res.loi if res.loi else "OK",
    }


# ==============================================================================
# ⚙️ ZONE 2: CẤU HÌNH GIAO DIỆN & SHEET
# ==============================================================================
st.set_page_config(page_title="Tính Tin Nhắn Xổ Số", layout="wide")
st.title("Phần mềm Tính Tin Nhắn Xổ Số & Đồng bộ Google Sheets")

st.sidebar.header("Cấu hình Google Sheets")
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1gD4xNTKf61tiDlI9an8suM82-84oU5kC5Xj0qb3yDPk/edit?usp=sharing"

sheet_url = st.sidebar.text_input("Google Sheet URL hoặc ID", value=DEFAULT_SHEET_URL)
ws_name = st.sidebar.text_input("Tên Sheet (Worksheet Name)", value="SMS")
input_range = st.sidebar.text_input("Dải ô đọc dữ liệu", value="A2:A40")
ngay_do = st.sidebar.date_input("Ngày dò xổ số", value=date.today())
output_start_cell = st.sidebar.text_input("Ô bắt đầu ghi kết quả", value="B2")


if "calc_result" not in st.session_state:
    st.session_state["calc_result"] = None

# ==============================================================================
# 🟡 ZONE 3: LẤY DỮ LIỆU & TÍNH TOÁN
# ==============================================================================
if st.button("📥 1. Lấy dữ liệu từ Sheet & Tính toán"):
    if not sheet_url or not ws_name:
        st.error("Vui lòng nhập URL và tên Tab Sheet ở thanh bên trái!")
    else:
        try:
            with st.spinner("Đang đọc dữ liệu từ Google Sheets..."):
                raw_data = read_sheet_range(sheet_url, ws_name, input_range)

            if not raw_data:
                st.warning(f"Không tìm thấy dữ liệu trong dải ô {input_range}!")
            else:
                st.success(f"Đã đọc thành công {len(raw_data)} hàng!")

                bet_checker = None
                try:
                    with st.spinner(f"Đang tải kết quả xổ số ngày {ngay_do.strftime('%d/%m/%Y')}..."):
                        kqxs = lay_kqxs_theo_ngay(ngay_do)
                    if kqxs:
                        bet_checker = BetChecker(kqxs)
                        st.success(f"✅ Đã tải KQXS của {len(kqxs)} đài để dò số trúng.")
                    else:
                        st.warning("Không tải được KQXS. Cột 'Sotrung' sẽ để trống.")
                except Exception as e:
                    st.warning(f"Không thể tải KQXS: {str(e)}")

                sms_parser = SMSParser()
                calculated_rows = []

                # KHUÔN MẪU HÀNG RỖNG (để bảo toàn đúng vị trí hàng)
                EMPTY_ROW = {
                    "2S": "",
                    "3S": "",
                    "TienXac": "",
                    "Sotrung": "",
                    "TenDai": "",
                    "TrangThai": "",
                    "GhiChu": "",
                }

                for row in raw_data:
                    sms_line = str(row[0]) if len(row) > 0 else ""
                    sms_clean = sms_line.strip()

                    # 1. Nếu ô trống -> Vẫn thêm hàng rỗng để giữ đúng vị trí dòng
                    if not sms_clean:
                        calculated_rows.append(EMPTY_ROW.copy())
                        continue

                    # 2. Bỏ qua nếu là dòng tiêu đề cũ
                    if sms_clean.lower() == "noidungsms":
                        calculated_rows.append(EMPTY_ROW.copy())
                        continue

                    # 3. Phân tích và tính toán tin nhắn
                    row_result = process_xoso_sms(
                        sms_clean,
                        parser_instance=sms_parser,
                        check_results_list=None,
                        bet_checker=bet_checker,
                        ngay_chay=ngay_do,
                        he_so_2s=1.0,
                        he_so_3s=1.0,
                    )
                    
                    calculated_rows.append(row_result if row_result else EMPTY_ROW.copy())

                if calculated_rows:
                    df_result = pd.DataFrame(calculated_rows)
                    st.session_state["calc_result"] = df_result

                    # --- TÍNH TỔNG AN TOÀN (chuyển ô rỗng thành 0) ---
                    s_2s = pd.to_numeric(df_result["2S"], errors="coerce").fillna(0)
                    s_3s = pd.to_numeric(df_result["3S"], errors="coerce").fillna(0)
                    s_xac = pd.to_numeric(df_result["TienXac"], errors="coerce").fillna(0)

                    sum_2s = int(s_2s.sum())
                    sum_3s = int(s_3s.sum())
                    sum_xac = int(s_xac.sum())

                    st.markdown("### 📊 Tổng kết doanh số:")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("💰 Tổng Tiền Xác 2S", f"{sum_2s:,.0f}đ".replace(",", "."))
                    c2.metric("💰 Tổng Tiền Xác 3S", f"{sum_3s:,.0f}đ".replace(",", "."))
                    c3.metric("🎯 Tổng Tiền Xác (2S + 3S)", f"{sum_xac:,.0f}đ".replace(",", "."))

                    st.subheader("📋 Bảng chi tiết từng tin nhắn (Khớp từng hàng với cột A):")
                    st.dataframe(df_result, use_container_width=True)
                else:
                    st.warning("Dải ô được chọn không có dữ liệu.")

        except Exception as e:
            st.error(f"Lỗi khi đọc/tính toán: {str(e)}")

# ==============================================================================
# 📤 ZONE 4: GHI KẾT QUẢ VỀ GOOGLE SHEETS
# ==============================================================================
if st.session_state.get("calc_result") is not None:
    st.divider()
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        include_header = st.checkbox("Ghi cả dòng Tiêu đề cột (Headers)", value=False)
    with col_opt2:
        include_summary = st.checkbox("Thêm hàng 'TỔNG CỘNG' ở cuối bảng", value=False)

    if st.button("📤 2. Ghi kết quả về Google Sheet"):
        try:
            df_to_export = st.session_state["calc_result"].copy()
            if df_to_export.empty:
                st.warning("Không có dữ liệu để ghi!")
            else:
                # 👉 HÀM LÀM SẠCH DỮ LIỆU: Bỏ hoàn toàn .0 và giữ nguyên ô trống
                def format_cell_value(val):
                    if val is None or pd.isna(val) or val == "":
                        return ""
                    try:
                        num = float(val)
                        return int(num) if num.is_integer() else round(num, 2)
                    except (ValueError, TypeError):
                        return str(val)

                # Chuyển đổi DataFrame thành danh sách giá trị sạch
                export_data = [
                    [format_cell_value(cell) for cell in row]
                    for row in df_to_export.values.tolist()
                ]

                # Xử lý hàng TỔNG CỘNG nếu có chọn
                if include_summary:
                    sum_2s = int(pd.to_numeric(df_to_export["2S"], errors="coerce").fillna(0).sum())
                    sum_3s = int(pd.to_numeric(df_to_export["3S"], errors="coerce").fillna(0).sum())
                    sum_xac = int(pd.to_numeric(df_to_export["TienXac"], errors="coerce").fillna(0).sum())
                    
                    summary_row = [
                        sum_2s,     # Gửi dạng số nguyên, Google Sheets sẽ hiển thị đúng chuẩn số
                        sum_3s,
                        sum_xac,
                        "",
                        "",
                        "TỔNG CỘNG",
                        f"Tổng 2S: {sum_2s:,.0f}đ | Tổng 3S: {sum_3s:,.0f}đ".replace(",", "."),
                    ]
                    export_data.append(summary_row)

                if include_header:
                    values_to_write = [df_to_export.columns.tolist()] + export_data
                else:
                    values_to_write = export_data

                with st.spinner("Đang ghi dữ liệu vào Google Sheet..."):
                    write_sheet_range(
                        sheet_url, ws_name, output_start_cell, values_to_write
                    )

                st.success(f"✅ Đã ghi thành công kết quả bắt đầu từ ô **{output_start_cell}**!")
        except Exception as e:
            st.error(f"Lỗi khi ghi dữ liệu: {str(e)}")