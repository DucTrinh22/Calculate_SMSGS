import streamlit as st  # <--- MUST ADD THIS LINE
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
        # Fallback to local file if running offline
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
    return gspread.authorize(creds)

def read_sheet_range(sheet_id_or_url, worksheet_name, cell_range="A1:A20"):
    client = get_gsheet_client()
    sh = client.open_by_key(sheet_id_or_url) if not sheet_id_or_url.startswith("http") else client.open_by_url(sheet_id_or_url)
    ws = sh.worksheet(worksheet_name)
    data = ws.get(cell_range)
    return data

def write_sheet_range(sheet_id_or_url, worksheet_name, start_cell, values):
    client = get_gsheet_client()
    sh = client.open_by_key(sheet_id_or_url) if not sheet_id_or_url.startswith("http") else client.open_by_url(sheet_id_or_url)
    ws = sh.worksheet(worksheet_name)
    ws.update(range_name=start_cell, values=values)
    return True