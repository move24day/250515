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
# MOVE_TYPE_OPTIONS는 data.py 또는 다른 설정 파일에서 가져오는 것이 이상적
# 여기서는 data.py에 정의된 것을 사용하도록 가정 (실제 data.py 구조에 따라 수정 필요)
DEFAULT_MOVE_TYPE = data.MOVE_TYPE_OPTIONS[0] if hasattr(data, 'MOVE_TYPE_OPTIONS') and data.MOVE_TYPE_OPTIONS else "가정 이사 🏠"
DEFAULT_STORAGE_TYPE = data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦"
DEFAULT_FROM_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
DEFAULT_TO_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
TODAY_ISO_DATE = datetime.now(KST).date().isoformat()

# --- 공통 헬퍼 함수 ---
def parse_date_flexible(date_str_input, current_year):
    """
    다양한 형식의 날짜 문자열 또는 datetime 객체를 YYYY-MM-DD 형식의 문자열로 변환합니다.
    시간 정보는 제거됩니다. "미정"이거나 빈 값이면 오늘 날짜를 반환합니다.
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
            # 날짜 문자열 전체가 패턴과 일치하는지 확인 (예: "5/10 가" 방지)
            # 정규식의 `\s*(일?)` 등이 있어 추가 텍스트가 있어도 매치될 수 있으므로,
            # 매치된 부분 외에 다른 문자가 남아있는지 확인 필요.
            # 여기서는 패턴 자체가 날짜 부분만 정확히 커버하도록 가정.
            # 만약 패턴이 "5/10"까지만 매치하고 뒤에 " 가"가 남는다면,
            # date_str[len(match.group(0)):].strip() 으로 남은 부분을 확인할 수 있음.
            # 이 코드에서는 일단 매치되면 날짜로 간주.
            try:
                year, month, day = extractor(match)
                return datetime(year, month, day).strftime('%Y-%m-%d')
            except ValueError: # 잘못된 날짜 (예: 2월 30일)
                continue
                
    return TODAY_ISO_DATE # 어떤 패턴과도 맞지 않으면 오늘 날짜로 (요청에 따라 None 반환도 가능)

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
        # ... 기타 필요한 모든 키의 기본값 추가 (state_manager.py 참고)
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
        "via_point_method": DEFAULT_FROM_METHOD,
        "via_point_surcharge": 0,
        "regional_ladder_surcharge": 0,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
    }

def extract_floor_from_address_enhanced(address_str):
    """
    주소 문자열에서 층수 정보를 추출합니다.
    "XXX호" 패턴의 경우, 숫자 뒤 2자리를 제외한 앞부분을 층수로 간주합니다.
    (예: "1102호" -> 11층, "302호" -> 3층)
    "N층" 패턴도 처리합니다.
    """
    if not address_str or not isinstance(address_str, str):
        return address_str if address_str else "", ""

    address_cleaned = address_str.strip()
    floor_str = ""

    # 패턴 1: "XXX호" (예: "1102호", "302 호")
    # "호" 바로 앞의 숫자 전체를 캡처하고, "호" 및 앞뒤 공백 제거 시도
    ho_match = re.search(r'(\d+)\s*호(?!\d)', address_cleaned) # "호" 뒤에 숫자가 오지 않는 경우 (예: "101호텔" 방지)
    if ho_match:
        ho_number_str = ho_match.group(1) # "1102", "302"
        
        if len(ho_number_str) > 2 : # 3자리 이상 (예: 302, 1102)
            floor_str = ho_number_str[:-2] # 뒤 2자리 제외 (302 -> 3, 1102 -> 11)
        elif len(ho_number_str) > 0 : # 1~2자리 (예: 52호, 2호) -> 그대로 사용 (예: 52, 2) - 이 부분은 정책에 따라 변경 가능
             floor_str = ho_number_str
        # else: 숫자가 없으면 floor_str은 "" 유지

        # 주소에서 "XXX호" 부분 제거 시도 (더 정확하게)
        # 주의: "XXX호"가 주소 중간에 있을 수도 있고, 끝에 있을 수도 있음
        # address_cleaned = re.sub(r'\s*' + re.escape(ho_match.group(0)) + r'\s*', ' ', address_cleaned, 1).strip()
        # 위 방식은 복잡하고 오류 가능성 있음. "XXX호"를 포함한 전체 매치 부분을 제거하는 것이 더 안전할 수 있으나,
        # "XXX호"가 항상 주소의 불필요한 부분이 아닐 수도 있음 (예: 건물 이름 자체가 "101호 빌딩")
        # 여기서는 일단 "호"까지만 보고 층수를 추출하고, 주소는 원본에서 크게 변경하지 않는 방향으로 접근.
        # 사용자가 명시적으로 "101동 302호"에서 "302호"를 제거하고 싶다면, 해당 로직 추가 필요.
        # 현재는 주소에서 "호" 관련 부분을 적극적으로 제거하지 않음.
        # 다만, "OO아파트 101동 1102호" -> "OO아파트 101동 " 과 같이 뒤에 붙은 호수만 제거하는 정도는 고려 가능
        
        # "XXX호"가 주소 끝에 명확히 있을 때만 제거
        address_cleaned_temp = re.sub(r'\s+\d+\s*호$', '', address_cleaned) 
        if address_cleaned_temp != address_cleaned: # 실제로 제거가 일어났다면
            address_cleaned = address_cleaned_temp.strip()
        
        # 추출된 층수가 있으면 반환
        if floor_str:
            return address_cleaned, floor_str

    # 패턴 2: 주소 끝에 "숫자+층/F/f" (예: "OO빌딩 3층", "XX아파트 10F")
    # 이 패턴은 "호" 패턴보다 우선순위가 낮아야 함. ("101호 3층" 같은 경우 "호"에서 먼저 처리)
    floor_ending_match = re.search(r'^(.*?)(\s*(-?\d+)\s*(층|F|f))$', address_cleaned, re.IGNORECASE)
    if floor_ending_match:
        address_part = floor_ending_match.group(1).strip()
        floor_num_part = floor_ending_match.group(3)
        return address_part, floor_num_part
        
    return address_cleaned, "" # 어떤 패턴에도 해당 없으면, 원래 주소와 빈 층수 반환

# --- 텍스트 입력 처리 함수 ---
PHONE_REGEX_TEXT = re.compile(r'(01[016789]-?\d{3,4}-?\d{4}|0\d{1,2}-?\d{3,4}-?\d{4})')
MOVE_TYPE_KEYWORDS_TEXT = {"가정": ["가정", "가"], "사무실": ["사무실", "사"]} # data.py의 MOVE_TYPE_OPTIONS 와 연계 고려

def parse_line_to_json_flexible(line_text, current_year, line_number_display=""):
    state = get_default_state() # 기본 상태로 초기화
    original_line = line_text.strip()
    if not original_line: return None, None, f"{line_number_display}빈 줄"

    # 1. 전화번호 파싱 (필수)
    phone_match = PHONE_REGEX_TEXT.search(original_line)
    if not phone_match: return None, None, f"{line_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = phone_match.group(0)
    filename_phone_part = normalize_phone_number_for_filename(state["customer_phone"])
    if not filename_phone_part: return None, None, f"{line_number_display}유효하지 않은 전화번호"

    # 전화번호 기준 앞/뒤 텍스트 분리
    before_phone = original_line[:phone_match.start()].strip()
    after_phone = original_line[phone_match.end():].strip()

    # 2. 이름 및 날짜 파싱 (전화번호 앞 부분)
    # 이름과 날짜는 공백 또는 탭으로 구분될 수 있음
    # 예: "홍길동 05/10", "05/10 홍길동", "홍길동", "05/10"
    parts_before_phone = [p.strip() for p in re.split(r'\s+|\t+', before_phone) if p.strip()] # 공백 또는 탭으로 분리

    potential_name_parts = []
    date_found_in_before = False
    for part in parts_before_phone:
        parsed_date = parse_date_flexible(part, current_year) # YYYY-MM-DD 형식 또는 오늘날짜 반환
        if parsed_date != TODAY_ISO_DATE or (parsed_date == TODAY_ISO_DATE and part.strip() != "" and part.strip().lower() !="미정"): # 명시적 날짜 입력으로 간주
            # "미정"이나 빈 값이 아닌데 오늘 날짜로 파싱된 경우는, 실제 날짜 입력으로 봄.
            # 또는 오늘이 아닌 다른 날짜로 파싱된 경우.
            if not date_found_in_before : # 첫 번째 유효한 날짜를 이사 날짜로 설정
                 state["moving_date"] = parsed_date
                 date_found_in_before = True
            # else: 여러 날짜가 있으면 첫 번째 것만 사용 (또는 다른 로직 적용 가능)
        else: # 날짜로 파싱되지 않은 부분은 이름의 일부로 간주
            potential_name_parts.append(part)
    
    if potential_name_parts:
        state["customer_name"] = " ".join(potential_name_parts)
    else: # 전화번호 앞에 이름 부분이 없으면
        state["customer_name"] = DEFAULT_CUSTOMER_NAME # 기본값 "무명" 사용

    if not date_found_in_before: # 전화번호 앞에서 날짜를 못 찾았으면
        state["moving_date"] = TODAY_ISO_DATE # 오늘 날짜로 설정

    # 고객명에서 "보관" 키워드 확인 (기존 로직 유지)
    if "보관" in state["customer_name"]:
        state["is_storage_move"] = True
        state["storage_type"] = DEFAULT_STORAGE_TYPE

    # 3. 이사 유형, 주소, 메모 파싱 (전화번호 뒷 부분)
    # 예: "가 서울 강남구 XXX 101동 302호 경기 수원시 YYY 202동 1102호 에어컨 이전 설치"
    # 예: "사무실 용산구 ... 성동구 ... 파티션 분해조립"
    # 예: "서울 강남구 XXX 101동 302호" (유형, 도착지, 메모 생략된 경우)

    parts_after_phone = [p.strip() for p in re.split(r'\s{2,}|\t+', after_phone) if p.strip()] # 2개 이상 공백 또는 탭으로 분리
    if not parts_after_phone and after_phone: # 분리되지 않았지만 내용이 있으면 전체를 한 덩어리로
        parts_after_phone = [after_phone]
        
    part_idx = 0

    # 이사 유형 ("가", "사") 먼저 체크 (선택적)
    if part_idx < len(parts_after_phone):
        current_part_lower = parts_after_phone[part_idx].lower()
        found_move_type_keyword = False
        for type_key_text, keywords_text in MOVE_TYPE_KEYWORDS_TEXT.items(): # 가정, 사무실
            # 키워드가 정확히 일치하거나, 키워드로 시작하고 바로 뒤에 다른 내용이 오는 경우
            # (예: "가 서울...", "사무실 용산...")
            for kw in keywords_text: # "가정", "가" 또는 "사무실", "사"
                if current_part_lower == kw: # 정확히 "가" 또는 "사무실"
                    # data.py의 MOVE_TYPE_OPTIONS와 매핑 (이모티콘 포함된 값으로)
                    if type_key_text == "가정" and hasattr(data, 'MOVE_TYPE_OPTIONS') and data.MOVE_TYPE_OPTIONS:
                        state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
                    elif type_key_text == "사무실" and hasattr(data, 'MOVE_TYPE_OPTIONS') and data.MOVE_TYPE_OPTIONS:
                        state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE)
                    
                    parts_after_phone.pop(part_idx) # 해당 파트 소모 (인덱스 조정 필요 없게끔)
                    found_move_type_keyword = True
                    break 
                elif current_part_lower.startswith(kw + " ") and len(current_part_lower) > len(kw) + 1: # "가 서울..."
                    if type_key_text == "가정" and hasattr(data, 'MOVE_TYPE_OPTIONS') and data.MOVE_TYPE_OPTIONS:
                        state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
                    elif type_key_text == "사무실" and hasattr(data, 'MOVE_TYPE_OPTIONS') and data.MOVE_TYPE_OPTIONS:
                        state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE)

                    parts_after_phone[part_idx] = parts_after_phone[part_idx][len(kw):].strip() # 키워드 제거 후 남은 부분으로 업데이트
                    found_move_type_keyword = True
                    break
            if found_move_type_keyword:
                break 
        # 이사 유형 키워드가 첫 파트에 없었으면, part_idx는 그대로 0, parts_after_phone도 그대로.

    # 출발지 주소 및 층수 (필수)
    if part_idx < len(parts_after_phone):
        from_loc_raw = parts_after_phone[part_idx]
        state["from_location"], state["from_floor"] = extract_floor_from_address_enhanced(from_loc_raw)
        part_idx += 1
    else: # 전화번호 뒤에 아무 내용도 없으면 출발지 누락
        if not state.get("from_location"): # 혹시 다른 경로로 이미 채워지지 않았다면
             return None, None, f"{line_number_display}출발지 주소 없음 (필수)"


    # 도착지 주소 및 층수 (선택적)
    if part_idx < len(parts_after_phone):
        # 다음 파트가 도착지로 간주될 수 있는지? (예: 특정 키워드, 또는 단순히 다음 주소 형태)
        # 여기서는 일단 다음 파트를 도착지로 간주.
        # 만약 다음 파트가 명백히 메모처럼 보이면 (예: "에어컨", "조립") 도착지는 없는 것으로 처리해야 함.
        # 간단하게는, 남은 파트가 1개 초과일 때만 두 번째를 도착지로 볼 수도 있음.
        # 여기서는 일단 순서대로 할당.
        to_loc_raw = parts_after_phone[part_idx]
        # 도착지가 될 수 없는 키워드 예시 (이런 경우 메모로 넘김)
        skip_keywords_for_to_location = ["에어컨", "장롱", "조립", "이전", "설치", "보관", "폐기"] # 더 추가 가능
        if not any(keyword in to_loc_raw for keyword in skip_keywords_for_to_location):
            state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_loc_raw)
            part_idx += 1
        # else: 도착지로 보이지 않으면, 이 파트는 아래 메모로 합쳐짐.
    
    # 특이사항 (나머지 부분)
    if part_idx < len(parts_after_phone):
        state["special_notes"] = " ".join(parts_after_phone[part_idx:])

    # 최종 출발지 확인
    if not state.get("from_location"): # 다시 한번 출발지 필수 확인
        return None, None, f"{line_number_display}출발지 누락 (재확인 필요)"
        
    return state, filename_phone_part + ".json", None


# --- 엑셀 입력 처리 함수 ---
COLUMN_ALIASES_EXCEL = {
    'moving_date': ['날짜', '이사날짜'], 
    'customer_name': ['고객명', '이름', '성함'],
    'customer_phone': ['전화번호', '연락처', '휴대폰번호', '전화', '핸드폰'], 
    'base_move_type': ['이사종류', '구분'], # '가', '사' 또는 "가정이사", "사무실이사" 등
    'from_location': ['출발지주소', '출발지', '출발'], 
    'from_floor': ['층수', '출발지 층수', '출발층수', '출발 층'], # '출발 층' 추가
    'to_location': ['도착지주소', '도착지', '도착주소', '도착'], 
    'to_floor': ['도착지 층수', '도착층수', '도착 층'], # '도착 층' 추가
    'special_notes': ['특이사항', '요구사항', '희망사항', '건의', '메모', '비고'], # '메모', '비고' 추가
}
def get_column_value(row, field_name, aliases, default=""):
    # field_name 자체도 컬럼명으로 간주
    all_possible_names = [field_name] + aliases.get(field_name, [])
    for alias in all_possible_names:
        if alias in row.index and pd.notna(row[alias]):
            return str(row[alias]).strip()
    return default

def parse_excel_row_to_json(row, current_year, row_number_display=""):
    state = get_default_state()
    if row.isnull().all() or all(str(x).strip() == "" for x in row if pd.notna(x)):
        return None, None, f"{row_number_display}빈 행"

    # 날짜
    moving_date_raw = get_column_value(row, 'moving_date', COLUMN_ALIASES_EXCEL)
    state["moving_date"] = parse_date_flexible(moving_date_raw, current_year) # 없으면 오늘 날짜 반환

    # 고객명
    customer_name_raw = get_column_value(row, 'customer_name', COLUMN_ALIASES_EXCEL)
    if customer_name_raw and customer_name_raw.lower() != "미정":
        state["customer_name"] = customer_name_raw
    else: # 이름이 없거나 "미정"이면
        state["customer_name"] = DEFAULT_CUSTOMER_NAME
    
    if "보관" in state["customer_name"]: # 고객명에 "보관" 있으면 보관이사 처리
        state["is_storage_move"] = True
        state["storage_type"] = DEFAULT_STORAGE_TYPE

    # 전화번호 (필수)
    customer_phone_raw = get_column_value(row, 'customer_phone', COLUMN_ALIASES_EXCEL)
    if not customer_phone_raw: return None, None, f"{row_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = customer_phone_raw
    filename_phone_part = normalize_phone_number_for_filename(customer_phone_raw)
    if not filename_phone_part: return None, None, f"{row_number_display}유효하지 않은 전화번호"

    # 이사 종류
    move_type_raw = get_column_value(row, 'base_move_type', COLUMN_ALIASES_EXCEL)
    if move_type_raw:
        move_type_char = move_type_raw.strip().lower()
        # data.py의 MOVE_TYPE_OPTIONS (이모티콘 포함된 원본)과 매핑
        if any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["가정"]) or "가정" in move_type_char:
            state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE) if hasattr(data, 'MOVE_TYPE_OPTIONS') else DEFAULT_MOVE_TYPE
        elif any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["사무실"]) or "사무실" in move_type_char:
            state["base_move_type"] = next((opt for opt in data.MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE) if hasattr(data, 'MOVE_TYPE_OPTIONS') else DEFAULT_MOVE_TYPE
        # else: 일치하는 유형 없으면 기본값(state 초기값) 유지

    # 출발지 주소 (필수) 및 층수
    from_location_raw = get_column_value(row, 'from_location', COLUMN_ALIASES_EXCEL)
    if not from_location_raw: return None, None, f"{row_number_display}출발지 주소 없음 (필수)"
    
    from_floor_raw_col = get_column_value(row, 'from_floor', COLUMN_ALIASES_EXCEL) # 엑셀의 명시적 층수 컬럼
    if from_floor_raw_col:
        state["from_floor"] = "".join(filter(str.isdigit, from_floor_raw_col)) # 숫자만 추출
        state["from_location"] = from_location_raw # 주소도 함께 저장
    else: # 명시적 층수 컬럼 없으면 주소에서 추출 시도
        state["from_location"], state["from_floor"] = extract_floor_from_address_enhanced(from_location_raw)

    # 도착지 주소 및 층수 (선택적)
    to_location_raw = get_column_value(row, 'to_location', COLUMN_ALIASES_EXCEL)
    to_floor_raw_col = get_column_value(row, 'to_floor', COLUMN_ALIASES_EXCEL) # 엑셀의 명시적 층수 컬럼
    if to_location_raw or to_floor_raw_col : # 도착지 주소나 층수 중 하나라도 있으면 처리
        if to_floor_raw_col:
            state["to_floor"] = "".join(filter(str.isdigit, to_floor_raw_col))
            if to_location_raw: state["to_location"] = to_location_raw
        elif to_location_raw: # 층수 컬럼은 없지만 주소는 있을 때
            state["to_location"], state["to_floor"] = extract_floor_from_address_enhanced(to_location_raw)
    
    # 특이사항
    state["special_notes"] = get_column_value(row, 'special_notes', COLUMN_ALIASES_EXCEL)
    
    # 최종 출발지 확인
    if not state.get("from_location"):
        return None, None, f"{row_number_display}출발지 누락 (재확인 필요)"
        
    return state, filename_phone_part + ".json", None


# --- Streamlit UI ---
st.set_page_config(page_title="이사정보 JSON 변환기", layout="wide") # 오타 수정: 이사견적 -> 이사정보
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
    - 필수 컬럼: `전화번호`, `출발지주소` (또는 `출발지`, `출발` 등 유사어)
    - 선택 컬럼: `날짜`, `고객명`, `이사종류`('가' 또는 '사', 또는 "가정 이사", "사무실 이사"), `출발지 층수`, `도착지주소`, `도착지 층수`, `특이사항` (또는 `메모`, `비고` 등 유사어)
    - 층수는 주소에서 "XXX호" 패턴(예: "강남아파트 101동 302호" -> 3층) 또는 "N층" 패턴으로 자동인식 시도. 명시적 층수 컬럼이 우선합니다.
    - 고객명에 "보관"이 포함되면 보관이사로 처리됩니다.
    - 날짜가 없으면 오늘 날짜, 고객명이 없으면 "무명"으로 자동 입력됩니다.
    """)

if st.button("🔄 JSON 변환 및 Google Drive에 저장하기"):
    current_year_for_parsing = datetime.now(KST).year # parse_date_flexible에 전달될 현재 연도
    success_count = 0; error_count = 0; processed_items = 0; total_items = 0
    all_log_messages = []; items_to_process = []; is_excel_input = False # 변수명 변경
    
    if input_method == '텍스트 직접 입력':
        if not text_input.strip():
            st.warning("입력된 텍스트가 없습니다.")
        else:
            items_to_process = [line for line in text_input.strip().split('\n') if line.strip()]
            total_items = len(items_to_process)
    elif input_method == 'Excel 파일 업로드':
        is_excel_input = True # Excel 입력임을 표시
        if uploaded_file is None:
            st.warning("업로드된 파일이 없습니다.")
        else:
            try:
                try: df = pd.read_excel(uploaded_file, engine='openpyxl')
                except Exception: # openpyxl 실패 시 xlrd 시도
                    uploaded_file.seek(0); df = pd.read_excel(uploaded_file, engine='xlrd')
                
                df.columns = [str(col).strip() for col in df.columns] # 컬럼명 공백 제거
                items_to_process = [row for _, row in df.iterrows() if not row.isnull().all()] # 빈 행 제외
                total_items = len(items_to_process)
            except Exception as e:
                st.error(f"Excel 파일 읽기 중 오류 발생: {e}"); items_to_process = []
    
    if not items_to_process:
        if text_input.strip() or uploaded_file: # 입력 시도는 있었으나 처리할 데이터가 없는 경우
            st.info("변환할 유효한 데이터가 없습니다. 입력 내용을 확인해주세요.")
    else:
        st.subheader("✨ 처리 결과")
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, item_data_row_or_line in enumerate(items_to_process):
            processed_items += 1
            status_obj, filename, error_msg = (None, None, "알 수 없는 입력 형식 또는 처리 오류") # 기본 오류 메시지
            
            # 각 줄/행 번호 표시용 접두사
            row_display_prefix = f"엑셀 {i+2}행" if is_excel_input else f"텍스트 {i+1}줄"

            if is_excel_input:
                status_obj, filename, error_msg = parse_excel_row_to_json(item_data_row_or_line, current_year_for_parsing, row_display_prefix + ": ")
            else: # 텍스트 입력
                status_obj, filename, error_msg = parse_line_to_json_flexible(item_data_row_or_line, current_year_for_parsing, row_display_prefix + ": ")

            status_text.text(f"처리 중... {processed_items}/{total_items} ({filename if filename else '데이터 분석 중'})")
            progress_bar.progress(processed_items / total_items if total_items > 0 else 0)

            # 로그용 식별자 생성
            log_identifier_parts = []
            if status_obj and status_obj.get('customer_phone'): log_identifier_parts.append(status_obj['customer_phone'])
            if status_obj and status_obj.get('customer_name') != DEFAULT_CUSTOMER_NAME : log_identifier_parts.append(status_obj['customer_name'])
            log_identifier = f"({', '.join(log_identifier_parts)})" if log_identifier_parts else ""

            if status_obj and filename: # 성공적으로 파싱된 경우
                final_state_to_save = get_default_state() # 항상 기본 상태로 시작
                final_state_to_save.update(status_obj)    # 파싱된 데이터로 업데이트
                
                # STATE_KEYS_TO_SAVE 필터링 로직은 현재 사용 안 함 (모든 파싱된 키 저장)
                # 필요시 state_manager.py에서 STATE_KEYS_TO_SAVE를 가져와 필터링 가능
                
                try:
                    gdrive_folder_id_secret = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")
                    # gdrive.save_json_file 함수는 google_drive_helper.py에 정의되어 있어야 함
                    save_result = gdrive.save_json_file(filename, final_state_to_save, folder_id=gdrive_folder_id_secret)
                    if save_result and save_result.get('id'):
                        log_message = f"✅ <span style='color:green;'>저장 성공</span>: {filename} {log_identifier} (ID: {save_result.get('id')})"
                        all_log_messages.append(log_message); success_count += 1
                    else:
                        log_message = f"❌ <span style='color:red;'>저장 실패</span>: {filename} {log_identifier} (응답: {save_result})"
                        all_log_messages.append(log_message); error_count += 1
                except AttributeError as ae: # gdrive 모듈에 save_json_file 함수가 없을 경우 등
                     log_message = f"❌ <span style='color:red;'>저장 함수 오류</span>: {filename} {log_identifier} (오류: {ae})"
                     all_log_messages.append(log_message); error_count += 1
                except Exception as e_save:
                    log_message = f"❌ <span style='color:red;'>저장 중 예외</span>: {filename if filename else '데이터'} {log_identifier} ({str(e_save)})"
                    all_log_messages.append(log_message); error_count += 1
            else: # 파싱 실패 또는 필수 정보 누락
                log_message = f"⚠️ <span style='color:orange;'>건너뜀/오류</span>: {error_msg if error_msg else '사유 불명'} {log_identifier}"
                all_log_messages.append(log_message); error_count +=1
        
        status_text.empty(); progress_bar.empty() # 진행 상태 초기화
        st.info(f"총 분석 대상: {total_items} 건 (실제 처리 시도: {processed_items} 건)")
        st.success(f"Google Drive 저장 성공: {success_count} 건")
        if error_count > 0: st.error(f"실패 또는 건너뜀: {error_count} 건")
        else: st.info(f"실패 또는 건너뜀: {error_count} 건") # 오류가 없어도 건너뛴 항목이 있을 수 있음

        if all_log_messages:
            # 오류가 있거나, 성공 건수가 전체 건수보다 적을 때만 기본으로 펼쳐서 보여줌
            expanded_log = (error_count > 0 or success_count < total_items)
            with st.expander("▼ 상세 처리 로그 보기 (클릭)", expanded=expanded_log):
                # 로그 메시지 HTML 생성 (더 안전한 방식 고려 가능, 여기서는 단순 replace 사용)
                log_html = "".join([f"<div style='font-size:small; margin-bottom:3px;'>{log.replace('✅','✔️')}</div>" for log in all_log_messages])
                st.markdown(log_html, unsafe_allow_html=True)
