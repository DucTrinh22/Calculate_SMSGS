import streamlit as st
import pandas as pd
from gsheet_handler import read_sheet_range, write_sheet_range

# --- CẤU HÌNH GIAO DIỆN STREAMLIT ---
st.title("Phần mềm Tính Tin Nhắn Xổ Số & Đồng bộ Google Sheets")

st.sidebar.header("Cấu hình Google Sheets")
sheet_url = st.sidebar.text_input("Google Sheet URL hoặc Sheet ID")
ws_name = st.sidebar.text_input("Tên Sheet (Worksheet Name)", value="Sheet1")
input_range = st.sidebar.text_input("Dải ô đọc dữ liệu", value="A1:C10")
output_start_cell = st.sidebar.text_input("Ô bắt đầu ghi kết quả", value="D1")

# Khởi tạo session state lưu trữ dữ liệu tính
if "calc_result" not in st.session_state:
    st.session_state["calc_result"] = None

# --- BƯỚC 1: LẤY DỮ LIỆU & TÍNH TOÁN ---
if st.button("📥 1. Lấy dữ liệu từ Sheet & Tính toán"):
    if not sheet_url or not ws_name:
        st.error("Vui lòng điền URL và tên Sheet ở thanh bên trái!")
    else:
        try:
            with st.spinner("Đang đọc dữ liệu từ Google Sheets..."):
                raw_data = read_sheet_range(sheet_url, ws_name, input_range)
            
            # Giả sử dữ liệu đọc về là các dòng tin nhắn:
            # Gộp các ô thành chuỗi tin nhắn hoặc xử lý từng dòng
            st.success(f"Đã đọc thành công {len(raw_data)} dòng dữ liệu!")
            st.write("Dữ liệu thô từ Sheet:", raw_data)

            # --- GỌI HÀM XỬ LÝ/TÍNH TOÁN CỦA BẠN TỪ CODE CŨ ---
            # Ví dụ: nối các dòng thành text để đưa vào hàm parse hiện tại của bạn:
            combined_sms_text = "\n".join([" ".join(str(cell) for cell in row) for row in raw_data])
            
            # [CHÈN HÀM XỬ LÝ TIN NHẮN TỪ APP.PY CỦA BẠN TẠI ĐÂY]
            # Giả sử kết quả trả về là một DataFrame hoặc bảng kết quả:
            # df_result = your_calculation_function(combined_sms_text)
            
            # Ví dụ mẫu bảng kết quả:
            df_result = pd.DataFrame({
                "STT": range(1, len(raw_data) + 1),
                "NoiDungGoc": [str(r) for r in raw_data],
                "KetQuaTinh": ["Đã tính " + str(i) for i in range(1, len(raw_data) + 1)],
                "TongTien": [100000 * i for i in range(1, len(raw_data) + 1)]
            })
            
            st.session_state["calc_result"] = df_result
            st.subheader("Kết quả sau khi tính toán:")
            st.dataframe(df_result)
            
        except Exception as e:
            st.error(f"Lỗi khi xử lý: {str(e)}")

# --- BƯỚC 2: GHI NGƯỢC LẠI GOOGLE SHEET ---
if st.session_state["calc_result"] is not None:
    if st.button("📤 2. Ghi kết quả về Google Sheet"):
        try:
            df_to_export = st.session_state["calc_result"]
            
            # Chuyển DataFrame thành dạng list 2 chiều bao gồm tiêu đề
            values_to_write = [df_to_export.columns.tolist()] + df_to_export.astype(str).values.tolist()
            
            with st.spinner("Đang ghi dữ liệu vào Google Sheet..."):
                write_sheet_range(sheet_url, ws_name, output_start_cell, values_to_write)
                
            st.success(f"✅ Đã ghi thành công kết quả từ ô {output_start_cell}!")
        except Exception as e:
            st.error(f"Lỗi khi ghi dữ liệu: {str(e)}")