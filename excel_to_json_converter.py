# excel_to_json_converter.py
import streamlit as st
import json
import re
from datetime import datetime, date
import pytz
import pandas as pd

# 필수 모듈 로딩
try:
    import google_drive_helper as gdrive
    import data # data.py의 METHOD_OPTIONS, DEFAULT_STORAGE_TYPE 등을 위함
except ImportError as e:
    st.error(f"필수 모듈 로딩 실패: {e}. (google_drive_helper.py, data.py 등을 현재 스크립트와 같은 폴더에 위치시켜주세요)")
    st.stop()

# 시간대 설정
try:
    KST = pytz.timezone("Asia/Seoul")
except pytz.UnknownTimeZoneError:
    st.warning("Asia/Seoul 시간대를 찾을 수 없어 UTC를 사용합니다. 날짜 처리에 영향이 있을 수 있습니다.")
    KST = pytz.utc

# --- MOVE_TYPE_OPTIONS 정의 ---
# data.item_definitions의 키에서 직접 가져와서 스크립트 내 지역 변수로 정의
MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions and isinstance(data.item_definitions, dict) else ["가정 이사 🏠", "사무실 이사 🏢"]


# 기본값 설정
DEFAULT_CUSTOMER_NAME = "무명"
# 이제 스크립트 내에 정의된 MOVE_TYPE_OPTIONS 사용
DEFAULT_MOVE_TYPE = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠"
DEFAULT_STORAGE_TYPE = data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦"
DEFAULT_FROM_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
DEFAULT_TO_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
STAIR_METHOD_DEFAULT = "계단 🚶" # 요청된 기본 작업 방법

TODAY_ISO_DATE = datetime.now(KST).date().isoformat()

# --- 공통 헬퍼 함수 ---
def parse_date_flexible(date_str_input, current_year):
    if isinstance(date_str_input, (datetime, date)):
        return date_str_input.strftime('%Y-%m-%d')
    if not date_str_input or str(date_str_input).strip().lower() == "미정":
        return TODAY_ISO_DATE
    date_str = str(date_str_input).strip()
    date_str = re.split(r'\s+[0-9]{1,2}\s*[:시]', date_str)[0].strip()
    patterns = [
        (r'(\d{4})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*(일?)', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{1,2})\s*[-/월\.]\s*(\d{1,2})\s*(일?)', lambda m: (current_year, int(m.group(1)), int(m.group(2)))), # "06월 30일" 처리 가능
        (r'(\d{2})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*(일?)', lambda m: (2000 + int(m.group(1)), int(m.group(2)), int(m.group(3))))
    ]
    for pattern, extractor in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                year, month, day = extractor(match)
                # Ensure the matched part is the whole date string part
                if len(match.group(0).replace(" ","")) == len(date_str.replace(" ","")): # 공백제거후 길이비교 (유연성)
                     return datetime(year, month, day).strftime('%Y-%m-%d')
            except ValueError:
                continue
    return TODAY_ISO_DATE

def normalize_phone_number_for_filename(phone_str):
    if not phone_str or not isinstance(phone_str, str): return None
    return "".join(filter(str.isdigit, phone_str))

def get_default_state():
    # 스크립트 상단에 정의된 MOVE_TYPE_OPTIONS와 DEFAULT_MOVE_TYPE 사용
    return {
        "moving_date": TODAY_ISO_DATE, "customer_name": DEFAULT_CUSTOMER_NAME, "customer_phone": "",
        "base_move_type": DEFAULT_MOVE_TYPE, "from_location": "", "to_location": "", "special_notes": "",
        "from_floor": "", "to_floor": "",
        "from_method": DEFAULT_FROM_METHOD, "to_method": DEFAULT_TO_METHOD,
        "is_storage_move": False, "storage_type": DEFAULT_STORAGE_TYPE,
        "apply_long_distance": False, "has_via_point": False,
        "deposit_amount": 0, "adjustment_amount": 0,
        "issue_tax_invoice": False, "card_payment": False, "remove_base_housewife": False,
        "dispatched_1t":0, "dispatched_2_5t":0, "dispatched_3_5t":0, "dispatched_5t":0,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "waste_tons_input": 0.5, "has_waste_check": False,
        "uploaded_image_paths": [],
        "vehicle_select_radio": "자동 추천 차량 사용", "manual_vehicle_select_value": None,
        "final_selected_vehicle": None, "recommended_vehicle_auto": None,
        "storage_duration": 1, "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "via_point_location": "", "via_point_method": DEFAULT_FROM_METHOD,
        "via_point_floor": "", "via_point_surcharge": 0,
        "regional_ladder_surcharge": 0,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        "total_volume": 0.0, "total_weight": 0.0,
        "tab3_deposit_amount": 0, "tab3_adjustment_amount": 0, "tab3_regional_ladder_surcharge": 0,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "prev_final_selected_vehicle": None,
        "gdrive_search_term": "", "gdrive_search_results": [],
        "gdrive_file_options_map": {}, "gdrive_selected_filename": None, "gdrive_selected_file_id": None,
    }

def extract_floor_from_address_enhanced(address_str):
    if not address_str or not isinstance(address_str, str):
        return address_str if address_str else "", ""
    address_cleaned = address_str.strip()
    parsed_floor = ""
    address_part = address_cleaned
    ho_match = re.search(r'(\d+)\s*호(?!\d)', address_cleaned)
    if ho_match:
        ho_number_str = ho_match.group(1)
        if len(ho_number_str) > 2: parsed_floor = ho_number_str[:-2]
        elif len(ho_number_str) > 0: parsed_floor = ho_number_str
        
        if parsed_floor:
            address_part = address_cleaned[:ho_match.start(0)].strip()
            return address_part, parsed_floor
    
    floor_ending_match = re.search(r'^(.*?)(\s*(-?\d+)\s*(층|F|f))$', address_cleaned, re.IGNORECASE)
    if floor_ending_match:
        address_part = floor_ending_match.group(1).strip()
        parsed_floor = floor_ending_match.group(3)
        return address_part, parsed_floor
    return address_cleaned, ""

# --- 텍스트 입력 처리 함수 (사용자 요청사항 반영) ---
PHONE_REGEX_TEXT = re.compile(r'(01[016789]-?\d{3,4}-?\d{4}|0\d{1,2}-?\d{3,4}-?\d{4})')
MOVE_TYPE_KEYWORDS_TEXT = {"가정": ["가정", "가"], "사무실": ["사무실", "사"]}

def parse_line_to_json_flexible(line_text, current_year, line_number_display=""):
    state = get_default_state()
    original_line = line_text.strip()
    if not original_line: return None, None, f"{line_number_display}빈 줄"

    phone_match = PHONE_REGEX_TEXT.search(original_line)
    if not phone_match: return None, None, f"{line_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = phone_match.group(0).strip()
    filename_phone_part = normalize_phone_number_for_filename(state["customer_phone"])
    if not filename_phone_part: return None, None, f"{line_number_display}유효하지 않은 전화번호"

    text_before_phone = original_line[:phone_match.start()].strip()
    text_after_phone = original_line[phone_match.end():].strip()

    parts_before_phone = [p.strip() for p in text_before_phone.split(maxsplit=2) if p.strip()]
    date_found = False
    if parts_before_phone:
        date_candidate_1 = parts_before_phone[0]
        parsed_date_1 = parse_date_flexible(date_candidate_1, current_year)
        if parsed_date_1 != TODAY_ISO_DATE or \
           (parsed_date_1 == TODAY_ISO_DATE and date_candidate_1 and date_candidate_1.lower()!="미정"):
            state["moving_date"] = parsed_date_1
            state["customer_name"] = " ".join(parts_before_phone[1:]) if len(parts_before_phone) > 1 else DEFAULT_CUSTOMER_NAME
            date_found = True
        elif len(parts_before_phone) > 1:
            date_candidate_2 = parts_before_phone[0] + " " + parts_before_phone[1]
            parsed_date_2 = parse_date_flexible(date_candidate_2, current_year)
            if parsed_date_2 != TODAY_ISO_DATE or \
               (parsed_date_2 == TODAY_ISO_DATE and date_candidate_2 and date_candidate_2.lower()!="미정"):
                state["moving_date"] = parsed_date_2
                state["customer_name"] = " ".join(parts_before_phone[2:]) if len(parts_before_phone) > 2 else DEFAULT_CUSTOMER_NAME
                date_found = True
    
    if not date_found:
        state["customer_name"] = text_before_phone if text_before_phone else DEFAULT_CUSTOMER_NAME
        state["moving_date"] = TODAY_ISO_DATE
    if not state["customer_name"].strip():
        state["customer_name"] = DEFAULT_CUSTOMER_NAME

    raw_parts_after_phone = re.split(r'\s{2,}|\t+', text_after_phone)
    parts_after_phone = [p.strip() for p in raw_parts_after_phone if p and p.strip()]

    if not parts_after_phone:
        return None, None, f"{line_number_display}이사 종류 및 주소 정보 없음 (필수)"

    # 이사 종류 파싱 시 MOVE_TYPE_OPTIONS (스크립트 상단에 정의된 변수) 사용
    if parts_after_phone[0].lower() == "가":
        state["base_move_type"] = next((opt for opt in MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
        parts_after_phone.pop(0)
    elif parts_after_phone[0].lower() == "사":
        state["base_move_type"] = next((opt for opt in MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE)
        parts_after_phone.pop(0)

    if not parts_after_phone:
        return None, None, f"{line_number_display}출발지 주소 정보 없음 (필수)"

    from_loc_str_parts = []
    from_loc_found = False
    for i, part in enumerate(parts_after_phone):
        from_loc_str_parts.append(part)
        current_from_loc_candidate = " ".join(from_loc_str_parts)
        ho_match = re.search(r'(\d+)호$', current_from_loc_candidate)
        if ho_match:
            ho_digits = ho_match.group(1)
            state["from_location"] = current_from_loc_candidate[:ho_match.start(0)].strip()
            if len(ho_digits) > 2:
                state["from_floor"] = ho_digits[:-2]
            else:
                state["from_floor"] = ""
            parts_after_phone = parts_after_phone[i+1:]
            from_loc_found = True
            break
    
    if not from_loc_found:
        return None, None, f"{line_number_display}출발지 주소에서 '...호' 패턴을 찾을 수 없습니다."

    if parts_after_phone:
        last_part_candidate = parts_after_phone[-1]
        is_last_part_time_info = False
        if re.match(r'^[월화수목금토일]', last_part_candidate) or \
           (re.search(r'\d', last_part_candidate) and last_part_candidate.endswith('시')):
            is_last_part_time_info = True

        if is_last_part_time_info:
            if len(parts_after_phone) > 1:
                to_location_str = " ".join(parts_after_phone[:-1])
                state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_location_str)
        else:
            to_location_str = " ".join(parts_after_phone)
            state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_location_str)
            
    if hasattr(data, 'METHOD_OPTIONS') and STAIR_METHOD_DEFAULT in data.METHOD_OPTIONS:
        state["from_method"] = STAIR_METHOD_DEFAULT
        state["to_method"] = STAIR_METHOD_DEFAULT
    else:
        state["from_method"] = DEFAULT_FROM_METHOD
        state["to_method"] = DEFAULT_TO_METHOD
        if 'special_notes' not in state or not state['special_notes']: state['special_notes'] = ""
        state['special_notes'] += " (참고: 요청된 '계단' 작업방법을 찾을 수 없어 기본값 사용)"

    if not state.get("from_location"):
        return None, None, f"{line_number_display}출발지 주소 최종 파싱 실패."
        
    return state, filename_phone_part + ".json", None

# --- 엑셀 입력 처리 함수 ---
COLUMN_ALIASES_EXCEL = {
    'moving_date': ['날짜', '이사날짜', '일자'],
    'customer_name': ['고객명', '이름', '성함', '상호'],
    'customer_phone': ['전화번호', '연락처', '휴대폰번호', '전화', '핸드폰', 'H.P', 'HP'],
    'base_move_type': ['이사종류', '구분', '종류'],
    'from_location': ['출발지주소', '출발지', '출발주소', '출발'],
    'from_floor': ['층수', '출발지 층수', '출발층수', '출발 층'],
    'to_location': ['도착지주소', '도착지', '도착주소', '도착'],
    'to_floor': ['도착지 층수', '도착층수', '도착 층'],
    'special_notes': ['특이사항', '요구사항', '희망사항', '건의', '메모', '비고', '참고사항'],
}
def get_column_value(row, field_name, aliases, default=""):
    all_possible_names = [field_name.lower()] + [a.lower() for a in aliases.get(field_name, [])]
    row_index_lower = {str(idx_item).lower(): idx_item for idx_item in row.index}
    for alias_lower in all_possible_names:
        if alias_lower in row_index_lower and pd.notna(row[row_index_lower[alias_lower]]):
            return str(row[row_index_lower[alias_lower]]).strip()
    return default

def parse_excel_row_to_json(row, current_year, row_number_display=""):
    state = get_default_state()
    if row.isnull().all() or all(str(x).strip() == "" for x in row if pd.notna(x)):
        return None, None, f"{row_number_display}빈 행"

    moving_date_raw = get_column_value(row, 'moving_date', COLUMN_ALIASES_EXCEL)
    state["moving_date"] = parse_date_flexible(moving_date_raw, current_year)
    log_info_for_date = ""
    if moving_date_raw and moving_date_raw.strip().lower() != "미정" and state["moving_date"] == TODAY_ISO_DATE:
        log_info_for_date = f"제공된 날짜 '{moving_date_raw}'가 오늘 날짜로 처리됨 (형식/내용 확인 필요)."

    customer_name_raw = get_column_value(row, 'customer_name', COLUMN_ALIASES_EXCEL)
    if customer_name_raw and customer_name_raw.lower() != "미정": state["customer_name"] = customer_name_raw
    else: state["customer_name"] = DEFAULT_CUSTOMER_NAME
    if "보관" in state["customer_name"]:
        state["is_storage_move"] = True; state["storage_type"] = DEFAULT_STORAGE_TYPE

    customer_phone_raw = get_column_value(row, 'customer_phone', COLUMN_ALIASES_EXCEL)
    if not customer_phone_raw: return None, None, f"{row_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = customer_phone_raw
    filename_phone_part = normalize_phone_number_for_filename(customer_phone_raw)
    if not filename_phone_part: return None, None, f"{row_number_display}유효하지 않은 전화번호"

    move_type_raw = get_column_value(row, 'base_move_type', COLUMN_ALIASES_EXCEL)
    if move_type_raw: # 이사 종류 파싱 시 MOVE_TYPE_OPTIONS (스크립트 상단에 정의된 변수) 사용
        move_type_char = move_type_raw.strip().lower()
        if any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["가정"]) or "가정" in move_type_char:
            state["base_move_type"] = next((opt for opt in MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
        elif any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["사무실"]) or "사무실" in move_type_char:
            state["base_move_type"] = next((opt for opt in MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE)

    from_location_raw = get_column_value(row, 'from_location', COLUMN_ALIASES_EXCEL)
    if not from_location_raw: return None, None, f"{row_number_display}출발지 주소 없음 (필수)"
    from_floor_raw_col = get_column_value(row, 'from_floor', COLUMN_ALIASES_EXCEL)
    if from_floor_raw_col:
        state["from_floor"] = "".join(filter(str.isdigit, from_floor_raw_col))
        state["from_location"] = from_location_raw
    else:
        state["from_location"], state["from_floor"] = extract_floor_from_address_enhanced(from_location_raw)

    to_location_raw = get_column_value(row, 'to_location', COLUMN_ALIASES_EXCEL)
    to_floor_raw_col = get_column_value(row, 'to_floor', COLUMN_ALIASES_EXCEL)
    if to_location_raw or to_floor_raw_col:
        if to_floor_raw_col:
            state["to_floor"] = "".join(filter(str.isdigit, to_floor_raw_col))
            if to_location_raw: state["to_location"] = to_location_raw
        elif to_location_raw:
             state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_location_raw)

    state["special_notes"] = get_column_value(row, 'special_notes', COLUMN_ALIASES_EXCEL)
    if log_info_for_date and state["special_notes"]: state["special_notes"] = log_info_for_date + " " + state["special_notes"]
    elif log_info_for_date: state["special_notes"] = log_info_for_date

    if not state.get("from_location"):
        return None, None, f"{row_number_display}출발지 누락 (재확인 필요)"
    return state, filename_phone_part + ".json", None

# --- Streamlit UI ---
st.set_page_config(page_title="이사정보 JSON 변환기", layout="wide")
st.title("🚚 이사 정보 JSON 변환 및 Drive 저장")
st.caption("텍스트 또는 Excel 파일로 된 이사 정보를 분석하여 JSON 파일로 변환하고 Google Drive에 저장합니다.")

input_method = st.radio("입력 방식 선택:", ('텍스트 직접 입력', 'Excel 파일 업로드'), horizontal=True)
text_input = ""
uploaded_file = None

if input_method == '텍스트 직접 입력':
    text_input = st.text_area("여기에 이사 정보를 한 줄씩 입력하세요:", height=200,
                              placeholder="예시: 06월 30일 금지원 010-2228-0418 가 광진구 광나루로56길 29 6동 1022호 송파구 잠실동 수 9시-12시")
else:
    uploaded_file = st.file_uploader("변환할 Excel 파일을 업로드하세요.", type=["xlsx", "xls"])
    st.markdown("""
    **Excel 파일 형식 가이드:**
    - 첫 번째 행은 헤더(컬럼명)여야 합니다. 컬럼명은 대소문자를 구분하지 않습니다.
    - **필수 컬럼**: `전화번호`, `출발지주소` (또는 유사어)
    - **선택 컬럼**: `날짜` (인식 가능한 형식, 미입력/인식불가 시 오늘 날짜), `고객명` (미입력시 '무명'), `이사종류`('가'/'사' 또는 '가정', '사무실'), `출발지 층수`, `도착지주소`, `도착지 층수`, `특이사항` (또는 유사어)
    - 층수는 주소에서 "XXX호" 또는 "N층" 패턴으로 자동 인식 시도하며, 명시적 층수 컬럼이 우선합니다. "XXX호"의 경우, "호" 앞부분이 주소로 처리됩니다.
    - 고객명에 "보관"이 포함되면 보관이사로 간주됩니다.
    """)

if st.button("🔄 JSON 변환 및 Google Drive에 저장하기"):
    current_year_for_parsing = datetime.now(KST).year
    success_count = 0; error_count = 0; processed_items = 0; total_items = 0
    all_log_messages = []; items_to_process = []; is_excel_input = False

    if input_method == '텍스트 직접 입력':
        if not text_input.strip(): st.warning("입력된 텍스트가 없습니다.")
        else:
            items_to_process = [line for line in text_input.strip().split('\n') if line.strip()]
            total_items = len(items_to_process)
    elif input_method == 'Excel 파일 업로드':
        is_excel_input = True
        if uploaded_file is None: st.warning("업로드된 파일이 없습니다.")
        else:
            try:
                try: df = pd.read_excel(uploaded_file, engine='openpyxl')
                except Exception: uploaded_file.seek(0); df = pd.read_excel(uploaded_file, engine='xlrd')
                df.columns = [str(col).strip().lower() for col in df.columns] # 컬럼명 소문자 변환 및 공백 제거
                items_to_process = [row for _, row in df.iterrows() if not row.isnull().all()]
                total_items = len(items_to_process)
            except Exception as e: st.error(f"Excel 파일 읽기 중 오류 발생: {e}"); items_to_process = []

    if not items_to_process:
        if text_input.strip() or uploaded_file:
            st.info("변환할 유효한 데이터가 없습니다. 입력 내용을 확인해주세요.")
    else:
        st.subheader("✨ 처리 결과")
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, item_data_row_or_line in enumerate(items_to_process):
            processed_items += 1
            status_obj, filename, error_msg = (None, None, "알 수 없는 입력 형식 또는 처리 오류")
            row_display_prefix = f"엑셀 {df.index[i]+2}행" if is_excel_input and hasattr(df, 'index') and i < len(df.index) else \
                                 (f"엑셀 {i+2}행" if is_excel_input else f"텍스트 {i+1}줄")


            if is_excel_input:
                status_obj, filename, error_msg = parse_excel_row_to_json(item_data_row_or_line, current_year_for_parsing, row_display_prefix + ": ")
            else: # 텍스트 입력
                status_obj, filename, error_msg = parse_line_to_json_flexible(item_data_row_or_line, current_year_for_parsing, row_display_prefix + ": ")

            status_text.text(f"처리 중... {processed_items}/{total_items} ({filename if filename else '데이터 분석 중'})")
            progress_bar.progress(processed_items / total_items if total_items > 0 else 0)

            log_identifier_parts = []
            if status_obj and status_obj.get('customer_phone'): log_identifier_parts.append(status_obj['customer_phone'])
            if status_obj and status_obj.get('customer_name') != DEFAULT_CUSTOMER_NAME : log_identifier_parts.append(status_obj['customer_name'])
            log_identifier = f"({', '.join(log_identifier_parts)})" if log_identifier_parts else ""
            
            if is_excel_input and status_obj and isinstance(item_data_row_or_line, pd.Series): # Excel 입력 시 로그 추가
                moving_date_raw_excel = get_column_value(item_data_row_or_line, 'moving_date', COLUMN_ALIASES_EXCEL)
                if moving_date_raw_excel and moving_date_raw_excel.strip().lower() != "미정" and status_obj.get("moving_date") == TODAY_ISO_DATE:
                    all_log_messages.append(f"ℹ️ <span style='color:blue;'>정보</span>: {row_display_prefix} 제공된 날짜 '{moving_date_raw_excel}'가 오늘 날짜로 처리됨 (형식 또는 내용 확인 필요). {filename if filename else ''} {log_identifier}")

            if status_obj and filename:
                final_state_to_save = get_default_state()
                final_state_to_save.update(status_obj)
                try:
                    gdrive_folder_id_secret = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")
                    save_result = gdrive.save_json_file(filename, final_state_to_save, folder_id=gdrive_folder_id_secret)
                    if save_result and save_result.get('id'):
                        log_message = f"✔️ <span style='color:green;'>저장 성공</span>: {filename} {log_identifier} (ID: {save_result.get('id')})"
                        all_log_messages.append(log_message); success_count += 1
                    else:
                        log_message = f"❌ <span style='color:red;'>저장 실패</span>: {filename} {log_identifier} (응답: {save_result})"
                        all_log_messages.append(log_message); error_count += 1
                except AttributeError as ae:
                     log_message = f"❌ <span style='color:red;'>저장 함수 오류</span>: {filename} {log_identifier} (오류: {ae})"
                     all_log_messages.append(log_message); error_count += 1
                except Exception as e_save:
                    log_message = f"❌ <span style='color:red;'>저장 중 예외</span>: {filename if filename else '데이터'} {log_identifier} ({str(e_save)})"
                    all_log_messages.append(log_message); error_count += 1
            else:
                log_message = f"⚠️ <span style='color:orange;'>건너뜀/오류</span>: {error_msg if error_msg else '사유 불명'} {log_identifier}"
                all_log_messages.append(log_message); error_count +=1

        status_text.empty(); progress_bar.empty()
        st.info(f"총 분석 대상: {total_items} 건 (실제 처리 시도: {processed_items} 건)")
        st.success(f"Google Drive 저장 성공: {success_count} 건")
        if error_count > 0: st.error(f"실패 또는 건너뜀: {error_count} 건")
        else: st.info(f"실패 또는 건너뜀: {error_count} 건")

        if all_log_messages:
            expanded_log = (error_count > 0 or success_count < total_items or any("정보" in log for log in all_log_messages))
            with st.expander("▼ 상세 처리 로그 보기 (클릭)", expanded=expanded_log):
                log_html = "".join([f"<div style='font-size:small; margin-bottom:3px;'>{log}</div>" for log in all_log_messages])
                st.markdown(log_html, unsafe_allow_html=True)
