# callbacks.py
import streamlit as st
import traceback

try:
    import data
    import calculations
    from state_manager import MOVE_TYPE_OPTIONS
except ImportError as ie:
    st.warning(f"콜백 모듈: 필수 모듈(data, calculations, state_manager.MOVE_TYPE_OPTIONS) 로딩 실패 - {ie}. 기능이 제한될 수 있습니다.")
    if 'MOVE_TYPE_OPTIONS' not in globals(): MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
    if 'calculations' not in globals():
        class DummyCalculations:
            def calculate_total_volume_weight(self, s, m): return 0.0, 0.0
            def recommend_vehicle(self, v, w, m): return None, 0.0
        calculations = DummyCalculations()
    if 'data' not in globals(): data = None
except Exception as e:
    st.error(f"Callbacks: 모듈 로딩 중 예외 발생 - {e}")
    if 'MOVE_TYPE_OPTIONS' not in globals(): MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
    if 'calculations' not in globals():
        class DummyCalculationsOnError:
            def calculate_total_volume_weight(self, s, m): return 0.0, 0.0
            def recommend_vehicle(self, v, w, m): return None, 0.0
        calculations = DummyCalculationsOnError()
    if 'data' not in globals(): data = None


def update_basket_quantities():
    vehicle_choice_method = st.session_state.get('vehicle_select_radio', "자동 추천 차량 사용")
    current_move_type = st.session_state.get('base_move_type', MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠")

    available_trucks_for_type = []
    if hasattr(data, 'vehicle_prices') and data and isinstance(data.vehicle_prices, dict) and current_move_type in data.vehicle_prices:
        available_trucks_for_type = list(data.vehicle_prices[current_move_type].keys())

    _determined_vehicle = None
    if vehicle_choice_method == "자동 추천 차량 사용":
        recommended_auto = st.session_state.get('recommended_vehicle_auto')
        if recommended_auto and "초과" not in recommended_auto and recommended_auto in available_trucks_for_type:
            _determined_vehicle = recommended_auto
    else:
        manual_choice = st.session_state.get('manual_vehicle_select_value')
        if manual_choice and manual_choice in available_trucks_for_type:
            _determined_vehicle = manual_choice

    prev_final_vehicle = st.session_state.get("prev_final_selected_vehicle")
    st.session_state.final_selected_vehicle = _determined_vehicle

    vehicle_has_actually_changed = (prev_final_vehicle != st.session_state.final_selected_vehicle)

    if vehicle_has_actually_changed:
        vehicle_for_baskets = st.session_state.final_selected_vehicle
        basket_section_name = "포장 자재 📦"

        item_defs_for_move_type = {}
        if hasattr(data, 'item_definitions') and data and isinstance(data.item_definitions, dict) and current_move_type in data.item_definitions:
            item_defs_for_move_type = data.item_definitions[current_move_type]

        defined_basket_items_in_section = []
        if isinstance(item_defs_for_move_type, dict):
            defined_basket_items_in_section = item_defs_for_move_type.get(basket_section_name, [])

        if not hasattr(data, 'default_basket_quantities') or not data:
            for item_name_in_def in defined_basket_items_in_section:
                st.session_state[f"qty_{current_move_type}_{basket_section_name}_{item_name_in_def}"] = 0

        if vehicle_for_baskets and hasattr(data, 'default_basket_quantities') and isinstance(data.default_basket_quantities,dict) and vehicle_for_baskets in data.default_basket_quantities:
            basket_vehicle_defaults = data.default_basket_quantities[vehicle_for_baskets]
            for defined_item_name in defined_basket_items_in_section:
                default_qty = 0
                if defined_item_name in basket_vehicle_defaults:
                    default_qty = basket_vehicle_defaults[defined_item_name]
                elif defined_item_name == "중박스" and "중자바구니" in basket_vehicle_defaults:
                    default_qty = basket_vehicle_defaults["중자바구니"]
                item_ss_key = f"qty_{current_move_type}_{basket_section_name}_{defined_item_name}"
                st.session_state[item_ss_key] = default_qty
        else:
            for item_name_in_def in defined_basket_items_in_section:
                key_to_zero_no_vehicle_data = f"qty_{current_move_type}_{basket_section_name}_{item_name_in_def}"
                st.session_state[key_to_zero_no_vehicle_data] = 0

    st.session_state.prev_final_selected_vehicle = st.session_state.final_selected_vehicle

def handle_item_update():
    try:
        current_move_type = st.session_state.get('base_move_type', MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠")
        if not current_move_type or not calculations or not data:
            st.session_state.update({"total_volume": 0.0, "total_weight": 0.0, "recommended_vehicle_auto": None, "remaining_space": 0.0})
            if callable(update_basket_quantities):
                update_basket_quantities()
            return

        vol, wt = calculations.calculate_total_volume_weight(st.session_state.to_dict(), current_move_type)
        st.session_state.total_volume = vol
        st.session_state.total_weight = wt

        rec_vehicle, rem_space = calculations.recommend_vehicle(vol, wt, current_move_type)
        st.session_state.recommended_vehicle_auto = rec_vehicle
        st.session_state.remaining_space = rem_space
    except Exception as e:
        st.error(f"실시간 업데이트 중 계산 오류: {e}")
        traceback.print_exc()
        st.session_state.update({"total_volume": 0.0, "total_weight": 0.0, "recommended_vehicle_auto": None, "remaining_space": 0.0})

    if callable(update_basket_quantities):
        update_basket_quantities()

def sync_move_type(widget_key):
    if not MOVE_TYPE_OPTIONS:
        return

    if widget_key in st.session_state:
        new_move_type = st.session_state[widget_key]
        if new_move_type not in MOVE_TYPE_OPTIONS:
            return

        previous_move_type = st.session_state.get('base_move_type')
        if previous_move_type != new_move_type:
            st.session_state.base_move_type = new_move_type
            other_widget_key = 'base_move_type_widget_tab3' if widget_key == 'base_move_type_widget_tab1' else 'base_move_type_widget_tab1'
            if other_widget_key in st.session_state:
                st.session_state[other_widget_key] = new_move_type
            if callable(handle_item_update):
                handle_item_update()

def update_selected_gdrive_id():
    selected_name = st.session_state.get("gdrive_selected_filename_widget_tab1")
    if selected_name and 'gdrive_file_options_map' in st.session_state:
        file_id = st.session_state.gdrive_file_options_map.get(selected_name)
        if file_id:
            st.session_state.gdrive_selected_file_id = file_id
            st.session_state.gdrive_selected_filename = selected_name