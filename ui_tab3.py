# ui_tab3.py
import streamlit as st
import pandas as pd
import io
import pytz
from datetime import datetime, date, timedelta
import traceback
import re
import math 

try:
    import data
    import utils
    import calculations
    import pdf_generator
    import excel_filler
    import email_utils
    import callbacks
    from state_manager import MOVE_TYPE_OPTIONS # state_manager에서 가져옴
    import image_generator
except ImportError as e:
    st.error(f"UI Tab 3: 필수 모듈 로딩 실패 - {e}")
    if hasattr(e, "name"):
        if e.name == "email_utils": st.warning("email_utils.py 로드 실패. 이메일 발송 비활성화.")
        elif e.name == "pdf_generator": st.warning("pdf_generator.py 로드 실패. PDF 관련 기능 제한 가능.")
        elif e.name == "image_generator": st.error("image_generator.py 로드 실패! 회사 양식 이미지 생성 비활성화.")
    if "MOVE_TYPE_OPTIONS" not in globals(): # globals()로 전역변수 확인
        MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"] 
    if not all(module_name in globals() for module_name in ["data", "utils", "calculations", "callbacks", "state_manager", "image_generator", "pdf_generator"]):
        st.error("UI Tab 3: 핵심 데이터/유틸리티 모듈 로딩 실패.")
except Exception as e:
    st.error(f"UI Tab 3: 모듈 로딩 중 오류 - {e}")
    traceback.print_exc()
    if "MOVE_TYPE_OPTIONS" not in globals():
        MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
    st.stop()

def get_method_full_name(method_key):
    method_str = str(st.session_state.get(method_key, '')).strip() 
    method_parts = method_str.split(" ") 
    return method_parts[0] if method_parts else "정보 없음"

def get_validation_warnings(state):
    warnings = []
    moving_date_input = state.get('moving_date')
    if not isinstance(moving_date_input, date):
        if moving_date_input is None:
            warnings.append("이사 예정일이 설정되지 않았습니다. 날짜를 선택해주세요.")
        else:
            warnings.append(f"이사 예정일의 형식이 올바르지 않습니다: {moving_date_input}. 날짜를 다시 선택해주세요.")
    
    if not str(state.get('from_address_full', '')).strip(): 
        warnings.append("출발지 주소 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")
    if not str(state.get('from_floor', '')).strip():
        warnings.append("출발지 층수 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")
    
    if not str(state.get('to_address_full', '')).strip(): 
        warnings.append("도착지 주소 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")
    if not str(state.get('to_floor', '')).strip():
        warnings.append("도착지 층수 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")

    if not state.get('final_selected_vehicle'):
        warnings.append("견적 계산용 차량 종류가 선택되지 않았습니다. '차량 선택' 섹션에서 차량을 선택해주세요.")
    
    if state.get('final_selected_vehicle'):
        total_dispatched_trucks = sum(
            st.session_state.get(key, 0) or 0
            for key in ['dispatched_1t', 'dispatched_2_5t', 'dispatched_3_5t', 'dispatched_5t']
        )
        if total_dispatched_trucks == 0:
            warnings.append("실제 투입 차량 대수가 입력되지 않았습니다. '실제 투입 차량' 섹션에서 각 톤수별 차량 대수를 입력해주세요.")
    return warnings

def format_cost_item_for_detailed_list(name, cost, note, storage_details_text_param=""):
    cost_val = int(float(cost or 0))
    
    is_discount_item = "할인" in name or "제외" in name or cost_val < 0 
    if name != "보관료" and cost_val == 0 and not is_discount_item: 
        return None

    formatted_name_detail = name
    note_display_detail = f" ({note})" if note and name not in ["보관료", "기본 운임", "부가세 (10%)", "카드결제 (VAT 및 수수료 포함)", "장거리 운송료"] else ""

    if name == "기본 운임": formatted_name_detail = "이사비"; note_display_detail = f" ({note})" if note else ""
    elif "사다리차" in name and "추가" not in name and "할인" not in name : formatted_name_detail = name 
    elif "스카이 장비" in name: formatted_name_detail = name 
    elif name == "보관료": # storage_details_text_param은 여기서 사용됨
        formatted_name_detail = f"보관료({storage_details_text_param})" if storage_details_text_param else "보관료"
        note_display_detail = "" 
    elif "조정 금액" in name: formatted_name_detail = name 
    elif name == "기본 여성 인원 중 1명 제외 할인": formatted_name_detail = "여성인원(1명)제외"
    elif name == "기본 남성 인원 중 1명 제외 할인": formatted_name_detail = "남성인원(1명)제외"
    elif name == "추가 인력": formatted_name_detail = "인원추가"
    elif name == "날짜 할증": formatted_name_detail = "날짜할증"
    elif name == "장거리 운송료": formatted_name_detail = "장거리"; note_display_detail = f" ({note})" if note else ""
    elif name == "폐기물 처리": formatted_name_detail = "폐기물"
    elif name == "경유지 추가요금": formatted_name_detail = "경유지추가"
    elif name == "부가세 (10%)": formatted_name_detail = "부가세"
    elif name == "카드결제 (VAT 및 수수료 포함)": formatted_name_detail = "카드결제처리"
    else: 
        note_display_detail = f" ({note})" if note else ""
    
    return f"  - {formatted_name_detail}: {cost_val:,.0f}원{note_display_detail}"

def render_tab3():
    st.header("계산 및 옵션")
    update_basket_quantities_callback = getattr(callbacks, "update_basket_quantities", None)
    sync_move_type_callback = getattr(callbacks, "sync_move_type", None)
    handle_item_update_callback = getattr(callbacks, "handle_item_update", None)

    if not callable(update_basket_quantities_callback) or not callable(sync_move_type_callback):
        st.error("UI Tab 3: 콜백 함수 로드 실패.")

    st.subheader("이사 유형")
    current_move_type_from_state_tab3 = st.session_state.get("base_move_type", MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠")
    current_index_tab3 = 0
    
    if MOVE_TYPE_OPTIONS:
        try:
            current_index_tab3 = MOVE_TYPE_OPTIONS.index(current_move_type_from_state_tab3)
        except ValueError: 
            current_index_tab3 = 0 
            st.session_state.base_move_type = MOVE_TYPE_OPTIONS[0] 
            if callable(handle_item_update_callback):
                 handle_item_update_callback()
    else:
        st.error("이사 유형 옵션을 불러올 수 없습니다."); return

    st.radio(
        "기본 이사 유형:",
        options=MOVE_TYPE_OPTIONS, 
        index=current_index_tab3, 
        horizontal=True,
        key="base_move_type_widget_tab3", 
        on_change=sync_move_type_callback, 
        args=("base_move_type_widget_tab3",)
    )
    st.divider()

    with st.container(border=True):
        st.subheader("차량 선택 (견적 계산용)")
        col_v1_widget, col_v2_widget = st.columns([1, 2])
        with col_v1_widget:
            st.radio("차량 선택 방식:", ["자동 추천 차량 사용", "수동으로 차량 선택"], key="vehicle_select_radio", on_change=update_basket_quantities_callback)
        with col_v2_widget:
            current_move_type_widget_tab3_radio = st.session_state.get('base_move_type')
            vehicle_prices_options_widget, available_trucks_widget = {}, []
            if current_move_type_widget_tab3_radio and hasattr(data, 'vehicle_prices') and isinstance(data.vehicle_prices, dict):
                vehicle_prices_options_widget = data.vehicle_prices.get(current_move_type_widget_tab3_radio, {})
            if vehicle_prices_options_widget and hasattr(data, 'vehicle_specs') and isinstance(data.vehicle_specs, dict):
                available_trucks_widget = sorted(
                    [truck for truck in vehicle_prices_options_widget.keys() if truck in data.vehicle_specs],
                    key=lambda x: data.vehicle_specs.get(x, {}).get("capacity", 0)
                )

            use_auto_widget = st.session_state.get('vehicle_select_radio') == "자동 추천 차량 사용"
            recommended_vehicle_auto_from_state = st.session_state.get('recommended_vehicle_auto')
            final_vehicle_from_state = st.session_state.get('final_selected_vehicle')
            current_total_volume = st.session_state.get("total_volume", 0.0)
            current_total_weight = st.session_state.get("total_weight", 0.0)

            if use_auto_widget:
                if final_vehicle_from_state and final_vehicle_from_state in available_trucks_widget:
                    st.success(f"자동 선택됨: {final_vehicle_from_state}")
                    spec = data.vehicle_specs.get(final_vehicle_from_state) if hasattr(data, "vehicle_specs") else None
                    if spec:
                        st.caption(f"선택차량 최대 용량: {spec.get('capacity', 'N/A')}m³, {spec.get('weight_capacity', 'N/A'):,}kg")
                        st.caption(f"현재 이사짐 예상: {current_total_volume:.2f}m³, {current_total_weight:.2f}kg")
                else:
                    error_msg = "자동 추천 불가: "
                    if recommended_vehicle_auto_from_state and "초과" in recommended_vehicle_auto_from_state:
                        error_msg += f"물량 초과({recommended_vehicle_auto_from_state}). 수동 선택 필요."
                    elif recommended_vehicle_auto_from_state and recommended_vehicle_auto_from_state not in available_trucks_widget :
                        error_msg += f"추천 차량({recommended_vehicle_auto_from_state})은 현재 이사 유형에 없음. 수동 선택 필요."
                    elif current_total_volume > 0 or current_total_weight > 0 :
                        error_msg += "적합 차량 없음. 수동 선택 필요."
                    else:
                        error_msg += "물품 미선택 또는 정보 부족."
                    st.error(error_msg)
                    if not available_trucks_widget:
                        st.error("현재 이사 유형에 선택 가능한 차량 정보가 없습니다.")
                    else:
                        current_manual_selection_widget = st.session_state.get("manual_vehicle_select_value")
                        try:
                            current_index_widget = available_trucks_widget.index(current_manual_selection_widget) if current_manual_selection_widget in available_trucks_widget else 0
                        except ValueError:
                             current_index_widget = 0
                        if not current_manual_selection_widget and available_trucks_widget:
                             st.session_state.manual_vehicle_select_value = available_trucks_widget[0]
                        st.selectbox("수동으로 차량 선택:", available_trucks_widget, index=current_index_widget, key="manual_vehicle_select_value", on_change=update_basket_quantities_callback)
                        if final_vehicle_from_state and final_vehicle_from_state in available_trucks_widget:
                             st.info(f"수동 선택됨: {final_vehicle_from_state}")
            else: 
                if not available_trucks_widget:
                    st.error("현재 이사 유형에 선택 가능한 차량 정보가 없습니다.")
                else:
                    current_manual_selection_widget = st.session_state.get("manual_vehicle_select_value")
                    try:
                        current_index_widget = available_trucks_widget.index(current_manual_selection_widget) if current_manual_selection_widget in available_trucks_widget else 0
                    except ValueError:
                        current_index_widget = 0
                    if not current_manual_selection_widget and available_trucks_widget: 
                        st.session_state.manual_vehicle_select_value = available_trucks_widget[0]
                    st.selectbox("차량 직접 선택:", available_trucks_widget, index=current_index_widget, key="manual_vehicle_select_value", on_change=update_basket_quantities_callback)
                    if final_vehicle_from_state and final_vehicle_from_state in available_trucks_widget:
                        st.info(f"수동 선택됨: {final_vehicle_from_state}")
                        spec_manual = data.vehicle_specs.get(final_vehicle_from_state) if hasattr(data, "vehicle_specs") else None
                        if spec_manual:
                            st.caption(f"선택차량 최대 용량: {spec_manual.get('capacity', 'N/A')}m³, {spec_manual.get('weight_capacity', 'N/A'):,}kg")
                            st.caption(f"현재 이사짐 예상: {current_total_volume:.2f}m³, {current_total_weight:.2f}kg")
    st.divider()

    with st.container(border=True):
        st.subheader("작업 조건 및 추가 옵션")
        from_method_no_emoji_tab3_sky = get_method_full_name("from_method")
        to_method_no_emoji_tab3_sky = get_method_full_name("to_method")
        sky_from_tab3_cond = (from_method_no_emoji_tab3_sky == "스카이")
        sky_to_tab3_cond = (to_method_no_emoji_tab3_sky == "스카이")

        if sky_from_tab3_cond or sky_to_tab3_cond:
            st.warning("스카이 작업 선택됨 - 시간 입력 필요")
            cols_sky = st.columns(2)
            if sky_from_tab3_cond: cols_sky[0].number_input("출발 스카이 시간(h)", min_value=1, step=1, key="sky_hours_from")
            if sky_to_tab3_cond: cols_sky[1].number_input("도착 스카이 시간(h)", min_value=1, step=1, key="sky_hours_final")
            st.write("")
        col_add1, col_add2 = st.columns(2)
        col_add1.number_input("추가 남성 인원", min_value=0, step=1, key="add_men")
        col_add2.number_input("추가 여성 인원", min_value=0, step=1, key="add_women")
        st.write("")
        st.subheader("실제 투입 차량 (견적서 및 내부 기록용)")
        dispatched_cols = st.columns(4)
        dispatched_cols[0].number_input("1톤", min_value=0, step=1, key="dispatched_1t")
        dispatched_cols[1].number_input("2.5톤", min_value=0, step=1, key="dispatched_2_5t")
        dispatched_cols[2].number_input("3.5톤", min_value=0, step=1, key="dispatched_3_5t")
        dispatched_cols[3].number_input("5톤", min_value=0, step=1, key="dispatched_5t")
        st.caption("실제 현장에 투입될 차량 대수를 입력합니다.")
        st.write("")

        base_personnel_cost_one = getattr(data, "ADDITIONAL_PERSON_COST", 200000) 

        current_move_type_for_option_tab3 = st.session_state.get("base_move_type") 
        final_vehicle_for_option_display_tab3 = st.session_state.get("final_selected_vehicle") 

        base_housewife_count_for_option = 0
        if current_move_type_for_option_tab3 and \
           final_vehicle_for_option_display_tab3 and \
           hasattr(data, "vehicle_prices") and \
           isinstance(data.vehicle_prices.get(current_move_type_for_option_tab3), dict) and \
           final_vehicle_for_option_display_tab3 in data.vehicle_prices[current_move_type_for_option_tab3]:
            vehicle_details = data.vehicle_prices[current_move_type_for_option_tab3][final_vehicle_for_option_display_tab3]
            base_housewife_count_for_option = vehicle_details.get("housewife", 0)
        
        if base_housewife_count_for_option > 0:
            st.checkbox(
                f"기본 여성 중 1명 제외 (할인: -{base_personnel_cost_one:,.0f}원, 현재 차량 기본 {base_housewife_count_for_option}명)", 
                key="remove_base_housewife"
            )
        else: 
            if "remove_base_housewife" in st.session_state: st.session_state.remove_base_housewife = False
        
        base_man_count_for_option = 0
        if current_move_type_for_option_tab3 and \
           final_vehicle_for_option_display_tab3 and \
           hasattr(data, "vehicle_prices") and \
           isinstance(data.vehicle_prices.get(current_move_type_for_option_tab3), dict) and \
           final_vehicle_for_option_display_tab3 in data.vehicle_prices[current_move_type_for_option_tab3]:
            vehicle_details_man = data.vehicle_prices[current_move_type_for_option_tab3][final_vehicle_for_option_display_tab3]
            base_man_count_for_option = vehicle_details_man.get("men", 0) 
        
        if base_man_count_for_option > 0:
            st.checkbox(
                f"기본 남성 중 1명 제외 (할인: -{base_personnel_cost_one:,.0f}원, 현재 차량 기본 {base_man_count_for_option}명)", 
                key="remove_base_man" 
            )
        else: 
            if "remove_base_man" in st.session_state: st.session_state.remove_base_man = False


        col_waste1, col_waste2 = st.columns([1,2])
        col_waste1.checkbox("폐기물 처리 필요", key="has_waste_check")
        if st.session_state.get("has_waste_check"):
            waste_cost_per_ton = getattr(data, "WASTE_DISPOSAL_COST_PER_TON", 0)
            waste_cost_display = waste_cost_per_ton if isinstance(waste_cost_per_ton, (int, float)) else 0
            col_waste2.number_input("폐기물 양 (톤)", min_value=0.5, max_value=10.0, step=0.5, key="waste_tons_input", format="%.1f")
            if waste_cost_display > 0: col_waste2.caption(f"1톤당 {waste_cost_display:,}원 추가 비용 발생")

        st.write("날짜 유형 선택 (중복 가능, 해당 시 할증)")
        date_surcharges_defined = hasattr(data, "special_day_prices") and isinstance(data.special_day_prices, dict)
        if not date_surcharges_defined: st.warning("data.py에 날짜 할증 정보(special_day_prices)가 없습니다.")
        
        date_option_keys_from_data = list(data.special_day_prices.keys()) if date_surcharges_defined else []
        date_options_text_for_ui = [key.split(" ")[0] for key in date_option_keys_from_data]


        cols_date_tab3 = st.columns(len(date_options_text_for_ui) if date_options_text_for_ui else 1)
        for i, option_text_display_tab3 in enumerate(date_options_text_for_ui):
            widget_key_date_opt = f"date_opt_{i}_widget" 
            surcharge = data.special_day_prices.get(date_option_keys_from_data[i], 0) if date_surcharges_defined else 0
            cols_date_tab3[i].checkbox(option_text_display_tab3, key=widget_key_date_opt, help=f"{surcharge:,}원 할증" if surcharge > 0 else "")
    st.divider()

    with st.container(border=True):
        st.subheader("수기 조정 및 계약금")
        col_adj_dep, col_adj_amount = st.columns(2)
        with col_adj_dep:
            st.number_input("계약금", min_value=0, step=10000, key="deposit_amount", format="%d")
        with col_adj_amount:
            st.number_input("추가 조정 (+/-)", step=10000, key="adjustment_amount", format="%d") 

        st.markdown("**수동 사다리 추가금/할인**") 
        col_ladder_manual1, col_ladder_manual2 = st.columns(2)
        with col_ladder_manual1:
            st.checkbox("출발지 수동 사다리 적용", key="manual_ladder_from_check") 
            st.number_input("출발지 사다리 수동 (+/-)", step=10000, key="departure_ladder_surcharge_manual", format="%d", 
                              disabled=not st.session_state.get("manual_ladder_from_check", False)) 
        with col_ladder_manual2:
            st.checkbox("도착지 수동 사다리 적용", key="manual_ladder_to_check") 
            st.number_input("도착지 사다리 수동 (+/-)", step=10000, key="arrival_ladder_surcharge_manual", format="%d",
                              disabled=not st.session_state.get("manual_ladder_to_check", False))
        
        if st.session_state.get("has_via_point", False):
            st.number_input("경유지 추가요금", min_value=0, step=10000, key="via_point_surcharge", format="%d")
            
    st.divider()

    st.header("최종 견적 결과")
    final_selected_vehicle_for_calc_val = st.session_state.get("final_selected_vehicle")
    total_cost_display, cost_items_display, personnel_info_display, has_cost_error = 0, [], {}, False

    validation_messages = get_validation_warnings(st.session_state.to_dict())
    if validation_messages:
        warning_html = "<div style='padding:10px; border: 1px solid #FFC107; background-color: #FFF3CD; border-radius: 5px; color: #664D03; margin-bottom: 15px;'>"
        warning_html += "<h5 style='margin-top:0; margin-bottom:10px;'>다음 필수 정보를 확인하거나 수정해주세요:</h5><ul style='margin-bottom: 0px; padding-left: 20px;'>"
        for msg in validation_messages:
            warning_html += f"<li style='margin-bottom: 5px;'>{msg}</li>"
        warning_html += "</ul></div>"
        st.markdown(warning_html, unsafe_allow_html=True)

    if not final_selected_vehicle_for_calc_val and not validation_messages :
        st.info("차량을 선택하고 필수 정보(주소, 층수 등)를 입력하시면 최종 견적 결과를 확인할 수 있습니다.")
    elif final_selected_vehicle_for_calc_val:
        try:
            if st.session_state.get("is_storage_move"):
                m_dt = st.session_state.get("moving_date")
                a_dt = st.session_state.get("arrival_date")
                if isinstance(m_dt, date) and isinstance(a_dt, date) and a_dt >= m_dt:
                    st.session_state.storage_duration = max(1, (a_dt - m_dt).days + 1)
                else: 
                    st.session_state.storage_duration = 1
                    if isinstance(m_dt, date) and (not isinstance(a_dt, date) or a_dt < m_dt) : 
                         st.session_state.arrival_date = m_dt + timedelta(days=1) 

            current_state_dict = st.session_state.to_dict()
            if hasattr(calculations, "calculate_total_moving_cost") and callable(calculations.calculate_total_moving_cost):
                total_cost_display, cost_items_display, personnel_info_display = calculations.calculate_total_moving_cost(current_state_dict)
                st.session_state.update({
                    "calculated_cost_items_for_pdf": cost_items_display,
                    "total_cost_for_pdf": total_cost_display,
                    "personnel_info_for_pdf": personnel_info_display
                })
                if any(isinstance(item, (list, tuple)) and len(item) > 0 and str(item[0]) == "오류" for item in cost_items_display):
                    has_cost_error = True
            else:
                st.error("최종 비용 계산 함수 로드 실패."); has_cost_error = True
                st.session_state.update({"calculated_cost_items_for_pdf": [], "total_cost_for_pdf": 0, "personnel_info_for_pdf": {}})

            total_cost_num = int(total_cost_display) if isinstance(total_cost_display, (int, float)) else 0
            
            st.subheader(f"총 견적 비용: {total_cost_num:,.0f} 원")
            st.write("")

            st.subheader("이사 정보 요약 (텍스트)")
            summary_display_possible = bool(final_selected_vehicle_for_calc_val) and not has_cost_error

            if summary_display_possible:
                try:
                    customer_name_summary = st.session_state.get('customer_name', '고객명 없음')
                    phone_summary = st.session_state.get('customer_phone', '연락처 없음')
                    email_summary = st.session_state.get('customer_email', '')
                    
                    from_addr_full_summary = st.session_state.get('from_address_full', '출발지 정보 없음')
                    to_addr_full_summary = st.session_state.get('to_address_full', '도착지 정보 없음')
                    
                    selected_vehicle_summary = st.session_state.get('final_selected_vehicle', '차량정보없음')
                    vehicle_tonnage_summary = ""
                    if isinstance(selected_vehicle_summary, str):
                        match_ton = re.search(r'(\d+(\.\d+)?)', selected_vehicle_summary)
                        if match_ton: vehicle_tonnage_summary = f"{match_ton.group(1)}톤"
                        else: vehicle_tonnage_summary = selected_vehicle_summary if selected_vehicle_summary else "차량정보없음"
                    elif isinstance(selected_vehicle_summary, (int, float)):
                        vehicle_tonnage_summary = f"{selected_vehicle_summary}톤"

                    p_info_summary = personnel_info_display 
                    men_summary = p_info_summary.get('final_men', 0)
                    women_summary = p_info_summary.get('final_women', 0)
                    ppl_summary = f"{men_summary}명"
                    if women_summary > 0: ppl_summary += f"+{women_summary}명"
                    vehicle_personnel_summary = f"{vehicle_tonnage_summary} / {ppl_summary}"

                    from_method_full = get_method_full_name('from_method')
                    to_method_full = get_method_full_name('to_method')
                    has_via_point_summary = st.session_state.get('has_via_point', False)
                    via_method_full = get_method_full_name('via_point_method') if has_via_point_summary else ""
                    via_loc_sum = st.session_state.get('via_point_address', '') if has_via_point_summary else ""
                    via_floor_sum = st.session_state.get('via_point_floor', '') if has_via_point_summary else ""
                    
                    deposit_total_input = int(st.session_state.get("deposit_amount", 0)) 
                    
                    is_storage_move_summary = st.session_state.get('is_storage_move', False)
                    storage_details_text_for_item = "" # For cost item note
                    storage_details_multiline_str = "" # For summary body
                    storage_location_name_for_route = "보관장소" 
                    storage_duration_for_route = st.session_state.get('storage_duration', 1)
                    storage_type_clean = "" 
                    moving_date_obj = st.session_state.get("moving_date") # Get date objects
                    arrival_date_obj = st.session_state.get("arrival_date")

                    if is_storage_move_summary:
                        storage_type_value = st.session_state.get('storage_type')
                        storage_type_raw_sum = str(storage_type_value) if storage_type_value is not None else "정보 없음" 
                        storage_type_clean = storage_type_raw_sum.split(" ")[0] if storage_type_raw_sum else "정보없음"
                        storage_location_name_for_route = storage_type_clean 
                        electricity_used_text = " (전기사용)" if st.session_state.get('storage_use_electricity', False) else ""
                        storage_details_text_for_item = f"{storage_type_clean} {storage_duration_for_route}일{electricity_used_text}"
                        
                        if isinstance(moving_date_obj, date) and isinstance(arrival_date_obj, date):
                            storage_details_multiline_str = f"{storage_type_clean}\n{moving_date_obj.month}월{moving_date_obj.day}일-{arrival_date_obj.month}월{arrival_date_obj.day}일({storage_duration_for_route}일)"
                        else: # Fallback if dates are not proper date objects
                            storage_details_multiline_str = f"{storage_type_clean}\n({storage_duration_for_route}일)"


                    bask_summary_str = "" 
                    q_b_s, q_mb_s, q_book_s = 0,0,0
                    original_move_type_key_sum_basket = st.session_state.get('base_move_type')
                    original_basket_section_key_sum_basket = "포장 자재 📦" 
                    if original_move_type_key_sum_basket and hasattr(data, 'items') and hasattr(data, 'item_definitions'):
                        item_defs_for_basket = data.item_definitions.get(original_move_type_key_sum_basket, {})
                        if original_basket_section_key_sum_basket in item_defs_for_basket:
                            try:
                                q_b_s = int(st.session_state.get(f"qty_{original_move_type_key_sum_basket}_{original_basket_section_key_sum_basket}_바구니",0) or 0)
                                q_mb_s_key1 = f"qty_{original_move_type_key_sum_basket}_{original_basket_section_key_sum_basket}_중박스"
                                q_mb_s_key2 = f"qty_{original_move_type_key_sum_basket}_{original_basket_section_key_sum_basket}_중자바구니" 
                                q_mb_s = int(st.session_state.get(q_mb_s_key1, st.session_state.get(q_mb_s_key2,0)) or 0)
                                q_book_s = int(st.session_state.get(f"qty_{original_move_type_key_sum_basket}_{original_basket_section_key_sum_basket}_책바구니",0) or 0)
                            except Exception as e_bask: print(f"Error getting basket summary: {e_bask}")
                    bask_parts = []
                    if q_b_s > 0: bask_parts.append(f"바{q_b_s}")
                    if q_mb_s > 0: bask_parts.append(f"중자{q_mb_s}") 
                    if q_book_s > 0: bask_parts.append(f"책{q_book_s}")
                    bask_summary_str = ", ".join(bask_parts) if bask_parts else ""

                    note_summary = st.session_state.get('special_notes', '')
                    
                    is_tax_invoice_selected = st.session_state.get("issue_tax_invoice", False)
                    is_card_payment_selected = st.session_state.get("card_payment", False)
                    payment_options_summary_str = "" 
                    if is_card_payment_selected:
                        payment_options_summary_str = "  (카드 결제 예정)"
                    elif is_tax_invoice_selected:
                        payment_options_summary_str = "  (계산서 발행 예정)"

                    summary_output_lines = [] 
                    
                    first_line_indicators = []
                    move_time_opt_summary = st.session_state.get("move_time_option", "미선택")
                    afternoon_details_summary = st.session_state.get("afternoon_move_details", "").strip()
                    
                    if is_storage_move_summary: first_line_indicators.append("보관이사")
                    if is_tax_invoice_selected and not is_card_payment_selected: first_line_indicators.append("계산서발행")
                    if is_card_payment_selected: first_line_indicators.append("카드결제") 
                    if st.session_state.get('apply_long_distance', False): first_line_indicators.append("장거리이사")
                    if move_time_opt_summary == "오후": 
                        indicator_txt = "오후"
                        if afternoon_details_summary and afternoon_details_summary.isdigit():
                             indicator_txt += f"{afternoon_details_summary}시이사"
                        elif afternoon_details_summary:
                             indicator_txt += f" ({afternoon_details_summary})이사"
                        else:
                             indicator_txt += "이사"
                        first_line_indicators.append(indicator_txt)

                    if first_line_indicators:
                        summary_output_lines.append(f"** [{', '.join(first_line_indicators)}] **")
                    
                    def build_summary_first_line(current_date_str, from_route_disp, to_route_disp, 
                                                 vehicle_tonnage_str, customer_email_str_param, 
                                                 is_tax_flag_param_local, has_via_flag_param_local, via_loc_str_for_route_param, via_floor_str_for_route_param, 
                                                 is_long_dist_flag_param, long_dist_selector_str_val_param):
                        
                        line_parts = [f"{current_date_str} / {from_route_disp}"]
                        if has_via_flag_param_local and (not is_storage_move_summary or (is_storage_move_summary and storage_location_name_for_route not in str(to_route_disp))):
                            via_display_text = via_loc_str_for_route_param
                            if via_floor_str_for_route_param: via_display_text += f" ({via_floor_str_for_route_param}층)"
                            line_parts.append(f"- {via_display_text} (경유) -")
                        
                        if to_route_disp and str(to_route_disp).strip():
                            if not (has_via_flag_param_local and from_route_disp.endswith("-")): 
                                line_parts.append("-") 
                            line_parts.append(to_route_disp)

                        line_parts.append(f"/ {vehicle_tonnage_str}")
                        
                        if is_tax_flag_param_local and not st.session_state.get("card_payment", False) and customer_email_str_param and \
                           (not is_storage_move_summary or (is_storage_move_summary and storage_location_name_for_route not in str(to_route_disp))):
                            line_parts.append(f"(계산서: {customer_email_str_param})")
                        
                        return " ".join(line_parts)

                    if is_storage_move_summary:
                        departure_specific_costs_val = 0
                        arrival_specific_costs_val = 0
                        common_splitable_costs_val = 0 
                        storage_fee_val = 0
                        total_vat_from_items = 0 

                        departure_cost_item_labels = ["출발지 사다리차", "출발지 스카이 장비", "출발지 수동 사다리 추가", "출발지 수동 사다리 할인"]
                        arrival_cost_item_labels = ["도착지 사다리차", "도착지 스카이 장비", "도착지 수동 사다리 추가", "도착지 수동 사다리 할인"]

                        for name, cost, note in cost_items_display: 
                            cost_int = 0
                            try: cost_int = int(float(cost or 0))
                            except: pass

                            if name in departure_cost_item_labels:
                                departure_specific_costs_val += cost_int
                            elif name in arrival_cost_item_labels:
                                arrival_specific_costs_val += cost_int
                            elif name == "보관료":
                                storage_fee_val = cost_int 
                            elif name == "부가세 (10%)": 
                                total_vat_from_items = cost_int
                            elif name == "카드결제 (VAT 및 수수료 포함)": 
                                pass 
                            elif name != "오류": 
                                common_splitable_costs_val += cost_int
                        
                        departure_date_str_display = moving_date_obj.strftime('%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj)
                        arrival_date_str_display = arrival_date_obj.strftime('%m-%d') if isinstance(arrival_date_obj, date) else str(arrival_date_obj)

                        deposit_leg1 = math.floor(deposit_total_input / 2)
                        deposit_leg2 = deposit_total_input - deposit_leg1

                        common_costs_leg1_split = round(common_splitable_costs_val / 2)
                        common_costs_leg2_split = common_splitable_costs_val - common_costs_leg1_split
                        
                        costs_leg1_pre_vat_sum = common_costs_leg1_split + departure_specific_costs_val
                        costs_leg2_pre_vat_sum_before_storage_fee = common_costs_leg2_split + arrival_specific_costs_val 

                        vat_leg1 = 0; vat_leg2 = 0
                        if is_tax_invoice_selected and not is_card_payment_selected and total_vat_from_items > 0:
                            total_pre_vat_for_vat_distribution = costs_leg1_pre_vat_sum + costs_leg2_pre_vat_sum_before_storage_fee + storage_fee_val #  VAT 분배시 보관료도 포함
                            if total_pre_vat_for_vat_distribution > 0:
                                # 각 레그의 (공통분할+특정작업비+해당레그보관료) 비율로 전체 VAT 분배
                                ratio_leg1 = costs_leg1_pre_vat_sum / total_pre_vat_for_vat_distribution
                                vat_leg1 = round(total_vat_from_items * ratio_leg1)
                                vat_leg2 = total_vat_from_items - vat_leg1
                            else: 
                                vat_leg1 = round(total_vat_from_items / 2)
                                vat_leg2 = total_vat_from_items - vat_leg1
                        
                        costs_leg2_pre_vat_sum_with_storage = costs_leg2_pre_vat_sum_before_storage_fee + storage_fee_val

                        payment_leg1_final = costs_leg1_pre_vat_sum + vat_leg1
                        payment_leg2_final = costs_leg2_pre_vat_sum_with_storage + vat_leg2
                        
                        remaining_leg1 = payment_leg1_final - deposit_leg1
                        remaining_leg2 = payment_leg2_final - deposit_leg2
                        
                        # --- Part 1: Departure to Storage ---
                        summary_output_lines.append(build_summary_first_line(
                            departure_date_str_display, 
                            from_addr_full_summary, 
                            storage_location_name_for_route, # 수정: 기간 제외
                            vehicle_tonnage_summary, email_summary,
                            is_tax_invoice_selected, 
                            has_via_point_summary, 
                            via_loc_sum, via_floor_sum, 
                            st.session_state.get('apply_long_distance', False), 
                            st.session_state.get('long_distance_selector', '')
                        ))
                        summary_output_lines.append("")

                        summary_output_lines.append(f"{customer_name_summary}"); summary_output_lines.append(f"{phone_summary}")
                        if email_summary and not (is_tax_invoice_selected and not is_card_payment_selected): summary_output_lines.append(email_summary)
                        summary_output_lines.append(""); summary_output_lines.append(vehicle_personnel_summary); summary_output_lines.append("")
                        summary_output_lines.append(f"출발 작업: {from_method_full}")
                        if has_via_point_summary: summary_output_lines.append(f"경유지 작업: {via_method_full}") 
                        summary_output_lines.append("")
                        summary_output_lines.append(f"계약금: {int(deposit_leg1):,.0f}원 / 잔금: {int(remaining_leg1):,.0f}원")
                        
                        leg1_breakdown_line_parts = [f"총 (출발일 결제액) {payment_leg1_final:,.0f}원 중 (분할이사비 {common_costs_leg1_split:,.0f}원", f"출발작업비 {departure_specific_costs_val:,.0f}원"]
                        if is_tax_invoice_selected and not is_card_payment_selected and vat_leg1 != 0:
                            leg1_breakdown_line_parts.append(f"출발일세액 {vat_leg1:,.0f}원")
                        elif is_card_payment_selected and payment_options_summary_str:
                             summary_output_lines[-1] += payment_options_summary_str 
                        summary_output_lines.append(f"{','.join(leg1_breakdown_line_parts)})")
                        summary_output_lines.append("")
                        
                        summary_output_lines.append("세부 비용 내역 (출발일 관련):")
                        leg1_detailed_costs_text = []
                        for name, cost, note in cost_items_display:
                            cost_int_detail = int(float(cost or 0))
                            if name in departure_cost_item_labels and cost_int_detail !=0 : 
                                formatted_line = format_cost_item_for_detailed_list(name, cost_int_detail, note, "") 
                                if formatted_line: leg1_detailed_costs_text.append(formatted_line)
                        for name, cost, note in cost_items_display: 
                            cost_int_detail = int(float(cost or 0))
                            if name not in departure_cost_item_labels + arrival_cost_item_labels + ["보관료", "부가세 (10%)", "카드결제 (VAT 및 수수료 포함)", "오류"]:
                                if cost_int_detail != 0: 
                                    cost_leg1_part = round(cost_int_detail / 2) 
                                    if cost_leg1_part != 0 : 
                                        formatted_line = format_cost_item_for_detailed_list(f"{name}(출발분)", cost_leg1_part, note, "") 
                                        if formatted_line: leg1_detailed_costs_text.append(formatted_line)
                        if is_tax_invoice_selected and not is_card_payment_selected and vat_leg1 !=0:
                            leg1_detailed_costs_text.append(f"  - 출발일 세액: {int(vat_leg1):,.0f}원")
                        
                        if leg1_detailed_costs_text: summary_output_lines.extend(leg1_detailed_costs_text)
                        else: summary_output_lines.append("  (출발일 해당 세부 비용 없음)")
                        summary_output_lines.append("")
                        
                        summary_output_lines.append("출발지 주소:")
                        summary_output_lines.append(from_addr_full_summary)
                        summary_output_lines.append("")
                        summary_output_lines.extend(storage_details_multiline_str.split('\n')) # 수정: 여러 줄 보관 정보 사용
                        summary_output_lines.append("") 

                        if bask_summary_str:
                            summary_output_lines.append(bask_summary_str)
                            summary_output_lines.append("") 
                        if note_summary and note_summary.strip():
                            summary_output_lines.append("고객요구사항:") # 수정: 개행 제거
                            summary_output_lines.extend([f"  - {note_line.strip()}" for note_line in note_summary.strip().replace('\r\n', '\n').split('\n') if note_line.strip()])
                        summary_output_lines.append("\n" + "="*30 + "\n")

                        # --- Part 2: Storage to Arrival ---
                        summary_output_lines.append(build_summary_first_line(
                            arrival_date_str_display,
                            storage_location_name_for_route, # 수정: 기간 제외
                            to_addr_full_summary,
                            vehicle_tonnage_summary, email_summary,
                            is_tax_invoice_selected, 
                            False, "", "", 
                            False, ""       
                        ))
                        summary_output_lines.append("")

                        summary_output_lines.append(f"{customer_name_summary}")
                        summary_output_lines.append(f"{phone_summary}")
                        summary_output_lines.append("")
                        summary_output_lines.append(vehicle_personnel_summary)
                        summary_output_lines.append("")
                        summary_output_lines.append(f"도착 작업: {to_method_full}")
                        summary_output_lines.append("")
                        summary_output_lines.append(f"계약금: {int(deposit_leg2):,.0f}원 / 잔금: {int(remaining_leg2):,.0f}원")
                        
                        leg2_breakdown_line_parts = [f"총 (도착일 지불액) {payment_leg2_final:,.0f}원 중 (분할이사비 {common_costs_leg2_split:,.0f}원", f"도착작업비 {arrival_specific_costs_val:,.0f}원", f"보관료 {storage_fee_val:,.0f}원"]
                        if is_tax_invoice_selected and not is_card_payment_selected and vat_leg2 != 0:
                            leg2_breakdown_line_parts.append(f"도착일세액 {vat_leg2:,.0f}원")
                        elif is_card_payment_selected and payment_options_summary_str:
                            summary_output_lines[-1] += payment_options_summary_str 
                        summary_output_lines.append(f"{','.join(leg2_breakdown_line_parts)})")
                        summary_output_lines.append("")
                        
                        summary_output_lines.append("세부 비용 내역 (도착일 관련):")
                        leg2_detailed_costs_text = []
                        for name, cost, note in cost_items_display: 
                            cost_int_detail = int(float(cost or 0))
                            if name not in departure_cost_item_labels + arrival_cost_item_labels + ["보관료", "부가세 (10%)", "카드결제 (VAT 및 수수료 포함)", "오류"]:
                                if cost_int_detail != 0:
                                    cost_leg2_part = cost_int_detail - round(cost_int_detail / 2) 
                                    if cost_leg2_part !=0:
                                        formatted_line = format_cost_item_for_detailed_list(f"{name}(도착분)", cost_leg2_part, note, "")
                                        if formatted_line: leg2_detailed_costs_text.append(formatted_line)
                        for name, cost, note in cost_items_display:
                            cost_int_detail = int(float(cost or 0))
                            if name in arrival_cost_item_labels and cost_int_detail != 0 :
                                formatted_line = format_cost_item_for_detailed_list(name, cost_int_detail, note, "")
                                if formatted_line: leg2_detailed_costs_text.append(formatted_line)
                        
                        if storage_fee_val != 0: 
                             formatted_line = format_cost_item_for_detailed_list("보관료", storage_fee_val, next((item[2] for item in cost_items_display if item[0] == "보관료"),""), storage_details_text_for_item) 
                             if formatted_line: leg2_detailed_costs_text.append(formatted_line)
                        if is_tax_invoice_selected and not is_card_payment_selected and vat_leg2 !=0:
                            leg2_detailed_costs_text.append(f"  - 도착일 세액: {int(vat_leg2):,.0f}원")

                        if leg2_detailed_costs_text: summary_output_lines.extend(leg2_detailed_costs_text)
                        else: summary_output_lines.append("  (도착일 해당 세부 비용 없음)")
                        summary_output_lines.append("")

                        summary_output_lines.extend(storage_details_multiline_str.split('\n')) # 수정: 여러 줄 보관 정보 사용
                        summary_output_lines.append("") 

                        summary_output_lines.append("도착지 주소:")
                        summary_output_lines.append(to_addr_full_summary)
                        summary_output_lines.append("")
                        
                        if note_summary and note_summary.strip():
                            summary_output_lines.append("고객요구사항:") # 수정: 개행 제거
                            summary_output_lines.extend([f"  - {note_line.strip()}" for note_line in note_summary.strip().replace('\r\n', '\n').split('\n') if note_line.strip()])
                    else: # 일반 이사 (보관이사 아님)
                        if summary_output_lines and len(summary_output_lines) > 0 and not summary_output_lines[0].startswith("**"): summary_output_lines.insert(0,"")

                        moving_date_val = st.session_state.get('moving_date')
                        formatted_date = moving_date_val.strftime('%m-%d') if isinstance(moving_date_val, date) else str(moving_date_val)
                        
                        summary_output_lines.append(build_summary_first_line(
                            formatted_date,
                            from_addr_full_summary,
                            to_addr_full_summary,
                            vehicle_tonnage_summary, email_summary,
                            is_tax_invoice_selected, has_via_point_summary, via_loc_sum, via_floor_sum,
                            st.session_state.get('apply_long_distance', False), st.session_state.get('long_distance_selector', '')
                        ))
                        summary_output_lines.append("") 

                        if customer_name_summary: summary_output_lines.append(customer_name_summary)
                        if phone_summary: summary_output_lines.append(phone_summary)
                        summary_output_lines.append("") 

                        summary_output_lines.append(vehicle_personnel_summary)
                        summary_output_lines.append("") 

                        summary_output_lines.append(f"출발지 작업: {from_method_full}")
                        if has_via_point_summary: 
                            summary_output_lines.append(f"경유지 작업: {via_method_full}")
                        summary_output_lines.append(f"도착지 작업: {to_method_full}")
                        summary_output_lines.append("") 
                        
                        summary_output_lines.append(f"계약금: {deposit_total_input:,.0f}원 / 잔금: {total_cost_num - deposit_total_input:,.0f}원")
                        if payment_options_summary_str: 
                            summary_output_lines.append(payment_options_summary_str)
                        summary_output_lines.append("") 

                        summary_output_lines.append("세부 비용 내역:")
                        cost_item_details_for_summary = []
                        for name, cost, note in cost_items_display:
                            formatted_line = format_cost_item_for_detailed_list(name, cost, note, storage_details_text_for_item)
                            if formatted_line:
                                cost_item_details_for_summary.append(formatted_line)
                        
                        if cost_item_details_for_summary:
                            summary_output_lines.extend(cost_item_details_for_summary)
                        else:
                            summary_output_lines.append("  (상세 비용 내역 없음)")
                        summary_output_lines.append("")

                        summary_output_lines.append("출발지 주소:")
                        summary_output_lines.append(from_addr_full_summary)
                        if has_via_point_summary:
                            summary_output_lines.append("\n경유지 주소:")
                            summary_output_lines.append(f"{via_loc_sum}" + (f" ({via_floor_sum}층)" if via_floor_sum else ""))
                        summary_output_lines.append("\n도착지 주소:")
                        summary_output_lines.append(to_addr_full_summary)
                        summary_output_lines.append("") 

                        if bask_summary_str: 
                            summary_output_lines.append(bask_summary_str) 
                            summary_output_lines.append("") 
                        
                        if note_summary and note_summary.strip():
                            summary_output_lines.append("고객요구사항:")
                            summary_output_lines.extend([f"  - {note_line.strip()}" for note_line in note_summary.strip().replace('\r\n', '\n').split('\n') if note_line.strip()])

                    st.text_area("요약 정보", "\n".join(summary_output_lines), height=700, key="summary_text_area_readonly_tab3", disabled=True)

                except Exception as e_summary_direct_final_err:
                    st.error(f"요약 정보 생성 중 오류: {e_summary_direct_final_err}"); traceback.print_exc()
            elif not final_selected_vehicle_for_calc_val:
                if not validation_messages or not any("차량 종류가 선택되지 않았습니다" in msg for msg in validation_messages):
                    st.info("견적 계산용 차량 미선택으로 요약 정보 표시 불가.")
            st.divider()
        except Exception as calc_err_outer_display_final_err:
            st.error(f"최종 견적 표시 중 외부 오류 발생: {calc_err_outer_display_final_err}")
            traceback.print_exc()

    st.subheader("견적서 생성, 발송 및 다운로드")

    can_generate_anything = bool(final_selected_vehicle_for_calc_val) and \
                          not has_cost_error and \
                          st.session_state.get("calculated_cost_items_for_pdf") and \
                          st.session_state.get("total_cost_for_pdf", 0) > 0
    actions_disabled = not can_generate_anything

    with st.container(border=True):
        st.markdown("**고객 전달용 파일**")
        col_pdf_btn, col_pdf_img_btn = st.columns(2)

        pdf_generation_possible = hasattr(pdf_generator, "generate_pdf") and callable(pdf_generator.generate_pdf) and can_generate_anything
        pdf_to_image_possible = hasattr(pdf_generator, "generate_quote_image_from_pdf") and callable(pdf_generator.generate_quote_image_from_pdf) and pdf_generation_possible

        with col_pdf_btn:
            if st.button("고객용 PDF 생성", key="generate_customer_pdf_btn_tab3", disabled=actions_disabled or not pdf_generation_possible):
                current_session_data_for_pdf = st.session_state.to_dict()
                pdf_specific_state_data = current_session_data_for_pdf.copy()
                pdf_specific_state_data['from_location'] = current_session_data_for_pdf.get('from_address_full', '-')
                pdf_specific_state_data['to_location'] = current_session_data_for_pdf.get('to_address_full', '-')
                if current_session_data_for_pdf.get('has_via_point', False):
                    pdf_specific_state_data['via_point_location'] = current_session_data_for_pdf.get('via_point_address', '-')
                else:
                    pdf_specific_state_data['via_point_location'] = '-'

                pdf_args_to_pass = {
                    "state_data": pdf_specific_state_data, 
                    "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
                    "total_cost": st.session_state.get("total_cost_for_pdf", 0),
                    "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
                }
                with st.spinner("고객용 PDF 생성 중..."):
                    pdf_data = pdf_generator.generate_pdf(**pdf_args_to_pass) 
                if pdf_data:
                    st.session_state['customer_final_pdf_data'] = pdf_data
                    st.success("고객용 PDF 생성 완료!")
                else:
                    st.error("고객용 PDF 생성 실패.")
                    if 'customer_final_pdf_data' in st.session_state: del st.session_state['customer_final_pdf_data']
            
            if st.session_state.get('customer_final_pdf_data'):
                fname_pdf_cust = f"견적서_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d') if hasattr(utils, 'get_current_kst_time_str') else datetime.now().strftime('%y%m%d')}.pdf"
                st.download_button(
                    label="고객용 PDF 다운로드",
                    data=st.session_state['customer_final_pdf_data'],
                    file_name=fname_pdf_cust, mime="application/pdf",
                    key='dl_btn_customer_final_pdf_tab3', disabled=actions_disabled
                )

        with col_pdf_img_btn: 
            if pdf_to_image_possible:
                if st.button("고객용 견적서 이미지 생성 (PDF기반)", key="generate_customer_pdf_image_btn_tab3", disabled=actions_disabled or not st.session_state.get('customer_final_pdf_data')):
                    with st.spinner("PDF 기반 고객용 이미지 생성 중..."):
                        pdf_to_convert = st.session_state.get('customer_final_pdf_data')
                        if pdf_to_convert:
                            img_data_from_pdf = pdf_generator.generate_quote_image_from_pdf(pdf_to_convert) 
                            if img_data_from_pdf:
                                st.session_state['customer_pdf_image_data_tab3'] = img_data_from_pdf
                                st.success("PDF 기반 고객용 이미지 생성 완료!")
                            else:
                                st.warning("PDF 기반 고객용 이미지 생성 실패.")
                                if 'customer_pdf_image_data_tab3' in st.session_state: del st.session_state['customer_pdf_image_data_tab3']
                        else: st.warning("먼저 고객용 PDF를 생성해주세요.")
                
                if st.session_state.get('customer_pdf_image_data_tab3'):
                    fname_pdf_img_cust = f"견적서_이미지_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d') if hasattr(utils, 'get_current_kst_time_str') else datetime.now().strftime('%y%m%d')}.png"
                    st.download_button(
                        label="고객용 견적서 이미지 다운로드",
                        data=st.session_state['customer_pdf_image_data_tab3'],
                        file_name=fname_pdf_img_cust, mime="image/png",
                        key='dl_btn_customer_pdf_image_tab3', disabled=actions_disabled
                    )
            else: st.caption("PDF 이미지 변환 기능이 로드되지 않았습니다.")


    with st.container(border=True):
        st.markdown("**내부 검토용 파일**")
        col_internal_img_btn, col_internal_excel_btn = st.columns(2)
        
        company_image_possible = hasattr(image_generator, "create_quote_image") and callable(image_generator.create_quote_image) and can_generate_anything

        with col_internal_img_btn:
            if st.button("내부 검토용 양식 이미지 생성", key="generate_internal_form_image_btn_tab3", disabled=actions_disabled or not company_image_possible):
                current_session_data_for_img = st.session_state.to_dict()
                img_specific_state_data = current_session_data_for_img.copy()
                img_specific_state_data['from_location'] = current_session_data_for_img.get('from_address_full', '-')
                img_specific_state_data['to_location'] = current_session_data_for_img.get('to_address_full', '-')
                if current_session_data_for_img.get('has_via_point', False): 
                    img_specific_state_data['via_point_location'] = current_session_data_for_img.get('via_point_address', '-')

                company_form_image_args_updated = {
                    "state_data": img_specific_state_data, 
                    "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
                    "total_cost_overall": st.session_state.get("total_cost_for_pdf", 0),
                    "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
                }
                with st.spinner("내부 검토용 양식 이미지 생성 중..."):
                    internal_image_data = image_generator.create_quote_image(**company_form_image_args_updated)
                if internal_image_data:
                    st.session_state['internal_form_image_data_tab3'] = internal_image_data
                    st.success("내부 검토용 양식 이미지 생성 완료!")
                else:
                    st.error("내부 검토용 양식 이미지 생성 실패.")
                    if 'internal_form_image_data_tab3' in st.session_state: del st.session_state['internal_form_image_data_tab3']

            if st.session_state.get('internal_form_image_data_tab3'):
                fname_internal_img = f"내부양식_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d') if hasattr(utils, 'get_current_kst_time_str') else datetime.now().strftime('%y%m%d')}.png"
                st.download_button(
                    label="내부 검토용 양식 이미지 다운로드",
                    data=st.session_state['internal_form_image_data_tab3'],
                    file_name=fname_internal_img, mime="image/png",
                    key='dl_btn_internal_form_image_tab3', disabled=actions_disabled
                )
        
        with col_internal_excel_btn:
            excel_possible = hasattr(excel_filler, "fill_final_excel_template") and callable(excel_filler.fill_final_excel_template) and can_generate_anything
            if st.button("내부용 Excel 생성", key="generate_internal_excel_btn_tab3", disabled=actions_disabled or not excel_possible):
                if excel_possible:
                    _current_state_excel_orig = st.session_state.to_dict()
                    excel_specific_state_data = _current_state_excel_orig.copy()
                    excel_specific_state_data['from_location'] = _current_state_excel_orig.get('from_address_full', '-')
                    excel_specific_state_data['to_location'] = _current_state_excel_orig.get('to_address_full', '-')
                    if _current_state_excel_orig.get('has_via_point', False):
                        excel_specific_state_data['via_point_location'] = _current_state_excel_orig.get('via_point_address', '-')
                    
                    _total_cost_excel_calc, _cost_items_excel_calc, _personnel_info_excel_calc = calculations.calculate_total_moving_cost(st.session_state.to_dict())

                    with st.spinner("내부용 Excel 파일 생성 중..."):
                        filled_excel_data_dl = excel_filler.fill_final_excel_template(
                            excel_specific_state_data, 
                            _cost_items_excel_calc,    
                            _total_cost_excel_calc,    
                            _personnel_info_excel_calc 
                        )
                    if filled_excel_data_dl:
                        st.session_state['internal_excel_data_for_download_tab3'] = filled_excel_data_dl
                        st.success("내부용 Excel 생성 완료!")
                    else:
                        st.error("내부용 Excel 파일 생성 실패.")
                        if 'internal_excel_data_for_download_tab3' in st.session_state: del st.session_state['internal_excel_data_for_download_tab3']

            if st.session_state.get('internal_excel_data_for_download_tab3') and excel_possible:
                fname_excel_dl = f"내부견적_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d') if hasattr(utils, 'get_current_kst_time_str') else datetime.now().strftime('%y%m%d')}.xlsx"
                st.download_button(label="Excel 다운로드 (내부용)", data=st.session_state['internal_excel_data_for_download_tab3'], file_name=fname_excel_dl, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='dl_btn_excel_internal_tab3', disabled=actions_disabled)
    st.divider()

    with st.container(border=True):
        st.markdown("**이메일 발송 (고객용 PDF 첨부)**")
        email_recipient_exists = bool(st.session_state.get("customer_email", "").strip())
        email_modules_ok = hasattr(email_utils, "send_quote_email") and callable(email_utils.send_quote_email) and hasattr(pdf_generator, "generate_pdf") and callable(pdf_generator.generate_pdf)
        email_possible = email_modules_ok and can_generate_anything and email_recipient_exists

        if st.button("이메일 발송", key="email_send_button_main_tab3", disabled=actions_disabled or not email_possible):
            recipient_email_send = st.session_state.get("customer_email")
            customer_name_send = st.session_state.get("customer_name", "고객")

            pdf_email_bytes_send = st.session_state.get('customer_final_pdf_data')
            if not pdf_email_bytes_send and pdf_generation_possible:
                current_session_data_for_email_pdf = st.session_state.to_dict()
                email_pdf_specific_state_data = current_session_data_for_email_pdf.copy()
                email_pdf_specific_state_data['from_location'] = current_session_data_for_email_pdf.get('from_address_full', '-')
                email_pdf_specific_state_data['to_location'] = current_session_data_for_email_pdf.get('to_address_full', '-')
                if current_session_data_for_email_pdf.get('has_via_point', False):
                    email_pdf_specific_state_data['via_point_location'] = current_session_data_for_email_pdf.get('via_point_address', '-')
                else:
                    email_pdf_specific_state_data['via_point_location'] = '-'
                
                email_pdf_args_to_pass = {
                    "state_data": email_pdf_specific_state_data,
                    "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
                    "total_cost": st.session_state.get("total_cost_for_pdf", 0),
                    "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
                }
                with st.spinner("이메일 첨부용 PDF 생성 중..."):
                    pdf_email_bytes_send = pdf_generator.generate_pdf(**email_pdf_args_to_pass)
                if pdf_email_bytes_send:
                     st.session_state['customer_final_pdf_data'] = pdf_email_bytes_send

            if pdf_email_bytes_send:
                subject_send = f"[{customer_name_send}님] 이삿날 이사 견적서입니다."
                body_send = f"{customer_name_send}님,\n\n요청하신 이사 견적서를 첨부 파일로 보내드립니다.\n\n감사합니다.\n이삿날 드림"
                pdf_filename_send = f"견적서_{customer_name_send}_{utils.get_current_kst_time_str('%Y%m%d') if hasattr(utils, 'get_current_kst_time_str') else datetime.now().strftime('%y%m%d')}.pdf"

                with st.spinner(f"{recipient_email_send}(으)로 이메일 발송 중..."):
                    email_sent_status = email_utils.send_quote_email(recipient_email_send, subject_send, body_send, pdf_email_bytes_send, pdf_filename_send)

                if email_sent_status: st.success(f"이메일 발송 성공!")
                else: st.error("이메일 발송 실패.")
            else:
                st.error("첨부할 PDF 생성에 실패하여 이메일을 발송할 수 없습니다.")
        elif actions_disabled:
            st.caption("견적 내용을 먼저 완성해주세요.")
        elif not email_recipient_exists:
            st.caption("고객 이메일 주소가 입력되지 않았습니다.")
        elif not email_modules_ok:
            st.caption("이메일 또는 PDF 생성 모듈에 문제가 있습니다.")
        elif not can_generate_anything :
            st.caption("견적 내용이 충분하지 않아 이메일을 발송할 수 없습니다.")
