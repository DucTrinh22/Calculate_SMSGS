import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from bs4 import BeautifulSoup

# Page setup
st.set_page_config(page_title="SMS Calculator", layout="centered")
st.title("📊 SMS Google Sheet Calculator")

# 1. Connect to Google Sheets using Streamlit Secrets
@st.cache_resource
def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # We load credentials securely from st.secrets
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    return gspread.authorize(credentials)

try:
    gc = get_gsheet_client()

    # Paste your Spreadsheet ID or Sheet Name
    SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"  # Replace with your Sheet ID
    TAB_NAME = "SMS"

    # Open the spreadsheet and the specific tab
    sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(TAB_NAME)

    # 2. Read existing data
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    st.subheader("Current Data from Sheet:")
    st.dataframe(df)

    # 3. Calculation and Write Back
    if st.button("Run Calculation & Update Sheet"):
        with st.spinner("Calculating and updating Google Sheet..."):
            
            # --- EXAMPLE CALCULATION ---
            # Suppose you want to calculate something (e.g. character count, cost, etc.)
            # Replace this logic with your exact SMS formula:
            results = []
            for index, row in df.iterrows():
                # Example: Calculate a value based on Column A / Row
                calc_val = f"Done - Row {index + 1}"
                results.append([calc_val])

            # 4. Write back to a specific range (e.g., Column C, rows C2 down to C...)
            end_row = 1 + len(results)
            target_range = f"C2:C{end_row}"   # Change 'C' to your destination column
            
            # Update the range in Google Sheet
            sheet.update(range_name=target_range, values=results)

            st.success(f"Successfully updated range {target_range} in tab '{TAB_NAME}'!")

except Exception as e:
    st.error(f"Error: {e}")