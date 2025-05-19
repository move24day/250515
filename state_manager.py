# state_manager.py
import streamlit as st
from datetime import datetime, date
import pytz
import json # json 임포트는 현재 코드에서 직접 사용되지 않으나, 로드/저장 로직에 필요할 수 있음

try:
    import data
    import utils # utils는 현재 직접 사용되지 않으나, 다른 모듈에서 필요할 수 있음
except ImportError as e:
    st.error(f"State Manager: 필수 모듈 로딩 실패 - {e}")
    st.stop()
except Exception as e:
    st.error(f"State Manager: 모듈 로딩 중 오류 - {e}")
    st.stop()

# --- Constants ---
try:
    # MOVE_TYPE_OPTIONS: data.py의 실제 키(이모티콘 포함)를 사용하고, UI 표시는 format_func 등으로 처리
    MOVE_TYPE_OPTIONS_FROM_DATA = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions else ["가정 이사 🏠", "사무실 이사 🏢"]
    MOVE_TYPE_OPTIONS = MOVE_TYPE_OPTIONS_FROM_DATA # 세션 및 로직에서는 이모티콘 포함된 원본 사용
except Exception as e:
    MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"] # 기본값도 이모티콘 포함
    st.warning(f"data.py에서 이사 유형 로딩 중 오류 발생: {e}. 기본값을 사용합니다.")

STATE_KEYS_TO_SAVE = [
    "base_move_type", "is_storage_move", "storage_type", "apply_long_distance",
    "customer_name", "customer_phone", "customer_email",
    "from_location", "to_location", "moving_date", "arrival_date",
    "from_floor", "from_method", "to_floor", "to_method", "special_notes",
    "storage_duration", "storage_use_electricity",
    "long_distance_selector", "vehicle_select_radio",
    "manual_vehicle_select_value", "final_selected_vehicle", "sky_hours_from",
    "sky_hours_final",
    "add_men", "add_women",
    "has_waste_check", "waste_tons_input",
    "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget", # Tab3 UI 직접 바인딩용 (저장 시 tab3_로 매핑)
    "date_opt_3_widget", "date_opt_4_widget",
    "tab3_deposit_amount",      # 저장/로드용 (deposit_amount에서 매핑)
    "tab3_adjustment_amount",   # 저장/로드용 (adjustment_amount에서 매핑)
    "tab3_regional_ladder_surcharge", # 저장/로드용 (regional_ladder_surcharge에서 매핑)
    "tab3_date_opt_0_widget", "tab3_date_opt_1_widget", "tab3_date_opt_2_widget", # 날짜 옵션 저장/로드용
    "tab3_date_opt_3_widget", "tab3_date_opt_4_widget",
    "remove_base_housewife",
    "issue_tax_invoice",
    "card_payment",
    "prev_final_selected_vehicle", # 바구니 수량 자동 업데이트 로직용
    "dispatched_1t", "dispatched_2_5t", "dispatched_3_5t", "dispatched_5t", # 실제 투입 차량
    "has_via_point", "via_point_location", "via_point_method", "via_point_surcharge",
    "via_point_floor",  # --- via_point_floor 추가 ---
    "uploaded_image_paths", # 이미지 경로 리스트
    # 계산 결과 (저장/로드 대상은 아니지만, 세션 상태에 존재할 수 있음)
    # "total_volume", "total_weight", "recommended_vehicle_auto", "remaining_space",
    # "calculated_cost_items_for_pdf", "total_cost_for_pdf", "personnel_info_for_pdf"
]

def initialize_session_state(update_basket_callback=None):
    try: kst = pytz.timezone("Asia/Seoul"); default_date = datetime.now(kst).date()
    except Exception: default_date = datetime.now().date()

    # METHOD_OPTIONS, STORAGE_TYPE_OPTIONS 등도 data.py에서 이모티콘 포함된 원본 사용
    defaults = {
        "base_move_type": MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠",
        "is_storage_move": False,
        "storage_type": data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦",
        "apply_long_distance": False, "customer_name": "", "customer_phone": "",
        "customer_email": "",
        "from_location": "", "to_location": "", "moving_date": default_date,
        "arrival_date": default_date, # 보관 이사 시 도착일
        "from_floor": "",
        "from_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜",
        "to_floor": "",
        "to_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜",
        "special_notes": "", "storage_duration": 1, # 보관 기간 (일)
        "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "vehicle_select_radio": "자동 추천 차량 사용", # 차량 선택 방식
        "manual_vehicle_select_value": None,     # 수동 선택 차량
        "final_selected_vehicle": None,          # 최종 계산용 차량
        "recommended_vehicle_auto": None,        # 자동 추천 차량 결과
        "sky_hours_from": 1, "sky_hours_final": 1, # 스카이 사용 시간
        "add_men": 0, "add_women": 0, # 추가 인력
        "has_waste_check": False, "waste_tons_input": 0.5, # 폐기물
        # 날짜 옵션 (Tab3 UI 직접 바인딩용, state_manager.py의 STATE_KEYS_TO_SAVE에는 tab3_ 접두사 붙은 키로 저장/로드)
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        # 날짜 옵션 (저장/로드 용)
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        # 계산 결과 (휘발성, 로드 시 재계산됨)
        "total_volume": 0.0, "total_weight": 0.0, "remaining_space": 0.0,
        # PDF/Excel 생성용 데이터 (휘발성)
        'pdf_data_customer': None, 'final_excel_data': None, 'internal_form_image_data': None, 'customer_pdf_image_data': None,
        # 수기 조정 및 계약금 (Tab3 UI 직접 바인딩용, state_manager.py의 STATE_KEYS_TO_SAVE에는 tab3_ 접두사 붙은 키로 저장/로드)
        "deposit_amount": 0,
        "adjustment_amount": 0,
        "regional_ladder_surcharge": 0, # 지방 사다리 추가금 UI용
        "via_point_surcharge": 0,      # 경유지 추가금 UI용 (이 값은 STATE_KEYS_TO_SAVE에 직접 포함)
        # 수기 조정 및 계약금 (저장/로드 용)
        "tab3_deposit_amount": 0,
        "tab3_adjustment_amount": 0,
        "tab3_regional_ladder_surcharge": 0,
        # 기타 옵션
        "remove_base_housewife": False, # 기본 여성 인원 제외
        "issue_tax_invoice": False,     # 세금계산서 발행
        "card_payment": False,          # 카드 결제
        # 차량 변경 감지용 (바구니 콜백)
        "prev_final_selected_vehicle": None,
        # 실제 투입 차량
        "dispatched_1t": 0, "dispatched_2_5t": 0, "dispatched_3_5t": 0, "dispatched_5t": 0,
        # 구글 드라이브 검색 관련
        "gdrive_search_term_tab1": "", "gdrive_search_results": [], # Tab1용 검색어 및 결과
        "gdrive_file_options_map": {}, "gdrive_selected_filename": None, # Tab1용
        "gdrive_selected_file_id": None, # Tab1용
        # 탭 간 이사 유형 동기화용 (UI 위젯 키)
        "base_move_type_widget_tab1": MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠",
        "base_move_type_widget_tab3": MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠",
        # 경유지 정보
        "has_via_point": False,
        "via_point_location": "",
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜",
        "via_point_floor": "",  # --- via_point_floor 기본값 추가 ---
        # 이미지 업로드
        "uploaded_image_paths": [],
        "image_uploader_key_counter": 0, # 이미지 업로더 위젯 리셋용
        # 앱 초기화 플래그
        "_app_initialized": True # 이 함수 호출 시점에는 이미 초기화된 것으로 간주
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # base_move_type 위젯 값 동기화 (앱 시작 시 또는 로드 후)
    if st.session_state.base_move_type_widget_tab1 != st.session_state.base_move_type:
        st.session_state.base_move_type_widget_tab1 = st.session_state.base_move_type
    if st.session_state.base_move_type_widget_tab3 != st.session_state.base_move_type:
        st.session_state.base_move_type_widget_tab3 = st.session_state.base_move_type

    # 숫자형, 불리언형, 리스트형 키 타입 변환 및 기본값 재확인 (로드 시 필요)
    int_keys = [k for k,v in defaults.items() if isinstance(v, int) and not isinstance(v, bool)] # deposit_amount 등
    float_keys = [k for k,v in defaults.items() if isinstance(v, float)] # waste_tons_input 등
    bool_keys = [k for k,v in defaults.items() if isinstance(v, bool)]   # is_storage_move 등
    list_keys = [k for k,v in defaults.items() if isinstance(v, list)]   # uploaded_image_paths 등
    string_keys = ["via_point_floor", "customer_name", "customer_phone", "customer_email", 
                   "from_location", "to_location", "from_floor", "to_floor", "special_notes",
                   "long_distance_selector", "vehicle_select_radio", "manual_vehicle_select_value",
                   "final_selected_vehicle", "recommended_vehicle_auto", "prev_final_selected_vehicle",
                   "gdrive_search_term_tab1", "gdrive_selected_filename", "gdrive_selected_file_id",
                   "via_point_location"] # 문자열로 유지해야 하는 키들
                   # base_move_type, storage_type, from_method, to_method, via_point_method는 data.py의 원본값을 유지해야 하므로 여기서 제외

    for k in int_keys + float_keys + bool_keys + list_keys + string_keys:
        default_val_k = defaults.get(k) # 해당 키의 기본값 가져오기
        if k not in st.session_state: # 세션에 키가 없으면 기본값으로 설정
            st.session_state[k] = default_val_k
            continue # 다음 키로

        # 세션에 키가 이미 있는 경우, 타입 검사 및 변환 시도
        val = st.session_state.get(k)
        if val is None: # 값이 None이면 기본값으로 설정
            st.session_state[k] = default_val_k
            continue

        try:
            if k in bool_keys:
                 if isinstance(val, str): st.session_state[k] = val.lower() in ["true", "yes", "1", "on", "t"]
                 else: st.session_state[k] = bool(val)
            elif k in int_keys:
                 if isinstance(val, str) and val.strip() == "": st.session_state[k] = default_val_k; continue
                 converted_val = int(float(val)) # 소수점 있는 문자열 "1.0" 등을 대비해 float 거쳐 int
                 # 음수 허용 키 (adjustment_amount 등) 확인 필요
                 allow_negative_keys_init = ["adjustment_amount", "tab3_adjustment_amount"]
                 if k in allow_negative_keys_init: st.session_state[k] = converted_val
                 else: st.session_state[k] = max(0, converted_val) # 대부분의 정수형은 0 이상
                 if k == "storage_duration": st.session_state[k] = max(1, st.session_state[k]) # 최소 1일
            elif k in float_keys:
                 if isinstance(val, str) and val.strip() == "": st.session_state[k] = default_val_k; continue
                 converted_val = float(val)
                 st.session_state[k] = max(0.0, converted_val) # 대부분 0.0 이상
            elif k in list_keys:
                if not isinstance(val, list): st.session_state[k] = default_val_k # 리스트 아니면 기본 빈 리스트로
            elif k in string_keys: # 문자열 키는 그대로 문자열로 유지
                st.session_state[k] = str(val)

        except (ValueError, TypeError): # 타입 변환 실패 시
            st.session_state[k] = default_val_k # 안전하게 기본값으로 복원
        except KeyError: # defaults 딕셔너리에 키가 없는 경우 (이론상 발생 안해야 함)
            # 해당 타입에 맞는 안전한 기본값으로 설정
            if k in int_keys: st.session_state[k] = 0
            elif k in float_keys: st.session_state[k] = 0.0
            elif k in bool_keys: st.session_state[k] = False
            elif k in list_keys: st.session_state[k] = []
            elif k in string_keys: st.session_state[k] = ""


    # 품목 수량(qty_...) 키 초기화 (STATE_KEYS_TO_SAVE에 동적으로 추가될 것이므로 여기서도 확인)
    global STATE_KEYS_TO_SAVE # 전역 변수 사용 명시
    processed_item_keys_init = set()
    dynamic_item_keys = [] # 동적으로 생성된 품목 키 목록
    if hasattr(data, "item_definitions") and data.item_definitions:
        for move_type_key, sections in data.item_definitions.items(): # 이모티콘 포함된 원본 키 사용
            if isinstance(sections, dict):
                for section_key, item_list in sections.items(): # 이모티콘 포함된 원본 키 사용
                    if section_key == "폐기 처리 품목 🗑️": continue
                    if isinstance(item_list, list):
                        for item_name in item_list:
                            if hasattr(data, "items") and item_name in data.items: # 유효한 품목인지 확인
                                # 세션 상태 키 생성 시에도 이모티콘 포함된 원본 move_type, section 사용
                                key = f"qty_{move_type_key}_{section_key}_{item_name}"
                                dynamic_item_keys.append(key) # STATE_KEYS_TO_SAVE 업데이트용
                                if key not in st.session_state and key not in processed_item_keys_init:
                                    st.session_state[key] = 0 # 기본값 0으로 초기화
                                processed_item_keys_init.add(key)
    
    # 동적으로 생성된 품목 수량 키들을 STATE_KEYS_TO_SAVE에 추가 (중복 방지)
    for item_key in dynamic_item_keys:
        if item_key not in STATE_KEYS_TO_SAVE:
            STATE_KEYS_TO_SAVE.append(item_key)


    # prev_final_selected_vehicle 초기화 (바구니 콜백용)
    if "prev_final_selected_vehicle" not in st.session_state: 
        st.session_state["prev_final_selected_vehicle"] = st.session_state.get("final_selected_vehicle")

    # 바구니 수량 업데이트 콜백 호출 (필요한 경우)
    if callable(update_basket_callback):
        update_basket_callback()


def prepare_state_for_save():
    state_to_save = {}
    # 저장 시 제외할 UI 직접 바인딩용 키 (tab3_ 접두사 붙은 키로 이미 매핑되어 저장됨)
    keys_to_exclude_ui_mapped = {
        "deposit_amount", "adjustment_amount", "regional_ladder_surcharge",
        "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget",
        "date_opt_3_widget", "date_opt_4_widget",
    }
    # 기타 저장 제외 키 (휘발성 데이터, UI 전용 위젯 키 등)
    keys_to_exclude_other = {
        "_app_initialized", 
        "base_move_type_widget_tab1", "base_move_type_widget_tab3", # UI 위젯용
        "gdrive_selected_filename_widget_tab1", # UI 위젯용 (gdrive_selected_filename으로 저장)
        "gdrive_search_term_tab1", # UI 위젯용 (저장 불필요)
        "pdf_data_customer", "final_excel_data", # 생성된 파일 데이터 (휘발성)
        "internal_form_image_data", "customer_pdf_image_data", # 생성된 이미지 데이터 (휘발성)
        "gdrive_search_results", "gdrive_file_options_map", # 검색 결과 (휘발성)
        "image_uploader_key_counter", # UI 리셋용
        # 계산 결과는 저장 안 함 (로드 시 재계산)
        "total_volume", "total_weight", "remaining_space", "recommended_vehicle_auto",
        "calculated_cost_items_for_pdf", "total_cost_for_pdf", "personnel_info_for_pdf"
    }
    keys_to_exclude_all = keys_to_exclude_ui_mapped.union(keys_to_exclude_other)

    # Tab3 UI 입력값을 저장용 tab3_ 키로 매핑 (STATE_KEYS_TO_SAVE에 정의된 키 기준)
    st.session_state.tab3_deposit_amount = st.session_state.get("deposit_amount", 0)
    st.session_state.tab3_adjustment_amount = st.session_state.get("adjustment_amount", 0)
    st.session_state.tab3_regional_ladder_surcharge = st.session_state.get("regional_ladder_surcharge", 0)
    for i in range(5): # 날짜 옵션
        st.session_state[f"tab3_date_opt_{i}_widget"] = st.session_state.get(f"date_opt_{i}_widget", False)

    # STATE_KEYS_TO_SAVE (품목키 포함된 전역 리스트) 기준으로 저장할 데이터 구성
    actual_keys_to_save_final = [key for key in STATE_KEYS_TO_SAVE if key not in keys_to_exclude_all]

    for key in actual_keys_to_save_final:
        if key in st.session_state: # 세션에 해당 키가 있을 때만 저장 시도
            value = st.session_state[key]
            # 날짜 객체는 ISO 형식 문자열로 변환
            if isinstance(value, date):
                try: state_to_save[key] = value.isoformat()
                except Exception: print(f"Warning: Could not serialize date key '{key}' for saving.")
            # 기본 직렬화 가능 타입은 그대로 저장
            elif isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                 state_to_save[key] = value
            else: # 그 외 타입은 문자열로 변환 시도 (경고와 함께)
                 try: 
                     state_to_save[key] = str(value)
                     print(f"Info: Converted key '{key}' of type {type(value)} to string for saving.")
                 except Exception: 
                     print(f"Warning: Skipping non-serializable key '{key}' of type {type(value)} during save.")
    
    # uploaded_image_paths는 항상 리스트 형태로 저장 (비어있더라도)
    if "uploaded_image_paths" not in state_to_save or \
       not isinstance(state_to_save.get("uploaded_image_paths"), list):
        state_to_save["uploaded_image_paths"] = st.session_state.get("uploaded_image_paths", []) # 세션 값 없으면 빈 리스트
    
    return state_to_save


def load_state_from_data(loaded_data, update_basket_callback):
    if not isinstance(loaded_data, dict):
        st.error("잘못된 형식의 파일입니다 (딕셔셔리가 아님).")
        return False

    try: kst = pytz.timezone("Asia/Seoul"); default_date = datetime.now(kst).date()
    except Exception: default_date = datetime.now().date()
    
    # 로드 시 기본값 설정 (initialize_session_state의 defaults와 유사하게 구성)
    # via_point_floor 포함
    defaults_for_recovery = {
        "base_move_type": MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠",
        "is_storage_move": False, 
        "storage_type": data.DEFAULT_STORAGE_TYPE if hasattr(data, "DEFAULT_STORAGE_TYPE") else "컨테이너 보관 📦",
        "apply_long_distance": False, "customer_name": "", "customer_phone": "", "customer_email": "",
        "from_location": "", "to_location": "", "moving_date": default_date, "arrival_date": default_date,
        "from_floor": "", 
        "from_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "사다리차 🪜",
        "to_floor": "", 
        "to_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "사다리차 🪜",
        "special_notes": "", "storage_duration": 1, "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, "long_distance_options") else "선택 안 함",
        "vehicle_select_radio": "자동 추천 차량 사용", "manual_vehicle_select_value": None,
        "final_selected_vehicle": None, "prev_final_selected_vehicle": None, # prev도 여기서 None으로 초기화
        "sky_hours_from": 1, "sky_hours_final": 1, "add_men": 0, "add_women": 0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        # tab3_ 접두사 붙은 키로 로드 시 기본값 설정
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "tab3_deposit_amount": 0, "tab3_adjustment_amount": 0, "tab3_regional_ladder_surcharge": 0,
        "remove_base_housewife": False, "issue_tax_invoice": False, "card_payment": False,
        "dispatched_1t": 0, "dispatched_2_5t": 0, "dispatched_3_5t": 0, "dispatched_5t": 0,
        "has_via_point": False, "via_point_location": "",
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "사다리차 🪜",
        "via_point_surcharge": 0, 
        "via_point_floor": "",  # --- via_point_floor 기본값 추가 ---
        "uploaded_image_paths": [],
    }
    # 품목 수량 키에 대한 기본값 (0) 추가
    if hasattr(data, "item_definitions") and data.item_definitions:
        for move_type_load, sections_load in data.item_definitions.items():
            if isinstance(sections_load, dict):
                for section_load, item_list_load in sections_load.items():
                    if section_load == "폐기 처리 품목 🗑️": continue
                    if isinstance(item_list_load, list):
                        for item_load in item_list_load:
                            if hasattr(data, "items") and item_load in data.items:
                                key_load = f"qty_{move_type_load}_{section_load}_{item_load}"
                                if key_load not in defaults_for_recovery: defaults_for_recovery[key_load] = 0
    
    # 타입별 키 그룹 정의 (initialize_session_state와 유사하게)
    int_keys_load = [k for k,v in defaults_for_recovery.items() if isinstance(v, int) and not isinstance(v, bool)]
    float_keys_load = [k for k,v in defaults_for_recovery.items() if isinstance(v, float)]
    bool_keys_load = [k for k,v in defaults_for_recovery.items() if isinstance(v, bool)]
    list_keys_load = [k for k,v in defaults_for_recovery.items() if isinstance(v, list)]
    # via_point_floor를 string_keys_load에 명시적으로 추가
    string_keys_load = [k for k,v in defaults_for_recovery.items() if isinstance(v, str) and k != "via_point_floor"] 
    string_keys_load.append("via_point_floor")


    # loaded_data에 있는 값으로 세션 상태 업데이트, 없으면 defaults_for_recovery 값 사용
    for key in defaults_for_recovery.keys(): # 모든 예상되는 키에 대해 반복
        loaded_value = loaded_data.get(key) # 로드된 데이터에서 값 가져오기
        default_value_for_key = defaults_for_recovery.get(key) # 현재 키의 기본값

        final_value = default_value_for_key # 기본적으로 기본값 사용
        if loaded_value is not None: # 로드된 값이 있으면 타입 변환 시도
            try:
                if key in ["moving_date", "arrival_date"]:
                    if isinstance(loaded_value, str): final_value = datetime.fromisoformat(loaded_value).date()
                    elif isinstance(loaded_value, date): final_value = loaded_value
                    # else final_value는 이미 default_date로 설정됨 (위에서)
                elif key in int_keys_load:
                    if isinstance(loaded_value, str) and loaded_value.strip() == "": final_value = default_value_for_key
                    else: 
                        converted = int(float(loaded_value)) # 소수점 문자열 ".0" 등 처리
                        allow_neg = ["tab3_adjustment_amount", "adjustment_amount"] # state_manager에서 관리하는 키 기준
                        if key in allow_neg: final_value = converted
                        else: final_value = max(0, converted)
                        if key == "storage_duration": final_value = max(1, final_value)
                elif key in float_keys_load:
                    if isinstance(loaded_value, str) and loaded_value.strip() == "": final_value = default_value_for_key
                    else: final_value = float(loaded_value)
                    final_value = max(0.0, final_value)
                elif key in bool_keys_load:
                    if isinstance(loaded_value, str): final_value = loaded_value.lower() in ["true", "yes", "1", "on", "t"]
                    else: final_value = bool(loaded_value)
                elif key in list_keys_load: 
                    final_value = loaded_value if isinstance(loaded_value, list) else default_value_for_key
                elif key in string_keys_load or isinstance(default_value_for_key, str): # 명시적 문자열 또는 기본값이 문자열
                    final_value = str(loaded_value)
                else: # 그 외 타입 (주로 data.py의 원본 값을 유지해야 하는 selectbox 선택값 등)
                    final_value = loaded_value # 원본 값 그대로 사용
            except (ValueError, TypeError) as e_load_conv:
                print(f"Error converting loaded key '{key}' (value: '{loaded_value}', type: {type(loaded_value)}). Using default. Error: {e_load_conv}")
                # final_value는 이미 default_value_for_key로 설정되어 있음
        
        st.session_state[key] = final_value


    # Tab3 UI 입력 필드들(deposit_amount 등)을 tab3_ 접두사 붙은 값으로 동기화
    st.session_state.deposit_amount = st.session_state.get("tab3_deposit_amount", 0)
    st.session_state.adjustment_amount = st.session_state.get("tab3_adjustment_amount", 0)
    st.session_state.regional_ladder_surcharge = st.session_state.get("tab3_regional_ladder_surcharge", 0)
    for i in range(5): # 날짜 옵션
        st.session_state[f"date_opt_{i}_widget"] = st.session_state.get(f"tab3_date_opt_{i}_widget", False)

    # 탭 간 base_move_type 동기화
    if "base_move_type" in st.session_state:
        st.session_state.base_move_type_widget_tab1 = st.session_state.base_move_type
        st.session_state.base_move_type_widget_tab3 = st.session_state.base_move_type

    # uploaded_image_paths가 항상 리스트인지 확인
    if "uploaded_image_paths" not in st.session_state or not isinstance(st.session_state.uploaded_image_paths, list):
        st.session_state.uploaded_image_paths = []

    # 바구니 수량 업데이트 콜백 호출
    if callable(update_basket_callback):
        update_basket_callback()
    return True
