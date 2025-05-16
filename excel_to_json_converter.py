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
    from state_manager import STATE_KEYS_TO_SAVE, MOVE_TYPE_OPTIONS # MOVE_TYPE_OPTIONS 등을 위함
except ImportError as e:
    st.error(f"필수 모듈 로딩 실패: {e}. (google_drive_helper.py, data.py, state_manager.py를 현재 스크립트와 같은 폴더에 위치시켜주세요)")
    st.stop()

# 시간대 설정
try:
    KST = pytz.timezone("Asia/Seoul")
except pytz.UnknownTimeZoneError:
    st.warning("Asia/Seoul 시간대를 찾을 수 없어 UTC를 사용합니다. 날짜 처리에 영향이 있을 수 있습니다.")
    KST = pytz.utc

# 기본값 설정
DEFAULT_CUSTOMER_NAME = "무명"
DEFAULT_MOVE_TYPE = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠"
DEFAULT_STORAGE_TYPE = data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦" # data.py에서 가져오도록 수정
DEFAULT_FROM_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
DEFAULT_TO_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
TODAY_ISO_DATE = datetime.now(KST).date().isoformat()

# --- 공통 헬퍼 함수 ---
def parse_date_flexible(date_str_input, current_year):
    if isinstance(date_str_input, (datetime, date)): # 이미 datetime 또는 date 객체인 경우
        return date_str_input.date().isoformat()
    if not date_str_input or str(date_str_input).strip().lower() == "미정":
        return TODAY_ISO_DATE # "미정"일 경우 오늘 날짜로 설정
    
    date_str = str(date_str_input).strip()
    # 다양한 날짜 형식 지원 (YYYY-MM-DD, MM-DD, MM/DD 등)
    patterns = [
        (r'(\d{4})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*일?', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{1,2})\s*[-/월\.]\s*(\d{1,2})\s*(일?)', lambda m: (current_year, int(m.group(1)), int(m.group(2)))), # 연도 없이 월/일만 있는 경우
        (r'(\d{2})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*일?', lambda m: (2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))) # YY-MM-DD 형식
    ]
    for pattern, extractor in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                # 매치된 부분과 전체 문자열이 일치하는지, 또는 남은 부분이 공백인지 확인
                matched_date_str = match.group(0)
                # 날짜 문자열 뒤에 다른 유효한 문자가 붙어있는지 확인 (예: "5/10 가", "5/10 사무실")
                remaining_text = date_str[len(matched_date_str):].strip()
                if remaining_text and not remaining_text.isspace(): # 공백이 아닌 다른 문자가 남아있다면
                    # 이 부분은 날짜 패턴에 정확히 부합하지 않는 것으로 간주할 수 있음
                    # 또는, 이 remaining_text를 다른 정보(예: 이사 유형)로 파싱할 수도 있음
                    # 현재 로직에서는 날짜로만 간주하고, 남은 텍스트는 무시하거나 다른 필드에서 처리
                    pass # 여기서는 일단 날짜로만 처리

                year, month, day = extractor(match)
                return datetime(year, month, day).date().isoformat()
            except ValueError: # 잘못된 날짜 (예: 2월 30일)
                continue
    return None # 어떤 패턴과도 맞지 않으면 None 반환

def normalize_phone_number_for_filename(phone_str):
    if not phone_str or not isinstance(phone_str, str): return None
    return "".join(filter(str.isdigit, phone_str))

def get_default_state():
    # state_manager.py 와 최대한 유사하게 기본값 설정
    return {
        "moving_date": TODAY_ISO_DATE, "customer_name": DEFAULT_CUSTOMER_NAME, "customer_phone": "",
        "base_move_type": DEFAULT_MOVE_TYPE, "from_location": "", "to_location": "", "special_notes": "",
        "from_floor": "", "to_floor": "", 
        "from_method": DEFAULT_FROM_METHOD, 
        "to_method": DEFAULT_TO_METHOD,
        "is_storage_move": False, 
        "storage_type": DEFAULT_STORAGE_TYPE, 
        "apply_long_distance": False, "has_via_point": False,
        "deposit_amount": 0, "adjustment_amount": 0, 
        "issue_tax_invoice": False, "card_payment": False, "remove_base_housewife": False,
        "dispatched_1t":0, "dispatched_2_5t":0, "dispatched_3_5t":0, "dispatched_5t":0,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "waste_tons_input": 0.5, "has_waste_check": False,
        "uploaded_image_paths": [],
        # STATE_KEYS_TO_SAVE 에 있는 모든 키의 기본값을 여기에 명시하는 것이 좋음
        # 예시:
        "vehicle_select_radio": "자동 추천 차량 사용", 
        "manual_vehicle_select_value": None,
        "final_selected_vehicle": None,
        "recommended_vehicle_auto": None,
        "storage_duration": 1, 
        "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "via_point_location": "",
        "via_point_method": DEFAULT_FROM_METHOD, # 경유지도 기본 작업방법 설정
        "via_point_surcharge": 0,
        "regional_ladder_surcharge": 0,
        # 날짜 옵션 위젯 (tab1과 tab3 동기화 고려 필요)
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
    }

# 수정된 층수 추출 함수
def extract_floor_from_address_enhanced(address_str):
    if not address_str or not isinstance(address_str, str):
        return address_str if address_str else "", "" # 주소가 없으면 그대로, 층도 빈칸
    
    address_cleaned = address_str.strip()
    floor_str = ""

    # 패턴 1: "1102호", "302 호" 등 (숫자 + 선택적 공백 + "호")
    # "호" 바로 앞의 숫자 전체를 캡처 (예: 1102, 302)
    ho_match = re.search(r'(\d+)\s*호', address_cleaned)
    if ho_match:
        floor_candidate = ho_match.group(1) # 예: "1102", "302"
        
        # 요청사항: "호 끝자리 두자리를 제외한 숫자가 층수" -> "302는 3층, 2204호는 22층"
        if len(floor_candidate) > 2: # 숫자가 3자리 이상일 경우 (예: 302, 1102, 2204)
            floor_str = floor_candidate[:-2] # 뒤 두자리를 제외 (302 -> 3, 1102 -> 11, 2204 -> 22)
        elif floor_candidate: # 1~2자리 숫자면 (예: 52호 -> 5, 2호 -> '') 이 경우는 어떻게? 일단은 비워두거나, 그대로 두거나. 요청이 명확치 않음.
                              # 현재는 3자리 이상일때만 처리. 102호 -> 1층. 902호 -> 9층.
            floor_str = floor_candidate # 1~2자리면 일단 그대로. (예: 52호 -> 52) -> 추후 재정의 필요하면 수정
        
        # 주소에서 "XXX호" 부분 제거 시도 (더 정확하게)
        # 호수로 끝나는 경우: "OO아파트 101동 1102호" -> "OO아파트 101동"
        address_cleaned = re.sub(r'\s*\d+\s*호\s*$', '', address_cleaned).strip()
        # 중간에 호수가 있는 경우: "OO아파트 101동 1102호 뒷편" -> "OO아파트 101동  뒷편" (공백2개 주의)
        address_cleaned = re.sub(r'(\s+)\d+\s*호(\s+)', r'\1\2', address_cleaned).strip() # 중간 공백 유지하며 제거
        address_cleaned = re.sub(r'^\d+\s*호(\s+)', r'\1', address_cleaned).strip() # 맨 앞 호수 제거
        
        if floor_str: # 유효한 층수가 추출된 경우만 반환
             return address_cleaned, floor_str

    # 패턴 2: 주소 끝에 "숫자+층/F/f" (예: "OO빌딩 3층", "XX아파트 10F")
    floor_ending_match = re.search(r'^(.*?)(\s*(\d+)\s*(층|F|f))$', address_cleaned, re.IGNORECASE)
    if floor_ending_match:
        address_cleaned = floor_ending_match.group(1).strip()
        floor_str = floor_ending_match.group(3)
        return address_cleaned, floor_str
        
    return address_cleaned, "" # 어떤 패턴에도 해당 없으면, 원래 주소와 빈 층수 반환

# --- 텍스트 입력 처리 함수 ---
PHONE_REGEX_TEXT = re.compile(r'(01[016789]-?\d{3,4}-?\d{4}|0\d{1,2}-?\d{3,4}-?\d{4})')
MOVE_TYPE_KEYWORDS_TEXT = {"가정": ["가정", "가"], "사무실": ["사무실", "사"]}

def parse_line_to_json_flexible(line_text, current_year, line_number_display=""):
    state = get_default_state()
    original_line = line_text.strip()
    if not original_line: return None, None, f"{line_number_display}빈 줄"

    phone_match = PHONE_REGEX_TEXT.search(original_line)
    if not phone_match: return None, None, f"{line_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = phone_match.group(0)
    filename_phone_part = normalize_phone_number_for_filename(state["customer_phone"])
    if not filename_phone_part: return None, None, f"{line_number_display}유효하지 않은 전화번호"

    before_phone = original_line[:phone_match.start()].strip()
    after_phone = original_line[phone_match.end():].strip()

    # 이름 및 날짜 파싱
    if '\t' in before_phone: parts_before_phone = [p.strip() for p in before_phone.split('\t') if p.strip()]
    else: parts_before_phone = [p.strip() for p in re.split(r'\s{2,}', before_phone) if p.strip()] or ([before_phone] if before_phone else [])
    
    potential_name_parts = []; date_found = False
    for part in parts_before_phone:
        parsed_date = parse_date_flexible(part, current_year)
        if parsed_date:
            if not date_found: state["moving_date"] = parsed_date; date_found = True
        else: potential_name_parts.append(part)
    
    if potential_name_parts: state["customer_name"] = " ".join(potential_name_parts)
    if not date_found and not state.get("moving_date"): state["moving_date"] = TODAY_ISO_DATE # 날짜 없으면 오늘

    # 고객명에서 "보관" 키워드 확인
    if "보관" in state["customer_name"]:
        state["is_storage_move"] = True
        state["storage_type"] = DEFAULT_STORAGE_TYPE # data.py의 기본 컨테이너 보관

    # 이사 유형, 주소, 메모 파싱
    if '\t' in after_phone: parts_after_phone = [p.strip() for p in after_phone.split('\t') if p.strip()]
    else: parts_after_phone = [p.strip() for p in re.split(r'\s{2,}', after_phone) if p.strip()] or ([after_phone] if after_phone else [])
    
    part_idx = 0
    # 이사 유형 ("가", "사")
    if part_idx < len(parts_after_phone):
        current_part_lower = parts_after_phone[part_idx].lower()
        found_move_type_in_after_phone = False
        for type_key, keywords in MOVE_TYPE_KEYWORDS_TEXT.items():
            # 키워드가 정확히 일치하거나, 키워드로 시작하고 바로 뒤에 공백이 오는 경우를 고려
            is_keyword_match = any(current_part_lower == kw or current_part_lower.startswith(kw + " ") for kw in keywords)
            if is_keyword_match:
                original_part_len = len(parts_after_phone[part_idx])
                matched_keyword_actual_len = 0
                for kw in keywords: # 실제 매칭된 키워드 길이 찾기
                    if current_part_lower.startswith(kw):
                        matched_keyword_actual_len = len(kw)
                        break
                
                if type_key == "가정" and MOVE_TYPE_OPTIONS:
                    state["base_move_type"] = MOVE_TYPE_OPTIONS[0]
                elif type_key == "사무실" and len(MOVE_TYPE_OPTIONS) > 1:
                    state["base_move_type"] = MOVE_TYPE_OPTIONS[1]
                
                # "가 서울..." 또는 "사무실 강남..." 같은 경우 처리
                remaining_after_keyword = parts_after_phone[part_idx][matched_keyword_actual_len:].strip()
                if remaining_after_keyword: # 키워드 뒤에 내용이 있으면
                    parts_after_phone[part_idx] = remaining_after_keyword # 해당 파트 업데이트
                else: # 키워드만 있었으면 해당 파트 소모
                    part_idx += 1
                found_move_type_in_after_phone = True
                break 
        # "가" 또는 "사" 가 아니었다면, 이 파트는 주소의 시작으로 간주됨. part_idx는 증가하지 않음.

    # 출발지 주소 및 층수
    if part_idx < len(parts_after_phone):
        from_loc_raw = parts_after_phone[part_idx]
        state["from_location"], state["from_floor"] = extract_floor_from_address_enhanced(from_loc_raw)
        part_idx += 1
    else:
        if not state.get("from_location"): # 주소 필드가 비었으면 에러
             return None, None, f"{line_number_display}출발지 주소 없음 (필수)"

    # 도착지 주소 및 층수 (선택적)
    if part_idx < len(parts_after_phone):
        to_loc_raw = parts_after_phone[part_idx]
        state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_loc_raw)
        part_idx += 1
    
    if part_idx < len(parts_after_phone):
        state["special_notes"] = " ".join(parts_after_phone[part_idx:])

    if not state.get("from_location"):
        return None, None, f"{line_number_display}출발지 누락 (재확인)"
        
    return state, filename_phone_part + ".json", None


# --- 엑셀 입력 처리 함수 ---
COLUMN_ALIASES_EXCEL = {
    'moving_date': ['날짜', '이사날짜'], 
    'customer_name': ['고객명', '이름', '성함'],
    'customer_phone': ['전화번호', '연락처', '휴대폰번호', '전화'], 
    'base_move_type': ['이사종류', '구분'],
    'from_location': ['출발지주소', '출발지', '출발'], 
    'from_floor': ['층수', '출발지 층수', '출발층수'],
    'to_location': ['도착지주소', '도착지', '도착주소'], 
    'to_floor': ['도착지 층수', '도착층수'],
    'special_notes': ['특이사항', '요구사항', '희망사항', '건의'],
}
def get_column_value(row, field_name, aliases, default=""):
    for alias in aliases.get(field_name, []):
        if alias in row.index and pd.notna(row[alias]):
            return str(row[alias]).strip()
    return default

def parse_excel_row_to_json(row, current_year, row_number_display=""):
    state = get_default_state()
    if row.isnull().all() or all(str(x).strip() == "" for x in row if pd.notna(x)):
        return None, None, f"{row_number_display}빈 행"

    moving_date_raw = get_column_value(row, 'moving_date', COLUMN_ALIASES_EXCEL)
    parsed_date_excel = parse_date_flexible(moving_date_raw, current_year)
    if parsed_date_excel: state["moving_date"] = parsed_date_excel

    customer_name_raw = get_column_value(row, 'customer_name', COLUMN_ALIASES_EXCEL)
    if customer_name_raw and customer_name_raw.lower() != "미정":
        state["customer_name"] = customer_name_raw
    # 고객명에서 "보관" 키워드 확인
    if "보관" in state["customer_name"]:
        state["is_storage_move"] = True
        state["storage_type"] = DEFAULT_STORAGE_TYPE # data.py의 기본 컨테이너 보관

    customer_phone_raw = get_column_value(row, 'customer_phone', COLUMN_ALIASES_EXCEL)
    if not customer_phone_raw: return None, None, f"{row_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = customer_phone_raw
    filename_phone_part = normalize_phone_number_for_filename(customer_phone_raw)
    if not filename_phone_part: return None, None, f"{row_number_display}유효하지 않은 전화번호"

    move_type_raw = get_column_value(row, 'base_move_type', COLUMN_ALIASES_EXCEL)
    if move_type_raw:
        move_type_char = move_type_raw.strip().lower()
        if any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["가정"]):
            state["base_move_type"] = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else DEFAULT_MOVE_TYPE
        elif any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["사무실"]):
            state["base_move_type"] = MOVE_TYPE_OPTIONS[1] if len(MOVE_TYPE_OPTIONS) > 1 else DEFAULT_MOVE_TYPE

    from_location_raw = get_column_value(row, 'from_location', COLUMN_ALIASES_EXCEL)
    if not from_location_raw: return None, None, f"{row_number_display}출발지 주소 없음 (필수)"
    
    from_floor_raw_col = get_column_value(row, 'from_floor', COLUMN_ALIASES_EXCEL)
    if from_floor_raw_col: # 엑셀에 명시적 층수 컬럼 값이 있으면 사용
        state["from_floor"] = "".join(filter(str.isdigit, from_floor_raw_col))
        state["from_location"] = from_location_raw # 주소도 함께 저장
    else: # 없으면 주소에서 추출 시도
        state["from_location"], state["from_floor"] = extract_floor_from_address_enhanced(from_location_raw)

    to_location_raw = get_column_value(row, 'to_location', COLUMN_ALIASES_EXCEL)
    to_floor_raw_col = get_column_value(row, 'to_floor', COLUMN_ALIASES_EXCEL)
    if to_floor_raw_col:
        state["to_floor"] = "".join(filter(str.isdigit, to_floor_raw_col))
        if to_location_raw: state["to_location"] = to_location_raw
    elif to_location_raw:
        state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_location_raw)

    state["special_notes"] = get_column_value(row, 'special_notes', COLUMN_ALIASES_EXCEL)
    
    if not state.get("from_location"):
        return None, None, f"{row_number_display}출발지 누락 (재확인)"
        
    return state, filename_phone_part + ".json", None


# --- Streamlit UI ---
st.set_page_config(page_title="이사견적 변환기", layout="wide")
st.title("🚚 이사 정보 JSON 변환 및 Drive 저장")
st.caption("텍스트 또는 Excel 파일로 된 이사 정보를 분석하여 JSON 파일로 변환하고 Google Drive에 저장합니다.")

input_method = st.radio("입력 방식 선택:", ('텍스트 직접 입력', 'Excel 파일 업로드'), horizontal=True)
text_input = ""
uploaded_file = None

if input_method == '텍스트 직접 입력':
    text_input = st.text_area("여기에 이사 정보를 한 줄씩 입력하세요:", height=200, 
                              placeholder="예시: 홍길동 010-1234-5678 5/10 가 서울 강남구 XXX 101동 302호 경기 수원시 YYY 202동 1102호 에어컨 이전 설치")
else: # Excel 파일 업로드
    uploaded_file = st.file_uploader("변환할 Excel 파일을 업로드하세요.", type=["xlsx", "xls"])
    st.markdown("""
    **Excel 파일 형식 가이드:**
    - 첫 번째 행은 헤더(컬럼명)여야 합니다.
    - 필수 컬럼: `전화번호`, `출발지주소` (또는 유사어)
    - 선택 컬럼: `날짜`, `고객명`, `이사종류`('가' 또는 '사'), `출발지 층수`, `도착지주소`, `도착지 층수`, `특이사항` (또는 유사어)
    - 층수는 주소에서 "XXX호" 패턴으로 자동인식 시도 가능 (예: "강남아파트 101동 302호" -> 3층). 명시적 층수 컬럼이 우선합니다.
    - 이름에 "보관"이 포함되면 보관이사로 처리됩니다.
    """)

if st.button("🔄 JSON 변환 및 Google Drive에 저장하기"):
    current_year = datetime.now(KST).year
    success_count = 0; error_count = 0; processed_items = 0; total_items = 0
    all_log_messages = []; items_to_process = []; is_excel = False
    
    if input_method == '텍스트 직접 입력':
        if not text_input.strip():
            st.warning("입력된 텍스트가 없습니다.")
        else:
            items_to_process = [line for line in text_input.strip().split('\n') if line.strip()]
            total_items = len(items_to_process)
    elif input_method == 'Excel 파일 업로드':
        if uploaded_file is None:
            st.warning("업로드된 파일이 없습니다.")
        else:
            try:
                try: df = pd.read_excel(uploaded_file, engine='openpyxl')
                except Exception:
                    uploaded_file.seek(0); df = pd.read_excel(uploaded_file, engine='xlrd')
                
                df.columns = [str(col).strip() for col in df.columns]
                items_to_process = [row for _, row in df.iterrows() if not row.isnull().all()]
                total_items = len(items_to_process)
                is_excel = True
            except Exception as e:
                st.error(f"Excel 파일 읽기 중 오류 발생: {e}"); items_to_process = []
    
    if not items_to_process:
        if text_input.strip() or uploaded_file:
            st.info("변환할 유효한 데이터가 없습니다. 입력 내용을 확인해주세요.")
    else:
        st.subheader("✨ 처리 결과")
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, item_data in enumerate(items_to_process):
            processed_items += 1
            status_obj, filename, error_msg = (None, None, "알 수 없는 입력 형식")
            row_display_prefix = f"엑셀 {i+2}행" if is_excel else f"텍스트 {i+1}줄"

            if is_excel:
                status_obj, filename, error_msg = parse_excel_row_to_json(item_data, current_year, row_display_prefix + ": ")
            else:
                status_obj, filename, error_msg = parse_line_to_json_flexible(item_data, current_year, row_display_prefix + ": ")

            status_text.text(f"처리 중... {processed_items}/{total_items} ({filename if filename else '데이터 분석 중'})")
            progress_bar.progress(processed_items / total_items)

            log_identifier_parts = []
            if status_obj and status_obj.get('customer_phone'): log_identifier_parts.append(status_obj['customer_phone'])
            if status_obj and status_obj.get('customer_name') != DEFAULT_CUSTOMER_NAME : log_identifier_parts.append(status_obj['customer_name'])
            log_identifier = f"({', '.join(log_identifier_parts)})" if log_identifier_parts else ""

            if status_obj and filename:
                final_state_to_save = get_default_state()
                final_state_to_save.update(status_obj)
                
                # STATE_KEYS_TO_SAVE에 정의된 키만 저장하도록 필터링 (선택적)
                # filtered_state = {k: v for k, v in final_state_to_save.items() if k in STATE_KEYS_TO_SAVE or k.startswith("qty_")}
                # 현재는 모든 파싱된 키를 저장함. 필요시 위 필터링 로직 활성화.
                
                try:
                    gdrive_folder_id = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")
                    save_result = gdrive.save_json_file(filename, final_state_to_save, folder_id=gdrive_folder_id) # filtered_state 대신 final_state_to_save 사용
                    if save_result and save_result.get('id'):
                        log_message = f"✅ <span style='color:green;'>저장 성공</span>: {filename} {log_identifier} (ID: {save_result.get('id')})"
                        all_log_messages.append(log_message); success_count += 1
                    else:
                        log_message = f"❌ <span style='color:red;'>저장 실패</span>: {filename} {log_identifier} (응답: {save_result})"
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
            with st.expander("▼ 상세 처리 로그 보기 (클릭)", expanded=(error_count > 0 or success_count < total_items)):
                log_html = "".join([f"<div style='font-size:small; margin-bottom:3px;'>{log.replace('✅','✔️')}</div>" for log in all_log_messages])
                st.markdown(log_html, unsafe_allow_html=True)