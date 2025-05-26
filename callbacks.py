# callbacks.py (수정 후)
import streamlit as st
import traceback

try:
    import data
    import calculations
    from state_manager import MOVE_TYPE_OPTIONS # state_manager에서 직접 가져오도록 수정
except ImportError as ie:
    st.warning(f"콜백 모듈: 필수 모듈(data, calculations, state_manager.MOVE_TYPE_OPTIONS) 로딩 실패 - {ie}. 기능이 제한될 수 있습니다.")
    if 'MOVE_TYPE_OPTIONS' not in globals(): MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
    if 'calculations' not in globals():
        class DummyCalculations:
            def calculate_total_volume_weight(self, s, m): return 0.0, 0.0
            def recommend_vehicle(self, v, w, m): return None, 0.0, 0, 0 # 반환값 4개로 수정
        calculations = DummyCalculations()
    if 'data' not in globals(): data = None
except Exception as e:
    st.error(f"Callbacks: 모듈 로딩 중 예외 발생 - {e}")
    if 'MOVE_TYPE_OPTIONS' not in globals(): MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
    if 'calculations' not in globals():
        class DummyCalculationsOnError:
            def calculate_total_volume_weight(self, s, m): return 0.0, 0.0
            def recommend_vehicle(self, v, w, m): return None, 0.0, 0, 0 # 반환값 4개로 수정
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
        elif vehicle_for_baskets and hasattr(data, 'default_basket_quantities') and isinstance(data.default_basket_quantities,dict) and vehicle_for_baskets in data.default_basket_quantities: # elif로 변경 및 data None 체크 추가
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
        # data 모듈 존재 여부도 확인
        if not current_move_type or not calculations or not data:
            st.session_state.update({
                "total_volume": 0.0, "total_weight": 0.0,
                "recommended_vehicle_auto": None, "remaining_space": 0.0,
                "recommended_base_price_auto": 0.0, # 추가된 세션 상태키
                "recommended_base_men_auto":0,       # 추가된 세션 상태키
                "recommended_base_women_auto":0      # 추가된 세션 상태키
            })
            if callable(update_basket_quantities):
                update_basket_quantities()
            return

        vol, wt = calculations.calculate_total_volume_weight(st.session_state.to_dict(), current_move_type)
        st.session_state.total_volume = vol
        st.session_state.total_weight = wt

        # --- 수정된 부분: recommend_vehicle 반환값 4개 모두 받기 ---
        rec_vehicle_name, rec_base_price, rec_base_men, rec_base_women = calculations.recommend_vehicle(vol, wt, current_move_type)
        st.session_state.recommended_vehicle_auto = rec_vehicle_name
        st.session_state.recommended_base_price_auto = rec_base_price
        st.session_state.recommended_base_men_auto = rec_base_men
        st.session_state.recommended_base_women_auto = rec_base_women
        # --- 수정 끝 ---

        # --- 추가된 부분: remaining_space (여유 공간 %) 계산 ---
        remaining_space_percentage = 0.0
        if rec_vehicle_name and "초과" not in rec_vehicle_name and \
           hasattr(data, 'vehicle_specs') and data.vehicle_specs and \
           rec_vehicle_name in data.vehicle_specs:

            truck_spec = data.vehicle_specs[rec_vehicle_name]
            truck_capacity_volume = truck_spec.get('capacity', 0.0)
            # data.py에 LOADING_EFFICIENCY가 정의되어 있다고 가정
            loading_efficiency = getattr(data, 'LOADING_EFFICIENCY', 1.0) # 기본값 1.0
            usable_truck_capacity_volume = truck_capacity_volume * loading_efficiency

            if usable_truck_capacity_volume > 0:
                if vol <= usable_truck_capacity_volume:
                    remaining_absolute_volume = usable_truck_capacity_volume - vol
                    remaining_space_percentage = (remaining_absolute_volume / usable_truck_capacity_volume) * 100
                # else: 용량 초과 시 remaining_space_percentage는 0.0 유지
        # elif rec_vehicle_name and "초과" in rec_vehicle_name: # 이미 위에서 처리됨
        #     remaining_space_percentage = 0.0
        st.session_state.remaining_space = remaining_space_percentage
        # --- 추가 끝 ---

    except Exception as e:
        st.error(f"실시간 업데이트 중 계산 오류: {e}")
        traceback.print_exc()
        st.session_state.update({
            "total_volume": 0.0, "total_weight": 0.0,
            "recommended_vehicle_auto": None, "remaining_space": 0.0,
            "recommended_base_price_auto": 0.0,
            "recommended_base_men_auto":0,
            "recommended_base_women_auto":0
        })

    if callable(update_basket_quantities):
        update_basket_quantities()

def sync_move_type(widget_key):
    if not MOVE_TYPE_OPTIONS:
        return

    if widget_key in st.session_state:
        new_move_type = st.session_state[widget_key]
        if new_move_type not in MOVE_TYPE_OPTIONS: # 유효한 MOVE_TYPE_OPTIONS 값인지 확인
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


def find_item_section_for_default_set(move_type, item_name_to_find):
    if not hasattr(data, 'item_definitions') or not data.item_definitions:
        return None
    item_defs_for_type = data.item_definitions.get(move_type, {})
    if isinstance(item_defs_for_type, dict):
        for section, item_list in item_defs_for_type.items():
            if isinstance(item_list, list) and item_name_to_find in item_list:
                return section
    return None

def apply_default_home_set():
    current_move_type = st.session_state.get("base_move_type")
    if current_move_type != "가정 이사 🏠":
        st.toast("ℹ️ '기본 가정 세트'는 '가정 이사 🏠' 유형 선택 시에만 적용할 수 있습니다.", icon="ℹ️")
        return

    # data.py에 정의된 실제 품목명과 일치해야 함
    default_items_config = {
        "4도어 냉장고": 1, "TV(75인치)": 1, "김치냉장고(스탠드형)": 1,
        "컴퓨터&모니터": 1, "책상&의자": 1, "옷장": 3,
        "옷행거": 4, "세탁기 및 건조기": 1, "에어컨": 1, "더블침대": 1,
    }

    items_applied_count = 0
    items_not_found_details = []

    for actual_item_name, quantity in default_items_config.items():
        # data.items에 품목이 정의되어 있는지 확인
        if not (hasattr(data, 'items') and data.items is not None and actual_item_name in data.items):
            items_not_found_details.append(f"'{actual_item_name}' (data.items에 없음)")
            continue

        section = find_item_section_for_default_set(current_move_type, actual_item_name)
        if section:
            item_key = f"qty_{current_move_type}_{section}_{actual_item_name}"
            st.session_state[item_key] = quantity
            items_applied_count += 1
        else:
            items_not_found_details.append(f"'{actual_item_name}' (섹션 못 찾음 또는 data.items 내 품목 정의 오류)")

    if items_applied_count > 0:
        st.toast(f"✅ 기본 가정 세트 ({items_applied_count}개 품목) 적용 완료!", icon="👍")
        if callable(handle_item_update):
            handle_item_update()
        else:
            st.warning("품목 업데이트 콜백(handle_item_update)을 찾을 수 없어 물량 정보가 갱신되지 않았을 수 있습니다.")
    else:
        st.error("⚠️ 기본 가정 세트 적용에 실패했거나, 설정할 품목이 없습니다.", icon="❗")

    if items_not_found_details:
        st.warning(f"다음 품목은 data.py 정의에서 찾을 수 없거나 섹션 매칭에 실패하여 기본 세트에 포함되지 못했습니다: {', '.join(items_not_found_details)}", icon="⚠️")
