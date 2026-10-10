# File: components/input_form.py
import streamlit as st
import re
from core.parser import SMSParser 
from config.constants import DAI_XO_SO, LOAI_CUOC
import streamlit.components.v1 as components

def set_cursor_js(position):
    """
    Hàm Inject JS để đặt con trỏ tại vị trí 'position'
    """
    js_code = f"""
    <script>
        function setCursor() {{
            var textAreas = window.parent.document.querySelectorAll('textarea');
            if (textAreas.length > 0) {{
                var ta = textAreas[0];
                ta.focus();
                ta.setSelectionRange({position}, {position});
                ta.blur(); // Mẹo để trình duyệt cuộn tới vị trí đó
                ta.focus();
            }}
        }}
        setTimeout(setCursor, 100); // Đợi 1 chút để UI ổn định
    </script>
    """
    components.html(js_code, height=0)
    
def highlight_syntax(text):
    """
    Hàm phân tích nhanh để tô màu HTML (Giữ nguyên logic cũ)
    """
    if not text: return ""
    
    text_lower = text.lower()
    # 1. Coi dấu chấm, phẩy, gạch chéo như khoảng trắng để tách token chuẩn hơn
    text_lower = re.sub(r'[,:;./-]', ' ', text_lower)
    
    # 2. Tách chữ và số nhưng TRỪ các đơn vị tiền tệ ra (để 10n không bị tách)
    # Tách Chữ + Số: da20 -> da 20
    text_lower = re.sub(r'([a-z]+)(\d)', r'\1 \2', text_lower)
    # Tách Số + Chữ (nếu chữ đó không phải là n, k, d, đ...): 20tp -> 20 tp
    text_lower = re.sub(r'(\d)(?!(?:n|k|d|đ|tr|ng|ngan)\b)([a-z]+)', r'\1 \2', text_lower)
    
    tokens = text_lower.split()
    
    all_dai = set()
    for shorts in DAI_XO_SO.values():
        for s in shorts: all_dai.add(s.lower())
    # Thêm các đài gộp vào danh sách nhận diện
    all_dai.update(['dmn', 'dmt', 'dmb', 'mb'])
        
    all_bet = set(LOAI_CUOC.keys())
    all_bet.update(['blo', 'b', 'x', 'da', 'dá', 'dax', 'daxien', 'bao', 'dd', 'dau', 'duoi', 'bdao', 'kéo', 'keo', 'kèo'])
    
    html_out = []
    prev_is_num = False 
    
    money_units = ['n', 'k', 'd', 'đ', 'tr', 'ng']

    for token in tokens:
        color = "black"
        style = ""
        is_num = False
        token_display = token 
        
        # Kiểm tra tiền (VD: 20n, 0.5n)
        if re.match(r'^\d+(\.\d+)?[nkdđ(tr)(ng)(ngan)]+$', token) or token in money_units:
            color = "#d63031" # Đỏ
            style = "font-weight:bold;"
        # Kiểm tra số đánh (VD: 95, 75)
        elif re.match(r'^\d+$', token):
            color = "#10d8b0" # Xanh lục
            style = "font-weight:bold;"
            is_num = True
        # Kiểm tra Đài hoặc Loại cược
        elif token in all_dai or token in all_bet:
            if token in all_dai: 
                color = "#0931e3" # Xanh dương
                token_display = token.upper()
            else: 
                color = "#e17055" # Cam
            style = "font-weight:bold;"
        else:
            # Từ lạ
            color = "red"
            style = "font-weight: bold; text-decoration: underline wavy red; background-color: #ffeaa7;"
            token_display = f"{token} (?)"

        html_out.append(f'<span style="color:{color}; {style} margin-right:4px; font-family: monospace;">{token_display}</span>')
        prev_is_num = is_num

    return " ".join(html_out)

def render_input_form():
    """
    Hiển thị vùng nhập liệu và style viền (stroke)
    """
    st.subheader("📩 Nhập tin nhắn SMS cược xổ số")
    
    # CSS tạo viền và chỉnh font
    st.markdown("""
        <style>
        .stTextArea textarea {
            font-size: 25px !important; 
            font-family: 'Courier New', monospace;
            line-height: 1.3 !important;
            border: 3px solid #4b7bec !important; 
            border-radius: 8px !important;
            padding: 10px !important;
        }
        .stTextArea textarea:focus {
            border-color: #eb3b5a !important;
            box-shadow: 0 0 5px rgba(235, 59, 90, 0.5);
        }
        </style>
    """, unsafe_allow_html=True)
    
    raw_text = st.text_area(
        "Label ẩn",
        height=250,
        placeholder="Ví dụ: tp 10 20 blo 5n",
        label_visibility="collapsed",
        key="input_sms_area"
    )
    
    lines = [raw_text.strip()] if raw_text.strip() else []
    return raw_text, lines

def render_syntax_check(raw_text, lines):
    # Nếu không có nội dung thì thoát
    if not raw_text.strip():
        return

    parser = SMSParser()
    
    # [QUAN TRỌNG] Tách văn bản gốc thành các dòng nguyên bản (giữ nguyên khoảng trắng)
    raw_lines_list = raw_text.split('\n')
    
    # Mapping: Dòng hiển thị (đã strip) ứng với index nào trong raw_lines_list
    # Vì lines bỏ qua dòng trống, ta cần map lại để tính vị trí cho đúng
    line_map = []
    idx_raw = 0
    for l in lines:
        while idx_raw < len(raw_lines_list) and not raw_lines_list[idx_raw].strip():
            idx_raw += 1
        if idx_raw < len(raw_lines_list):
            line_map.append(idx_raw)
            idx_raw += 1
            
    with st.expander("🔍 KIỂM TRA LỖI & CÚ PHÁP (Click để xem)", expanded=True):
        for i, line in enumerate(lines):
            parse_result = parser.parse(line)
            highlighted_html = highlight_syntax(line)
            
            # Style khung
            border_color = "red" if not parse_result.hop_le else "#ccc"
            bg_color = "#fff0f0" if not parse_result.hop_le else "#f8f9fa"
            
            st.markdown(f"""
            <div style='background-color:{bg_color}; border-left: 5px solid {border_color}; padding:10px; border-radius:5px; margin-bottom:8px;'>
                <div style='font-size: 16px; margin-bottom: 4px;'>{highlighted_html}</div>
            """, unsafe_allow_html=True)

            if not parse_result.hop_le:
                col_err, col_btn = st.columns([0.85, 0.15])
                
                with col_err:
                    st.markdown(f"<div style='color: red; font-weight: bold; font-size: 14px;'>❌ {parse_result.loi}</div>", unsafe_allow_html=True)
                
                with col_btn:
                    # Tạo key duy nhất
                    if st.button("👉 Sửa", key=f"btn_fix_{i}", help="Nhấn để con trỏ nhảy tới vị trí lỗi"):
                        
                        # --- THUẬT TOÁN TÍNH VỊ TRÍ ---
                        
                        # 1. Xác định dòng nguyên bản (Raw Line) tương ứng
                        # Nếu map lỗi thì lấy theo index, nhưng thường map sẽ chuẩn
                        current_raw_idx = line_map[i] if i < len(line_map) else i
                        current_raw_line = raw_lines_list[current_raw_idx]
                        
                        # 2. Tính tổng độ dài các ký tự ĐỨNG TRƯỚC dòng này
                        # (Bao gồm cả ký tự xuống dòng \n của các dòng trước)
                        start_offset = 0
                        for k in range(current_raw_idx):
                            start_offset += len(raw_lines_list[k]) + 1 
                        
                        # 3. Trích xuất TẤT CẢ các token trong dấu nháy đơn từ thông báo lỗi
                        # Ví dụ: "Cược 'da' lỗi số '433'" -> tokens = ['da', '433']
                        error_tokens = re.findall(r"'([^']*)'", parse_result.loi or "")
                        
                        target_token = ""
                        match_pos_end = -1
                        
                        # Chiến thuật tìm kiếm:
                        # Ưu tiên tìm token cuối cùng trong thông báo lỗi (thường là giá trị cụ thể bị sai)
                        # Nếu token đó tồn tại trong dòng input, lấy vị trí ngay sau nó.
                        found_match = False
                        
                        # Duyệt ngược từ token cuối cùng lên đầu (ưu tiên số bị sai hơn là loại cược)
                        for token in reversed(error_tokens):
                            # Tìm kiếm token trong dòng hiện tại (IGNORECASE để bắt kg/KG)
                            # re.escape để xử lý nếu token có ký tự đặc biệt
                            pattern = re.compile(re.escape(token), re.IGNORECASE)
                            
                            # Tìm tất cả các vị trí xuất hiện
                            matches = list(pattern.finditer(current_raw_line))
                            
                            if matches:
                                # Lấy vị trí xuất hiện ĐẦU TIÊN trong dòng (hoặc logic khác nếu cần)
                                # match.end() là vị trí con trỏ ngay sau từ đó
                                match_pos_end = matches[0].end()
                                if match_pos_end < len(current_raw_line):
                                    next_char = current_raw_line[match_pos_end]
                                    if next_char in ['.', ',', ';']:
                                        match_pos_end += 1
                                found_match = True
                                break # Đã tìm thấy từ khóa quan trọng nhất, dừng lại
                        
                        # 4. Tính toán vị trí cuối cùng
                        if found_match:
                            final_pos = start_offset + match_pos_end
                        else:
                            # Fallback: Nếu không tìm thấy từ nào khớp (hiếm gặp), đặt cuối dòng
                            final_pos = start_offset + len(current_raw_line)
                        
                        # Gọi JS
                        set_cursor_js(final_pos)

            else:
                tom_tat = f"✅ Hợp lệ: {len(parse_result.danh_sach_cuoc)} cược | {parse_result.tong_tien_format}"
                st.markdown(f"<div style='color: green; font-size: 13px; font-style: italic;'>{tom_tat}</div>", unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)