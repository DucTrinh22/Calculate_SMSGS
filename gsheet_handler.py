import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gsheet_client():
    if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPES
        )
    else:
        # Fallback khi chạy thử ở máy local
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds)

def read_sheet_range(sheet_id_or_url: str, worksheet_name: str, cell_range="A1:A50"):
    client = get_gsheet_client()
    target = sheet_id_or_url.strip()
    sh = client.open_by_url(target) if target.startswith("http") else client.open_by_key(target)
    ws = sh.worksheet(worksheet_name.strip())
    return ws.get(cell_range.strip())

def write_sheet_range(sheet_id_or_url: str, worksheet_name: str, start_cell: str, values: list):
    client = get_gsheet_client()
    target = sheet_id_or_url.strip()
    sh = client.open_by_url(target) if target.startswith("http") else client.open_by_key(target)
    ws = sh.worksheet(worksheet_name.strip())
    # Cú pháp chuẩn tương thích tốt với gspread
    ws.update(values=values, range_name=start_cell.strip())
    return True