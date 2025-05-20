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
    # state_manager 모듈에서 STATE_KEYS_TO_SAVE, MOVE_TYPE_OPTIONS는 현재 이 스크립트에서 직접 사용되지 않음
    # 만약 해당 변수들이 필요하다면 주석 해제 또는 data.py 등을 통해 가져오도록 수정
    # from state_manager import STATE_KEYS_TO_SAVE, MOVE_TYPE_OPTIONS
except ImportError as e:
    st.error(f"필수 모듈 로딩 실패: {e}. (google_drive_helper.py, data.py 등을 현재 스크립트와 같은 폴더에 위치시켜주세요)")
    st.stop()

# 시간대 설정
try:
    KST = pytz.timezone("Asia/Seoul")
except pytz.UnknownTimeZoneError:
    st.warning("Asia/Seoul 시간대를 찾을 수 없어 UTC를 사용합니다. 날짜 처리에 영향이 있을 수 있습니다.")
    KST = pytz.utc

# 기본값 설정
DEFAULT_CUSTOMER_NAME = "무명"
DEFAULT_MOVE_TYPE = data.MOVE_TYPE_OPTIONS[0] if hasattr(data, 'MOVE_TYPE_OPTIONS') and data.MOVE_TYPE_OPTIONS else "가정 이사 🏠"
DEFAULT_STORAGE_TYPE = data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦"
DEFAULT_FROM_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
DEFAULT_TO_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
TODAY_ISO_DATE = datetime.now(KST).date().isoformat()

# --- 공통 헬퍼 함수 ---
def parse_date_flexible(date_str_input, current_year):
    """
    다양한 형식의 날짜 문자열 또는 datetime 객체를 YYYY-MM-DD 형식의 문자열로 변환합니다.
    시간 정보는 제거됩니다. "미정"이거나 빈 값이거나 인식 불가능한 형식이면 오늘 날짜를 반환합니다.
    """
    if isinstance(date_str_input, (datetime, date)): # 이미 datetime 또는 date 객체인 경우
        return date_str_input.strftime('%Y-%m-%d')

    if not date_str_input or str(date_str_input).strip().lower() == "미정":
        return TODAY_ISO_DATE # "미정" 또는 빈 값이면 오늘 날짜로 설정

    date_str = str(date_str_input).strip()
    # 시간 정보 제거 시도 (예: "5/10 14시", "2024-05-10 14:00")
    date_str = re.split(r'\s+[0-9]{1,2}\s*[:시]', date_str)[0].strip() # 공백 후 숫자 + : 또는 시

    patterns = [
        # YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, YYYY년 MM월 DD일
        (r'(\d{4})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*(일?)', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        # MM-DD, MM/DD, MM.DD, MM월 DD일 (현재 연도 사용)
        (r'(\d{1,2})\s*[-/월\.]\s*(\d{1,2})\s*(일?)', lambda m: (current_year, int(m.group(1)), int(m.group(2)))),
        # YY-MM-DD, YY/MM/DD, YY.MM.DD (20YY년으로 간주)
        (r'(\d{2})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*(일?)', lambda m: (2000 + int(m.group(1)), int(m.group(2)), int(m.group(3))))
    ]

    for pattern, extractor in patterns:
        match = re.match(pattern, date_str)
        if match:
            # 매치된 부분 외에 다른 문자가 남아있는지 확인하여 정확도 향상 시도
            # 예: "5/10 가" 와 같이 날짜 뒤에 추가 텍스트가 있는 경우를 걸러내기 위함.
            # 하지만 현재 정규식은 이미 날짜로 끝나는 부분을 잘 처리하고 있을 수 있음.
            # 좀 더 엄격하게 하려면, match.group(0) (매치된 전체 문자열)의 길이와
            # 원본 date_str의 길이가 같은지, 또는 남은 부분이 공백인지 등을 확인할 수 있음.
            # 여기서는 기존 로직을 유지하되, 주석으로 가능성을 남겨둡니다.
            # if len(match.group(0)) != len(date_str) and date_str[len(match.group(0)):].strip():
            #     continue # 날짜 패턴 뒤에 유효하지 않은 문자가 있으면 다음 패턴으로
            try:
                year, month, day = extractor(match)
                return datetime(year, month, day).strftime('%Y-%m-%d')
            except ValueError: # 잘못된 날짜 (예: 2월 30일)
                continue

    return TODAY_ISO_DATE # 어떤 패턴과도 맞지 않으면 오늘 날짜로

def normalize_phone_number_for_filename(phone_str):
    if not phone_str or not isinstance(phone_str, str): return None
    return "".join(filter(str.isdigit, phone_str))

def get_default_state():
    # state_manager.py 와 최대한 유사하게 기본값 설정 (필요시 해당 파일에서 가져오도록 수정)
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
        "vehicle_select_radio": "자동 추천 차량 사용",
        "manual_vehicle_select_value": None,
        "final_selected_vehicle": None,
        "recommended_vehicle_auto": None,
        "storage_duration": 1,
        "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "via_point_location": "",
        "via_point_method": DEFAULT_FROM_METHOD, # 경유지 작업 방법 기본값
        "via_point_floor": "",                  # 경유지 층수 기본값
        "via_point_surcharge": 0,
        "regional_ladder_surcharge": 0,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        # state_manager.py에 정의된 다른 모든 키의 기본값을 여기에 추가하는 것이 좋습니다.
        # (예: total_volume, total_weight, 기타 UI 관련 상태 등은 0이나 None, False로)
        "total_volume": 0.0, "total_weight": 0.0,
        "tab3_deposit_amount": 0, "tab3_adjustment_amount": 0, "tab3_regional_ladder_surcharge": 0,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "prev_final_selected_vehicle": None,
        "gdrive_search_term": "", "gdrive_search_results": [],
        "gdrive_file_options_map": {},
        "gdrive_selected_filename": None,
        "gdrive_selected_file_id": None,
    }

def extract_floor_from_address_enhanced(address_str): #
    """
    주소 문자열에서 층수 정보를 추출하고, "OO호" 앞부분을 주소로 사용합니다.
    "XXX호" 패턴이 우선하며, 그 다음 "N층" 패턴을 확인합니다.
    """
    if not address_str or not isinstance(address_str, str):
        return address_str if address_str else "", "" # 입력이 없으면 그대로 반환

    address_cleaned = address_str.strip()
    parsed_floor = ""
    address_part = address_cleaned # 기본 주소 부분은 원본 (수정될 수 있음)

    # 패턴 1: "XXX호" (예: "1102호", "302 호")
    # "호" 바로 앞의 숫자 전체를 캡처. "호" 뒤에 다른 숫자가 오지 않도록 (?!\d) 사용 (예: "101호텔" 방지)
    ho_match = re.search(r'(\d+)\s*호(?!\d)', address_cleaned)
    if ho_match:
        ho_number_str = ho_match.group(1) # "호" 앞의 숫자 문자열 (예: "1102", "302")

        # 층수 파싱: 숫자 길이가 3 이상이면 뒤 2자리 제외 (예: "1102" -> "11"), 그 외는 숫자 전체 사용
        if len(ho_number_str) > 2:
            parsed_floor = ho_number_str[:-2]
        elif len(ho_number_str) > 0:
            parsed_floor = ho_number_str
        # else: ho_number_str이 비었으면 parsed_floor는 "" 유지

        # "OO호" 패턴으로 층수가 성공적으로 파싱된 경우
        if parsed_floor:
            # 주소 부분은 "OO호" 패턴의 시작점 이전까지의 문자열로 정의
            address_part = address_cleaned[:ho_match.start(0)].strip()
            return address_part, parsed_floor
        # else: "OO호" 패턴은 찾았으나 유효한 층수 숫자를 못 얻었으면 (예: "호"만 있거나) 다음 패턴으로 넘어감

    # 패턴 2: 주소 문자열 끝에 "숫자+층/F/f" (예: "OO빌딩 3층", "XX아파트 10F", "엘리베이터 B2층")
    # 이 패턴은 "호" 패턴에서 층수를 찾지 못했을 경우에만 시도됨.
    # ^(.*?) : 주소의 시작부터 최대한 많은 문자 (non-greedy) - 주소 부분
    # (\s*(-?\d+)\s*(층|F|f)) : 공백 + (선택적 마이너스 + 숫자) + 공백 + (층 또는 F 또는 f) - 층수 부분
    # $ : 문자열의 끝
    floor_ending_match = re.search(r'^(.*?)(\s*(-?\d+)\s*(층|F|f))$', address_cleaned, re.IGNORECASE)
    if floor_ending_match:
        address_part = floor_ending_match.group(1).strip() # 층수 부분을 제외한 주소
        parsed_floor = floor_ending_match.group(3)      # 숫자 부분 (음수 포함 가능)
        return address_part, parsed_floor

    # 어떤 패턴에도 해당 없으면, 원래 주소와 빈 층수 반환
    return address_cleaned, ""

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

    parts_before_phone = [p.strip() for p in re.split(r'\s+|\t+', before_phone) if p.strip()]
    potential_name_parts = []
    date_found_in_before = False

    # 텍스트 첫 부분에서 날짜 우선 파싱
    if parts_before_phone:
        first_part_for_date = parts_before_phone[0]
        parsed_date_from_first = parse_date_flexible(first_part_for_date, current_year)
        # 첫 부분이 성공적으로 다른 날짜로 파싱되거나, 또는 오늘이지만 원본이 비어있지 않고 "미정"도 아니면
        if parsed_date_from_first != TODAY_ISO_DATE or \
           (parsed_date_from_first == TODAY_ISO_DATE and first_part_for_date and first_part_for_date.lower() != "미정"):
            state["moving_date"] = parsed_date_from_first
            date_found_in_before = True
            potential_name_parts.extend(parts_before_phone[1:]) # 첫 부분을 날짜로 썼으니 이름은 나머지
        else: # 첫 부분이 날짜가 아니면, 전체를 이름 후보로
            potential_name_parts.extend(parts_before_phone)
    
    # 이름 후보들 중에서 다시 날짜 찾아보기 (첫 부분이 날짜가 아니었을 경우)
    if not date_found_in_before:
        temp_name_parts = []
        for part in potential_name_parts:
            parsed_date = parse_date_flexible(part, current_year)
            if not date_found_in_before and \
               (parsed_date != TODAY_ISO_DATE or \
               (parsed_date == TODAY_ISO_DATE and part and part.lower() != "미정")):
                state["moving_date"] = parsed_date
                date_found_in_before = True
            else:
                temp_name_parts.append(part)
        potential_name_parts = temp_name_parts


    if potential_name_parts:
        state["customer_name"] = " ".join(potential_name_parts)
    else: # 이름 부분이 없으면 기본값
        state["customer_name"] = DEFAULT_CUSTOMER_NAME

    if not date_found_in_before: # 그래도 날짜 못 찾았으면 오늘 날짜
        state["moving_date"] = TODAY_ISO_DATE

    if "보관" in state["customer_name"]:
        state["is_storage_move"] = True
        state["storage_type"] = DEFAULT_STORAGE_TYPE

    parts_after_phone = [p.strip() for p in re.split(r'\s{2,}|\t+', after_phone) if p.strip()]
    if not parts_after_phone and after_phone:
        parts_after_phone = [after_phone]

    part_idx = 0
    if part_idx < len(parts_after_phone):
        current_part_lower = parts_after_phone[part_idx].lower()
        found_move_type_keyword = False
        for type_key_text, keywords_text in MOVE_TYPE_KEYWORDS_TEXT.items():
            for kw in keywords_text:
                if current_part_lower == kw:
                    if type_key_text == "가정": state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
                    elif type_key_text == "사무실": state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE)
                    parts_after_phone.pop(part_idx)
                    found_move_type_keyword = True; break
                elif current_part_lower.startswith(kw + " ") and len(current_part_lower) > len(kw) + 1:
                    if type_key_text == "가정": state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
                    elif type_key_text == "사무실": state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE)
                    parts_after_phone[part_idx] = parts_after_phone[part_idx][len(kw):].strip()
                    found_move_type_keyword = True; break
            if found_move_type_keyword: break
    
    # 출발지
    if part_idx < len(parts_after_phone):
        from_loc_raw = parts_after_phone[part_idx]
        state["from_location"], state["from_floor"] = extract_floor_from_address_enhanced(from_loc_raw) #
        part_idx += 1
    else:
        if not state.get("from_location"): return None, None, f"{line_number_display}출발지 주소 없음 (필수)"
    
    # 도착지
    if part_idx < len(parts_after_phone):
        to_loc_raw = parts_after_phone[part_idx]
        skip_keywords_for_to_location = ["에어컨", "장롱", "조립", "이전", "설치", "보관", "폐기"]
        if not any(keyword in to_loc_raw for keyword in skip_keywords_for_to_location):
            state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_loc_raw) #
            part_idx += 1

    if part_idx < len(parts_after_phone):
        state["special_notes"] = " ".join(parts_after_phone[part_idx:])

    if not state.get("from_location"):
        return None, None, f"{line_number_display}출발지 누락 (재확인 필요)"

    return state, filename_phone_part + ".json", None


# --- 엑셀 입력 처리 함수 ---
COLUMN_ALIASES_EXCEL = {
    'moving_date': ['날짜', '이사날짜', '일자'], # '일자' 추가
    'customer_name': ['고객명', '이름', '성함', '상호'], # '상호' 추가
    'customer_phone': ['전화번호', '연락처', '휴대폰번호', '전화', '핸드폰', 'H.P', 'HP'], # H.P, HP 추가
    'base_move_type': ['이사종류', '구분', '종류'], # '종류' 추가
    'from_location': ['출발지주소', '출발지', '출발주소', '출발'], # '출발주소' 추가
    'from_floor': ['층수', '출발지 층수', '출발층수', '출발 층'],
    'to_location': ['도착지주소', '도착지', '도착주소', '도착'],
    'to_floor': ['도착지 층수', '도착층수', '도착 층'],
    'special_notes': ['특이사항', '요구사항', '희망사항', '건의', '메모', '비고', '참고사항'], # '참고사항' 추가
}
def get_column_value(row, field_name, aliases, default=""):
    all_possible_names = [field_name.lower()] + [a.lower() for a in aliases.get(field_name, [])]
    # 엑셀 컬럼명을 소문자로 변환하여 비교 (대소문자 구분 없애기 위함)
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
    # 날짜 파싱 결과에 대한 추가 로그 (사용자 요청 사항 간접 반영)
    if moving_date_raw and moving_date_raw.strip().lower() != "미정" and state["moving_date"] == TODAY_ISO_DATE:
        # st.sidebar.info(f"{row_number_display}제공된 날짜 '{moving_date_raw}'가 오늘 날짜로 처리됨 (형식 확인 필요).") # UI 피드백
        pass # 로그는 최종 결과에서 출력

    customer_name_raw = get_column_value(row, 'customer_name', COLUMN_ALIASES_EXCEL)
    if customer_name_raw and customer_name_raw.lower() != "미정":
        state["customer_name"] = customer_name_raw
    else:
        state["customer_name"] = DEFAULT_CUSTOMER_NAME
    if "보관" in state["customer_name"]:
        state["is_storage_move"] = True; state["storage_type"] = DEFAULT_STORAGE_TYPE

    customer_phone_raw = get_column_value(row, 'customer_phone', COLUMN_ALIASES_EXCEL)
    if not customer_phone_raw: return None, None, f"{row_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = customer_phone_raw
    filename_phone_part = normalize_phone_number_for_filename(customer_phone_raw)
    if not filename_phone_part: return None, None, f"{row_number_display}유효하지 않은 전화번호"

    move_type_raw = get_column_value(row, 'base_move_type', COLUMN_ALIASES_EXCEL)
    if move_type_raw:
        move_type_char = move_type_raw.strip().lower()
        if any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["가정"]) or "가정" in move_type_char:
            state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
        elif any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["사무실"]) or "사무실" in move_type_char:
            state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE)

    from_location_raw = get_column_value(row, 'from_location', COLUMN_ALIASES_EXCEL)
    if not from_location_raw: return None, None, f"{row_number_display}출발지 주소 없음 (필수)"
    from_floor_raw_col = get_column_value(row, 'from_floor', COLUMN_ALIASES_EXCEL)
    if from_floor_raw_col: # 명시적 층수 컬럼값이 있으면 사용
        state["from_floor"] = "".join(filter(str.isdigit, from_floor_raw_col)) # B, F 등 문자 제거
        state["from_location"] = from_location_raw # 주소는 그대로 사용
    else: # 없으면 주소에서 추출
        state["from_location"], state["from_floor"] = extract_floor_from_address_enhanced(from_location_raw) #

    to_location_raw = get_column_value(row, 'to_location', COLUMN_ALIASES_EXCEL)
    to_floor_raw_col = get_column_value(row, 'to_floor', COLUMN_ALIASES_EXCEL)
    if to_location_raw or to_floor_raw_col:
        if to_floor_raw_col:
            state["to_floor"] = "".join(filter(str.isdigit, to_floor_raw_col))
            if to_location_raw: state["to_location"] = to_location_raw
        elif to_location_raw:
             state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_location_raw) #

    state["special_notes"] = get_column_value(row, 'special_notes', COLUMN_ALIASES_EXCEL)

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
                              placeholder="예시: 홍길동 010-1234-5678 5/10 가 서울 강남구 XXX 101동 302호 경기 수원시 YYY 202동 1102호 에어컨 이전 설치\n또는: 010-9876-5432 강남 아파트 102동 1501호 용인 빌라 303호 5/12")
else: # Excel 파일 업로드
    uploaded_file = st.file_uploader("변환할 Excel 파일을 업로드하세요.", type=["xlsx", "xls"])
    st.markdown("""
    **Excel 파일 형식 가이드:**
    - 첫 번째 행은 헤더(컬럼명)여야 합니다.
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
                df.columns = [str(col).strip() for col in df.columns]
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
            row_display_prefix = f"엑셀 {df.index[i]+2}행" if is_excel_input and hasattr(df, 'index') else (f"엑셀 {i+2}행" if is_excel_input else f"텍스트 {i+1}줄")


            if is_excel_input:
                status_obj, filename, error_msg = parse_excel_row_to_json(item_data_row_or_line, current_year_for_parsing, row_display_prefix + ": ")
                # 엑셀에서 날짜 파싱 관련 로그 추가
                if status_obj and item_data_row_or_line is not None: # item_data_row_or_line이 Series 객체인지 확인
                    moving_date_raw_excel = get_column_value(item_data_row_or_line, 'moving_date', COLUMN_ALIASES_EXCEL)
                    if moving_date_raw_excel and moving_date_raw_excel.strip().lower() != "미정" and status_obj.get("moving_date") == TODAY_ISO_DATE:
                         all_log_messages.append(f"🔔 <span style='color:blue;'>정보</span>: {row_display_prefix} 제공된 날짜 '{moving_date_raw_excel}'가 오늘 날짜로 처리됨 (형식 또는 내용 확인 필요). {filename if filename else ''}")

            else: # 텍스트 입력
                status_obj, filename, error_msg = parse_line_to_json_flexible(item_data_row_or_line, current_year_for_parsing, row_display_prefix + ": ")
                # 텍스트 첫 부분 날짜 파싱 관련 로그 (필요시 추가)
                if status_obj and original_line: # original_line 변수는 parse_line_to_json_flexible 내부 변수라 여기서 직접 접근은 어려움.
                                                 # error_msg에 관련 내용을 포함시키거나, parse_line_to_json_flexible에서 반환값을 수정해야 함.
                                                 # 여기서는 일단 생략.
                    pass


            status_text.text(f"처리 중... {processed_items}/{total_items} ({filename if filename else '데이터 분석 중'})")
            progress_bar.progress(processed_items / total_items if total_items > 0 else 0)

            log_identifier_parts = []
            if status_obj and status_obj.get('customer_phone'): log_identifier_parts.append(status_obj['customer_phone'])
            if status_obj and status_obj.get('customer_name') != DEFAULT_CUSTOMER_NAME : log_identifier_parts.append(status_obj['customer_name'])
            log_identifier = f"({', '.join(log_identifier_parts)})" if log_identifier_parts else ""

            if status_obj and filename:
                final_state_to_save = get_default_state()
                final_state_to_save.update(status_obj)
                try:
                    gdrive_folder_id_secret = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")
                    save_result = gdrive.save_json_file(filename, final_state_to_save, folder_id=gdrive_folder_id_secret)
                    if save_result and save_result.get('id'):
                        log_message = f"✅ <span style='color:green;'>저장 성공</span>: {filename} {log_identifier} (ID: {save_result.get('id')})"
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
            expanded_log = (error_count > 0 or success_count < total_items or any("정보" in log for log in all_log_messages)) # 정보 로그도 펼침 조건 추가
            with st.expander("▼ 상세 처리 로그 보기 (클릭)", expanded=expanded_log):
                log_html = "".join([f"<div style='font-size:small; margin-bottom:3px;'>{log.replace('✅','✔️').replace('🔔','ℹ️')}</div>" for log in all_log_messages])
                st.markdown(log_html, unsafe_allow_html=True)
