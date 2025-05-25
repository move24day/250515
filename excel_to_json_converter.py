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
MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions and isinstance(data.item_definitions, dict) else ["가정 이사 🏠", "사무실 이사 🏢"]

# 기본값 설정
DEFAULT_CUSTOMER_NAME = "무명"
DEFAULT_MOVE_TYPE = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠"
DEFAULT_STORAGE_TYPE = data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦"
DEFAULT_FROM_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
DEFAULT_TO_METHOD = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜"
STAIR_METHOD_DEFAULT = "계단 🚶" # data.py 에 정의된 "계단" 작업 방법과 일치해야 함
TODAY_ISO_DATE = datetime.now(KST).date().isoformat()

# --- 공통 헬퍼 함수 ---
def parse_date_flexible(date_str_input, current_year):
    if isinstance(date_str_input, (datetime, date)):
        return date_str_input.strftime('%Y-%m-%d')
    if not date_str_input or str(date_str_input).strip().lower() == "미정":
        return TODAY_ISO_DATE
    date_str = str(date_str_input).strip()
    # 시간 정보 제거 (예: "06월 30일 10시" -> "06월 30일")
    date_str = re.split(r'\s+[0-9]{1,2}\s*[:시]', date_str)[0].strip()
    patterns = [
        # YYYY-MM-DD, YYYY/MM/DD, YYYY.MM.DD, YYYY년 MM월 DD일
        (r'(\d{4})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*(일?)', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        # MM월 DD일 (올해 기준)
        (r'(\d{1,2})\s*월\s*(\d{1,2})\s*일?', lambda m: (current_year, int(m.group(1)), int(m.group(2)))),
        # MM/DD, MM-DD, MM.DD (올해 기준)
        (r'(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*', lambda m: (current_year, int(m.group(1)), int(m.group(2)))),
        # YY-MM-DD, YY/MM/DD, YY.MM.DD (20YY년 기준)
        (r'(\d{2})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*(일?)', lambda m: (2000 + int(m.group(1)), int(m.group(2)), int(m.group(3))))
    ]
    for pattern, extractor in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                # 전체 문자열이 패턴과 일치하는지 확인 (예: "이순임06월30일" 방지)
                # 정규화된 매치와 정규화된 입력 문자열 비교
                normalized_match = "".join(match.group(0).split())
                normalized_date_str = "".join(date_str.split()) # 입력도 정규화
                if normalized_match == normalized_date_str:
                    year, month, day = extractor(match)
                    return datetime(year, month, day).strftime('%Y-%m-%d')
            except ValueError:
                continue
    return TODAY_ISO_DATE # 어떤 패턴과도 맞지 않으면 오늘 날짜

def normalize_phone_number_for_filename(phone_str):
    if not phone_str or not isinstance(phone_str, str): return None
    return "".join(filter(str.isdigit, phone_str))

def get_default_state(): # 모든 필요한 키에 대한 기본값 설정
    return {
        "moving_date": TODAY_ISO_DATE, "customer_name": DEFAULT_CUSTOMER_NAME, "customer_phone": "",
        "base_move_type": DEFAULT_MOVE_TYPE, "from_location": "", "to_location": "", "special_notes": "",
        "from_floor": "", "to_floor": "",
        "from_method": DEFAULT_FROM_METHOD, "to_method": DEFAULT_TO_METHOD,
        "is_storage_move": False, "storage_type": DEFAULT_STORAGE_TYPE,
        "apply_long_distance": False, "has_via_point": False,
        "deposit_amount": 0, "adjustment_amount": 0,
        "issue_tax_invoice": False, "card_payment": False, "remove_base_housewife": False, "remove_base_man": False, # remove_base_man 추가
        "dispatched_1t":0, "dispatched_2_5t":0, "dispatched_3_5t":0, "dispatched_5t":0,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "waste_tons_input": 0.5, "has_waste_check": False,
        "uploaded_image_paths": [],
        "vehicle_select_radio": "자동 추천 차량 사용", "manual_vehicle_select_value": None,
        "final_selected_vehicle": None, "recommended_vehicle_auto": None,
        "storage_duration": 1, "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "via_point_location": "", "via_point_method": DEFAULT_FROM_METHOD, # via_point_method도 기본값 설정
        "via_point_floor": "", "via_point_surcharge": 0,
        "departure_ladder_surcharge_manual": 0, "arrival_ladder_surcharge_manual": 0, # 수동 사다리차 비용 키 추가
        "manual_ladder_from_check": False, "manual_ladder_to_check": False, # 수동 사다리차 체크박스 키 추가
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        "total_volume": 0.0, "total_weight": 0.0,
        "tab3_deposit_amount": 0, "tab3_adjustment_amount": 0, "tab3_departure_ladder_surcharge_manual": 0, "tab3_arrival_ladder_surcharge_manual":0, # tab3 관련 키들 추가
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "prev_final_selected_vehicle": None,
        "contract_date": TODAY_ISO_DATE, # 계약일
        "move_time_option": "오전", "afternoon_move_details": "", # 이사 시간 관련
        "from_address_full": "", "to_address_full": "" # ui_tab1.py 에서 사용하는 주소 키
    }


def extract_floor_from_address_enhanced(address_str):
    if not address_str or not isinstance(address_str, str):
        return address_str if address_str else "", "" # 입력이 없거나 문자열 아니면 그대로 반환, 주소부분은 원본, 층수는 빈 문자열
    address_cleaned = address_str.strip()
    parsed_floor = ""
    address_part = address_cleaned # 기본적으로 주소 부분은 전체 클린된 주소

    # 1. "...호" 패턴으로 층수 추출 시도 (가장 구체적인 패턴 우선)
    #    "101동 1203호" -> 12층, "302호" -> 3층
    ho_match = re.search(r'(\d+)\s*호(?!\d)', address_cleaned) # "호" 뒤에 숫자가 바로 오지 않는 경우
    if ho_match:
        ho_number_str = ho_match.group(1)
        if len(ho_number_str) > 2: # 예: 1203호 -> 12층
            parsed_floor = ho_number_str[:-2]
        elif len(ho_number_str) > 0: # 예: 302호 -> 3층, 22호 -> 층수 아님 (정책에 따라 2층으로 볼 수도 있음)
             # 1-2자리 "호" 앞 숫자는 층수로 간주하지 않거나, 매우 낮은 층(예: 1층, 2층)으로 볼 수 있음.
             # 여기서는 1-2자리는 층수로 안 봄. 만약 봐야 한다면 parsed_floor = ho_number_str 로 변경.
             # 현재 요청에 따라, 3자리 이상일 때만 앞 부분을 층으로 인식.
             # 사용자 요청: "...호 다음에 나오는 것은 도착지 주소야" -> 이 함수는 층수만 추출.
             # "호" 까지가 주소의 일부로 간주될 수 있으므로, 주소 부분에서 "호"를 자르지 않음.
             # 이 함수는 주로 층수 "숫자"를 빼내는 데 집중.
             pass # 1-2자리는 층수로 안봄. 필요시 수정.

        # "호" 정보가 층수 추출에 사용되었다면, 주소 부분에서 해당 "호" 부분은 그대로 두거나,
        # 명시적으로 제거하고 싶다면 아래와 같이 처리 가능하나, 현재는 "호"까지 주소로 포함.
        # address_part = address_cleaned[:ho_match.start(0)].strip() # "호" 앞부분까지만 주소로.
        if parsed_floor: # "호"에서 유효한 층수가 나왔으면 반환 (주소는 전체 유지)
            return address_cleaned, parsed_floor


    # 2. "N층", "N F", "N f" 패턴으로 층수 추출 (주소의 끝에 오는 경우)
    #    예: "강남빌딩 5층", "엘지아파트 10 F"
    #    주소 중간에 "5층상가" 같은 경우는 여기서 처리 안 함.
    floor_ending_match = re.search(r'^(.*?)(\s*(-?\d+)\s*(층|F|f))$', address_cleaned, re.IGNORECASE)
    if floor_ending_match:
        address_part = floor_ending_match.group(1).strip() # "층" 앞부분
        parsed_floor = floor_ending_match.group(3)     # 숫자 부분
        return address_part, parsed_floor

    # 3. "지하 N층", "B N층", "B N F" 패턴 (주소의 끝에 오는 경우)
    #    예: "상가 B2층", "건물 지하1층"
    basement_floor_match = re.search(r'^(.*?)\s*(지하|-?B|b)\s*(\d+)\s*(층|F|f)?$', address_cleaned, re.IGNORECASE)
    if basement_floor_match:
        address_part = basement_floor_match.group(1).strip()
        parsed_floor = "-" + basement_floor_match.group(3) # 지하층은 음수로
        return address_part, parsed_floor

    return address_cleaned, "" # 어떤 패턴에도 안 맞으면 원래 주소와 빈 층수 반환


# --- 텍스트 입력 처리 함수 (사용자 요청사항 반영) ---
PHONE_REGEX_TEXT = re.compile(r'(01[016789]-?\d{3,4}-?\d{4}|0\d{1,2}-?\d{3,4}-?\d{4})')
MOVE_TYPE_KEYWORDS_TEXT = {"가정": ["가정", "가"], "사무실": ["사무실", "사"]}

def parse_line_to_json_flexible(line_text, current_year, line_number_display=""):
    state = get_default_state()
    original_line = line_text.strip()
    if not original_line: return None, None, f"{line_number_display}빈 줄"

    # 1. 전화번호 파싱 (필수)
    phone_match = PHONE_REGEX_TEXT.search(original_line)
    if not phone_match: return None, None, f"{line_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = phone_match.group(0).strip()
    filename_phone_part = normalize_phone_number_for_filename(state["customer_phone"])
    if not filename_phone_part: return None, None, f"{line_number_display}유효하지 않은 전화번호"

    text_before_phone = original_line[:phone_match.start()].strip()
    text_after_phone = original_line[phone_match.end():].strip()

    # 2. 날짜 및 고객명 파싱 (전화번호 앞부분)
    parts_bf_phone = [p.strip() for p in text_before_phone.split() if p.strip()]
    date_parsed_from_bf = False
    customer_name_parts_bf = []

    temp_date_candidate_bf = ""
    if len(parts_bf_phone) >= 1:
        # 최대 2개 파트까지 날짜 후보로 고려 (예: "06월 30일", "6월30일", "6/30")
        potential_date_str_bf = parts_bf_phone[0]
        if len(parts_bf_phone) >= 2 and not re.search(r'\d', parts_bf_phone[1]): # 두번째 파트에 숫자가 없으면 첫번째만
             pass
        elif len(parts_bf_phone) >= 2 : # 두번째 파트도 날짜일 가능성 (예: "06월", "30일")
            # "월"이나 "일"로 끝나거나 숫자로만 구성된 경우 이어붙여 시도
            if (parts_bf_phone[0].endswith('월') and parts_bf_phone[1].endswith('일')) or \
               (parts_bf_phone[0].replace('.', '').replace('-', '').replace('/', '').isdigit() and parts_bf_phone[1].replace('.', '').replace('-', '').replace('/', '').isdigit()):
                 potential_date_str_bf = parts_bf_phone[0] + " " + parts_bf_phone[1]


        parsed_dt_bf = parse_date_flexible(potential_date_str_bf, current_year)
        if parsed_dt_bf != TODAY_ISO_DATE or \
           (parsed_dt_bf == TODAY_ISO_DATE and potential_date_str_bf and potential_date_str_bf.lower() != "미정" and "오늘" not in potential_date_str_bf): # "오늘"도 오늘날짜로 처리
            state["moving_date"] = parsed_dt_bf
            date_parsed_from_bf = True
            # 날짜로 사용된 파트 개수 확인
            num_parts_for_date = len(potential_date_str_bf.split())
            customer_name_parts_bf = parts_bf_phone[num_parts_for_date:]
        else: # 날짜 파싱 안되면 전체를 이름 후보로
            customer_name_parts_bf = parts_bf_phone

    state["customer_name"] = " ".join(customer_name_parts_bf) if customer_name_parts_bf else DEFAULT_CUSTOMER_NAME
    if not state["customer_name"].strip(): state["customer_name"] = DEFAULT_CUSTOMER_NAME


    # 3. 이사 구분, 출발지, 도착지, 특이사항 파싱 (전화번호 뒷부분)
    remaining_text = text_after_phone

    # 3a. 이사 구분 ("가" 또는 "사")
    #     첫 단어가 "가" 또는 "사"이고 바로 뒤에 공백이 오거나, 단독으로 "가", "사"인 경우
    if remaining_text.lower().startswith("가 ") or remaining_text.lower() == "가":
        state["base_move_type"] = next((opt for opt in MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
        remaining_text = remaining_text[2:].lstrip() if remaining_text.lower().startswith("가 ") else remaining_text[1:].lstrip()
    elif remaining_text.lower().startswith("사 ") or remaining_text.lower() == "사":
        state["base_move_type"] = next((opt for opt in MOVE_TYPE_OPTIONS if "사무실" in opt), DEFAULT_MOVE_TYPE) # 사무실 기본값으로 수정필요
        remaining_text = remaining_text[2:].lstrip() if remaining_text.lower().startswith("사 ") else remaining_text[1:].lstrip()
    # 이사 구분이 명시되지 않으면 기본값(가정 이사) 사용 (state 초기값에 이미 설정됨)

    # 3b. 출발지 주소 ( "...호"로 끝나는 부분까지) 및 층수
    from_location_candidate = ""
    # 가장 마지막 "...호" 패턴을 찾음
    last_ho_match = None
    for match_ho in re.finditer(r'([^\s]+동\s*\d+호|\d+호)', remaining_text): # "XXX동 YYY호" 또는 그냥 "YYY호"
        last_ho_match = match_ho

    if last_ho_match:
        from_location_candidate = remaining_text[:last_ho_match.end()].strip()
        state["from_location"] = from_location_candidate
        _, state["from_floor"] = extract_floor_from_address_enhanced(from_location_candidate) # "호" 정보에서 층수 추출
        remaining_text_after_from_loc = remaining_text[last_ho_match.end():].lstrip()
    else:
        # "...호"를 못찾으면, 첫번째 주요 블록을 출발지로 가정 (탭이나 2칸 이상 공백으로 구분)
        first_block_match_text = re.match(r'([^\s\t]+(?:\s+[^\s\t]+)*)(\s{2,}|\t+|$)', remaining_text)
        if first_block_match_text:
            from_location_candidate = first_block_match_text.group(1).strip()
            # 출발지 주소와 층수를 한 번에 추출 시도
            addr_part, floor_part = extract_floor_from_address_enhanced(from_location_candidate)
            state["from_location"] = addr_part
            state["from_floor"] = floor_part
            remaining_text_after_from_loc = remaining_text[first_block_match_text.end():].lstrip()
        else: # 이것도 실패하면 전체를 출발지로 (층수 없음)
            addr_part, floor_part = extract_floor_from_address_enhanced(remaining_text) # 전체에서 시도
            state["from_location"] = addr_part
            state["from_floor"] = floor_part
            remaining_text_after_from_loc = "" # 모든 텍스트가 출발지로 사용됨

    if not state["from_location"]: # 출발지가 파싱 안됐으면 오류
        return None, None, f"{line_number_display}출발지 주소 특정 불가: '{original_line}'"


    # 3c. 도착지 주소 및 특이사항 (출발지 파싱 후 남은 텍스트에서)
    #     remaining_text_after_from_loc 에서 파싱
    #     "...호 다음에 나오는 것은 도착지 주소" 라는 요구사항 반영
    
    # 시간 패턴 정의 (요일/시간 정보 제거용)
    time_pattern = re.compile(r"([월화수목금토일](요일)?\s*\d{1,2}\s*[:시][^-\s]*(\s*-\s*\d{1,2}\s*[:시][^-\s]*)?|\d{1,2}\s*[:시][^-\s]*(\s*-\s*\d{1,2}\s*[:시][^-\s]*)?)\s*$")

    to_location_candidate_notes_combined = remaining_text_after_from_loc # 초기값
    
    # 1. 시간 정보가 있다면 분리 후 제거
    time_match_end = time_pattern.search(to_location_candidate_notes_combined)
    if time_match_end:
        to_location_candidate_notes_combined = to_location_candidate_notes_combined[:time_match_end.start()].strip()
        # state["special_notes"] = time_match_end.group(0).strip() # 시간 정보를 특이사항에 넣을 수도 있음 (선택)

    # 2. 남은 부분에서 도착지 주소와 특이사항 분리
    #    여기서는 첫번째 "주요 블록" (탭 또는 2개이상 공백으로 구분된)을 도착지로 간주
    #    나머지를 특이사항으로. 만약 구분자 없으면 전체가 도착지.
    if to_location_candidate_notes_combined:
        parts_for_to_loc_notes = [p.strip() for p in re.split(r'\s{2,}|\t+', to_location_candidate_notes_combined) if p.strip()]
        if parts_for_to_loc_notes:
            # 첫번째 블록을 도착지로
            to_address_candidate = parts_for_to_loc_notes.pop(0)
            addr_part_to, floor_part_to = extract_floor_from_address_enhanced(to_address_candidate)
            state["to_location"] = addr_part_to
            state["to_floor"] = floor_part_to
            
            # 남은 블록들이 있다면 특이사항으로 합침
            if parts_for_to_loc_notes:
                existing_notes = state.get("special_notes", "")
                new_notes = " ".join(parts_for_to_loc_notes)
                state["special_notes"] = f"{existing_notes} {new_notes}".strip() if existing_notes else new_notes
        else: # 주요 블록 구분자가 없으면, 전체를 도착지로 (특이사항 없음)
            addr_part_to, floor_part_to = extract_floor_from_address_enhanced(to_location_candidate_notes_combined)
            state["to_location"] = addr_part_to
            state["to_floor"] = floor_part_to
            # 특이사항은 이 경우 없음 (또는 위에서 시간 정보만 들어갔을 수 있음)

    # 작업 방법 기본값 설정 (계단)
    if hasattr(data, 'METHOD_OPTIONS') and STAIR_METHOD_DEFAULT in data.METHOD_OPTIONS:
        state["from_method"] = STAIR_METHOD_DEFAULT
        state["to_method"] = STAIR_METHOD_DEFAULT
    else: # data.py에 "계단"이 없을 경우에 대한 예외 처리 (특이사항에 명시)
        current_notes = state.get("special_notes", "")
        stair_method_name_for_note = STAIR_METHOD_DEFAULT.split(" ")[0] # "계단"
        note_addition = f"(참고: 요청된 '{stair_method_name_for_note}' 작업방법을 data.py에서 찾을 수 없어 기본값 사용)"
        state["special_notes"] = f"{current_notes} {note_addition}".strip() if current_notes else note_addition


    # 최종 필수 필드 (출발지) 확인
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
    # 컬럼명 비교 시 소문자로 통일, 공백 제거
    row_index_lower_stripped = {str(idx_item).lower().replace(" ", ""): idx_item for idx_item in row.index}
    
    # 기본 필드명 (소문자, 공백제거)
    standard_field_lower_stripped = field_name.lower().replace(" ", "")
    if standard_field_lower_stripped in row_index_lower_stripped and pd.notna(row[row_index_lower_stripped[standard_field_lower_stripped]]):
        return str(row[row_index_lower_stripped[standard_field_lower_stripped]]).strip()

    # 별칭 확인 (소문자, 공백제거)
    for alias_item in aliases.get(field_name, []):
        alias_lower_stripped = alias_item.lower().replace(" ", "")
        if alias_lower_stripped in row_index_lower_stripped and pd.notna(row[row_index_lower_stripped[alias_lower_stripped]]):
            return str(row[row_index_lower_stripped[alias_lower_stripped]]).strip()
    return default


def parse_excel_row_to_json(row, current_year, row_number_display=""):
    state = get_default_state() # 기본 상태값으로 시작
    # 행 전체가 비었는지 확인 (모든 값이 NA거나 빈 문자열)
    if row.isnull().all() or all(str(x).strip() == "" for x in row if pd.notna(x)):
        return None, None, f"{row_number_display}빈 행"

    # 필수: 전화번호, 출발지 주소
    customer_phone_raw = get_column_value(row, 'customer_phone', COLUMN_ALIASES_EXCEL)
    if not customer_phone_raw: return None, None, f"{row_number_display}전화번호 없음 (필수)"
    state["customer_phone"] = customer_phone_raw
    filename_phone_part = normalize_phone_number_for_filename(customer_phone_raw)
    if not filename_phone_part: return None, None, f"{row_number_display}유효하지 않은 전화번호"

    from_location_raw = get_column_value(row, 'from_location', COLUMN_ALIASES_EXCEL)
    if not from_location_raw: return None, None, f"{row_number_display}출발지 주소 없음 (필수)"
    
    # 날짜 파싱 및 기본값 처리
    moving_date_raw = get_column_value(row, 'moving_date', COLUMN_ALIASES_EXCEL)
    state["moving_date"] = parse_date_flexible(moving_date_raw, current_year)
    log_info_for_date = "" # 날짜 처리 관련 로그 메시지
    if moving_date_raw and moving_date_raw.strip().lower() != "미정" and state["moving_date"] == TODAY_ISO_DATE:
        # parse_date_flexible가 오늘 날짜를 반환했지만, 입력값이 "미정"이나 빈 값이 아니었던 경우
        log_info_for_date = f"제공된 날짜 '{moving_date_raw}'가 오늘 날짜로 처리됨 (형식/내용 확인 필요)."

    # 고객명 파싱 및 기본값, 보관이사 체크
    customer_name_raw = get_column_value(row, 'customer_name', COLUMN_ALIASES_EXCEL)
    if customer_name_raw and customer_name_raw.lower() != "미정": state["customer_name"] = customer_name_raw
    else: state["customer_name"] = DEFAULT_CUSTOMER_NAME # 미정이거나 비었으면 기본값 "무명"
    if "보관" in state["customer_name"]: # 고객명에 "보관" 포함 시
        state["is_storage_move"] = True
        state["storage_type"] = DEFAULT_STORAGE_TYPE # 기본 보관 유형 설정

    # 이사 종류
    move_type_raw = get_column_value(row, 'base_move_type', COLUMN_ALIASES_EXCEL)
    if move_type_raw:
        move_type_char = move_type_raw.strip().lower()
        if any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["가정"]) or "가정" in move_type_char :
            state["base_move_type"] = next((opt for opt in MOVE_TYPE_OPTIONS if "가정" in opt), DEFAULT_MOVE_TYPE)
        elif any(keyword == move_type_char for keyword in MOVE_TYPE_KEYWORDS_TEXT["사무실"]) or "사무실" in move_type_char:
            state["base_move_type"] = next((opt for opt in MOVE_TYPE_OPTIONS if "사무실" in opt), MOVE_TYPE_OPTIONS[1] if len(MOVE_TYPE_OPTIONS)>1 else DEFAULT_MOVE_TYPE)
    # 명시 안되면 기본값 (가정 이사) 유지

    # 출발지 주소 및 층수
    from_floor_raw_col = get_column_value(row, 'from_floor', COLUMN_ALIASES_EXCEL) # 명시적 층수 컬럼
    addr_part_from, floor_part_from = extract_floor_from_address_enhanced(from_location_raw)
    state["from_location"] = addr_part_from # extract_floor_from_address_enhanced가 주소 부분만 반환
    state["from_floor"] = from_floor_raw_col if from_floor_raw_col else floor_part_from # 명시적 층수 우선, 없으면 추출된 층수

    # 도착지 주소 및 층수
    to_location_raw = get_column_value(row, 'to_location', COLUMN_ALIASES_EXCEL)
    to_floor_raw_col = get_column_value(row, 'to_floor', COLUMN_ALIASES_EXCEL)
    if to_location_raw or to_floor_raw_col : # 도착지 정보가 하나라도 있으면
        if to_location_raw:
            addr_part_to, floor_part_to = extract_floor_from_address_enhanced(to_location_raw)
            state["to_location"] = addr_part_to
            state["to_floor"] = to_floor_raw_col if to_floor_raw_col else floor_part_to
        else: # 도착지 주소는 없고 층수만 있는 경우
            state["to_location"] = "" # 주소는 비워둠
            state["to_floor"] = to_floor_raw_col

    # 특이사항 (날짜 처리 로그와 합침)
    special_notes_raw = get_column_value(row, 'special_notes', COLUMN_ALIASES_EXCEL)
    if log_info_for_date and special_notes_raw:
        state["special_notes"] = log_info_for_date + " " + special_notes_raw
    elif log_info_for_date:
        state["special_notes"] = log_info_for_date
    elif special_notes_raw:
        state["special_notes"] = special_notes_raw
    
    # 엑셀 입력의 경우 작업방법은 기본값 유지 (텍스트 입력과 달리 명시적 규칙 없음)
    # state["from_method"] = STAIR_METHOD_DEFAULT (필요시 주석 해제)
    # state["to_method"] = STAIR_METHOD_DEFAULT (필요시 주석 해제)

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
                              placeholder="예시: 07월 04일 이순임 010-2701-0758 가 동대문구 한천로63길 10 이문e편한세상 103동 2101호  동대문구 휘경1동  이양식 수9시")
else:
    uploaded_file = st.file_uploader("변환할 Excel 파일을 업로드하세요.", type=["xlsx", "xls"])
    st.markdown("""
    **Excel 파일 형식 가이드:**
    - 첫 번째 행은 헤더(컬럼명)여야 합니다. 컬럼명은 대소문자를 구분하지 않으며, 공백은 무시됩니다.
    - **필수 컬럼**: `전화번호`, `출발지주소` (또는 유사어: 연락처, 출발지 등)
    - **선택 컬럼**: `날짜` (인식 가능한 형식, 미입력/인식불가 시 오늘 날짜), `고객명` (미입력시 '무명'), `이사종류`('가'/'사' 또는 '가정', '사무실'), `출발지 층수`, `도착지주소`, `도착지 층수`, `특이사항` (또는 유사어)
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
                # 컬럼명을 읽을 때 공백 제거 및 소문자화 (get_column_value 함수와 일관성)
                df.columns = [str(col).strip().lower().replace(" ", "") for col in df.columns]
                items_to_process = [row for _, row in df.iterrows() if not row.isnull().all()]
                total_items = len(items_to_process)
            except Exception as e: st.error(f"Excel 파일 읽기 중 오류 발생: {e}"); items_to_process = []

    if not items_to_process:
        if text_input.strip() or uploaded_file: # 입력 시도는 있었으나 처리할 아이템이 없는 경우
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

            # 엑셀에서 날짜 파싱 관련 로그 (parse_excel_row_to_json 함수 내부에서 special_notes에 이미 추가됨)
            # 중복 로그 방지를 위해 여기서는 추가하지 않음. 필요시 parse_excel_row_to_json의 로그 방식을 변경.

            if status_obj and filename:
                final_state_to_save = get_default_state() # 항상 모든 키를 포함하는 기본 상태에서 시작
                final_state_to_save.update(status_obj)    # 파싱된 결과로 업데이트
                try:
                    gdrive_folder_id_secret = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")
                    save_result = gdrive.save_json_file(filename, final_state_to_save, folder_id=gdrive_folder_id_secret)
                    if save_result and save_result.get('id'):
                        log_message = f"✔️ <span style='color:green;'>저장 성공</span>: {filename} {log_identifier} (ID: {save_result.get('id')})"
                        all_log_messages.append(log_message); success_count += 1
                    else:
                        log_message = f"❌ <span style='color:red;'>저장 실패</span>: {filename} {log_identifier} (응답: {save_result})"
                        all_log_messages.append(log_message); error_count += 1
                except AttributeError as ae: # gdrive 모듈 관련 오류 등
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
        else: st.info(f"실패 또는 건너뜀: {error_count} 건") # 실패가 0건일 때도 정보성으로 표시

        if all_log_messages:
            # 오류가 있거나, 성공 건수가 전체보다 적거나, "정보" 로그가 있을 경우 로그 창을 기본으로 펼침
            expanded_log = (error_count > 0 or success_count < total_items or any("정보" in log for log in all_log_messages))
            with st.expander("▼ 상세 처리 로그 보기 (클릭)", expanded=expanded_log):
                log_html = "".join([f"<div style='font-size:small; margin-bottom:3px;'>{log}</div>" for log in all_log_messages])
                st.markdown(log_html, unsafe_allow_html=True)
