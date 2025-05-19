# ui_tab3.py (수정된 전체 코드 - 요약 정보 포맷 변경 적용)
import streamlit as st
import pandas as pd
import io
import pytz
from datetime import datetime, date, timedelta
import traceback
import re

# Import necessary custom modules
try:
    import data
    import utils
    import calculations
    import pdf_generator
    import excel_filler
    import email_utils
    import callbacks
    from state_manager import MOVE_TYPE_OPTIONS
    import image_generator
except ImportError as e:
    st.error(f"UI Tab 3: 필수 모듈 로딩 실패 - {e}")
    if hasattr(e, "name"):
        if e.name == "email_utils": st.warning("email_utils.py 로드 실패. 이메일 발송 비활성화.")
        elif e.name == "pdf_generator": st.warning("pdf_generator.py 로드 실패. PDF 관련 기능 제한 가능.")
        elif e.name == "image_generator": st.error("image_generator.py 로드 실패! 회사 양식 이미지 생성 비활성화.")
    if "MOVE_TYPE_OPTIONS" not in globals():
        MOVE_TYPE_OPTIONS = ["가정 이사", "사무실 이사"] # 이모티콘 제거
    if not all(module_name in globals() for module_name in ["data", "utils", "calculations", "callbacks", "state_manager", "image_generator", "pdf_generator"]):
        st.error("UI Tab 3: 핵심 데이터/유틸리티 모듈 로딩 실패.")
except Exception as e:
    st.error(f"UI Tab 3: 모듈 로딩 중 오류 - {e}")
    traceback.print_exc()
    if "MOVE_TYPE_OPTIONS" not in globals():
        MOVE_TYPE_OPTIONS = ["가정 이사", "사무실 이사"] # 이모티콘 제거
    st.stop()

# get_method_full_name 함수 (ui_tab3.py 내에 필요할 수 있음)
def get_method_full_name(method_key):
    method_str = str(st.session_state.get(method_key, '')).strip()
    # 이모티콘 제거
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

    if not str(state.get('from_floor', '')).strip():
        warnings.append("출발지 층수 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")
    if not str(state.get('to_floor', '')).strip():
        warnings.append("도착지 층수 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")
    if not state.get('final_selected_vehicle'):
        warnings.append("견적 계산용 차량 종류가 선택되지 않았습니다. '차량 선택' 섹션에서 차량을 선택해주세요.")
    if not str(state.get('to_location', '')).strip():
        warnings.append("도착지 주소 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")

    if state.get('final_selected_vehicle'):
        total_dispatched_trucks = sum(
            st.session_state.get(key, 0) or 0
            for key in ['dispatched_1t', 'dispatched_2_5t', 'dispatched_3_5t', 'dispatched_5t']
        )
        if total_dispatched_trucks == 0:
            warnings.append("실제 투입 차량 대수가 입력되지 않았습니다. '실제 투입 차량' 섹션에서 각 톤수별 차량 대수를 입력해주세요.")
    return warnings

def render_tab3():
    st.header("계산 및 옵션") # 이모티콘 제거
    update_basket_quantities_callback = getattr(callbacks, "update_basket_quantities", None)
    sync_move_type_callback = getattr(callbacks, "sync_move_type", None)
    handle_item_update_callback = getattr(callbacks, "handle_item_update", None)

    if not callable(update_basket_quantities_callback) or not callable(sync_move_type_callback):
        st.error("UI Tab 3: 콜백 함수 로드 실패.")

    st.subheader("이사 유형") # 이모티콘 제거
    current_move_type = st.session_state.get("base_move_type", MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사")
    current_index_tab3 = 0
    # MOVE_TYPE_OPTIONS 이모티콘 제거 (상단에서 처리)
    move_type_options_no_emoji = [opt.split(" ")[0] for opt in MOVE_TYPE_OPTIONS]
    current_move_type_no_emoji = current_move_type.split(" ")[0]

    if move_type_options_no_emoji:
        try:
            current_index_tab3 = move_type_options_no_emoji.index(current_move_type_no_emoji)
        except ValueError:
            current_index_tab3 = 0
            st.session_state.base_move_type = MOVE_TYPE_OPTIONS[0]
            if 'base_move_type_widget_tab1' in st.session_state:
                 st.session_state.base_move_type_widget_tab1 = MOVE_TYPE_OPTIONS[0]
            if callable(handle_item_update_callback):
                 handle_item_update_callback()
    else:
        st.error("이사 유형 옵션을 불러올 수 없습니다."); return

    st.radio(
        "기본 이사 유형:", options=MOVE_TYPE_OPTIONS, format_func=lambda x: x.split(" ")[0], # 표시만 한글로
        index=current_index_tab3, horizontal=True,
        key="base_move_type_widget_tab3", on_change=sync_move_type_callback, args=("base_move_type_widget_tab3",)
    )
    st.divider()

    with st.container(border=True):
        st.subheader("차량 선택 (견적 계산용)") # 이모티콘 제거
        col_v1_widget, col_v2_widget = st.columns([1, 2])
        with col_v1_widget:
            st.radio("차량 선택 방식:", ["자동 추천 차량 사용", "수동으로 차량 선택"], key="vehicle_select_radio", on_change=update_basket_quantities_callback)
        with col_v2_widget:
            current_move_type_widget = st.session_state.get('base_move_type')
            vehicle_prices_options_widget, available_trucks_widget = {}, []
            if current_move_type_widget and hasattr(data, 'vehicle_prices') and isinstance(data.vehicle_prices, dict):
                vehicle_prices_options_widget = data.vehicle_prices.get(current_move_type_widget, {})
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
                    st.success(f"자동 선택됨: {final_vehicle_from_state}") # 이모티콘 제거
                    spec = data.vehicle_specs.get(final_vehicle_from_state) if hasattr(data, "vehicle_specs") else None
                    if spec:
                        st.caption(f"선택차량 최대 용량: {spec.get('capacity', 'N/A')}m³, {spec.get('weight_capacity', 'N/A'):,}kg")
                        st.caption(f"현재 이사짐 예상: {current_total_volume:.2f}m³, {current_total_weight:.2f}kg")
                else:
                    error_msg = "자동 추천 불가: " # 이모티콘 제거
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
                        st.error("현재 이사 유형에 선택 가능한 차량 정보가 없습니다.") # 이모티콘 제거
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
                             st.info(f"수동 선택됨: {final_vehicle_from_state}") # 이모티콘 제거
            else:
                if not available_trucks_widget:
                    st.error("현재 이사 유형에 선택 가능한 차량 정보가 없습니다.") # 이모티콘 제거
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
                        st.info(f"수동 선택됨: {final_vehicle_from_state}") # 이모티콘 제거
                        spec_manual = data.vehicle_specs.get(final_vehicle_from_state) if hasattr(data, "vehicle_specs") else None
                        if spec_manual:
                            st.caption(f"선택차량 최대 용량: {spec_manual.get('capacity', 'N/A')}m³, {spec_manual.get('weight_capacity', 'N/A'):,}kg")
                            st.caption(f"현재 이사짐 예상: {current_total_volume:.2f}m³, {current_total_weight:.2f}kg")
    st.divider()

    with st.container(border=True):
        st.subheader("작업 조건 및 추가 옵션") # 이모티콘 제거
        sky_from = (get_method_full_name("from_method") == "스카이") # 이모티콘 없는 비교
        sky_to = (get_method_full_name("to_method") == "스카이")   # 이모티콘 없는 비교
        if sky_from or sky_to:
            st.warning("스카이 작업 선택됨 - 시간 입력 필요") # 이모티콘 제거
            cols_sky = st.columns(2)
            if sky_from: cols_sky[0].number_input("출발 스카이 시간(h)", min_value=1, step=1, key="sky_hours_from")
            if sky_to: cols_sky[1].number_input("도착 스카이 시간(h)", min_value=1, step=1, key="sky_hours_final")
            st.write("")
        col_add1, col_add2 = st.columns(2)
        col_add1.number_input("추가 남성 인원", min_value=0, step=1, key="add_men") # 이모티콘 제거
        col_add2.number_input("추가 여성 인원", min_value=0, step=1, key="add_women") # 이모티콘 제거
        st.write("")
        st.subheader("실제 투입 차량 (견적서 및 내부 기록용)") # 이모티콘 제거
        dispatched_cols = st.columns(4)
        dispatched_cols[0].number_input("1톤", min_value=0, step=1, key="dispatched_1t")
        dispatched_cols[1].number_input("2.5톤", min_value=0, step=1, key="dispatched_2_5t")
        dispatched_cols[2].number_input("3.5톤", min_value=0, step=1, key="dispatched_3_5t")
        dispatched_cols[3].number_input("5톤", min_value=0, step=1, key="dispatched_5t")
        st.caption("실제 현장에 투입될 차량 대수를 입력합니다.")
        st.write("")

        show_remove_housewife_option = False
        base_housewife_count_for_option = 0
        discount_amount_for_option = 0
        current_move_type_for_option = st.session_state.get("base_move_type")
        final_vehicle_for_option_display = st.session_state.get("final_selected_vehicle")

        if current_move_type == MOVE_TYPE_OPTIONS[0] and \
           final_vehicle_for_option_display and \
           hasattr(data, "vehicle_prices") and \
           isinstance(data.vehicle_prices.get(current_move_type_for_option), dict) and \
           final_vehicle_for_option_display in data.vehicle_prices[current_move_type_for_option]:
            vehicle_details = data.vehicle_prices[current_move_type_for_option][final_vehicle_for_option_display]
            base_housewife_count_for_option = vehicle_details.get("housewife", 0)
            if base_housewife_count_for_option > 0:
                show_remove_housewife_option = True
                additional_person_cost_for_option = getattr(data, "ADDITIONAL_PERSON_COST", 200000)
                discount_amount_for_option = additional_person_cost_for_option * base_housewife_count_for_option

        if show_remove_housewife_option:
            st.checkbox(
                f"기본 여성({base_housewife_count_for_option}명) 제외 (비용 할인: -{discount_amount_for_option:,.0f}원)",
                key="remove_base_housewife"
            )
        else:
            if "remove_base_housewife" in st.session_state:
                st.session_state.remove_base_housewife = False

        col_waste1, col_waste2 = st.columns([1,2])
        col_waste1.checkbox("폐기물 처리 필요", key="has_waste_check") # 이모티콘 제거
        if st.session_state.get("has_waste_check"):
            waste_cost_per_ton = getattr(data, "WASTE_DISPOSAL_COST_PER_TON", 0)
            waste_cost_display = waste_cost_per_ton if isinstance(waste_cost_per_ton, (int, float)) else 0
            col_waste2.number_input("폐기물 양 (톤)", min_value=0.5, max_value=10.0, step=0.5, key="waste_tons_input", format="%.1f")
            if waste_cost_display > 0: col_waste2.caption(f"1톤당 {waste_cost_display:,}원 추가 비용 발생") # 이모티콘 제거

        st.write("날짜 유형 선택 (중복 가능, 해당 시 할증)") # 이모티콘 제거
        date_options_text = ["이사많은날", "손없는날", "월말", "공휴일", "금요일"] # 이모티콘 제거
        # data.py의 special_day_prices 키도 이모티콘 없이 "이사많은날" 등으로 변경 필요
        date_options_keys_data = ["이사많은날 🏠", "손없는날 ✋", "월말 📅", "공휴일 🎉", "금요일 📅"]


        date_surcharges_defined = hasattr(data, "special_day_prices") and isinstance(data.special_day_prices, dict)
        if not date_surcharges_defined: st.warning("data.py에 날짜 할증 정보가 없습니다.")
        date_keys = [f"date_opt_{i}_widget" for i in range(len(date_options_text))]
        cols_date = st.columns(len(date_options_text))
        for i, option_text in enumerate(date_options_text):
            # data.py의 키를 사용해 할증료 조회
            surcharge = data.special_day_prices.get(date_options_keys_data[i], 0) if date_surcharges_defined else 0
            cols_date[i].checkbox(option_text, key=date_keys[i], help=f"{surcharge:,}원 할증" if surcharge > 0 else "")
    st.divider()

    with st.container(border=True):
        st.subheader("수기 조정 및 계약금") # 이모티콘 제거
        cols_adj_new = st.columns(2)
        with cols_adj_new[0]:
            st.number_input("계약금", min_value=0, step=10000, key="deposit_amount", format="%d") # 이모티콘 제거
        with cols_adj_new[1]:
            st.number_input("추가 조정 (+/-)", step=10000, key="adjustment_amount", format="%d") # 이모티콘 제거

        cols_extra_fees = st.columns(2)
        with cols_extra_fees[0]:
            st.number_input("사다리 추가요금", min_value=0, step=10000, key="regional_ladder_surcharge", format="%d") # 이모티콘 제거
        if st.session_state.get("has_via_point", False):
             with cols_extra_fees[1]:
                st.number_input("경유지 추가요금", min_value=0, step=10000, key="via_point_surcharge", format="%d") # 이모티콘 제거
        else:
            with cols_extra_fees[1]:
                pass
    st.divider()

    st.header("최종 견적 결과") # 이모티콘 제거
    final_selected_vehicle_for_calc = st.session_state.get("final_selected_vehicle")
    total_cost_display, cost_items_display, personnel_info_display, has_cost_error = 0, [], {}, False

    validation_messages = get_validation_warnings(st.session_state.to_dict())
    if validation_messages:
        warning_html = "<div style='padding:10px; border: 1px solid #FFC107; background-color: #FFF3CD; border-radius: 5px; color: #664D03; margin-bottom: 15px;'>"
        warning_html += "<h5 style='margin-top:0; margin-bottom:10px;'>다음 필수 정보를 확인하거나 수정해주세요:</h5><ul style='margin-bottom: 0px; padding-left: 20px;'>" # 이모티콘 제거
        for msg in validation_messages:
            warning_html += f"<li style='margin-bottom: 5px;'>{msg}</li>"
        warning_html += "</ul></div>"
        st.markdown(warning_html, unsafe_allow_html=True)


    if not final_selected_vehicle_for_calc and not validation_messages :
        st.info("차량을 선택하고 필수 정보(주소, 층수 등)를 입력하시면 최종 견적 결과를 확인할 수 있습니다.")
    elif final_selected_vehicle_for_calc:
        try:
            if st.session_state.get("is_storage_move"):
                m_dt = st.session_state.get("moving_date")
                a_dt = st.session_state.get("arrival_date")
                if isinstance(m_dt, date) and isinstance(a_dt, date) and a_dt >= m_dt:
                    st.session_state.storage_duration = max(1, (a_dt - m_dt).days + 1)
                else:
                    st.session_state.storage_duration = 1

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
            deposit_val = st.session_state.get("deposit_amount", 0)
            deposit_amount_num = int(deposit_val) if deposit_val is not None else 0
            remaining_balance_num = total_cost_num - deposit_amount_num

            st.subheader(f"총 견적 비용: {total_cost_num:,.0f} 원") # 이모티콘 제거
            st.subheader(f"계약금: {deposit_amount_num:,.0f} 원") # 이모티콘 제거
            st.subheader(f"잔금 (총 비용 - 계약금): {remaining_balance_num:,.0f} 원") # 이모티콘 제거
            st.write("")

            st.subheader("비용 상세 내역") # 이모티콘 제거
            if has_cost_error:
                err_item = next((item for item in cost_items_display if isinstance(item, (list, tuple)) and len(item)>0 and str(item[0]) == "오류"), None)
                st.error(f"비용 계산 오류: {err_item[2] if err_item and len(err_item) > 2 else '알 수 없는 오류'}")
            elif cost_items_display:
                valid_costs = [item for item in cost_items_display if not (isinstance(item, (list, tuple)) and len(item) > 0 and str(item[0]) == "오류")]
                if valid_costs:
                    df_display_costs = pd.DataFrame(valid_costs, columns=["항목", "금액", "비고"])
                    df_display_costs["금액"] = pd.to_numeric(df_display_costs["금액"], errors='coerce').fillna(0).astype(int)
                    st.dataframe(
                        df_display_costs.style.format({"금액": "{:,.0f}"}).set_properties(**{'text-align':'right'}, subset=['금액']).set_properties(**{'text-align':'left'}, subset=['항목','비고']),
                        use_container_width=True,
                        hide_index=True
                    )
                else: st.info("유효한 비용 항목 없음.")
            else: st.info("계산된 비용 항목 없음.")
            st.write("")

            special_notes = st.session_state.get('special_notes')
            if special_notes and special_notes.strip():
                st.subheader("고객요구사항") # 이모티콘 제거
                st.info(special_notes)

            st.subheader("이사 정보 요약 (텍스트)") # 이모티콘 제거
            summary_display_possible = bool(final_selected_vehicle_for_calc) and not has_cost_error

            if summary_display_possible:
                try:
                    customer_name_summary = st.session_state.get('customer_name', '')
                    phone_summary = st.session_state.get('customer_phone', '')
                    email_summary = st.session_state.get('customer_email', '')
                    from_addr_summary = st.session_state.get('from_location', '정보 없음')
                    to_addr_summary = st.session_state.get('to_location', '정보 없음')
                    is_storage_move_summary = st.session_state.get('is_storage_move', False)
                    storage_details_text = ""
                    if is_storage_move_summary:
                        storage_type = st.session_state.get('storage_type', '정보 없음').split(" ")[0] # 이모티콘 제거
                        storage_electric_text = "(전기사용)" if st.session_state.get('storage_use_electricity', False) else ""
                        storage_details_text = f"{storage_type} {storage_electric_text}".strip()

                    vehicle_type_summary = final_selected_vehicle_for_calc
                    vehicle_tonnage_summary = ""
                    if isinstance(vehicle_type_summary, str):
                        match_summary = re.search(r'(\d+(\.\d+)?)', vehicle_type_summary)
                        vehicle_tonnage_summary = match_summary.group(1).strip() if match_summary else vehicle_type_summary.replace("톤","").strip()

                    p_info_summary = personnel_info_display
                    men_summary = p_info_summary.get('final_men', 0)
                    women_summary = p_info_summary.get('final_women', 0)
                    ppl_summary = f"{men_summary}명" + (f"+{women_summary}명" if women_summary > 0 else "")

                    from_method_full = get_method_full_name('from_method')
                    to_method_full = get_method_full_name('to_method')
                    via_method_full = get_method_full_name('via_point_method')

                    deposit_for_summary = int(st.session_state.get("deposit_amount", 0))
                    calculated_total_for_summary = int(total_cost_display) if isinstance(total_cost_display,(int,float)) else 0
                    remaining_for_summary = calculated_total_for_summary - deposit_for_summary

                    payment_option_texts = []
                    if st.session_state.get("issue_tax_invoice", False): payment_option_texts.append("세금계산서 발행 요청")
                    if st.session_state.get("card_payment", False): payment_option_texts.append("카드 결제 예정")
                    payment_options_summary = " / ".join(payment_option_texts) if payment_option_texts else ""
                    
                    b_name_summary, move_t_summary_for_basket = "포장 자재", st.session_state.get('base_move_type', '') # 이모티콘 없는 키 사용 가정
                    move_t_summary_for_basket = move_t_summary_for_basket.split(" ")[0] # "가정 이사" -> "가정"
                    
                    # data.py item_definitions의 키도 "가정 이사" 등으로 이모티콘 없이 가정
                    # 포장 자재 섹션 이름도 data.py에 "포장 자재"로 정의되어 있다고 가정
                    q_b_s, q_mb_s, q_book_s = 0, 0, 0

                    current_move_type_no_emoji_for_basket = st.session_state.get('base_move_type').split(" ")[0] # "가정"
                    basket_section_name_no_emoji = "포장 자재" # data.py 에 정의된 "포장 자재 📦" 와 매칭되도록 수정 필요

                    # data.py의 item_definitions 키와 basket_section_name 이 이모티콘 없이 정의되어 있다고 가정하고 수정
                    # 또는 data.py 자체를 수정하거나, 여기서 이모티콘을 제거한 키로 매핑
                    # 현재 코드는 data.py의 키가 "가정 이사 🏠", "포장 자재 📦" 등으로 되어있을 가능성이 높음
                    # 여기서는 data.py 키를 그대로 사용하고, st.session_state.get 키 생성 시 이모티콘 포함된 move_type 사용
                    
                    original_move_type_key = st.session_state.get('base_move_type') # "가정 이사 🏠"
                    original_basket_section_key = "포장 자재 📦" # data.py에 정의된 실제 키

                    if original_move_type_key and hasattr(data, 'items') and hasattr(data, 'item_definitions'):
                        if original_basket_section_key in data.item_definitions.get(original_move_type_key, {}):
                             try:
                                q_b_s = int(st.session_state.get(f"qty_{original_move_type_key}_{original_basket_section_key}_바구니", 0) or 0)
                                q_mb_s_key1 = f"qty_{original_move_type_key}_{original_basket_section_key}_중박스"
                                q_mb_s_key2 = f"qty_{original_move_type_key}_{original_basket_section_key}_중자바구니"
                                q_mb_s = int(st.session_state.get(q_mb_s_key1, st.session_state.get(q_mb_s_key2, 0)) or 0)
                                q_book_s = int(st.session_state.get(f"qty_{original_move_type_key}_{original_basket_section_key}_책바구니", 0) or 0)
                             except Exception as e_basket_sum:
                                print(f"요약 바구니 오류: {e_basket_sum}")


                    bask_display_parts = []
                    if q_b_s > 0: bask_display_parts.append(f"바구니 {q_b_s}개")
                    if q_mb_s > 0: bask_display_parts.append(f"중박스 {q_mb_s}개")
                    if q_book_s > 0: bask_display_parts.append(f"책바구니 {q_book_s}개")
                    bask_summary_str = ", ".join(bask_display_parts) if bask_display_parts else "" # 정보 없을 시 빈 문자열

                    note_summary = st.session_state.get('special_notes', '')
                    
                    summary_lines = []

                    moving_date_val_for_summary = st.session_state.get('moving_date')
                    formatted_moving_date_summary = ""
                    if isinstance(moving_date_val_for_summary, date):
                        formatted_moving_date_summary = moving_date_val_for_summary.strftime('%m-%d')
                    elif isinstance(moving_date_val_for_summary, str): # YYYY-MM-DD 형식의 문자열일 경우
                        try:
                            dt_obj = datetime.strptime(moving_date_val_for_summary, '%Y-%m-%d')
                            formatted_moving_date_summary = dt_obj.strftime('%m-%d')
                        except ValueError:
                            formatted_moving_date_summary = moving_date_val_for_summary # 형식 안맞으면 그대로 표시
                    else:
                        formatted_moving_date_summary = "정보 없음"
                    summary_lines.append(formatted_moving_date_summary)

                    address_flow_parts_summary = []
                    address_flow_parts_summary.append(from_addr_summary if from_addr_summary else "출발지 정보 없음")
                    
                    # 경유지 및 보관 정보는 여기서 제외 (아래 상세 주소 목록에만 표시)
                    # if st.session_state.get('has_via_point', False):
                    #     via_location_summary_flow = st.session_state.get('via_point_location', '경유지 정보 없음')
                    #     address_flow_parts_summary.append(f"{via_location_summary_flow}")
                    # if is_storage_move_summary and storage_details_text:
                    #     address_flow_parts_summary.append(f"{storage_details_text}")
                    
                    address_flow_parts_summary.append(to_addr_summary if to_addr_summary else "도착지 정보 없음")
                    vehicle_display_text_summary = f"/ {vehicle_tonnage_summary if vehicle_tonnage_summary else vehicle_type_summary}"
                    summary_lines.append(" - ".join(address_flow_parts_summary) + vehicle_display_text_summary)
                    summary_lines.append("") # 빈 줄

                    if customer_name_summary: summary_lines.append(customer_name_summary)
                    if phone_summary and phone_summary != '-': summary_lines.append(phone_summary)
                    if email_summary and email_summary != '-': summary_lines.append(email_summary)
                    summary_lines.append("")

                    summary_lines.append("출발지 주소:")
                    summary_lines.append(f"{from_addr_summary if from_addr_summary else '정보 없음'}")
                    if st.session_state.get('has_via_point', False):
                        via_location_detail_summary = st.session_state.get('via_point_location', '정보 없음')
                        summary_lines.append("경유지 주소:")
                        summary_lines.append(f"{via_location_detail_summary}")
                    if is_storage_move_summary and storage_details_text:
                        summary_lines.append("보관 정보:")
                        summary_lines.append(f"{storage_details_text}")
                    summary_lines.append("도착지 주소:")
                    summary_lines.append(f"{to_addr_summary if to_addr_summary else '정보 없음'}")
                    summary_lines.append("")

                    summary_lines.append(f"{vehicle_tonnage_summary if vehicle_tonnage_summary else vehicle_type_summary} / {ppl_summary}")
                    summary_lines.append("")
                    summary_lines.append(f"출발지 작업: {from_method_full}")
                    if st.session_state.get('has_via_point', False):
                        summary_lines.append(f"경유지 작업: {via_method_full}")
                    summary_lines.append(f"도착지 작업: {to_method_full}")
                    summary_lines.append("")
                    summary_lines.append(f"계약금 {deposit_for_summary:,.0f}원 / 잔금 {remaining_for_summary:,.0f}원")
                    if payment_options_summary:
                        summary_lines.append(f"  ({payment_options_summary})")
                    summary_lines.append("")

                    # 비용 상세 통합 표시
                    cost_breakdown_parts = []
                    vat_amount_str = ""
                    card_fee_amount_str = ""
                    
                    # 부가세와 카드 수수료를 먼저 찾아서 저장하고, 나머지 비용 합산
                    other_costs_sum = 0
                    other_cost_details_for_sum = []

                    if isinstance(cost_items_display, list):
                        for item_name_disp, item_cost_disp, _ in cost_items_display:
                            item_name_str = str(item_name_disp)
                            cost_val = int(item_cost_disp or 0)

                            if "부가세" in item_name_str:
                                vat_amount_str = f"부가세 ({item_name_str.split('(')[-1].split(')')[0]}): {cost_val:,}"
                            elif "카드결제 수수료" in item_name_str:
                                card_fee_amount_str = f"카드수수료 ({item_name_str.split('(')[-1].split(')')[0]}): {cost_val:,}"
                            elif cost_val != 0 : # 0원이 아닌 다른 비용들
                                other_costs_sum += cost_val
                                # 이사비, 추가 인력 등 개별 항목 표시 원하면 아래 주석 해제 후 조건 추가
                                if item_name_str == "기본 운임":
                                     other_cost_details_for_sum.append(f"이사비: {cost_val:,}")
                                elif item_name_str == "추가 인력":
                                     other_cost_details_for_sum.append(f"추가 인력: {cost_val:,}")
                                # 다른 주요 비용 항목들도 필요시 추가
                                # else:
                                #    other_cost_details_for_sum.append(f"{item_name_str}: {cost_val:,}")


                    cost_summary_line = f"총 {calculated_total_for_summary:,.0f}원"
                    
                    # other_cost_details_for_sum 이 비어있으면, 합산된 other_costs_sum을 "기타비용" 등으로 표시하거나,
                    # 또는 개별 항목을 모두 표시하도록 로직 수정 가능. 현재는 이사비와 추가인력만 개별 표시 시도.
                    # 모든 other_costs 를 합쳐서 하나의 값으로만 표현하려면:
                    # if other_costs_sum > 0: cost_breakdown_parts.append(f"총괄비용: {other_costs_sum:,}")
                    
                    # 여기서는 요청된 "이사비: 금액 + 추가 인력: 금액" 형태를 우선
                    if other_cost_details_for_sum:
                        cost_summary_line += f" ( {' + '.join(other_cost_details_for_sum)}"
                        # 만약 other_costs_sum 이 other_cost_details_for_sum의 합계와 다르면 (즉, 표시 안된 다른 항목이 있으면)
                        # current_detailed_sum = sum(int(re.sub(r'[^\d]', '', part.split(':')[-1])) for part in other_cost_details_for_sum)
                        # if other_costs_sum != current_detailed_sum and other_costs_sum - current_detailed_sum != 0 :
                        #    cost_summary_line += f" + 기타: {other_costs_sum - current_detailed_sum:,}"
                        cost_summary_line += ")"


                    if vat_amount_str: cost_summary_line += f" + {vat_amount_str}"
                    if card_fee_amount_str: cost_summary_line += f" + {card_fee_amount_str}" # 카드 수수료가 있다면 추가
                    
                    summary_lines.append(cost_summary_line)
                    summary_lines.append("")
                    
                    if bask_summary_str: # 빈 문자열이 아닐 때만 추가
                         summary_lines.append(f"포장자재: {bask_summary_str}") # 이모티콘 제거
                         summary_lines.append("")
                    
                    if note_summary and note_summary.strip() and note_summary != '-':
                        summary_lines.append("고객요구사항:") # 이모티콘 제거
                        summary_lines.extend([f"  - {note_line.strip()}" for note_line in note_summary.strip().replace('\r\n', '\n').split('\n') if note_line.strip()])

                    st.text_area("요약 정보", "\n".join(summary_lines), height=400, key="summary_text_area_readonly_tab3", disabled=True)

                except Exception as e_summary_direct:
                    st.error(f"요약 정보 생성 중 오류: {e_summary_direct}"); traceback.print_exc() # 이모티콘 제거
            elif not final_selected_vehicle_for_calc:
                if not validation_messages or not any("차량 종류가 선택되지 않았습니다" in msg for msg in validation_messages):
                    st.info("견적 계산용 차량 미선택으로 요약 정보 표시 불가.") # 이모티콘 제거
            st.divider()
        except Exception as calc_err_outer_display:
            st.error(f"최종 견적 표시 중 외부 오류 발생: {calc_err_outer_display}")
            traceback.print_exc()

    st.subheader("견적서 생성, 발송 및 다운로드") # 이모티콘 제거

    can_generate_anything = bool(final_selected_vehicle_for_calc) and \
                          not has_cost_error and \
                          st.session_state.get("calculated_cost_items_for_pdf") and \
                          st.session_state.get("total_cost_for_pdf", 0) > 0
    actions_disabled = not can_generate_anything

    with st.container(border=True):
        st.markdown("**고객 전달용 파일**")
        col_pdf_btn, col_pdf_img_btn = st.columns(2)

        pdf_args_common = {
            "state_data": st.session_state.to_dict(),
            "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
            "total_cost": st.session_state.get("total_cost_for_pdf", 0),
            "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
        }
        pdf_generation_possible = hasattr(pdf_generator, "generate_pdf") and can_generate_anything
        pdf_to_image_possible = hasattr(pdf_generator, "generate_quote_image_from_pdf") and pdf_generation_possible

        with col_pdf_btn:
            if st.button("고객용 PDF 생성", key="generate_customer_pdf_btn", disabled=actions_disabled or not pdf_generation_possible): # 이모티콘 제거
                with st.spinner("고객용 PDF 생성 중..."):
                    pdf_data = pdf_generator.generate_pdf(**pdf_args_common)
                if pdf_data:
                    st.session_state['customer_final_pdf_data'] = pdf_data
                    st.success("고객용 PDF 생성 완료!") # 이모티콘 제거
                    if pdf_to_image_possible:
                        with st.spinner("PDF 기반 고객용 이미지 생성 중..."):
                            poppler_bin_path = None
                            img_data_from_pdf = pdf_generator.generate_quote_image_from_pdf(pdf_data, poppler_path=poppler_bin_path)
                        if img_data_from_pdf:
                            st.session_state['customer_pdf_image_data'] = img_data_from_pdf
                            st.success("PDF 기반 고객용 이미지 생성 완료!") # 이모티콘 제거
                        else:
                            st.warning("PDF 기반 고객용 이미지 생성 실패. (PDF는 생성됨)") # 이모티콘 제거
                            if 'customer_pdf_image_data' in st.session_state: del st.session_state['customer_pdf_image_data']
                else:
                    st.error("고객용 PDF 생성 실패.") # 이모티콘 제거
                    if 'customer_final_pdf_data' in st.session_state: del st.session_state['customer_final_pdf_data']
                    if 'customer_pdf_image_data' in st.session_state: del st.session_state['customer_pdf_image_data']


            if st.session_state.get('customer_final_pdf_data'):
                fname_pdf_cust = f"견적서_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.pdf"
                st.download_button(
                    label="고객용 PDF 다운로드", # 이모티콘 제거
                    data=st.session_state['customer_final_pdf_data'],
                    file_name=fname_pdf_cust, mime="application/pdf",
                    key='dl_btn_customer_final_pdf', disabled=actions_disabled
                )
            elif pdf_generation_possible and not actions_disabled:
                st.caption("PDF 생성 버튼을 눌러 준비하세요.")

        with col_pdf_img_btn:
            if st.session_state.get('customer_pdf_image_data'):
                fname_pdf_img_cust = f"견적서_PDF이미지_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.png"
                st.download_button(
                    label="고객용 견적서 이미지 다운로드 (PDF 기반)", # 이모티콘 제거
                    data=st.session_state['customer_pdf_image_data'],
                    file_name=fname_pdf_img_cust, mime="image/png",
                    key='dl_btn_customer_pdf_image', disabled=actions_disabled
                )
            elif pdf_to_image_possible and st.session_state.get('customer_final_pdf_data') and not actions_disabled :
                st.caption("PDF 생성 시 함께 생성됩니다.")
            elif pdf_to_image_possible and not actions_disabled :
                 st.caption("고객용 PDF를 먼저 생성하세요.")

        if not pdf_generation_possible and not actions_disabled:
             st.caption("고객용 파일 생성 불가 (견적 내용 또는 PDF 모듈 확인)")
        elif actions_disabled:
             st.caption("견적 내용을 먼저 완성해주세요.")
    st.divider()

    with st.container(border=True):
        st.markdown("**내부 검토용 파일**")
        col_internal_img_btn, col_internal_excel_btn = st.columns(2)

        company_form_image_args = {
            "state_data": st.session_state.to_dict(),
            "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
            "total_cost_overall": st.session_state.get("total_cost_for_pdf", 0),
            "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
        }
        company_image_possible = hasattr(image_generator, "create_quote_image") and can_generate_anything

        with col_internal_img_btn:
            if st.button("내부 검토용 양식 이미지 생성", key="generate_internal_form_image_btn", disabled=actions_disabled or not company_image_possible): # 이모티콘 제거
                with st.spinner("내부 검토용 양식 이미지 생성 중..."):
                    internal_image_data = image_generator.create_quote_image(**company_form_image_args)
                if internal_image_data:
                    st.session_state['internal_form_image_data'] = internal_image_data
                    st.success("내부 검토용 양식 이미지 생성 완료!") # 이모티콘 제거
                else:
                    st.error("내부 검토용 양식 이미지 생성 실패.") # 이모티콘 제거
                    if 'internal_form_image_data' in st.session_state: del st.session_state['internal_form_image_data']

            if st.session_state.get('internal_form_image_data'):
                fname_internal_img = f"내부양식_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.png"
                st.download_button(
                    label="내부 검토용 양식 이미지 다운로드", # 이모티콘 제거
                    data=st.session_state['internal_form_image_data'],
                    file_name=fname_internal_img, mime="image/png",
                    key='dl_btn_internal_form_image', disabled=actions_disabled
                )
            elif company_image_possible and not actions_disabled:
                st.caption("생성 버튼을 눌러 내부 검토용 이미지를 준비하세요.")

        with col_internal_excel_btn:
            excel_possible = hasattr(excel_filler, "fill_final_excel_template") and can_generate_anything
            if st.button("내부용 Excel 생성", key="generate_internal_excel_tab3", disabled=actions_disabled or not excel_possible): # 이모티콘 제거
                if excel_possible:
                    _current_state = st.session_state.to_dict()
                    _total_cost_excel, _cost_items_excel, _personnel_info_excel = calculations.calculate_total_moving_cost(_current_state)
                    with st.spinner("내부용 Excel 파일 생성 중..."):
                        filled_excel_data_dl = excel_filler.fill_final_excel_template(
                            _current_state, _cost_items_excel, _total_cost_excel, _personnel_info_excel
                        )
                    if filled_excel_data_dl:
                        st.session_state['internal_excel_data_for_download'] = filled_excel_data_dl
                        st.success("내부용 Excel 생성 완료!") # 이모티콘 제거
                    else:
                        st.error("내부용 Excel 파일 생성 실패.") # 이모티콘 제거
                        if 'internal_excel_data_for_download' in st.session_state: del st.session_state['internal_excel_data_for_download']

            if st.session_state.get('internal_excel_data_for_download') and excel_possible:
                fname_excel_dl = f"내부견적_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.xlsx"
                st.download_button(label="Excel 다운로드 (내부용)", data=st.session_state['internal_excel_data_for_download'], file_name=fname_excel_dl, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='dl_btn_excel_internal_section_tab3', disabled=actions_disabled) # 이모티콘 제거
            elif excel_possible and not actions_disabled: st.caption("생성 버튼을 눌러 내부용 Excel 파일을 준비하세요.")

        if not company_image_possible and not excel_possible and not actions_disabled:
             st.caption("내부 검토용 파일 생성 불가 (견적 내용 또는 관련 모듈 확인)")
        elif actions_disabled:
             st.caption("견적 내용을 먼저 완성해주세요.")
    st.divider()

    with st.container(border=True):
        st.markdown("**이메일 발송 (고객용 PDF 첨부)**")
        email_recipient_exists = bool(st.session_state.get("customer_email", "").strip())
        email_modules_ok = hasattr(email_utils, "send_quote_email") and hasattr(pdf_generator, "generate_pdf")
        email_possible = email_modules_ok and can_generate_anything and email_recipient_exists

        if st.button("이메일 발송", key="email_send_button_main_tab3", disabled=actions_disabled or not email_possible): # 이모티콘 제거
            recipient_email_send = st.session_state.get("customer_email")
            customer_name_send = st.session_state.get("customer_name", "고객")

            pdf_email_bytes_send = st.session_state.get('customer_final_pdf_data')
            if not pdf_email_bytes_send and pdf_generation_possible:
                with st.spinner("이메일 첨부용 PDF 생성 중..."):
                    pdf_email_bytes_send = pdf_generator.generate_pdf(**pdf_args_common)
                if pdf_email_bytes_send:
                     st.session_state['customer_final_pdf_data'] = pdf_email_bytes_send

            if pdf_email_bytes_send:
                subject_send = f"[{customer_name_send}님] 이삿날 이사 견적서입니다."
                body_send = f"{customer_name_send}님,\n\n요청하신 이사 견적서를 첨부 파일로 보내드립니다.\n\n감사합니다.\n이삿날 드림"
                pdf_filename_send = f"견적서_{customer_name_send}_{utils.get_current_kst_time_str('%Y%m%d')}.pdf"

                with st.spinner(f"{recipient_email_send}(으)로 이메일 발송 중..."):
                    email_sent_status = email_utils.send_quote_email(recipient_email_send, subject_send, body_send, pdf_email_bytes_send, pdf_filename_send)

                if email_sent_status: st.success(f"이메일 발송 성공!") # 이모티콘 제거
                else: st.error("이메일 발송 실패.") # 이모티콘 제거
            else:
                st.error("첨부할 PDF 생성에 실패하여 이메일을 발송할 수 없습니다.") # 이모티콘 제거
        elif actions_disabled:
            st.caption("견적 내용을 먼저 완성해주세요.")
        elif not email_recipient_exists:
            st.caption("고객 이메일 주소가 입력되지 않았습니다.")
        elif not email_modules_ok:
            st.caption("이메일 또는 PDF 생성 모듈에 문제가 있습니다.")
        elif not can_generate_anything :
            st.caption("견적 내용이 충분하지 않아 이메일을 발송할 수 없습니다.")
