# state_manager.py

import streamlit as st
from datetime import datetime, date
import pytz
# import json # prepare_state_for_save 에서만 사용, 필요시 유지

try:
    import data
    # import utils # initialize_session_state에서 직접 사용하지 않으므로 주석 처리 가능
except ImportError as e:
    st.error(f"State Manager: 필수 모듈 로딩 실패 - {e}")
    st.stop()
# except Exception as e: # 중복 예외 처리 제거
#     st.error(f"State Manager: 모듈 로딩 중 오류 - {e}")
#     st.stop()

# --- Constants ---
try:
    # 이모티콘 포함된 원본 키 사용 (ui_tab1, ui_tab3의 라디오 버튼 옵션과 일치)
    MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions else ["가정 이사 🏠", "사무실 이사 🏢"]
except Exception as e:
    MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"] # 비상시 기본값
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
    "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget",
    "date_opt_3_widget", "date_opt_4_widget",
    "tab3_deposit_amount",
    "tab3_adjustment_amount",
    "tab3_regional_ladder_surcharge",
    "tab3_date_opt_0_widget", "tab3_date_opt_1_widget", "tab3_date_opt_2_widget",
    "tab3_date_opt_3_widget", "tab3_date_opt_4_widget",
    "remove_base_housewife",
    "issue_tax_invoice",
    "card_payment",
    "prev_final_selected_vehicle",
    "dispatched_1t", "dispatched_2_5t", "dispatched_3_5t", "dispatched_5t",
    "has_via_point", "via_point_location", "via_point_method", "via_point_surcharge",
    "via_point_floor",
    "uploaded_image_paths",
]

def initialize_session_state(update_basket_callback=None):
    try: kst = pytz.timezone("Asia/Seoul"); default_date = datetime.now(kst).date()
    except Exception: default_date = datetime.now().date()

    default_move_type = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠" # 이모티콘 포함

    defaults = {
        "base_move_type": default_move_type,
        "base_move_type_widget_tab1": default_move_type, # ui_tab1 라디오 버튼의 키
        "base_move_type_widget_tab3": default_move_type, # ui_tab3 라디오 버튼의 키
        "is_storage_move": False,
        "storage_type": data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦", # 이모티콘 포함
        "apply_long_distance": False, "customer_name": "", "customer_phone": "",
        "customer_email": "",
        "from_location": "", "to_location": "", "moving_date": default_date,
        "arrival_date": default_date,
        "from_floor": "",
        "from_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜", # 이모티콘 포함
        "to_floor": "",
        "to_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜", # 이모티콘 포함
        "special_notes": "", "storage_duration": 1,
        "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "vehicle_select_radio": "자동 추천 차량 사용",
        "manual_vehicle_select_value": None, # data.py의 차량 이름(톤수 문자열)이 될 수 있음
        "final_selected_vehicle": None,    # data.py의 차량 이름(톤수 문자열)이 될 수 있음
        "recommended_vehicle_auto": None,  # data.py의 차량 이름(톤수 문자열)이 될 수 있음
        "sky_hours_from": 1, "sky_hours_final": 1,
        "add_men": 0, "add_women": 0, "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "total_volume": 0.0, "total_weight": 0.0,
        'pdf_data_customer': None, 'final_excel_data': None, # BytesIO 객체 또는 None
        "deposit_amount": 0,
        "adjustment_amount": 0,
        "regional_ladder_surcharge": 0,
        "via_point_surcharge": 0,
        "tab3_deposit_amount": 0,       # 저장/로드용
        "tab3_adjustment_amount": 0,    # 저장/로드용
        "tab3_regional_ladder_surcharge": 0, # 저장/로드용
        "remove_base_housewife": False,
        "issue_tax_invoice": False,
        "card_payment": False,
        "prev_final_selected_vehicle": None, # data.py의 차량 이름(톤수 문자열)이 될 수 있음
        "dispatched_1t": 0, "dispatched_2_5t": 0, "dispatched_3_5t": 0, "dispatched_5t": 0,
        "gdrive_search_term": "", "gdrive_search_results": [], # list of dicts
        "gdrive_file_options_map": {}, # dict
        "gdrive_selected_filename": None, # string or None
        "gdrive_selected_file_id": None,  # string or None
        "has_via_point": False,
        "via_point_location": "",
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜", # 이모티콘 포함
        "via_point_floor": "",
        "uploaded_image_paths": [], # list of strings
        "_app_initialized": True
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # 타입 강제 및 기본값 보장 로직 (이전 답변의 상세 로직을 여기에 통합)
    int_keys = ["storage_duration", "sky_hours_from", "sky_hours_final", "add_men", "add_women",
                "deposit_amount", "adjustment_amount", "regional_ladder_surcharge",
                "via_point_surcharge", "tab3_deposit_amount", "tab3_adjustment_amount",
                "tab3_regional_ladder_surcharge", "dispatched_1t", "dispatched_2_5t",
                "dispatched_3_5t", "dispatched_5t"]
    float_keys = ["waste_tons_input", "total_volume", "total_weight"] # total_volume, total_weight도 float
    allow_negative_keys = ["adjustment_amount", "tab3_adjustment_amount"]
    bool_keys = ["is_storage_move", "apply_long_distance", "has_waste_check",
                 "remove_base_housewife", "issue_tax_invoice", "card_payment",
                 "storage_use_electricity", "has_via_point",
                 "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget",
                 "date_opt_3_widget", "date_opt_4_widget",
                 "tab3_date_opt_0_widget", "tab3_date_opt_1_widget", "tab3_date_opt_2_widget",
                 "tab3_date_opt_3_widget", "tab3_date_opt_4_widget"]
    list_keys = ["uploaded_image_paths", "gdrive_search_results"]
    dict_keys = ["gdrive_file_options_map", "personnel_info_for_pdf"] # personnel_info_for_pdf 추가될 수 있음
    # string_keys는 명시적으로 처리하기보다, 위 타입에 속하지 않으면 기본 str 변환 또는 기본값 유지

    for k in defaults.keys(): # 모든 기본값 키에 대해 반복
        default_val_k = defaults.get(k) # 현재 키의 기본값
        current_val_in_state = st.session_state.get(k) # 현재 세션 상태 값

        # 세션에 키가 없거나, 값이 None이면 기본값으로 설정 (이미 위에서 처리되었을 수 있음)
        if k not in st.session_state or current_val_in_state is None:
            st.session_state[k] = default_val_k
            current_val_in_state = default_val_k # 이후 타입 검사를 위해 현재값 업데이트

        try:
            if k in bool_keys:
                if isinstance(current_val_in_state, str): st.session_state[k] = current_val_in_state.lower() in ["true", "yes", "1", "on", "t"]
                else: st.session_state[k] = bool(current_val_in_state)
            elif k in int_keys:
                if isinstance(current_val_in_state, str) and current_val_in_state.strip() == "": st.session_state[k] = default_val_k; continue
                converted_val = int(float(current_val_in_state)) # 문자열 "1.0" 같은 경우 대비
                if k in allow_negative_keys: st.session_state[k] = converted_val
                else: st.session_state[k] = max(0, converted_val)
                if k == "storage_duration": st.session_state[k] = max(1, st.session_state[k])
            elif k in float_keys:
                if isinstance(current_val_in_state, str) and current_val_in_state.strip() == "": st.session_state[k] = default_val_k; continue
                st.session_state[k] = float(current_val_in_state)
                if k not in allow_negative_keys : st.session_state[k] = max(0.0, st.session_state[k]) # 음수 허용 안되는 float
            elif k in list_keys:
                if not isinstance(current_val_in_state, list): st.session_state[k] = default_val_k if isinstance(default_val_k, list) else []
            elif k in dict_keys:
                if not isinstance(current_val_in_state, dict): st.session_state[k] = default_val_k if isinstance(default_val_k, dict) else {}
            elif isinstance(default_val_k, date) and k in ["moving_date", "arrival_date"]: # 날짜 타입
                 if isinstance(current_val_in_state, str):
                     try: st.session_state[k] = datetime.fromisoformat(current_val_in_state).date()
                     except ValueError: st.session_state[k] = default_val_k
                 elif not isinstance(current_val_in_state, date) : st.session_state[k] = default_val_k
            # 다른 문자열 타입들은 기본값 할당 시 이미 문자열이므로 별도 처리 불필요 (None일 경우 빈 문자열로)
            elif isinstance(default_val_k, str):
                 st.session_state[k] = str(current_val_in_state) if current_val_in_state is not None else default_val_k


        except (ValueError, TypeError) as e_type:
            print(f"State Manager Init - Type Error for key '{k}', value '{current_val_in_state}': {e_type}. Using default: {default_val_k}")
            st.session_state[k] = default_val_k


    # 품목 수량 키들 초기화 ('qty_이사유형_섹션명_품목명')
    global STATE_KEYS_TO_SAVE # 전역 변수 사용 명시
    item_keys_to_save_dyn = [] # 동적으로 생성된 품목키 저장용 (STATE_KEYS_TO_SAVE에 추가 위함)
    if hasattr(data, "item_definitions") and data.item_definitions:
        for move_type_key, sections in data.item_definitions.items(): # 이모티콘 포함된 원본 키 사용
            if isinstance(sections, dict):
                for section_key, item_list in sections.items(): # 이모티콘 포함된 원본 키 사용
                    if section_key == "폐기 처리 품목 🗑️": continue # 폐기품목은 수량 관리 안함
                    if isinstance(item_list, list):
                        for item_name in item_list:
                            if hasattr(data, "items") and data.items is not None and item_name in data.items: # 유효한 품목인지 확인
                                dynamic_key = f"qty_{move_type_key}_{section_key}_{item_name}"
                                item_keys_to_save_dyn.append(dynamic_key)
                                if dynamic_key not in st.session_state:
                                    st.session_state[dynamic_key] = 0 # 기본 수량 0으로 초기화
                                else: # 이미 있으면 타입 확인 (정수여야 함)
                                    try: st.session_state[dynamic_key] = int(st.session_state[dynamic_key] or 0)
                                    except (ValueError, TypeError): st.session_state[dynamic_key] = 0


    # 동적으로 생성된 품목 키들을 STATE_KEYS_TO_SAVE에 추가 (중복 방지)
    for item_key_dyn in item_keys_to_save_dyn:
        if item_key_dyn not in STATE_KEYS_TO_SAVE:
            STATE_KEYS_TO_SAVE.append(item_key_dyn)

    # prev_final_selected_vehicle 초기화 (final_selected_vehicle 값으로)
    if "prev_final_selected_vehicle" not in st.session_state:
        st.session_state["prev_final_selected_vehicle"] = st.session_state.get("final_selected_vehicle")


    # 앱 초기화 완료 후 콜백 호출 (필요시)
    if callable(update_basket_callback):
        update_basket_callback()

# prepare_state_for_save 와 load_state_from_data 함수는 이전 답변의 최종본을 사용하면 됩니다.
# (STATE_KEYS_TO_SAVE에 via_point_floor가 포함되어 있으므로 자동으로 처리됩니다.)
# (load_state_from_data의 defaults_for_recovery에도 via_point_floor가 포함되어야 합니다.)

def prepare_state_for_save():
    state_to_save = {}
    # UI 위젯에 직접 바인딩되지만, 실제 저장은 다른 이름으로 되거나(tab3_ prefix)
    # 혹은 저장할 필요가 없는 UI 전용 상태들
    keys_to_exclude = {
        "_app_initialized",
        "base_move_type_widget_tab1", # base_move_type으로 통합 저장
        "base_move_type_widget_tab3", # base_move_type으로 통합 저장
        "gdrive_selected_filename_widget", # UI용 임시 상태
        "pdf_data_customer", # 생성된 파일 데이터 (저장 X)
        "final_excel_data",  # 생성된 파일 데이터 (저장 X)
        "gdrive_search_results", # UI용 임시 상태
        "gdrive_file_options_map", # UI용 임시 상태
        # 아래 키들은 tab3_ 접두사가 붙은 키로 저장되므로 원본은 제외
        "deposit_amount", "adjustment_amount", "regional_ladder_surcharge",
        "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget",
        "date_opt_3_widget", "date_opt_4_widget",
    }
    # Tab3의 UI 입력값을 tab3_ 접두사가 붙은 저장용 키로 매핑
    # (state_manager.py의 STATE_KEYS_TO_SAVE 목록과 일치해야 함)
    st.session_state.tab3_deposit_amount = st.session_state.get("deposit_amount", 0)
    st.session_state.tab3_adjustment_amount = st.session_state.get("adjustment_amount", 0)
    st.session_state.tab3_regional_ladder_surcharge = st.session_state.get("regional_ladder_surcharge", 0)
    for i in range(5): # 날짜 옵션 동기화
        st.session_state[f"tab3_date_opt_{i}_widget"] = st.session_state.get(f"date_opt_{i}_widget", False)

    # STATE_KEYS_TO_SAVE 목록에 있는 키들만 저장 대상으로 함
    # (이 목록에는 동적으로 추가된 qty_ 품목키와 via_point_floor 등이 이미 포함되어 있어야 함)
    actual_keys_to_save = [key for key in STATE_KEYS_TO_SAVE if key not in keys_to_exclude]

    for key in actual_keys_to_save:
        if key in st.session_state:
            value = st.session_state[key]
            if isinstance(value, date): # 날짜 객체는 ISO 형식 문자열로 변환
                try: state_to_save[key] = value.isoformat()
                except Exception: print(f"Warning: Could not serialize date key '{key}' for saving.")
            # JSON으로 직렬화 가능한 기본 타입들은 그대로 저장
            elif isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                 state_to_save[key] = value
            else: # 그 외 타입은 문자열로 변환 시도 (예상치 못한 타입 방지)
                 try: state_to_save[key] = str(value)
                 except Exception: print(f"Warning: Skipping non-serializable key '{key}' of type {type(value)} during save.")

    # uploaded_image_paths는 항상 리스트 형태로 저장되도록 보장
    if "uploaded_image_paths" not in state_to_save or not isinstance(state_to_save.get("uploaded_image_paths"), list):
        state_to_save["uploaded_image_paths"] = st.session_state.get("uploaded_image_paths", [])
    return state_to_save


def load_state_from_data(loaded_data, update_basket_callback):
    if not isinstance(loaded_data, dict):
        st.error("잘못된 형식의 파일입니다 (딕셔셔리가 아님).")
        return False

    try: kst = pytz.timezone("Asia/Seoul"); default_date_load = datetime.now(kst).date()
    except Exception: default_date_load = datetime.now().date()
    
    # 로드 시 기본값 정의 (initialize_session_state와 거의 동일해야 함)
    default_move_type_load = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠"
    defaults_for_recovery = {
        "base_move_type": default_move_type_load,
        "base_move_type_widget_tab1": default_move_type_load,
        "base_move_type_widget_tab3": default_move_type_load,
        "is_storage_move": False,
        "storage_type": data.DEFAULT_STORAGE_TYPE if hasattr(data, "DEFAULT_STORAGE_TYPE") else "컨테이너 보관 📦",
        "apply_long_distance": False, "customer_name": "", "customer_phone": "", "customer_email": "",
        "from_location": "", "to_location": "", "moving_date": default_date_load, "arrival_date": default_date_load,
        "from_floor": "",
        "from_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "사다리차 🪜",
        "to_floor": "",
        "to_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "사다리차 🪜",
        "special_notes": "", "storage_duration": 1, "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, "long_distance_options") else "선택 안 함",
        "vehicle_select_radio": "자동 추천 차량 사용", "manual_vehicle_select_value": None,
        "final_selected_vehicle": None, "prev_final_selected_vehicle": None,
        "recommended_vehicle_auto": None, # 추가된 키
        "sky_hours_from": 1, "sky_hours_final": 1, "add_men": 0, "add_women": 0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "tab3_deposit_amount": 0, "tab3_adjustment_amount": 0, "tab3_regional_ladder_surcharge": 0,
        "remove_base_housewife": False, "issue_tax_invoice": False, "card_payment": False,
        "dispatched_1t": 0, "dispatched_2_5t": 0, "dispatched_3_5t": 0, "dispatched_5t": 0,
        "has_via_point": False, "via_point_location": "",
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "사다리차 🪜",
        "via_point_surcharge": 0,
        "via_point_floor": "",  # via_point_floor 기본값 추가
        "uploaded_image_paths": [],
        "total_volume": 0.0, "total_weight": 0.0, # 계산 결과이므로 로드 시 0으로 초기화 가능
    }
    # 동적 품목키 기본값 추가 (0으로)
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
    
    # 타입 그룹 정의 (initialize_session_state와 유사하게)
    int_keys_load = [k for k,v_type in defaults_for_recovery.items() if isinstance(v_type, int) and not isinstance(v_type, bool)]
    float_keys_load = [k for k,v_type in defaults_for_recovery.items() if isinstance(v_type, float)]
    bool_keys_load = [k for k,v_type in defaults_for_recovery.items() if isinstance(v_type, bool)]
    list_keys_load = ["uploaded_image_paths", "gdrive_search_results"] # 명시적으로 지정
    dict_keys_load = ["gdrive_file_options_map", "personnel_info_for_pdf"]  # 명시적으로 지정
    allow_negative_keys_load = ["tab3_adjustment_amount", "adjustment_amount"]


    # 저장된 데이터(loaded_data)를 사용하여 세션 상태 업데이트
    for key_from_save_file in STATE_KEYS_TO_SAVE: # 저장된 키 목록을 기준으로 루프
        default_for_key = defaults_for_recovery.get(key_from_save_file) # 해당 키의 기본값 가져오기

        if key_from_save_file in loaded_data:
            value_from_file = loaded_data[key_from_save_file]
            try:
                target_value = None
                if key_from_save_file in ["moving_date", "arrival_date"]:
                    if isinstance(value_from_file, str):
                        try: target_value = datetime.fromisoformat(value_from_file).date()
                        except ValueError: target_value = default_for_key # ISO 포맷 아니면 기본값
                    elif isinstance(value_from_file, date): target_value = value_from_file
                    else: target_value = default_for_key
                elif key_from_save_file in int_keys_load: # 수량키(qty_) 포함
                    if isinstance(value_from_file, str) and value_from_file.strip() == "": target_value = default_for_key
                    else: target_value = int(float(value_from_file)) # 문자열 "1.0" 같은 경우 대비
                    if key_from_save_file not in allow_negative_keys_load: target_value = max(0, target_value)
                    if key_from_save_file == "storage_duration": target_value = max(1, target_value)
                elif key_from_save_file in float_keys_load:
                    if isinstance(value_from_file, str) and value_from_file.strip() == "": target_value = default_for_key
                    else: target_value = float(value_from_file)
                    if key_from_save_file not in allow_negative_keys_load : target_value = max(0.0, target_value)
                elif key_from_save_file in bool_keys_load:
                    if isinstance(value_from_file, str): target_value = value_from_file.lower() in ["true", "yes", "1", "on", "t"]
                    else: target_value = bool(value_from_file)
                elif key_from_save_file in list_keys_load:
                    target_value = value_from_file if isinstance(value_from_file, list) else (default_for_key if isinstance(default_for_key, list) else [])
                elif key_from_save_file in dict_keys_load:
                    target_value = value_from_file if isinstance(value_from_file, dict) else (default_for_key if isinstance(default_for_key, dict) else {})
                elif isinstance(default_for_key, str): # 기본값이 문자열인 나머지 키들
                    target_value = str(value_from_file) if value_from_file is not None else default_for_key
                else: # 그 외 타입은 일단 그대로 할당 (None일 경우 기본값)
                    target_value = value_from_file if value_from_file is not None else default_for_key
                st.session_state[key_from_save_file] = target_value
            except (ValueError, TypeError) as e_load_val:
                print(f"Error loading key '{key_from_save_file}' with value '{value_from_file}'. Type: {type(value_from_file)}. Error: {e_load_val}. Using default.")
                st.session_state[key_from_save_file] = default_for_key
        else: # 저장된 파일에 키가 없으면 기본값으로 설정
            st.session_state[key_from_save_file] = default_for_key

    # UI 입력 필드와 tab3_ 저장용 필드 동기화
    st.session_state.deposit_amount = st.session_state.get("tab3_deposit_amount", 0)
    st.session_state.adjustment_amount = st.session_state.get("tab3_adjustment_amount", 0)
    st.session_state.regional_ladder_surcharge = st.session_state.get("tab3_regional_ladder_surcharge", 0)
    for i in range(5): # 날짜 옵션 동기화
        st.session_state[f"date_opt_{i}_widget"] = st.session_state.get(f"tab3_date_opt_{i}_widget", False)

    # base_move_type 관련 UI 위젯 값 동기화
    if "base_move_type" in st.session_state:
        st.session_state.base_move_type_widget_tab1 = st.session_state.base_move_type
        st.session_state.base_move_type_widget_tab3 = st.session_state.base_move_type
    
    # uploaded_image_paths가 리스트인지 최종 확인
    if "uploaded_image_paths" not in st.session_state or not isinstance(st.session_state.uploaded_image_paths, list):
        st.session_state.uploaded_image_paths = []


    # 로드 후 콜백 호출 (예: 바구니 수량 업데이트)
    if callable(update_basket_callback):
        update_basket_callback()
    return True
