import pandas as pd
import streamlit as st
from core.parser import SMSParser
from gsheet_handler import read_sheet_range, write_sheet_range

# ==============================================================================
# 🟢 ZONE 1: HÀM XỬ LÝ GỌI PARSER
# ==============================================================================


def process_xoso_sms(text: str, parser_instance: SMSParser):
    clean_text = str(text).strip()
    if not clean_text:
        return None

    # Gọi hàm parse trong core/parser.py
    res = parser_instance.parse(clean_text)

    # Tóm tắt các cược
    chi_tiet = "; ".join(
        [
            f"{c.ten_loai}: {','.join(c.so_danh)} ({c.tien_format})"
            for c in res.danh_sach_cuoc
        ]
    )

    return {
        "NoiDungGoc": res.nguon,
        "TrangThai": "Hợp lệ" if res.hop_le else "Lỗi",
        "TenDai": ", ".join(res.ten_dai) if res.ten_dai else "",
        "TienXac": res.tong_tien,
        "ChiTietCuoc": chi_tiet,
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
input_range = st.sidebar.text_input("Dải ô đọc dữ liệu", value="A1:A20")
output_start_cell = st.sidebar.text_input("Ô bắt đầu ghi kết quả", value="C1")

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

                # Khởi tạo parser cho lượt tính này (để nhớ đài qua các dòng)
                sms_parser = SMSParser()

                calculated_rows = []
                for row in raw_data:
                    sms_line = str(row[0]) if len(row) > 0 else ""
                    if sms_line.strip():
                        row_result = process_xoso_sms(
                            sms_line, parser_instance=sms_parser
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