# state_manager.py (수정 후)

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
    "manual_ladder_from_check",
    "manual_ladder_to_check",
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
    # ... (rest of the state_manager.py file is unchanged and can be copied from the provided context) ...
