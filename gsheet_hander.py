import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gsheet_client(credentials_path="credentials.json"):
    """Khởi tạo kết nối tới Google Sheets"""
    creds = Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client

def read_sheet_range(sheet_id_or_url, worksheet_name, cell_range="A1:C10"):
    """
    Đọc dữ liệu từ 1 range chỉ định (ví dụ: A1:C10).
    Trả về list of lists.
    """
    client = get_gsheet_client()
    sh = client.open_by_key(sheet_id_or_url) if not sheet_id_or_url.startswith("http") else client.open_by_url(sheet_id_or_url)
    ws = sh.worksheet(worksheet_name)
    data = ws.get(cell_range)
    return data

def write_sheet_range(sheet_id_or_url, worksheet_name, start_cell, values):
    """
    Ghi dữ liệu (list 2 chiều) trở lại Google Sheet bắt đầu từ start_cell (ví dụ 'D1').
    """
    client = get_gsheet_client()
    sh = client.open_by_key(sheet_id_or_url) if not sheet_id_or_url.startswith("http") else client.open_by_url(sheet_id_or_url)
    ws = sh.worksheet(worksheet_name)
    ws.update(range_name=start_cell, values=values)
    return True