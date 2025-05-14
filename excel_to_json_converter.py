# text_excel_to_json_gdrive.py (UI 설명 최소화, 처리 결과 간소화)
import streamlit as st
import json
import re
from datetime import datetime, date
import pytz
import pandas as pd

# 필수 모듈 로딩 (google_drive_helper.py, data.py, state_manager.py는 동일 경로에 있어야 함)
try:
    import google_drive_helper as gdrive
    import data
    from state_manager import STATE_KEYS_TO_SAVE, MOVE_TYPE_OPTIONS
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
DEFAULT_FROM_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
DEFAULT_TO_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
TODAY_ISO_DATE = datetime.now(KST).date().isoformat()

# --- 공통 헬퍼 함수 ---
def parse_date_flexible(date_str_input, current_year):
    if isinstance(date_str_input, (datetime, date)):
        return date_str_input.date().isoformat()
    if not date_str_input or str(date_str_input).strip().lower() == "미정":
        return TODAY_ISO_DATE
    date_str = str(date_str_input).strip()
    patterns = [
        (r'(\d{4})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*일?', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{1,2})\s*[-/월\.]\s*(\d{1,2})\s*(일?)', lambda m: (current_year, int(m.group(1)), int(m.group(2)))),
        (r'(\d{2})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*일?', lambda m: (2000 + int(m.group(1)), int(m.group(2)), int(m.group(3))))
    ]
    for pattern, extractor in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                matched_date_str = match.group(0)
                if len(matched_date_str) != len(date_str) and not date_str[len(matched_date_str):].strip().isspace() and date_str[len(matched_date_str):].strip() != "":
                    continue
                year, month, day = extractor(match)
                return datetime(year, month, day).date().isoformat()
            except ValueError:
                continue
    return None

def normalize_phone_number_for_filename(phone_str):
    if not phone_str or not isinstance(phone_str, str): return None
    return "".join(filter(str.isdigit, phone_str))

def get_default_state():
    return {
        "moving_date": TODAY_ISO_DATE, "customer_name": DEFAULT_CUSTOMER_NAME, "customer_phone": "",
        "base_move_type": DEFAULT_MOVE_TYPE, "from_location": "", "to_location": "", "special_notes": "",
        "from_floor": "", "to_floor": "", "from_method": DEFAULT_FROM_METHOD, "to_method": DEFAULT_TO_METHOD,
        "is_storage_move": False, "apply_long_distance": False, "has_via_point": False,
        "deposit_amount": 0, "adjustment_amount": 0, "issue_tax_invoice": False, "card_payment": False,
        "remove_base_housewife": False, "dispatched_1t":0, "dispatched_2_5t":0, "dispatched_3_5t":0, "dispatched_5t":0,
        "uploaded_image_paths": []
    }

# --- 텍스트 입력 처리 함수 ---
PHONE_REGEX = re.compile(r'(01[016789]-?\d{3,4}-?\d{4}|0\d{1,2}-?\d{3,4}-?\d{4})')
MOVE_TYPE_KEYWORDS_TEXT = {"가정": ["가정", "가"], "사무실": ["사무실", "사"]}

def extract_floor_from_address(address_str):
    if not address_str: return "", ""
    floor_match = re.search(r'^(.*?)(\s*(\d+)\s*(층|F|f))$', address_str.strip(), re.IGNORECASE)
    if floor_match: return floor_match.group(1).strip(), floor_match.group(3)
    return address_str.strip(), ""

def parse_line_to_json_flexible(line_text, current_year, line_number_display=""):
    state = get_default_state()
    original_line = line_text.strip()
    if not original_line: return None, None, f"{line_number_display}빈 줄"

    phone_match = PHONE_REGEX.search(original_line)
    if not phone_match: return None, None, f"{line_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = phone_match.group(0)
    filename_phone_part = normalize_phone_number_for_filename(state["customer_phone"])
    if not filename_phone_part: return None, None, f"{line_number_display}유효하지 않은 전화번호"

    before_phone = original_line[:phone_match.start()].strip()
    after_phone = original_line[phone_match.end():].strip()

    if '\t' in before_phone: parts_before_phone = [p.strip() for p in before_phone.split('\t') if p.strip()]
    else: parts_before_phone = [p.strip() for p in re.split(r'\s{2,}', before_phone) if p.strip()] or ([before_phone] if before_phone else [])

    potential_name_parts = []; date_found = False
    for part in parts_before_phone:
        parsed_date = parse_date_flexible(part, current_year)
        if parsed_date:
            if not date_found: state["moving_date"] = parsed_date; date_found = True
        else: potential_name_parts.append(part)
    if potential_name_parts: state["customer_name"] = " ".join(potential_name_parts)
    if not date_found: state["moving_date"] = TODAY_ISO_DATE # 명시적 날짜 없으면 오늘

    if '\t' in after_phone: parts_after_phone = [p.strip() for p in after_phone.split('\t') if p.strip()]
    else: parts_after_phone = [p.strip() for p in re.split(r'\s{2,}', after_phone) if p.strip()] or ([after_phone] if after_phone else [])
    
    part_index = 0
    if part_index < len(parts_after_phone):
        current_part = parts_after_phone[part_index]
        for type_name, keywords in MOVE_TYPE_KEYWORDS_TEXT.items():
            if any(keyword == current_part.lower() for keyword in keywords):
                state["base_move_type"] = (MOVE_TYPE_OPTIONS[0] if type_name == "가정" and MOVE_TYPE_OPTIONS else
                                          (MOVE_TYPE_OPTIONS[1] if type_name == "사무실" and len(MOVE_TYPE_OPTIONS) > 1 else DEFAULT_MOVE_TYPE))
                part_index += 1; break
    
    if part_index < len(parts_after_phone):
        state["from_location"], state["from_floor"] = extract_floor_from_address(parts_after_phone[part_index]); part_index += 1
    else: return None, None, f"{line_number_display}출발지 주소 없음 (필수)"

    if part_index < len(parts_after_phone):
        state["to_location"], state["to_floor"] = extract_floor_from_address(parts_after_phone[part_index]); part_index += 1
    if part_index < len(parts_after_phone): state["special_notes"] = " ".join(parts_after_phone[part_index:])

    if not state.get("from_location"): return None, None, f"{line_number_display}출발지 누락 (재확인)"
    return state, filename_phone_part + ".json", None

# --- 엑셀 입력 처리 함수 ---
COLUMN_ALIASES = {
    'moving_date': ['날짜', '이사날짜'], 'customer_name': ['고객명', '이름', '성함'],
    'customer_phone': ['전화번호', '연락처', '휴대폰번호', '전화'], 'base_move_type': ['이사종류', '구분'],
    'from_location': ['출발지주소', '출발지', '출발'], 'from_floor': ['층수', '출발지 층수', '출발층수'],
    'to_location': ['도착지주소', '도착지', '도착주소'], 'to_floor': ['도착지 층수', '도착층수'],
    'special_notes': ['특이사항', '요구사항', '희망사항', '건의'],
}
def get_column_value(row, field_name, aliases, default=""):
    for alias in aliases.get(field_name, []):
        if alias in row.index and pd.notna(row[alias]): return str(row[alias]).strip()
    return default

def parse_excel_row_to_json(row, current_year, row_number_display=""):
    state = get_default_state()
    if row.isnull().all() or all(str(x).strip() == "" for x in row if pd.notna(x)):
        return None, None, f"{row_number_display}빈 행"

    moving_date_raw = get_column_value(row, 'moving_date', COLUMN_ALIASES)
    parsed_date_excel = parse_date_flexible(moving_date_raw, current_year)
    if parsed_date_excel: state["moving_date"] = parsed_date_excel

    customer_name_raw = get_column_value(row, 'customer_name', COLUMN_ALIASES)
    if customer_name_raw and customer_name_raw.lower() != "미정": state["customer_name"] = customer_name_raw
    
    customer_phone_raw = get_column_value(row, 'customer_phone', COLUMN_ALIASES)
    if not customer_phone_raw: return None, None, f"{row_number_display}전화번호 없음"
    state["customer_phone"] = customer_phone_raw
    filename_phone_part = normalize_phone_number_for_filename(customer_phone_raw)
    if not filename_phone_part: return None, None, f"{row_number_display}유효하지 않은 전화번호"

    move_type_raw = get_column_value(row, 'base_move_type', COLUMN_ALIASES)
    if move_type_raw:
        move_type_char = move_type_raw.strip().lower()
        if any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["가정"]): state["base_move_type"] = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else DEFAULT_MOVE_TYPE
        elif any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["사무실"]): state["base_move_type"] = MOVE_TYPE_OPTIONS[1] if len(MOVE_TYPE_OPTIONS) > 1 else DEFAULT_MOVE_TYPE

    from_location_raw = get_column_value(row, 'from_location', COLUMN_ALIASES)
    if not from_location_raw: return None, None, f"{row_number_display}출발지 없음"
    state["from_location"] = from_location_raw
    
    from_floor_raw = get_column_value(row, 'from_floor', COLUMN_ALIASES)
    if from_floor_raw: state["from_floor"] = "".join(filter(str.isdigit, from_floor_raw))
    else: _, state["from_floor"] = extract_floor_from_address(state["from_location"])

    to_location_raw = get_column_value(row, 'to_location', COLUMN_ALIASES)
    if to_location_raw: state["to_location"] = to_location_raw
    
    to_floor_raw = get_column_value(row, 'to_floor', COLUMN_ALIASES)
    if to_floor_raw: state["to_floor"] = "".join(filter(str.isdigit, to_floor_raw))
    elif state["to_location"]: _, state["to_floor"] = extract_floor_from_address(state["to_location"])

    state["special_notes"] = get_column_value(row, 'special_notes', COLUMN_ALIASES)
    
    if not state.get("from_location"): return None, None, f"{row_number_display}출발지 누락 (재확인)"
    return state, filename_phone_part + ".json", None

# --- Streamlit UI ---
st.title("이사 정보 JSON 변환") # 제목 간소화
input_method = st.radio("입력 방식:", ('텍스트', '엑셀 파일')) # 라디오 버튼 레이블 간소화
text_input = ""
uploaded_file = None

if input_method == '텍스트':
    text_input = st.text_area("텍스트 입력:", height=150, placeholder="여기에 이사 정보를 입력하세요...") # placeholder 간소화, 높이 조절
else: # 엑셀 파일
    uploaded_file = st.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"], label_visibility="collapsed") # 레이블 숨김, 타입만 표시

if st.button("JSON 변환 및 Drive 저장"): # 버튼 이름 유지 (기능 명시)
    current_year = datetime.now(KST).year
    success_count = 0; error_count = 0; processed_items = 0; total_items = 0
    all_log_messages = []; items_to_process = []; is_excel = False
    
    st.sidebar.empty()
    results_container = st.empty(); progress_bar = st.progress(0)

    if input_method == '텍스트':
        if not text_input.strip(): st.warning("입력 내용 없음")
        else: items_to_process = text_input.strip().split('\n'); total_items = len(items_to_process)
    elif input_method == '엑셀 파일':
        if uploaded_file is None: st.warning("파일 선택 안됨")
        else:
            try:
                df = pd.read_excel(uploaded_file); df.columns = [str(col) for col in df.columns]
                items_to_process = [row for _, row in df.iterrows()]; total_items = len(items_to_process); is_excel = True
            except Exception as e: st.error(f"파일 읽기 오류: {e}"); items_to_process = []
    
    if not items_to_process and (text_input.strip() or uploaded_file): # 입력 시도는 있었으나 처리할 아이템이 없는 경우
        st.info("처리할 데이터가 없습니다.")
    elif items_to_process: # 처리할 아이템이 있는 경우에만 아래 로직 실행
        st.subheader("처리 결과") # 이 subheader는 유지하는 것이 결과 구분에 좋음
        for i, item_data in enumerate(items_to_process):
            processed_items += 1; identifier_prefix = ""; log_identifier = ""
            status_obj, filename, error_msg = (None, None, "알 수 없는 입력")

            row_display_prefix = f"엑셀 {i+1}행" if is_excel else f"텍스트 {i+1}줄"

            if is_excel:
                cn_val = get_column_value(item_data, 'customer_name', COLUMN_ALIASES)
                cp_val = get_column_value(item_data, 'customer_phone', COLUMN_ALIASES)
                identifier_prefix = cp_val or cn_val or "" # 전화번호 우선
                status_obj, filename, error_msg = parse_excel_row_to_json(item_data, current_year, f"{row_display_prefix}: ")
            else: 
                phone_match_log = PHONE_REGEX.search(item_data)
                if phone_match_log: identifier_prefix = phone_match_log.group(0)
                else: # 전화번호가 없는 경우 (파싱 함수 내부에서 오류 처리되겠지만, 로그용으로 간략히)
                    identifier_prefix = item_data[:20] # 앞 20자 정도만

                status_obj, filename, error_msg = parse_line_to_json_flexible(item_data, current_year, f"{row_display_prefix}: ")

            progress_bar.progress(processed_items / total_items)
            # "처리 중..." 메시지는 너무 자주 바뀌므로 제거하거나, 매우 간결하게 (예: st.markdown(f"{processed_items}/{total_items}"))
            # results_container.markdown(f"{processed_items}/{total_items}") # 이 부분은 주석 처리하여 더 깔끔하게

            log_identifier = f"({identifier_prefix.strip()})" if identifier_prefix.strip() else ""

            if status_obj and filename:
                try:
                    save_result = gdrive.save_json_file(filename, status_obj) # 실제 저장 로직
                    if save_result and save_result.get('id'):
                        log_message = f"✅ {filename} {log_identifier} (ID: {save_result.get('id')})" # 성공 로그 간소화
                        all_log_messages.append(log_message); success_count += 1
                    else:
                        log_message = f"❌ 저장실패: {filename} {log_identifier} (응답: {save_result})"
                        all_log_messages.append(log_message); error_count += 1
                except Exception as e:
                    log_message = f"❌ 오류: {filename if filename else '데이터'} {log_identifier} ({str(e)})" # 오류 로그 간소화
                    all_log_messages.append(log_message); error_count += 1
            else:
                log_message = f"⚠️ 건너뜀: {error_msg if error_msg else '사유 불명'} {log_identifier}"
                all_log_messages.append(log_message); error_count +=1
        
        results_container.empty() # "처리 중" 메시지 최종 제거
        # 최종 요약 간소화
        st.info(f"총: {total_items} (시도: {processed_items})")
        st.info(f"성공: {success_count}")
        st.info(f"실패/건너뜀: {error_count}")

        if all_log_messages:
            with st.expander("상세 로그", expanded=error_count > 0): # 오류가 있을 때만 기본으로 펼치기
                for log_entry in all_log_messages:
                    color = "grey"; log_text = log_entry
                    if log_entry.startswith("✅"): color = "green"; log_text = log_entry.replace("✅ ","")
                    elif log_entry.startswith("❌"): color = "red"; log_text = log_entry.replace("❌ ","")
                    elif log_entry.startswith("⚠️"): color = "orange"; log_text = log_entry.replace("⚠️ ","")
                    st.markdown(f"<p style='color:{color}; margin-bottom:0; font-size:small;'>{log_text}</p>", unsafe_allow_html=True)