from datetime import date
import pandas as pd
import streamlit as st
from core.classifier import phan_loai_nhom_cuoc
from core.parser import SMSParser
from config.constants import DAI_XO_SO
from core.bet_checker import BetChecker
from core.lottery_fetcher import MinhNgocFetcher
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
            # Chuẩn hoá tên đài về key trong DAI_XO_SO để BetChecker tìm thấy
            for ten_dai, ds_so in data.items():
                ten_chuan = _chuan_hoa_ten_dai(ten_dai)
                if ten_chuan:
                    ket_qua[ten_chuan] = ds_so

    return ket_qua


# Tên đài do MinhNgocFetcher trả về có thể khác key trong DAI_XO_SO
# (VD: "Thừa Thiên Huế" -> "Huế") -> BetChecker sẽ không tìm thấy và luôn báo trống
_TEN_DAI_TUONG_DUONG = {
    "Thừa Thiên Huế": "Huế",
    "Huế": "Huế",
    "TP.HCM": "Tp.Hcm",
    "Tp. HCM": "Tp.Hcm",
    "Thành phố Hồ Chí Minh": "Tp.Hcm",
}


def _chuan_hoa_ten_dai(ten_dai):
    """Map tên đài lấy từ web về đúng key trong DAI_XO_SO.
    Trả về None nếu không nhận diện được (bỏ qua đài lạ)."""
    if not ten_dai:
        return None

    ten = str(ten_dai).strip()

    # 1. Đã đúng key chuẩn thì giữ nguyên
    if ten in DAI_XO_SO:
        return ten

    # 2. Tra bảng tương đương thủ công
    if ten in _TEN_DAI_TUONG_DUONG:
        return _TEN_DAI_TUONG_DUONG[ten]

    # 3. Tìm qua danh sách viết tắt (không phân biệt hoa/thường)
    ten_lower = ten.lower()
    for key_chuan, ds_viet_tat in DAI_XO_SO.items():
        if ten_lower == key_chuan.lower():
            return key_chuan
        if ten_lower in [s.lower() for s in ds_viet_tat]:
            return key_chuan

    # 4. Không nhận diện được -> bỏ qua
    return None


# ==============================================================================
# 🟢 ZONE 1: HÀM XỬ LÝ GỌI PARSER & TÍNH TOÁN
# ==============================================================================


def tinh_tien_xac_tung_cuoc(cuoc):
    """Tính tiền xác và mã nhóm theo đúng logic trong result_display.py"""
    ma_nhom, _ = phan_loai_nhom_cuoc(cuoc)
    if not ma_nhom and cuoc.ten_loai:
        tl_tmp = cuoc.ten_loai.lower()
        if (
            ("đảo" in tl_tmp or "dao" in tl_tmp)
            and cuoc.so_danh
            and len(cuoc.so_danh[0]) == 3
        ):
            ma_nhom = "3CXĐ"
        elif any(x in tl_tmp for x in ["đầu", "đuôi", "dau", "duoi", "dd"]):
            ma_nhom = "2CB"

    if not ma_nhom:
        return 0, None

    so_luong_so = len(cuoc.so_danh)
    so_luong_dai = len(cuoc.ten_dai.split(",")) if cuoc.ten_dai else 0
    is_mb = False
    if cuoc.ten_dai:
        td = cuoc.ten_dai.lower()
        if "mb" in td or "bắc" in td:
            is_mb = True
        if "2dmn" in td or "2 đài" in td:
            so_luong_dai = 2
        elif "3dmn" in td or "3 đài" in td:
            so_luong_dai = 3

    gia_tri_xac = 0
    # 1. Đá
    if ma_nhom in ["ĐáX", "ĐáT"] or "đá" in (
        cuoc.ten_loai.lower() if cuoc.ten_loai else ""
    ):
        n = len(cuoc.so_danh)
        so_cap = n * (n - 1) // 2 if n >= 2 else 0
        he_so = (
            54
            if is_mb
            else (
                18
                if (
                    ma_nhom == "ĐáX"
                    or "xiên" in (cuoc.ten_loai.lower() if cuoc.ten_loai else "")
                    or so_luong_dai == 1
                )
                else 36
            )
        )
        gia_tri_xac = cuoc.tien * he_so * so_cap * so_luong_dai

    # 2. 2CB
    elif ma_nhom == "2CB":
        tl = cuoc.ten_loai.lower() if cuoc.ten_loai else ""
        if is_mb:
            he_so = (
                5
                if ("đầu đuôi" in tl or "dd" in tl)
                else (
                    4
                    if ("đầu" in tl or "dau" in tl)
                    else (1 if ("đuôi" in tl or "duoi" in tl) else 27)
                )
            )
        else:
            he_so = 2 if ("đầu đuôi" in tl or "dd" in tl) else 1
        gia_tri_xac = so_luong_so * cuoc.tien * he_so * so_luong_dai

    # 3. 3CB
    elif ma_nhom == "3CB":
        gia_tri_xac = (
            so_luong_so * cuoc.tien * (23 if is_mb else 17) * so_luong_dai
        )

    # 4. 3CXC
    elif ma_nhom in ["3CXC", "3CXCDau", "3CXCDuoi"]:
        tl = cuoc.ten_loai.lower() if cuoc.ten_loai else ""
        if is_mb:
            he_so = (
                3
                if ("đầu" in tl or "dau" in tl)
                else (1 if ("đuôi" in tl or "duoi" in tl) else 4)
            )
        else:
            he_so = (
                1
                if (
                    ("đầu" in tl or "dau" in tl)
                    or ("đuôi" in tl or "duoi" in tl)
                )
                else 2
            )
        gia_tri_xac = so_luong_so * cuoc.tien * he_so * so_luong_dai

    # 5. 3CXĐ & 3CBĐ
    elif ma_nhom in ["3CXĐ", "3CBĐ"]:
        tong_hv = sum(
            6
            if len(set(s)) == 3
            else (3 if len(set(s)) == 2 else 1)
            for s in cuoc.so_danh
            if len(s) == 3
        )
        if ma_nhom == "3CXĐ":
            tl = cuoc.ten_loai.lower() if cuoc.ten_loai else ""
            he_so = (
                (
                    3
                    if ("đầu" in tl or "dau" in tl)
                    else (1 if ("đuôi" in tl or "duoi" in tl) else 4)
                )
                if is_mb
                else (
                    1
                    if (
                        ("đầu" in tl or "dau" in tl)
                        or ("đuôi" in tl or "duoi" in tl)
                    )
                    else 2
                )
            )
            gia_tri_xac = tong_hv * cuoc.tien * he_so * so_luong_dai
        else:  # 3CBĐ
            gia_tri_xac = (
                tong_hv
                * cuoc.tien
                * (23 if is_mb else 17)
                * (1 if is_mb else so_luong_dai)
            )

    # 6. 4CB
    elif ma_nhom == "4CB":
        gia_tri_xac = (
            so_luong_so * cuoc.tien * (20 if is_mb else 16) * so_luong_dai
        )

    # 7. 4CBĐ
    elif ma_nhom == "4CBĐ":
        tong_hv = 0
        for s in cuoc.so_danh:
            c = sorted([s.count(char) for char in set(s)])
            tong_hv += (
                24
                if c == [1, 1, 1, 1]
                else (
                    12
                    if c == [1, 1, 2]
                    else (6 if c == [2, 2] else (4 if c == [1, 3] else 1))
                )
            )
        gia_tri_xac = (
            tong_hv
            * cuoc.tien
            * (20 if is_mb else 16)
            * (1 if is_mb else so_luong_dai)
        )

    key_nhom = (
        "3CXC" if ma_nhom in ["3CXCDau", "3CXCDuoi"] else ma_nhom
    )
    return gia_tri_xac, key_nhom


def process_xoso_sms(
    text: str,
    parser_instance: SMSParser,
    check_results_list=None,
    bet_checker=None,
    ngay_chay=None,
):
    clean_text = str(text).strip()
    if not clean_text:
        return None

    res = parser_instance.parse(clean_text, ngay_chay=ngay_chay)

    group_totals = {
        "2CB": 0,
        "3CB": 0,
        "4CB": 0,
        "3CXC": 0,
        "3CBĐ": 0,
        "3CXĐ": 0,
        "4CBĐ": 0,
        "ĐáT": 0,
        "ĐáX": 0,
    }
    danh_sach_trung = []

    if res.hop_le and res.danh_sach_cuoc:
        for idx, cuoc in enumerate(res.danh_sach_cuoc):
            xac, nhom = tinh_tien_xac_tung_cuoc(cuoc)
            if nhom and nhom in group_totals:
                group_totals[nhom] += xac

            # Lấy số trúng:
            # - Nếu đã có danh sách dò sẵn (check_results_list) thì dùng luôn
            # - Nếu chưa có nhưng đã truyền BetChecker (có dữ liệu KQXS) -> tự dò
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
                danh_sach_trung.append(thong_bao if thong_bao else "Trúng")

    # Phân nhóm 2S và 3S
    total_2s = sum(
        group_totals.get(k, 0) for k in ["2CB", "ĐáX", "ĐáT"]
    )
    total_3s = sum(
        group_totals.get(k, 0)
        for k in ["3CB", "3CXC", "3CXĐ", "3CBĐ", "4CBĐ", "4CB"]
    )
    tong_xac = total_2s + total_3s

    # ĐÃ LOẠI BỎ "NoiDungGoc", chỉ trả về các cột cần thiết
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

sheet_url = st.sidebar.text_input(
    "Google Sheet URL hoặc ID", value=DEFAULT_SHEET_URL
)
ws_name = st.sidebar.text_input("Tên Sheet (Worksheet Name)", value="SMS")
input_range = st.sidebar.text_input("Dải ô đọc dữ liệu", value="A2:A25")
ngay_do = st.sidebar.date_input("Ngày dò xổ số", value=date.today())
output_start_cell = st.sidebar.text_input("Ô bắt đầu ghi kết quả", value="B1")

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

                # --- LẤY KQXS THEO NGÀY DÒ ĐỂ TÍNH CỘT "Sotrung" ---
                bet_checker = None
                try:
                    with st.spinner(
                        f"Đang tải kết quả xổ số ngày "
                        f"{ngay_do.strftime('%d/%m/%Y')}..."
                    ):
                        kqxs = lay_kqxs_theo_ngay(ngay_do)
                    if kqxs:
                        bet_checker = BetChecker(kqxs)
                        st.success(
                            f"✅ Đã tải KQXS của {len(kqxs)} đài để dò số trúng."
                        )
                    else:
                        st.warning(
                            "Không tải được KQXS (chưa có kết quả hoặc lỗi mạng). "
                            "Cột 'Sotrung' sẽ để trống."
                        )
                except Exception as e:
                    st.warning(f"Không thể tải KQXS: {str(e)}")

                # Khởi tạo parser cho lượt tính này
                sms_parser = SMSParser()

                calculated_rows = []
                for row in raw_data:
                    sms_line = str(row[0]) if len(row) > 0 else ""
                    sms_clean = sms_line.strip()

                    # Bỏ qua ô trống hoặc dòng tiêu đề "NoiDungSMS"
                    if not sms_clean or sms_clean.lower() == "noidungsms":
                        continue

                    row_result = process_xoso_sms(
                        sms_clean,
                        parser_instance=sms_parser,
                        check_results_list=None,
                        bet_checker=bet_checker,
                        ngay_chay=ngay_do,
                    )
                    if row_result:
                        calculated_rows.append(row_result)

                if calculated_rows:
                    df_result = pd.DataFrame(calculated_rows)
                    st.session_state["calc_result"] = df_result
                    st.subheader("📋 Bảng kết quả sau khi tính:")
                    st.dataframe(df_result, use_container_width=True)
                else:
                    st.warning(
                        "Dải ô được chọn không có nội dung tin nhắn nào hợp lệ."
                    )

        except Exception as e:
            st.error(f"Lỗi khi đọc/tính toán: {str(e)}")

# ==============================================================================
# 📤 ZONE 4: GHI KẾT QUẢ VỀ GOOGLE SHEETS
# ==============================================================================
if st.session_state["calc_result"] is not None:
    st.divider()
    if st.button("📤 2. Ghi kết quả về Google Sheet"):
        try:
            df_to_export = st.session_state["calc_result"]
            if df_to_export.empty:
                st.warning("Không có dữ liệu để ghi!")
            else:
                values_to_write = [
                    df_to_export.columns.tolist()
                ] + df_to_export.astype(str).values.tolist()

                with st.spinner("Đang ghi dữ liệu vào Google Sheet..."):
                    write_sheet_range(
                        sheet_url, ws_name, output_start_cell, values_to_write
                    )

                st.success(
                    f"✅ Đã ghi thành công kết quả bắt đầu từ ô **{output_start_cell}**!"
                )
        except Exception as e:
            st.error(f"Lỗi khi ghi dữ liệu: {str(e)}")