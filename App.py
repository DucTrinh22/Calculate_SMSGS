import streamlit as st
import pandas as pd
from gsheet_handler import read_sheet_range, write_sheet_range

# ==============================================================================
# 🟢 ZONE 1: PASTE YOUR CALCULATION LOGIC / FUNCTIONS HERE
# ==============================================================================
# Paste all helper functions, regex parsing, rate dictionaries, or rules from 
# your original Xoso_sms script right here.

def process_xoso_sms(text: str):
    """
    PASTE YOUR CALCULATION CODE HERE.
    
    Parameters:
        text (str): The raw SMS line (e.g., "de 45 50k, lo 23 100d")
        
    Returns:
        dict or list: The calculated breakdown (e.g., points, cost, prize)
    """
    # --- [YOUR CALCULATION LOGIC STARTS HERE] ---
    
    # Example placeholder: replace this with your real parsing formulas
    # clean_text = text.strip()
    # tien_xac = ...
    # tien_trung = ...
    # lai_lo = ...
    
    # Return a dictionary of the outputs for this message:
    return {
        "NoiDungGoc": text,
        "TienXac": 100000,   # Replace with your calculated cost
        "TienTrung": 0,      # Replace with your calculated win
        "LaiLo": -100000     # Replace with your calculated profit/loss
    }
    # --- [YOUR CALCULATION LOGIC ENDS HERE] ---


# ==============================================================================
# ⚙️ ZONE 2: STREAMLIT UI & GOOGLE SHEET CONFIGURATION
# ==============================================================================
st.set_page_config(page_title="Tính Tin Nhắn Xổ Số", layout="wide")
st.title("Phần mềm Tính Tin Nhắn Xổ Số & Đồng bộ Google Sheets")

st.sidebar.header("Cấu hình Google Sheets")

# Paste your default Google Sheet URL / ID here so you don't have to re-enter it:
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1gD4xNTKf61tiDlI9an8suM82-84oU5kC5Xj0qb3yDPk/edit?usp=sharing"
sheet_url = st.sidebar.text_input("Google Sheet URL hoặc Sheet ID", value=DEFAULT_SHEET_URL)
ws_name = st.sidebar.text_input("Tên Sheet (Worksheet Name)", value="Sheet1")
input_range = st.sidebar.text_input("Dải ô đọc dữ liệu", value="A1:A20")
output_start_cell = st.sidebar.text_input("Ô bắt đầu ghi kết quả", value="B1")

# Initialize session state to retain results across button clicks
if "calc_result" not in st.session_state:
    st.session_state["calc_result"] = None


# ==============================================================================
# 🟡 ZONE 3: FETCH FROM SHEET AND RUN YOUR CALCULATION
# ==============================================================================
if st.button("📥 1. Lấy dữ liệu từ Sheet & Tính toán"):
    if not sheet_url or not ws_name:
        st.error("Vui lòng điền URL và tên Sheet ở thanh bên trái!")
    else:
        try:
            with st.spinner("Đang đọc dữ liệu từ Google Sheets..."):
                # raw_data is a list of lists, e.g. [['de 45 50k'], ['lo 23 100d'], ...]
                raw_data = read_sheet_range(sheet_url, ws_name, input_range)

            if not raw_data:
                st.warning(f"Không tìm thấy dữ liệu trong dải ô {input_range}!")
            else:
                st.success(f"Đã đọc thành công {len(raw_data)} dòng dữ liệu!")

                # --- HOW TO RUN YOUR CALCULATION FUNCTION ON THE SHEET DATA ---
                calculated_rows = []

                for row in raw_data:
                    # Get the SMS string from column A
                    sms_line = str(row[0]) if len(row) > 0 else ""

                    if sms_line.strip():
                        # Call your calculation function from ZONE 1:
                        row_result = process_xoso_sms(sms_line)
                        calculated_rows.append(row_result)

                # Convert the final results to a DataFrame
                df_result = pd.DataFrame(calculated_rows)

                # Save to session_state so it is available for Zone 4
                st.session_state["calc_result"] = df_result

                st.subheader("📋 Bảng kết quả sau khi tính:")
                st.dataframe(df_result, use_container_width=True)

        except Exception as e:
            st.error(f"Lỗi khi đọc/tính toán: {str(e)}")


# ==============================================================================
# 📤 ZONE 4: WRITE THE RESULTS BACK TO GOOGLE SHEETS
# ==============================================================================
if st.session_state["calc_result"] is not None:
    st.divider()
    if st.button("📤 2. Ghi kết quả về Google Sheet"):
        try:
            df_to_export = st.session_state["calc_result"]

            # Convert DataFrame into a 2D list (including header titles)
            values_to_write = [df_to_export.columns.tolist()] + df_to_export.astype(str).values.tolist()

            with st.spinner("Đang ghi dữ liệu vào Google Sheet..."):
                write_sheet_range(sheet_url, ws_name, output_start_cell, values_to_write)

            st.success(f"✅ Đã ghi thành công kết quả bắt đầu từ ô **{output_start_cell}**!")
        except Exception as e:
            st.error(f"Lỗi khi ghi dữ liệu: {str(e)}")