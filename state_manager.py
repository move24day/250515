# state_manager.py

import streamlit as st
from datetime import datetime, date
import pytz

try:
    import data
except ImportError as e:
    st.error(f"State Manager: 필수 모듈 data.py 로딩 실패 - {e}")
    st.stop()

try:
    MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions else ["가정 이사 🏠", "사무실 이사 🏢"]
except Exception as e:
    MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"] 
    st.warning(f"data.py에서 이사 유형 로딩 중 오류 발생: {e}. 기본값을 사용합니다.")

STATE_KEYS_TO_SAVE = [
    "base_move_type", "is_storage_move", "storage_type", "apply_long_distance", "long_distance_selector",
    "customer_name", "customer_phone", "customer_email", 
    "moving_date", "arrival_date", "storage_duration", "storage_use_electricity",
    "contract_date", # <--- 계약일 키 추가
    "from_address_full", "from_floor", "from_method", 
    "to_address_full", "to_floor", "to_method",     
    "has_via_point", "via_point_address", "via_point_floor", "via_point_method", "via_point_surcharge", 
    "special_notes",
    "vehicle_select_radio", "manual_vehicle_select_value", "final_selected_vehicle",
    "add_men", "add_women", "remove_base_housewife", "remove_base_man",
    "sky_hours_from", "sky_hours_final",
    "dispatched_1t", "dispatched_2_5t","dispatched_3_5t", "dispatched_5t",
    "has_waste_check", "waste_tons_input",
    "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget", "date_opt_3_widget", "date_opt_4_widget", 
    "manual_ladder_from_check", "departure_ladder_surcharge_manual", 
    "manual_ladder_to_check", "arrival_ladder_surcharge_manual",       
    "deposit_amount", "adjustment_amount", 
    "issue_tax_invoice", "card_payment", 
    "move_time_option", "afternoon_move_details", 
    "uploaded_image_paths",
    "tab3_deposit_amount", "tab3_adjustment_amount", 
    "tab3_departure_ladder_surcharge_manual", "tab3_arrival_ladder_surcharge_manual",
    "tab3_date_opt_0_widget", "tab3_date_opt_1_widget", "tab3_date_opt_2_widget", 
    "tab3_date_opt_3_widget", "tab3_date_opt_4_widget",
    "prev_final_selected_vehicle" 
]

def get_default_times_for_date(selected_date): # 이 함수는 현재 직접 사용되지 않음
    if not isinstance(selected_date, date):
        selected_date = date.today()
    return selected_date.strftime("%H:%M") 

def initialize_session_state(update_basket_callback=None):
    try:
        KST = pytz.timezone("Asia/Seoul")
    except pytz.UnknownTimeZoneError:
        KST = pytz.utc
    
    today_kst = datetime.now(KST).date()
    
    defaults = {
        "base_move_type": MOVE_TYPE_OPTIONS[0],
        "is_storage_move": False,
        "storage_type": data.STORAGE_TYPES[0] if hasattr(data, "STORAGE_TYPES") and data.STORAGE_TYPES else "컨테이너 보관 📦",
        "apply_long_distance": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, "long_distance_options") and data.long_distance_options else "선택 안 함",
        "customer_name": "", "customer_phone": "", "customer_email": "",
        "moving_date": today_kst,
        "arrival_date": today_kst, 
        "contract_date": today_kst, # 계약일 기본값
        "storage_duration": 1, "storage_use_electricity": False,
        "from_address_full": "", "from_floor": "", 
        "from_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "계단 🚶",
        "to_address_full": "", "to_floor": "", 
        "to_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "계단 🚶",
        "has_via_point": False, "via_point_address": "", "via_point_floor": "", 
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "계단 🚶",
        "via_point_surcharge": 0,
        "special_notes": "",
        "vehicle_select_radio": "자동 추천 차량 사용",
        "manual_vehicle_select_value": None, 
        "final_selected_vehicle": None,
        "recommended_vehicle_auto": None, "recommended_base_price_auto": 0.0,
        "total_volume": 0.0, "total_weight": 0.0,
        "add_men": 0, "add_women": 0,
        "remove_base_housewife": False, "remove_base_man": False,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "dispatched_1t":0, "dispatched_2_5t":0, "dispatched_3_5t":0, "dispatched_5t":0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        "manual_ladder_from_check": False, "departure_ladder_surcharge_manual": getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0),
        "manual_ladder_to_check": False, "arrival_ladder_surcharge_manual": getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0),
        "deposit_amount": 0, "adjustment_amount": 0, 
        "issue_tax_invoice": False, "card_payment": False,
        "pdf_ready": False, "pdf_bytes": None,
        "selected_items": {}, 
        "move_time_option": "오전", "afternoon_move_details": "",
        "customer_final_pdf_data": None, 
        "uploaded_image_paths": [], 
        "tab3_deposit_amount": 0, 
        "tab3_adjustment_amount": 0, 
        "tab3_departure_ladder_surcharge_manual": 0,
        "tab3_arrival_ladder_surcharge_manual": 0,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False, 
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "prev_final_selected_vehicle": None,
        "_app_initialized": True
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    int_keys = ["storage_duration", "sky_hours_from", "sky_hours_final", "add_men", "add_women",
                "deposit_amount", "adjustment_amount", 
                "departure_ladder_surcharge_manual", "arrival_ladder_surcharge_manual", 
                "via_point_surcharge", "tab3_deposit_amount", "tab3_adjustment_amount",
                "tab3_departure_ladder_surcharge_manual", "tab3_arrival_ladder_surcharge_manual", 
                "dispatched_1t", "dispatched_2_5t", "dispatched_3_5t", "dispatched_5t"]
    float_keys = ["waste_tons_input", "total_volume", "total_weight"]
    allow_negative_keys = ["adjustment_amount", "tab3_adjustment_amount"]
    bool_keys = ["is_storage_move", "apply_long_distance", "has_waste_check",
                 "remove_base_housewife", "remove_base_man",
                 "issue_tax_invoice", "card_payment",
                 "storage_use_electricity", "has_via_point",
                 "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget",
                 "date_opt_3_widget", "date_opt_4_widget",
                 "tab3_date_opt_0_widget", "tab3_date_opt_1_widget", "tab3_date_opt_2_widget",
                 "tab3_date_opt_3_widget", "tab3_date_opt_4_widget",
                 "manual_ladder_from_check", "manual_ladder_to_check"]
    list_keys = ["uploaded_image_paths"] 
    dict_keys = ["selected_items", "personnel_info_for_pdf"] 
    string_keys = ["move_time_option", "afternoon_move_details", "customer_name", "customer_phone", "customer_email",
                   "from_address_full", "to_address_full", "from_floor", "to_floor", "special_notes", "long_distance_selector",
                   "manual_vehicle_select_value", "final_selected_vehicle", "recommended_vehicle_auto",
                   "prev_final_selected_vehicle", 
                   "via_point_address", "via_point_floor", "storage_type",
                   "from_method", "to_method", "via_point_method", "base_move_type",
                   "base_move_type_widget_tab1", "base_move_type_widget_tab3", "vehicle_select_radio"
                   ]

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
                if isinstance(current_val_in_state, str) and current_val_in_state.strip() == "": st.session_state[k] = default_val_k if isinstance(default_val_k, int) else 0; continue
                converted_val = int(float(current_val_in_state)) 
                if k in allow_negative_keys: st.session_state[k] = converted_val
                else: st.session_state[k] = max(0, converted_val)
                if k == "storage_duration": st.session_state[k] = max(1, st.session_state[k])
            elif k in float_keys:
                if isinstance(current_val_in_state, str) and current_val_in_state.strip() == "": st.session_state[k] = default_val_k if isinstance(default_val_k, float) else 0.0; continue
                st.session_state[k] = float(current_val_in_state)
                if k not in allow_negative_keys : st.session_state[k] = max(0.0, st.session_state[k]) 
            elif k in list_keys:
                if not isinstance(current_val_in_state, list): st.session_state[k] = default_val_k if isinstance(default_val_k, list) else []
            elif k in dict_keys:
                if not isinstance(current_val_in_state, dict): st.session_state[k] = default_val_k if isinstance(default_val_k, dict) else {}
            elif isinstance(default_val_k, date) and k in ["moving_date", "arrival_date", "contract_date"]: 
                 if isinstance(current_val_in_state, str):
                     try: st.session_state[k] = datetime.fromisoformat(current_val_in_state).date()
                     except ValueError: st.session_state[k] = default_val_k
                 elif not isinstance(current_val_in_state, date) : st.session_state[k] = default_val_k
            elif k in string_keys: 
                 st.session_state[k] = str(current_val_in_state) if current_val_in_state is not None else (default_val_k if default_val_k is not None else "")
            elif isinstance(default_val_k, str) : 
                 st.session_state[k] = str(current_val_in_state) if current_val_in_state is not None else (default_val_k if default_val_k is not None else "")
        except (ValueError, TypeError) as e_type:
            print(f"State Manager Init - Type Error for key '{k}', value '{current_val_in_state}': {e_type}. Using default: {default_val_k}")
            st.session_state[k] = default_val_k

    global STATE_KEYS_TO_SAVE 
    item_keys_to_save_dyn = []
    if hasattr(data, "item_definitions") and data.item_definitions:
        for move_type_key, sections in data.item_definitions.items():
            if isinstance(sections, dict):
                for section_key, item_list in sections.items():
                    if section_key == data.WASTE_SECTION_NAME if hasattr(data, "WASTE_SECTION_NAME") else False : continue
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

def prepare_state_for_save(current_state_dict): 
    state_to_save = {}
    keys_to_exclude = {
        "_app_initialized",
        "base_move_type_widget_tab1", "base_move_type_widget_tab3", 
        "gdrive_selected_filename_widget_tab1", 
        "pdf_data_customer", "final_excel_data", "customer_final_pdf_data", 
        "internal_form_image_data", "internal_excel_data_for_download",
        "gdrive_search_results", "gdrive_file_options_map", 
        "deposit_amount", "adjustment_amount", 
        "departure_ladder_surcharge_manual", "arrival_ladder_surcharge_manual",
        "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget",
        "date_opt_3_widget", "date_opt_4_widget",
        "recommended_vehicle_auto", "recommended_base_price_auto",
    }
    st.session_state.tab3_deposit_amount = current_state_dict.get("deposit_amount", 0)
    st.session_state.tab3_adjustment_amount = current_state_dict.get("adjustment_amount", 0)
    st.session_state.tab3_departure_ladder_surcharge_manual = current_state_dict.get("departure_ladder_surcharge_manual", 0)
    st.session_state.tab3_arrival_ladder_surcharge_manual = current_state_dict.get("arrival_ladder_surcharge_manual", 0)
    for i in range(5):
        st.session_state[f"tab3_date_opt_{i}_widget"] = current_state_dict.get(f"date_opt_{i}_widget", False)

    actual_keys_to_save = [key for key in STATE_KEYS_TO_SAVE if key not in keys_to_exclude]

    for key in actual_keys_to_save:
        if key in current_state_dict: 
            value = current_state_dict[key]
            if isinstance(value, date):
                try: state_to_save[key] = value.isoformat()
                except Exception: print(f"Warning: Could not serialize date key '{key}' for saving.")
            elif isinstance(value, (str, int, float, bool, list, dict)) or value is None:
                 state_to_save[key] = value
            else:
                 try: state_to_save[key] = str(value) 
                 except Exception: print(f"Warning: Skipping non-serializable key '{key}' of type {type(value)} during save.")

    if "uploaded_image_paths" not in state_to_save or not isinstance(state_to_save.get("uploaded_image_paths"), list):
        state_to_save["uploaded_image_paths"] = current_state_dict.get("uploaded_image_paths", [])
    
    state_to_save["app_version"] = "1.1.1" # 예시 버전 업데이트
    state_to_save["saved_at_kst"] = datetime.now(pytz.timezone("Asia/Seoul") if "pytz" in globals() else None).isoformat()

    return state_to_save


def load_state_from_data(loaded_data_dict, update_basket_callback=None):
    if not isinstance(loaded_data_dict, dict):
        st.error("로드할 데이터 형식이 올바르지 않습니다.")
        return False

    try: kst_load = pytz.timezone("Asia/Seoul"); default_date_load = datetime.now(kst_load).date()
    except Exception: default_date_load = datetime.now().date()
    default_move_type_load = MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠"
    
    defaults_for_loading = {
        "base_move_type": default_move_type_load, "is_storage_move": False, 
        "storage_type": data.STORAGE_TYPES[0] if hasattr(data, "STORAGE_TYPES") and data.STORAGE_TYPES else "컨테이너 보관 📦",
        "apply_long_distance": False, "long_distance_selector": data.long_distance_options[0] if hasattr(data, "long_distance_options") else "선택 안 함",
        "customer_name": "", "customer_phone": "", "customer_email": "",
        "moving_date": default_date_load, "arrival_date": default_date_load, "contract_date": default_date_load, # 계약일 추가
        "storage_duration": 1, "storage_use_electricity": False,
        "from_address_full": "", "from_floor": "", "from_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") else "계단 🚶",
        "to_address_full": "", "to_floor": "", "to_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") else "계단 🚶",
        "has_via_point": False, "via_point_address": "", "via_point_floor": "", 
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") else "계단 🚶",
        "via_point_surcharge": 0,
        "special_notes": "",
        "vehicle_select_radio": "자동 추천 차량 사용", "manual_vehicle_select_value": None, "final_selected_vehicle": None,
        "add_men": 0, "add_women": 0, "remove_base_housewife": False, "remove_base_man": False,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "dispatched_1t":0, "dispatched_2_5t":0, "dispatched_3_5t":0, "dispatched_5t":0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False, 
        "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "tab3_deposit_amount": 0, "tab3_adjustment_amount": 0, 
        "tab3_departure_ladder_surcharge_manual": 0, "tab3_arrival_ladder_surcharge_manual": 0,
        "issue_tax_invoice": False, "card_payment": False,
        "move_time_option": "오전", "afternoon_move_details": "",
        "uploaded_image_paths": [], "total_volume": 0.0, "total_weight": 0.0,
        "prev_final_selected_vehicle": None,
        "manual_ladder_from_check": False, # UI용 체크박스 상태
        "manual_ladder_to_check": False    # UI용 체크박스 상태
    }
    if hasattr(data, 'item_definitions') and data.item_definitions:
        for move_type_key, sections in data.item_definitions.items():
            if isinstance(sections, dict):
                for section_key, items_in_section in sections.items():
                    if isinstance(items_in_section, list):
                        for item_name_key in items_in_section:
                             if hasattr(data, "items") and item_name_key in data.items:
                                defaults_for_loading[f"qty_{move_type_key}_{section_key}_{item_name_key}"] = 0
    
    int_keys_load = [k for k,v_type in defaults_for_loading.items() if isinstance(v_type, int) and not isinstance(v_type, bool)]
    float_keys_load = [k for k,v_type in defaults_for_loading.items() if isinstance(v_type, float)]
    bool_keys_load = [k for k,v_type in defaults_for_loading.items() if isinstance(v_type, bool)]
    list_keys_load = ["uploaded_image_paths"]
    date_keys_load = ["moving_date", "arrival_date", "contract_date"]
    string_keys_load = [k for k,v_type in defaults_for_loading.items() if isinstance(v_type, str)] 
    allow_negative_keys_load = ["tab3_adjustment_amount", "adjustment_amount"]

    for key_from_save_file in STATE_KEYS_TO_SAVE + [k for k in defaults_for_loading if k.startswith("qty_")]: # 모든 키 확인
        default_for_key = defaults_for_loading.get(key_from_save_file) 
        value_from_file = loaded_data_dict.get(key_from_save_file)
        
        if value_from_file is None: # 파일에 없으면 기본값 사용
            st.session_state[key_from_save_file] = default_for_key
            continue

        try:
            target_value = value_from_file
            if key_from_save_file in date_keys_load:
                if isinstance(value_from_file, str):
                    try: target_value = date.fromisoformat(value_from_file)
                    except ValueError: target_value = default_for_key
                elif not isinstance(value_from_file, date): target_value = default_for_key
            elif key_from_save_file in int_keys_load or key_from_save_file.startswith("qty_"):
                if isinstance(value_from_file, str) and not value_from_file.strip(): target_value = default_for_key if isinstance(default_for_key, int) else 0
                else: target_value = int(float(value_from_file or 0))
                if key_from_save_file not in allow_negative_keys_load: target_value = max(0, target_value)
                if key_from_save_file == "storage_duration": target_value = max(1, target_value)
            elif key_from_save_file in float_keys_load:
                if isinstance(value_from_file, str) and not value_from_file.strip(): target_value = default_for_key if isinstance(default_for_key, float) else 0.0
                else: target_value = float(value_from_file or 0.0)
                if key_from_save_file not in allow_negative_keys_load: target_value = max(0.0, target_value)
            elif key_from_save_file in bool_keys_load:
                if isinstance(value_from_file, str): target_value = value_from_file.lower() in ["true", "yes", "1", "on", "t"]
                else: target_value = bool(value_from_file)
            elif key_from_save_file in list_keys_load:
                target_value = value_from_file if isinstance(value_from_file, list) else (default_for_key if isinstance(default_for_key, list) else [])
            elif key_from_save_file in string_keys_load:
                target_value = str(value_from_file) if value_from_file is not None else (default_for_key if default_for_key is not None else "")
            
            st.session_state[key_from_save_file] = target_value
        except (ValueError, TypeError) as e_load_val:
            print(f"Error loading key '{key_from_save_file}' with value '{value_from_file}'. Type: {type(value_from_file)}. Error: {e_load_val}. Using default.")
            st.session_state[key_from_save_file] = default_for_key
    
    st.session_state.deposit_amount = st.session_state.get("tab3_deposit_amount", defaults_for_loading["deposit_amount"])
    st.session_state.adjustment_amount = st.session_state.get("tab3_adjustment_amount", defaults_for_loading["adjustment_amount"])
    st.session_state.departure_ladder_surcharge_manual = st.session_state.get("tab3_departure_ladder_surcharge_manual", defaults_for_loading["departure_ladder_surcharge_manual"])
    st.session_state.arrival_ladder_surcharge_manual = st.session_state.get("tab3_arrival_ladder_surcharge_manual", defaults_for_loading["arrival_ladder_surcharge_manual"])
    for i in range(5):
        st.session_state[f"date_opt_{i}_widget"] = st.session_state.get(f"tab3_date_opt_{i}_widget", defaults_for_loading[f"date_opt_{i}_widget"])

    if "base_move_type" in st.session_state:
        st.session_state.base_move_type_widget_tab1 = st.session_state.base_move_type
        st.session_state.base_move_type_widget_tab3 = st.session_state.base_move_type
    
    if "uploaded_image_paths" not in st.session_state or not isinstance(st.session_state.uploaded_image_paths, list):
        st.session_state.uploaded_image_paths = []

    if callable(update_basket_callback):
        update_basket_callback() 
    return True
