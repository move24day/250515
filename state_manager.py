# state_manager.py

import streamlit as st
from datetime import datetime, date
import pytz

try:
    import data
    MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions else ["가정 이사 🏠", "사무실 이사 🏢"]
except ImportError:
    st.error("State Manager: 필수 모듈 data.py 로딩 실패. 앱이 정상적으로 작동하지 않을 수 있습니다.")
    MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
    data = None

STATE_KEYS_TO_SAVE = [
    "base_move_type", "is_storage_move", "storage_type", "apply_long_distance", "long_distance_selector",
    "customer_name", "customer_phone", "customer_email",
    "moving_date", "arrival_date", "storage_duration", "storage_use_electricity",
    "contract_date",
    "from_address_full", "from_floor", "from_method",
    "to_address_full", "to_floor", "to_method",
    "has_via_point", "via_point_address", "via_point_floor", "via_point_method", "via_point_surcharge",
    "special_notes",
    "vehicle_select_radio", "manual_vehicle_select_value", "final_selected_vehicle",
    "add_men", "add_women", "remove_base_housewife", "remove_base_man",
    "sky_hours_from", "sky_hours_final",
    "dispatched_1t", "dispatched_2_5t","dispatched_3_5t", "dispatched_5t",
    "has_waste_check", "waste_tons_input",
    "manual_ladder_from_check", "manual_ladder_to_check",
    "issue_tax_invoice", "card_payment",
    "move_time_option", "afternoon_move_details",
    "uploaded_images",
    "tab3_deposit_amount", "tab3_adjustment_amount",
    "tab3_departure_ladder_surcharge_manual",
    "tab3_arrival_ladder_surcharge_manual",
    "tab3_date_opt_0_widget", "tab3_date_opt_1_widget", "tab3_date_opt_2_widget",
    "tab3_date_opt_3_widget", "tab3_date_opt_4_widget",
    "prev_final_selected_vehicle"
]

def initialize_session_state(update_basket_callback=None):
    try:
        KST_init = pytz.timezone("Asia/Seoul")
    except pytz.UnknownTimeZoneError:
        KST_init = pytz.utc
    today_kst = datetime.now(KST_init).date()
    default_storage_type = data.DEFAULT_STORAGE_TYPE if data and hasattr(data, "DEFAULT_STORAGE_TYPE") else "컨테이너 보관 📦"
    default_long_dist_selector = data.long_distance_options[0] if data and hasattr(data, "long_distance_options") and data.long_distance_options else "선택 안 함"
    default_from_method = data.METHOD_OPTIONS[0] if data and hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "계단 🚶"
    default_to_method = default_from_method
    default_via_method = default_from_method
    default_manual_ladder_surcharge = getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0) if data else 0

    defaults = {
        "base_move_type": MOVE_TYPE_OPTIONS[0],
        "is_storage_move": False, "storage_type": default_storage_type,
        "apply_long_distance": False, "long_distance_selector": default_long_dist_selector,
        "customer_name": "", "customer_phone": "", "customer_email": "",
        "moving_date": today_kst, "arrival_date": today_kst, "contract_date": today_kst,
        "storage_duration": 1, "storage_use_electricity": False,
        "from_address_full": "", "from_floor": "", "from_method": default_from_method,
        "to_address_full": "", "to_floor": "", "to_method": default_to_method,
        "has_via_point": False, "via_point_address": "", "via_point_floor": "", "via_point_method": default_via_method, "via_point_surcharge": 0,
        "special_notes": "",
        "vehicle_select_radio": "자동 추천 차량 사용", "manual_vehicle_select_value": None, "final_selected_vehicle": None,
        "recommended_vehicle_auto": None, "recommended_base_price_auto": 0.0,
        "total_volume": 0.0, "total_weight": 0.0,
        "add_men": 0, "add_women": 0, "remove_base_housewife": False, "remove_base_man": False,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "dispatched_1t":0, "dispatched_2_5t":0, "dispatched_3_5t":0, "dispatched_5t":0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False, "date_opt_3_widget": False, "date_opt_4_widget": False,
        "manual_ladder_from_check": False, "departure_ladder_surcharge_manual": default_manual_ladder_surcharge,
        "manual_ladder_to_check": False, "arrival_ladder_surcharge_manual": default_manual_ladder_surcharge,
        "deposit_amount": 0, "adjustment_amount": 0,
        "issue_tax_invoice": False, "card_payment": False,
        "pdf_ready": False, "pdf_bytes": None, "selected_items": {},
        "move_time_option": "오전", "afternoon_move_details": "",
        "customer_final_pdf_data": None, "uploaded_images": [],
        "tab3_deposit_amount": 0, "tab3_adjustment_amount": 0,
        "tab3_departure_ladder_surcharge_manual": default_manual_ladder_surcharge,
        "tab3_arrival_ladder_surcharge_manual": default_manual_ladder_surcharge,
        "tab3_date_opt_0_widget": False, "tab3_date_opt_1_widget": False, "tab3_date_opt_2_widget": False, "tab3_date_opt_3_widget": False, "tab3_date_opt_4_widget": False,
        "prev_final_selected_vehicle": None, "_app_initialized": True
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    item_keys_to_save_dyn = []
    if data and hasattr(data, "item_definitions") and data.item_definitions:
        for move_type_key, sections in data.item_definitions.items():
            if isinstance(sections, dict):
                for section_key, item_list in sections.items():
                    if section_key == getattr(data, "WASTE_SECTION_NAME", "폐기 처리 품목 🗑️"): continue
                    if isinstance(item_list, list):
                        for item_name in item_list:
                            if hasattr(data, "items") and data.items is not None and item_name in data.items:
                                dynamic_key = f"qty_{move_type_key}_{section_key}_{item_name}"
                                item_keys_to_save_dyn.append(dynamic_key)
                                if dynamic_key not in st.session_state: st.session_state[dynamic_key] = 0
    
    global STATE_KEYS_TO_SAVE
    for item_key_dyn in item_keys_to_save_dyn:
        if item_key_dyn not in STATE_KEYS_TO_SAVE: STATE_KEYS_TO_SAVE.append(item_key_dyn)

    if "prev_final_selected_vehicle" not in st.session_state:
        st.session_state["prev_final_selected_vehicle"] = st.session_state.get("final_selected_vehicle")
    if callable(update_basket_callback): update_basket_callback()


def prepare_state_for_save(current_state_dict):
    state_to_save = {}
    try: KST_ps = pytz.timezone("Asia/Seoul")
    except pytz.UnknownTimeZoneError: KST_ps = pytz.utc

    current_state_dict["tab3_deposit_amount"] = current_state_dict.get("deposit_amount", 0)
    current_state_dict["tab3_adjustment_amount"] = current_state_dict.get("adjustment_amount", 0)
    current_state_dict["tab3_departure_ladder_surcharge_manual"] = current_state_dict.get("departure_ladder_surcharge_manual", 0)
    current_state_dict["tab3_arrival_ladder_surcharge_manual"] = current_state_dict.get("arrival_ladder_surcharge_manual", 0)
    for i in range(5):
        current_state_dict[f"tab3_date_opt_{i}_widget"] = current_state_dict.get(f"date_opt_{i}_widget", False)

    keys_to_exclude = {
        "_app_initialized", "base_move_type_widget_tab1", "base_move_type_widget_tab3",
        "gdrive_selected_filename_widget_tab1", "pdf_data_customer", "final_excel_data",
        "customer_final_pdf_data", "internal_form_image_data_tab3", "internal_excel_data_for_download_tab3",
        "customer_pdf_image_data_tab3", "gdrive_search_results", "gdrive_file_options_map",
        "recommended_vehicle_auto", "recommended_base_price_auto",
        "deposit_amount", "adjustment_amount", "departure_ladder_surcharge_manual", "arrival_ladder_surcharge_manual",
        "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget", "date_opt_3_widget", "date_opt_4_widget",
    }
    actual_keys_to_save = [key for key in STATE_KEYS_TO_SAVE if key not in keys_to_exclude]
    
    # 동적으로 추가된 품목 수량 키들도 저장 대상에 포함
    all_qty_keys = [k for k in current_state_dict if k.startswith('qty_')]
    for k in all_qty_keys:
        if k not in actual_keys_to_save:
            actual_keys_to_save.append(k)

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
    
    if "uploaded_images" not in state_to_save or not isinstance(state_to_save.get("uploaded_images"), list):
        state_to_save["uploaded_images"] = current_state_dict.get("uploaded_images", [])
    
    state_to_save["app_version"] = "1.2.0" # 버전 정보
    state_to_save["saved_at_kst"] = datetime.now(KST_ps).isoformat()
    return state_to_save

# --- 이 부분이 누락된 함수입니다 ---
def load_state_from_data(loaded_data_dict, update_basket_callback=None):
    if not isinstance(loaded_data_dict, dict):
        st.error("로드할 데이터 형식이 올바르지 않습니다.")
        return False

    # 모든 키에 대한 기본값을 다시 생성하여, 로드된 데이터에 없는 키를 초기화
    initialize_session_state(update_basket_callback)
    
    for key, value in loaded_data_dict.items():
        # 날짜 문자열을 date 객체로 변환
        if key in ["moving_date", "arrival_date", "contract_date"] and isinstance(value, str):
            try:
                st.session_state[key] = date.fromisoformat(value)
            except (ValueError, TypeError):
                # 파싱 실패 시 기본값(오늘 날짜)이 이미 설정되어 있으므로 그대로 둠
                pass
        # 호환성을 위해 옛날 주소 키 처리
        elif key == "from_location" and "from_address_full" not in loaded_data_dict:
            st.session_state["from_address_full"] = value
        elif key == "to_location" and "to_address_full" not in loaded_data_dict:
            st.session_state["to_address_full"] = value
        # 호환성을 위해 옛날 이미지 경로 키 처리
        elif key == "uploaded_image_paths" and "uploaded_images" not in loaded_data_dict:
            # 예전 경로 데이터는 이제 사용할 수 없으므로 비움
            st.session_state["uploaded_images"] = []
        elif key in st.session_state:
            st.session_state[key] = value

    # UI 입력 필드와 tab3_ 저장용 필드 동기화 (로드 후)
    st.session_state.deposit_amount = st.session_state.get("tab3_deposit_amount", 0)
    st.session_state.adjustment_amount = st.session_state.get("tab3_adjustment_amount", 0)
    st.session_state.departure_ladder_surcharge_manual = st.session_state.get("tab3_departure_ladder_surcharge_manual", 0)
    st.session_state.arrival_ladder_surcharge_manual = st.session_state.get("tab3_arrival_ladder_surcharge_manual", 0)
    for i in range(5):
        st.session_state[f"date_opt_{i}_widget"] = st.session_state.get(f"tab3_date_opt_{i}_widget", False)

    # 이사 유형 동기화
    if "base_move_type" in st.session_state:
        st.session_state.base_move_type_widget_tab1 = st.session_state.base_move_type
        st.session_state.base_move_type_widget_tab3 = st.session_state.base_move_type

    # 콜백 함수 호출
    if callable(update_basket_callback):
        update_basket_callback()
        
    return True
