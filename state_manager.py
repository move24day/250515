# state_manager.py

import streamlit as st
from datetime import datetime, date
import pytz

try:
    import data
except ImportError as e:
    st.error(f"State Manager: 필수 모듈 로딩 실패 - {e}")
    st.stop()

# --- Constants ---
try:
    MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions else ["가정 이사 🏠", "사무실 이사 🏢"]
except Exception as e:
    MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
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
    "tab3_regional_ladder_surcharge", # 기존 '지방 사다리 추가요금'은 이 키로 저장됨
    "departure_ladder_surcharge_manual", # <--- 신규: 출발지 수동 사다리 추가금
    "arrival_ladder_surcharge_manual",   # <--- 신규: 도착지 수동 사다리 추가금
    "tab3_date_opt_0_widget", "tab3_date_opt_1_widget", "tab3_date_opt_2_widget",
    "tab3_date_opt_3_widget", "tab3_date_opt_4_widget",
    "remove_base_housewife",
    "remove_base_man",
    "move_time_option",
    "afternoon_move_details",
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

    default_move_type = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠"

    defaults = {
        "base_move_type": default_move_type,
        "base_move_type_widget_tab1": default_move_type,
        "base_move_type_widget_tab3": default_move_type,
        "is_storage_move": False,
        "storage_type": data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦",
        "apply_long_distance": False, "customer_name": "", "customer_phone": "",
        "customer_email": "",
        "from_location": "", "to_location": "", "moving_date": default_date,
        "arrival_date": default_date,
        "from_floor": "",
        "from_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜",
        "to_floor": "",
        "to_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜",
        "special_notes": "", "storage_duration": 1,
        "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "vehicle_select_radio": "자동 추천 차량 사용",
        "manual_vehicle_select_value": None,
        "final_selected_vehicle": None,
        "recommended_vehicle_auto": None,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "add_men": 0, "add_women": 0, "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "total_volume": 0.0, "total_weight": 0.0,
        'pdf_data_customer': None, 'final_excel_data': None,
        "deposit_amount": 0,
        "adjustment_amount": 0,
        "regional_ladder_surcharge": 0, # 기존 지방 사다리 추가금
        "departure_ladder_surcharge_manual": 0, # <--- 신규 추가
        "arrival_ladder_surcharge_manual": 0,   # <--- 신규 추가
        "via_point_surcharge": 0,
        "tab3_deposit_amount": 0,
        "tab3_adjustment_amount": 0,
        "tab3_regional_ladder_surcharge": 0, # 저장/로드용
        "tab3_departure_ladder_surcharge_manual": 0, # <--- 신규 추가 (저장/로드용)
        "tab3_arrival_ladder_surcharge_manual": 0,   # <--- 신규 추가 (저장/로드용)
        "remove_base_housewife": False,
        "remove_base_man": False,
        "move_time_option": "미선택",
        "afternoon_move_details": "",
        "issue_tax_invoice": False,
        "card_payment": False,
        "prev_final_selected_vehicle": None,
        "dispatched_1t": 0, "dispatched_2_5t": 0, "dispatched_3_5t": 0, "dispatched_5t": 0,
        "gdrive_search_term": "", "gdrive_search_results": [],
        "gdrive_file_options_map": {},
        "gdrive_selected_filename": None,
        "gdrive_selected_file_id": None,
        "has_via_point": False,
        "via_point_location": "",
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "사다리차 🪜",
        "via_point_floor": "",
        "uploaded_image_paths": [],
        "_app_initialized": True
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    int_keys = ["storage_duration", "sky_hours_from", "sky_hours_final", "add_men", "add_women",
                "deposit_amount", "adjustment_amount", "regional_ladder_surcharge",
                "departure_ladder_surcharge_manual", "arrival_ladder_surcharge_manual", # <--- 신규 추가
                "via_point_surcharge", "tab3_deposit_amount", "tab3_adjustment_amount",
                "tab3_regional_ladder_surcharge", 
                "tab3_departure_ladder_surcharge_manual", "tab3_arrival_ladder_surcharge_manual", # <--- 신규 추가
                "dispatched_1t", "dispatched_2_5t",
                "dispatched_3_5t", "dispatched_5t"]
    # ... (기존 float_keys, allow_negative_keys, bool_keys, list_keys, dict_keys, string_keys 정의는 이전 답변과 동일하게 유지) ...
    float_keys = ["waste_tons_input", "total_volume", "total_weight"]
    allow_negative_keys = ["adjustment_amount", "tab3_adjustment_amount"]
    bool_keys = ["is_storage_move", "apply_long_distance", "has_waste_check",
                 "remove_base_housewife", "remove_base_man",
                 "issue_tax_invoice", "card_payment",
                 "storage_use_electricity", "has_via_point",
                 "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget",
                 "date_opt_3_widget", "date_opt_4_widget",
                 "tab3_date_opt_0_widget", "tab3_date_opt_1_widget", "tab3_date_opt_2_widget",
                 "tab3_date_opt_3_widget", "tab3_date_opt_4_widget"]
    list_keys = ["uploaded_image_paths", "gdrive_search_results"]
    dict_keys = ["gdrive_file_options_map", "personnel_info_for_pdf"]
    string_keys = ["move_time_option", "afternoon_move_details", "customer_name", "customer_phone", "customer_email",
                   "from_location", "to_location", "from_floor", "to_floor", "special_notes", "long_distance_selector",
                   "manual_vehicle_select_value", "final_selected_vehicle", "recommended_vehicle_auto",
                   "prev_final_selected_vehicle", "gdrive_search_term", "gdrive_selected_filename",
                   "gdrive_selected_file_id", "via_point_location", "via_point_floor", "storage_type",
                   "from_method", "to_method", "via_point_method", "base_move_type",
                   "base_move_type_widget_tab1", "base_move_type_widget_tab3", "vehicle_select_radio"
                   ] # string_keys에 새 키 추가 안해도 기본 처리됨

    for k in defaults.keys():
        default_val_k = defaults.get(k)
        current_val_in_state = st.session_state.get(k)

        if k not in st.session_state or current_val_in_state is None:
            st.session_state[k] = default_val_k
            current_val_in_state = default_val_k

        try:
            if k in bool_keys:
                if isinstance(current_val_in_state, str): st.session_state[k] = current_val_in_state.lower() in ["true", "yes", "1", "on", "t"]
                else: st.session_state[k] = bool(current_val_in_state)
            elif k in int_keys:
                if isinstance(current_val_in_state, str) and current_val_in_state.strip() == "": st.session_state[k] = default_val_k; continue
                converted_val = int(float(current_val_in_state))
                if k in allow_negative_keys: st.session_state[k] = converted_val
                else: st.session_state[k] = max(0, converted_val)
                if k == "storage_duration": st.session_state[k] = max(1, st.session_state[k])
            elif k in float_keys:
                if isinstance(current_val_in_state, str) and current_val_in_state.strip() == "": st.session_state[k] = default_val_k; continue
                st.session_state[k] = float(current_val_in_state)
                if k not in allow_negative_keys : st.session_state[k] = max(0.0, st.session_state[k])
            elif k in list_keys:
                if not isinstance(current_val_in_state, list): st.session_state[k] = default_val_k if isinstance(default_val_k, list) else []
            elif k in dict_keys:
                if not isinstance(current_val_in_state, dict): st.session_state[k] = default_val_k if isinstance(default_val_k, dict) else {}
            elif isinstance(default_val_k, date) and k in ["moving_date", "arrival_date"]:
                 if isinstance(current_val_in_state, str):
                     try: st.session_state[k] = datetime.fromisoformat(current_val_in_state).date()
                     except ValueError: st.session_state[k] = default_val_k
                 elif not isinstance(current_val_in_state, date) : st.session_state[k] = default_val_k
            elif k in string_keys: 
                 st.session_state[k] = str(current_val_in_state) if current_val_in_state is not None else default_val_k
            elif isinstance(default_val_k, str) : 
                 st.session_state[k] = str(current_val_in_state) if current_val_in_state is not None else default_val_k
        except (ValueError, TypeError) as e_type:
            print(f"State Manager Init - Type Error for key '{k}', value '{current_val_in_state}': {e_type}. Using default: {default_val_k}")
            st.session_state[k] = default_val_k

    global STATE_KEYS_TO_SAVE # 전역 변수 사용 명시
    item_keys_to_save_dyn = []
    if hasattr(data, "item_definitions") and data.item_definitions:
        for move_type_key, sections in data.item_definitions.items():
            if isinstance(sections, dict):
                for section_key, item_list in sections.items():
                    if section_key == "폐기 처리 품목 🗑️": continue
                    if isinstance(item_list, list):
                        for item_name in item_list:
                            if hasattr(data, "items") and data.items is not None and item_name in data.items:
                                dynamic_key = f"qty_{move_type_key}_{section_key}_{item_name}"
                                item_keys_to_save_dyn.append(dynamic_key)
                                if dynamic_key not in st.session_state:
                                    st.session_state[dynamic_key] = 0
                                else:
                                    try: st.session_state[dynamic_key] = int(st.session_state[dynamic_key] or 0)
                                    except (ValueError, TypeError): st.session_state[dynamic_key] = 0

    for item_key_dyn in item_keys_to_save_dyn:
        if item_key_dyn not in STATE_KEYS_TO_SAVE:
            STATE_KEYS_TO_SAVE.append(item_key_dyn)

    if "prev_final_selected_vehicle" not in st.session_state:
        st.session_state["prev_final_selected_vehicle"] = st.session_state.get("final_selected_vehicle")

    if callable(update_basket_callback):
        update_basket_callback()

def prepare_state_for_save():
    state_to_save = {}
    keys_to_exclude = {
        "_app_initialized",
        "base_move_type_widget_tab1", "base_move_type_widget_tab3",
        "gdrive_selected_filename_widget",
        "pdf_data_customer", "final_excel_data",
        "gdrive_search_results", "gdrive_file_options_map",
        "deposit_amount", "adjustment_amount", "regional_ladder_surcharge", # 이들은 tab3_ 접두사로 저장
        "departure_ladder_surcharge_manual", "arrival_ladder_surcharge_manual", # 이들도 tab3_ 접두사로 저장
        "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget",
        "date_opt_3_widget", "date_opt_4_widget",
    }
    # UI 입력값을 저장용 키로 매핑 (tab3_ 접두사)
    st.session_state.tab3_deposit_amount = st.session_state.get("deposit_amount", 0)
    st.session_state.tab3_adjustment_amount = st.session_state.get("adjustment_amount", 0)
    st.session_state.tab3_regional_ladder_surcharge = st.session_state.get("regional_ladder_surcharge", 0)
    st.session_state.tab3_departure_ladder_surcharge_manual = st.session_state.get("departure_ladder_surcharge_manual", 0) # <--- 신규 추가
    st.session_state.tab3_arrival_ladder_surcharge_manual = st.session_state.get("arrival_ladder_surcharge_manual", 0)     # <--- 신규 추가

    for i in range(5):
        st.session_state[f"tab3_date_opt_{i}_widget"] = st.session_state.get(f"date_opt_{i}_widget", False)

    actual_keys_to_save = [key for key in STATE_KEYS_TO_SAVE if key not in keys_to_exclude]

    for key in actual_keys_to_save:
        if key in st.session_state:
            value = st.session_state[key]
            if isinstance(value, date):
                try: state_to_save[key] = value.isoformat()
                except Exception: print(f"Warning: Could not serialize date key '{key}' for saving.")
            elif isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                 state_to_save[key] = value
            else:
                 try: state_to_save[key] = str(value)
                 except Exception: print(f"Warning: Skipping non-serializable key '{key}' of type {type(value)} during save.")

    if "uploaded_image_paths" not in state_to_save or not isinstance(state_to_save.get("uploaded_image_paths"), list):
        state_to_save["uploaded_image_paths"] = st.session_state.get("uploaded_image_paths", [])
    return state_to_save


def load_state_from_data(loaded_data, update_basket_callback):
    if not isinstance(loaded_data, dict):
        st.error("잘못된 형식의 파일입니다 (딕셔셔리가 아님).")
        return False

    try: kst = pytz.timezone("Asia/Seoul"); default_date_load = datetime.now(kst).date()
    except Exception: default_date_load = datetime.now().date()

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
        "recommended_vehicle_auto": None,
        "sky_hours_from": 1, "sky_hours_final": 1, "add_men": 0, "add_women": 0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False,
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "tab3_deposit_amount": 0, "tab3_adjustment_amount": 0, 
        "tab3_regional_ladder_surcharge": 0,
        "tab3_departure_ladder_surcharge_manual": 0, # <--- 신규 추가
        "tab3_arrival_ladder_surcharge_manual": 0,   # <--- 신규 추가
        "remove_base_housewife": False,
        "remove_base_man": False,
        "move_time_option": "미선택",
        "afternoon_move_details": "",
        "issue_tax_invoice": False, "card_payment": False,
        "dispatched_1t": 0, "dispatched_2_5t": 0, "dispatched_3_5t": 0, "dispatched_5t": 0,
        "has_via_point": False, "via_point_location": "",
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "사다리차 🪜",
        "via_point_surcharge": 0,
        "via_point_floor": "",
        "uploaded_image_paths": [],
        "total_volume": 0.0, "total_weight": 0.0,
    }
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

    int_keys_load = [k for k,v_type in defaults_for_recovery.items() if isinstance(v_type, int) and not isinstance(v_type, bool)]
    float_keys_load = [k for k,v_type in defaults_for_recovery.items() if isinstance(v_type, float)]
    bool_keys_load = [k for k,v_type in defaults_for_recovery.items() if isinstance(v_type, bool)]
    list_keys_load = ["uploaded_image_paths", "gdrive_search_results"]
    dict_keys_load = ["gdrive_file_options_map", "personnel_info_for_pdf"]
    string_keys_load = [k for k,v_type in defaults_for_recovery.items() if isinstance(v_type, str)] # 모든 문자열 기본값 키
    allow_negative_keys_load = ["tab3_adjustment_amount", "adjustment_amount"]


    for key_from_save_file in STATE_KEYS_TO_SAVE:
        default_for_key = defaults_for_recovery.get(key_from_save_file)

        if key_from_save_file in loaded_data:
            value_from_file = loaded_data[key_from_save_file]
            try:
                target_value = None
                if key_from_save_file in ["moving_date", "arrival_date"]:
                    if isinstance(value_from_file, str):
                        try: target_value = datetime.fromisoformat(value_from_file).date()
                        except ValueError: target_value = default_for_key
                    elif isinstance(value_from_file, date): target_value = value_from_file
                    else: target_value = default_for_key
                elif key_from_save_file in int_keys_load:
                    if isinstance(value_from_file, str) and value_from_file.strip() == "": target_value = default_for_key
                    else: target_value = int(float(value_from_file))
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
                elif key_from_save_file in string_keys_load:
                    target_value = str(value_from_file) if value_from_file is not None else default_for_key
                elif isinstance(default_for_key, str): # string_keys_load에 누락된 문자열 키가 있을 경우 대비
                    target_value = str(value_from_file) if value_from_file is not None else default_for_key
                else:
                    target_value = value_from_file if value_from_file is not None else default_for_key
                st.session_state[key_from_save_file] = target_value
            except (ValueError, TypeError) as e_load_val:
                print(f"Error loading key '{key_from_save_file}' with value '{value_from_file}'. Type: {type(value_from_file)}. Error: {e_load_val}. Using default.")
                st.session_state[key_from_save_file] = default_for_key
        else:
            st.session_state[key_from_save_file] = default_for_key

    # UI 입력 필드와 tab3_ 저장용 필드 동기화 (로드 시)
    st.session_state.deposit_amount = st.session_state.get("tab3_deposit_amount", 0)
    st.session_state.adjustment_amount = st.session_state.get("tab3_adjustment_amount", 0)
    st.session_state.regional_ladder_surcharge = st.session_state.get("tab3_regional_ladder_surcharge", 0)
    st.session_state.departure_ladder_surcharge_manual = st.session_state.get("tab3_departure_ladder_surcharge_manual", 0) # <--- 신규 추가
    st.session_state.arrival_ladder_surcharge_manual = st.session_state.get("tab3_arrival_ladder_surcharge_manual", 0)     # <--- 신규 추가

    for i in range(5):
        st.session_state[f"date_opt_{i}_widget"] = st.session_state.get(f"tab3_date_opt_{i}_widget", False)

    if "base_move_type" in st.session_state:
        st.session_state.base_move_type_widget_tab1 = st.session_state.base_move_type
        st.session_state.base_move_type_widget_tab3 = st.session_state.base_move_type

    if "uploaded_image_paths" not in st.session_state or not isinstance(st.session_state.uploaded_image_paths, list):
        st.session_state.uploaded_image_paths = []

    if callable(update_basket_callback):
        update_basket_callback()
    return True
