# ui_tab3.py (수정된 전체 코드)
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
    import pdf_generator # PDF 생성 및 PDF->이미지 변환
    import excel_filler
    import email_utils
    import callbacks
    from state_manager import MOVE_TYPE_OPTIONS
    import image_generator # 회사 양식 기반 이미지 생성
except ImportError as e:
    st.error(f"UI Tab 3: 필수 모듈 로딩 실패 - {e}")
    # ... (기존 오류 처리 로직 유지) ...
    if hasattr(e, "name"):
        if e.name == "email_utils": st.warning("email_utils.py 로드 실패. 이메일 발송 비활성화.")
        elif e.name == "pdf_generator": st.warning("pdf_generator.py 로드 실패. PDF 관련 기능 제한 가능.")
        elif e.name == "image_generator": st.error("image_generator.py 로드 실패! 회사 양식 이미지 생성 비활성화.")
    if "MOVE_TYPE_OPTIONS" not in globals():
        MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
    if not all(module_name in globals() for module_name in ["data", "utils", "calculations", "callbacks", "state_manager", "image_generator", "pdf_generator"]):
        st.error("UI Tab 3: 핵심 데이터/유틸리티 모듈 로딩 실패.")
except Exception as e:
    st.error(f"UI Tab 3: 모듈 로딩 중 오류 - {e}")
    traceback.print_exc()
    if "MOVE_TYPE_OPTIONS" not in globals():
        MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]
    st.stop()


def get_validation_warnings(state):
    # ... (기존 유효성 검사 로직 유지) ...
    warnings = []
    try:
        kst = pytz.timezone("Asia/Seoul")
        # quote_date = datetime.now(kst).date() # 사용되지 않으므로 주석 처리 또는 삭제 가능
    except Exception:
        # quote_date = datetime.now().date() # 사용되지 않으므로 주석 처리 또는 삭제 가능
        pass

    moving_date_input = state.get('moving_date')

    if isinstance(moving_date_input, date):
        pass
    elif moving_date_input is None:
        warnings.append("이사 예정일이 설정되지 않았습니다. 날짜를 선택해주세요.")
    else:
        warnings.append(f"이사 예정일의 형식이 올바르지 않습니다: {moving_date_input}. 날짜를 다시 선택해주세요.")

    from_floor = str(state.get('from_floor', '')).strip()
    to_floor = str(state.get('to_floor', '')).strip()
    if not from_floor:
        warnings.append("출발지 층수 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")
    if not to_floor:
        warnings.append("도착지 층수 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")

    final_selected_vehicle_for_calc = state.get('final_selected_vehicle')
    if not final_selected_vehicle_for_calc:
        warnings.append("견적 계산용 차량 종류가 선택되지 않았습니다. '차량 선택' 섹션에서 차량을 선택해주세요.")

    to_location = str(state.get('to_location', '')).strip()
    if not to_location:
        warnings.append("도착지 주소 정보가 입력되지 않았습니다. '고객 정보' 탭에서 입력해주세요.")

    if final_selected_vehicle_for_calc: # 차량이 선택된 경우에만 투입 차량 대수 확인
        dispatched_1t = state.get('dispatched_1t', 0)
        dispatched_2_5t = state.get('dispatched_2_5t', 0)
        dispatched_3_5t = state.get('dispatched_3_5t', 0)
        dispatched_5t = state.get('dispatched_5t', 0)
        # 각 차량 대수가 None일 경우 0으로 처리하여 합산
        total_dispatched_trucks = (dispatched_1t or 0) + \
                                  (dispatched_2_5t or 0) + \
                                  (dispatched_3_5t or 0) + \
                                  (dispatched_5t or 0)
        if total_dispatched_trucks == 0:
            warnings.append("실제 투입 차량 대수가 입력되지 않았습니다. '실제 투입 차량' 섹션에서 각 톤수별 차량 대수를 입력해주세요.")
    return warnings

def render_tab3():
    # ... (render_tab3 함수의 앞부분 UI 및 로직은 이전과 거의 동일하게 유지) ...
    st.header("💰 계산 및 옵션 ")
    update_basket_quantities_callback = getattr(callbacks, "update_basket_quantities", None)
    sync_move_type_callback = getattr(callbacks, "sync_move_type", None)
    handle_item_update_callback = getattr(callbacks, "handle_item_update", None)

    if not callable(update_basket_quantities_callback) or not callable(sync_move_type_callback):
        st.error("UI Tab 3: 콜백 함수 로드 실패.")
        # return # 중요한 콜백이 없으면 여기서 중단할 수 있습니다.

    st.subheader("🏢 이사 유형 ")
    current_move_type = st.session_state.get("base_move_type", MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠")
    current_index_tab3 = 0
    if MOVE_TYPE_OPTIONS:
        try:
            current_index_tab3 = MOVE_TYPE_OPTIONS.index(current_move_type)
        except (ValueError, TypeError): # 현재 값이 옵션에 없거나 잘못된 경우
            current_index_tab3 = 0 # 기본값으로 설정
            st.session_state.base_move_type = MOVE_TYPE_OPTIONS[0] # 세션 상태도 기본값으로 동기화
            if 'base_move_type_widget_tab1' in st.session_state: # 다른 탭의 위젯도 동기화
                 st.session_state.base_move_type_widget_tab1 = MOVE_TYPE_OPTIONS[0]
            if callable(handle_item_update_callback): # 물품 관련 정보 업데이트
                 handle_item_update_callback()
    else:
        st.error("이사 유형 옵션을 불러올 수 없습니다."); return

    st.radio(
        "기본 이사 유형:", options=MOVE_TYPE_OPTIONS, index=current_index_tab3, horizontal=True,
        key="base_move_type_widget_tab3", on_change=sync_move_type_callback, args=("base_move_type_widget_tab3",)
    )
    st.divider()

    with st.container(border=True):
        st.subheader("🚚 차량 선택 (견적 계산용)")
        col_v1_widget, col_v2_widget = st.columns([1, 2])
        with col_v1_widget:
            st.radio("차량 선택 방식:", ["자동 추천 차량 사용", "수동으로 차량 선택"], key="vehicle_select_radio", on_change=update_basket_quantities_callback)
        with col_v2_widget:
            current_move_type_widget = st.session_state.get('base_move_type')
            vehicle_prices_options_widget, available_trucks_widget = {}, []
            if current_move_type_widget and hasattr(data, 'vehicle_prices') and isinstance(data.vehicle_prices, dict):
                vehicle_prices_options_widget = data.vehicle_prices.get(current_move_type_widget, {})
            if vehicle_prices_options_widget and hasattr(data, 'vehicle_specs') and isinstance(data.vehicle_specs, dict):
                # 차량 제원(capacity) 기준으로 정렬
                available_trucks_widget = sorted(
                    [truck for truck in vehicle_prices_options_widget.keys() if truck in data.vehicle_specs],
                    key=lambda x: data.vehicle_specs.get(x, {}).get("capacity", 0)
                )

            use_auto_widget = st.session_state.get('vehicle_select_radio') == "자동 추천 차량 사용"
            recommended_vehicle_auto_from_state = st.session_state.get('recommended_vehicle_auto')
            final_vehicle_from_state = st.session_state.get('final_selected_vehicle') # 계산 콜백을 통해 업데이트된 값
            current_total_volume = st.session_state.get("total_volume", 0.0)
            current_total_weight = st.session_state.get("total_weight", 0.0)

            if use_auto_widget:
                # final_selected_vehicle은 자동 추천 또는 수동 선택의 최종 결과를 반영
                if final_vehicle_from_state and final_vehicle_from_state in available_trucks_widget:
                    st.success(f"✅ 자동 선택됨: **{final_vehicle_from_state}**")
                    spec = data.vehicle_specs.get(final_vehicle_from_state) if hasattr(data, "vehicle_specs") else None
                    if spec:
                        st.caption(f"선택차량 최대 용량: {spec.get('capacity', 'N/A')}m³, {spec.get('weight_capacity', 'N/A'):,}kg")
                        st.caption(f"현재 이사짐 예상: {current_total_volume:.2f}m³, {current_total_weight:.2f}kg")
                else: # 자동 추천이 불가능하거나, 추천된 차량이 현재 유형에 없는 경우
                    error_msg = "⚠️ 자동 추천 불가: "
                    if recommended_vehicle_auto_from_state and "초과" in recommended_vehicle_auto_from_state:
                        error_msg += f"물량 초과({recommended_vehicle_auto_from_state}). 수동 선택 필요."
                    elif recommended_vehicle_auto_from_state and recommended_vehicle_auto_from_state not in available_trucks_widget : # 추천 차량이 현재 이사 유형에 없음
                        error_msg += f"추천 차량({recommended_vehicle_auto_from_state})은 현재 이사 유형에 없음. 수동 선택 필요."
                    elif current_total_volume > 0 or current_total_weight > 0 : # 물품은 있으나 적합 차량 없음
                        error_msg += "적합 차량 없음. 수동 선택 필요."
                    else: # 물품 미선택 또는 정보 부족
                        error_msg += "물품 미선택 또는 정보 부족."
                    st.error(error_msg)
                    # 수동 선택 옵션 제공 (자동 추천 불가 시)
                    if not available_trucks_widget:
                        st.error("❌ 현재 이사 유형에 선택 가능한 차량 정보가 없습니다.")
                    else:
                        current_manual_selection_widget = st.session_state.get("manual_vehicle_select_value")
                        try: # 현재 수동 선택값이 옵션에 있으면 해당 인덱스, 없으면 0
                            current_index_widget = available_trucks_widget.index(current_manual_selection_widget) if current_manual_selection_widget in available_trucks_widget else 0
                        except ValueError: # 혹시 모를 오류 방지
                             current_index_widget = 0
                        if not current_manual_selection_widget and available_trucks_widget: # 수동 선택값이 없으면 첫번째 차량으로 초기화
                             st.session_state.manual_vehicle_select_value = available_trucks_widget[0] # 콜백 호출 안 함 (UI 초기화 단계)
                        st.selectbox("수동으로 차량 선택:", available_trucks_widget, index=current_index_widget, key="manual_vehicle_select_value", on_change=update_basket_quantities_callback)
                        if final_vehicle_from_state and final_vehicle_from_state in available_trucks_widget: # 수동 선택 결과 표시
                             st.info(f"ℹ️ 수동 선택됨: **{final_vehicle_from_state}**")
            else: # "수동으로 차량 선택" 라디오 버튼 선택 시
                if not available_trucks_widget:
                    st.error("❌ 현재 이사 유형에 선택 가능한 차량 정보가 없습니다.")
                else:
                    current_manual_selection_widget = st.session_state.get("manual_vehicle_select_value")
                    try:
                        current_index_widget = available_trucks_widget.index(current_manual_selection_widget) if current_manual_selection_widget in available_trucks_widget else 0
                    except ValueError:
                        current_index_widget = 0
                    if not current_manual_selection_widget and available_trucks_widget:
                        st.session_state.manual_vehicle_select_value = available_trucks_widget[0] # 콜백 호출 안 함 (UI 초기화 단계)
                    st.selectbox("차량 직접 선택:", available_trucks_widget, index=current_index_widget, key="manual_vehicle_select_value", on_change=update_basket_quantities_callback)
                    if final_vehicle_from_state and final_vehicle_from_state in available_trucks_widget:
                        st.info(f"ℹ️ 수동 선택됨: **{final_vehicle_from_state}**")
                        spec_manual = data.vehicle_specs.get(final_vehicle_from_state) if hasattr(data, "vehicle_specs") else None
                        if spec_manual: # 선택된 차량의 제원 표시
                            st.caption(f"선택차량 최대 용량: {spec_manual.get('capacity', 'N/A')}m³, {spec_manual.get('weight_capacity', 'N/A'):,}kg")
                            st.caption(f"현재 이사짐 예상: {current_total_volume:.2f}m³, {current_total_weight:.2f}kg")
    st.divider()

    with st.container(border=True):
        st.subheader("🛠️ 작업 조건 및 추가 옵션")
        sky_from = (st.session_state.get("from_method") == "스카이 🏗️")
        sky_to = (st.session_state.get("to_method") == "스카이 🏗️")
        if sky_from or sky_to:
            st.warning("스카이 작업 선택됨 - 시간 입력 필요", icon="🏗️")
            cols_sky = st.columns(2)
            if sky_from: cols_sky[0].number_input("출발 스카이 시간(h)", min_value=1, step=1, key="sky_hours_from")
            if sky_to: cols_sky[1].number_input("도착 스카이 시간(h)", min_value=1, step=1, key="sky_hours_final")
            st.write("") # 간격 추가
        col_add1, col_add2 = st.columns(2)
        col_add1.number_input("추가 남성 인원 👨", min_value=0, step=1, key="add_men")
        col_add2.number_input("추가 여성 인원 👩", min_value=0, step=1, key="add_women")
        st.write("") # 간격 추가
        st.subheader("🚚 실제 투입 차량 (견적서 및 내부 기록용)")
        dispatched_cols = st.columns(4)
        dispatched_cols[0].number_input("1톤", min_value=0, step=1, key="dispatched_1t")
        dispatched_cols[1].number_input("2.5톤", min_value=0, step=1, key="dispatched_2_5t")
        dispatched_cols[2].number_input("3.5톤", min_value=0, step=1, key="dispatched_3_5t")
        dispatched_cols[3].number_input("5톤", min_value=0, step=1, key="dispatched_5t")
        st.caption("실제 현장에 투입될 차량 대수를 입력합니다.")
        st.write("") # 간격 추가

        # 기본 여성 인원 제외 옵션
        show_remove_housewife_option = False
        base_housewife_count_for_option = 0
        discount_amount_for_option = 0
        current_move_type_for_option = st.session_state.get("base_move_type")
        final_vehicle_for_option_display = st.session_state.get("final_selected_vehicle") # 콜백을 통해 업데이트된 최종 차량

        if current_move_type_for_option == "가정 이사 🏠" and \
           final_vehicle_for_option_display and \
           hasattr(data, "vehicle_prices") and \
           isinstance(data.vehicle_prices.get(current_move_type_for_option), dict) and \
           final_vehicle_for_option_display in data.vehicle_prices[current_move_type_for_option]:
            vehicle_details = data.vehicle_prices[current_move_type_for_option][final_vehicle_for_option_display]
            base_housewife_count_for_option = vehicle_details.get("housewife", 0)
            if base_housewife_count_for_option > 0: # 기본 여성 인원이 있을 때만 옵션 표시
                show_remove_housewife_option = True
                additional_person_cost_for_option = getattr(data, "ADDITIONAL_PERSON_COST", 200000) # data.py에서 가져옴
                discount_amount_for_option = additional_person_cost_for_option * base_housewife_count_for_option

        if show_remove_housewife_option:
            st.checkbox(
                f"기본 여성({base_housewife_count_for_option}명) 제외 (비용 할인: -{discount_amount_for_option:,.0f}원)",
                key="remove_base_housewife"
            )
        else: # 옵션 표시 조건이 아닐 경우, 해당 session_state 키를 False로 확실히 설정 (선택 유지 방지)
            if "remove_base_housewife" in st.session_state: # 키가 존재하면
                st.session_state.remove_base_housewife = False

        # 폐기물 처리 옵션
        col_waste1, col_waste2 = st.columns([1,2])
        col_waste1.checkbox("폐기물 처리 필요 🗑️", key="has_waste_check")
        if st.session_state.get("has_waste_check"): # 폐기물 처리 선택 시
            waste_cost_per_ton = getattr(data, "WASTE_DISPOSAL_COST_PER_TON", 0) # data.py에서 가져옴
            waste_cost_display = waste_cost_per_ton if isinstance(waste_cost_per_ton, (int, float)) else 0
            col_waste2.number_input("폐기물 양 (톤)", min_value=0.5, max_value=10.0, step=0.5, key="waste_tons_input", format="%.1f")
            if waste_cost_display > 0: col_waste2.caption(f"💡 1톤당 {waste_cost_display:,}원 추가 비용 발생")

        # 날짜 유형 선택
        st.write("📅 **날짜 유형 선택** (중복 가능, 해당 시 할증)")
        date_options = ["이사많은날 🏠", "손없는날 ✋", "월말 📅", "공휴일 🎉", "금요일 📅"]
        date_surcharges_defined = hasattr(data, "special_day_prices") and isinstance(data.special_day_prices, dict)
        if not date_surcharges_defined: st.warning("data.py에 날짜 할증 정보가 없습니다.")

        # session_state 키는 state_manager.py와 일치하도록 'tab3_' 접두사 없이 사용 (저장/로드 시 매핑됨)
        date_keys = [f"date_opt_{i}_widget" for i in range(len(date_options))]
        cols_date = st.columns(len(date_options))
        for i, option in enumerate(date_options):
            surcharge = data.special_day_prices.get(option, 0) if date_surcharges_defined else 0
            cols_date[i].checkbox(option, key=date_keys[i], help=f"{surcharge:,}원 할증" if surcharge > 0 else "")
    st.divider()

    with st.container(border=True):
        st.subheader("💰 수기 조정 및 계약금")
        cols_adj_new = st.columns(2)
        with cols_adj_new[0]: # 계약금 (state_manager에서 tab3_deposit_amount로 저장됨)
            st.number_input("📝 계약금", min_value=0, step=10000, key="deposit_amount", format="%d")
        with cols_adj_new[1]: # 추가 조정 (state_manager에서 tab3_adjustment_amount로 저장됨)
            st.number_input("💰 추가 조정 (+/-)", step=10000, key="adjustment_amount", format="%d")

        cols_extra_fees = st.columns(2)
        with cols_extra_fees[0]: # 지방 사다리 추가요금 (state_manager에서 tab3_regional_ladder_surcharge로 저장됨)
            st.number_input("🪜 사다리 추가요금", min_value=0, step=10000, key="regional_ladder_surcharge", format="%d")
        if st.session_state.get("has_via_point", False): # 경유지 선택 시에만 표시
             with cols_extra_fees[1]: # 경유지 추가요금 (STATE_KEYS_TO_SAVE에 직접 포함)
                st.number_input("↪️ 경유지 추가요금", min_value=0, step=10000, key="via_point_surcharge", format="%d")
        else: # 경유지 미선택 시 빈 공간 유지
            with cols_extra_fees[1]:
                pass # st.empty() 또는 아무것도 안 함
    st.divider()

    st.header("💵 최종 견적 결과")
    final_selected_vehicle_for_calc = st.session_state.get("final_selected_vehicle")
    total_cost_display, cost_items_display, personnel_info_display, has_cost_error = 0, [], {}, False

    # 유효성 검사 메시지 표시
    validation_messages = get_validation_warnings(st.session_state.to_dict())
    if validation_messages:
        warning_html = "<div style='padding:10px; border: 1px solid #FFC107; background-color: #FFF3CD; border-radius: 5px; color: #664D03; margin-bottom: 15px;'>"
        warning_html += "<h5 style='margin-top:0; margin-bottom:10px;'>⚠️ 다음 필수 정보를 확인하거나 수정해주세요:</h5><ul style='margin-bottom: 0px; padding-left: 20px;'>"
        for msg in validation_messages:
            warning_html += f"<li style='margin-bottom: 5px;'>{msg}</li>"
        warning_html += "</ul></div>"
        st.markdown(warning_html, unsafe_allow_html=True)


    if not final_selected_vehicle_for_calc and not validation_messages : # 차량 선택 안됐고 다른 경고도 없을 때
        st.info("차량을 선택하고 필수 정보(주소, 층수 등)를 입력하시면 최종 견적 결과를 확인할 수 있습니다.")
    elif final_selected_vehicle_for_calc: # 차량이 선택된 경우에만 비용 계산 및 표시
        try:
            # 보관 이사 시 보관 기간 재계산 (state_manager와 유사하게)
            if st.session_state.get("is_storage_move"):
                m_dt = st.session_state.get("moving_date") # Tab1에서 입력된 이사일
                a_dt = st.session_state.get("arrival_date") # Tab1에서 입력된 도착일
                if isinstance(m_dt, date) and isinstance(a_dt, date) and a_dt >= m_dt:
                    st.session_state.storage_duration = max(1, (a_dt - m_dt).days + 1)
                else: # 날짜가 유효하지 않으면 기본값 1일
                    st.session_state.storage_duration = 1
            
            # 전체 세션 상태를 딕셔너리로 변환하여 계산 함수에 전달
            current_state_dict = st.session_state.to_dict()
            if hasattr(calculations, "calculate_total_moving_cost") and callable(calculations.calculate_total_moving_cost):
                total_cost_display, cost_items_display, personnel_info_display = calculations.calculate_total_moving_cost(current_state_dict)
                # PDF 및 이미지 생성을 위해 세션 상태에 저장
                st.session_state.update({
                    "calculated_cost_items_for_pdf": cost_items_display,
                    "total_cost_for_pdf": total_cost_display,
                    "personnel_info_for_pdf": personnel_info_display
                })
                # 비용 계산 결과에 "오류" 항목이 있는지 확인
                if any(isinstance(item, (list, tuple)) and len(item) > 0 and str(item[0]) == "오류" for item in cost_items_display):
                    has_cost_error = True
            else:
                st.error("최종 비용 계산 함수 로드 실패."); has_cost_error = True
                # 오류 발생 시 PDF/이미지 생성용 데이터 초기화
                st.session_state.update({"calculated_cost_items_for_pdf": [], "total_cost_for_pdf": 0, "personnel_info_for_pdf": {}})

            # 화면 표시용 금액 계산
            total_cost_num = int(total_cost_display) if isinstance(total_cost_display, (int, float)) else 0
            deposit_val = st.session_state.get("deposit_amount", 0) # Tab3 UI 직접 입력값
            deposit_amount_num = int(deposit_val) if deposit_val is not None else 0
            remaining_balance_num = total_cost_num - deposit_amount_num

            st.subheader(f"💰 총 견적 비용: {total_cost_num:,.0f} 원")
            st.subheader(f"➖ 계약금: {deposit_amount_num:,.0f} 원")
            st.subheader(f"➡️ 잔금 (총 비용 - 계약금): {remaining_balance_num:,.0f} 원")
            st.write("") # 간격

            st.subheader("📊 비용 상세 내역")
            if has_cost_error: # 비용 계산 함수에서 오류 반환 시
                err_item = next((item for item in cost_items_display if isinstance(item, (list, tuple)) and len(item)>0 and str(item[0]) == "오류"), None)
                st.error(f"비용 계산 오류: {err_item[2] if err_item and len(err_item) > 2 else '알 수 없는 오류'}")
            elif cost_items_display: # 오류 없이 비용 항목이 있을 때
                valid_costs = [item for item in cost_items_display if not (isinstance(item, (list, tuple)) and len(item) > 0 and str(item[0]) == "오류")]
                if valid_costs:
                    df_display_costs = pd.DataFrame(valid_costs, columns=["항목", "금액", "비고"])
                    df_display_costs["금액"] = pd.to_numeric(df_display_costs["금액"], errors='coerce').fillna(0).astype(int)
                    st.dataframe(
                        df_display_costs.style.format({"금액": "{:,.0f}"}).set_properties(**{'text-align':'right'}, subset=['금액']).set_properties(**{'text-align':'left'}, subset=['항목','비고']),
                        use_container_width=True,
                        hide_index=True
                    )
                else: st.info("ℹ️ 유효한 비용 항목 없음.") # 오류는 아니지만 표시할 비용 항목이 없음
            else: st.info("ℹ️ 계산된 비용 항목 없음.") # 비용 항목이 아예 없음
            st.write("") # 간격

            # 고객 요구사항 표시 (있을 경우)
            special_notes = st.session_state.get('special_notes')
            if special_notes and special_notes.strip():
                st.subheader("📝 고객요구사항")
                st.info(special_notes)

            # --- 이사 정보 요약 (텍스트) ---
            st.subheader("📋 이사 정보 요약 (텍스트)")
            summary_display_possible = bool(final_selected_vehicle_for_calc) and not has_cost_error

            if summary_display_possible:
                try:
                    # 필요한 변수들 (기존 로직에서 가져옴)
                    customer_name_summary = st.session_state.get('customer_name', '')
                    phone_summary = st.session_state.get('customer_phone', '')
                    email_summary = st.session_state.get('customer_email', '')

                    from_addr_summary = st.session_state.get('from_location', '정보 없음')
                    to_addr_summary = st.session_state.get('to_location', '정보 없음')
                    
                    is_storage_move_summary = st.session_state.get('is_storage_move', False)
                    storage_details_text = ""
                    if is_storage_move_summary:
                        storage_type = st.session_state.get('storage_type', '정보 없음')
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

                    # 작업 방법 가져오는 함수 (ui_tab3.py 내에 있거나 utils.py 등에 있어야 함)
                    # 이 함수가 현재 스코프에 없으면 정의 필요
                    def get_method_full_name(method_key):
                         method_str = str(st.session_state.get(method_key, '')).strip()
                         return method_str.split(" ")[0] if method_str else "정보 없음"

                    from_method_full = get_method_full_name('from_method')
                    to_method_full = get_method_full_name('to_method')
                    via_method_full = get_method_full_name('via_point_method') # 경유지 작업 방법

                    deposit_for_summary = int(st.session_state.get("deposit_amount", 0))
                    calculated_total_for_summary = int(total_cost_display) if isinstance(total_cost_display,(int,float)) else 0
                    remaining_for_summary = calculated_total_for_summary - deposit_for_summary

                    payment_option_texts = []
                    if st.session_state.get("issue_tax_invoice", False): payment_option_texts.append("세금계산서 발행 요청")
                    if st.session_state.get("card_payment", False): payment_option_texts.append("카드 결제 예정")
                    payment_options_summary = " / ".join(payment_option_texts) if payment_option_texts else ""
                    
                    b_name_summary, move_t_summary = "포장 자재 📦", st.session_state.get('base_move_type', '')
                    q_b_s, q_mb_s, q_book_s = 0, 0, 0
                    if move_t_summary and hasattr(data, 'items') and hasattr(data, 'item_definitions'):
                        try:
                            # item_definitions 구조에 따라 키 생성 방식 확인 필요
                            # 예시: data.item_definitions[move_t_summary][b_name_summary] 가 리스트여야 함
                            if b_name_summary in data.item_definitions.get(move_t_summary, {}):
                                q_b_s = int(st.session_state.get(f"qty_{move_t_summary}_{b_name_summary}_바구니", 0) or 0)
                                q_mb_s_key1 = f"qty_{move_t_summary}_{b_name_summary}_중박스"
                                q_mb_s_key2 = f"qty_{move_t_summary}_{b_name_summary}_중자바구니" # 중자바구니도 고려
                                q_mb_s = int(st.session_state.get(q_mb_s_key1, st.session_state.get(q_mb_s_key2, 0)) or 0)
                                q_book_s = int(st.session_state.get(f"qty_{move_t_summary}_{b_name_summary}_책바구니", 0) or 0)
                        except Exception as e_basket:
                            print(f"요약 정보 바구니 수량 가져오기 오류: {e_basket}") # 디버깅용
                            pass


                    bask_display_parts = []
                    if q_b_s > 0: bask_display_parts.append(f"바구니 {q_b_s}개")
                    if q_mb_s > 0: bask_display_parts.append(f"중박스 {q_mb_s}개") # "중자바구니" 대신 "중박스"로 통일
                    if q_book_s > 0: bask_display_parts.append(f"책바구니 {q_book_s}개")
                    bask_summary_str = ", ".join(bask_display_parts) if bask_display_parts else "포장자재 정보 없음"

                    note_summary = st.session_state.get('special_notes', '')
                    
                    # --- 요약 정보 라인 구성 시작 ---
                    summary_lines = []

                    # 1. 이사날짜
                    moving_date_val_for_summary = st.session_state.get('moving_date')
                    moving_date_obj_for_summary_display = None
                    if isinstance(moving_date_val_for_summary, date):
                        moving_date_obj_for_summary_display = moving_date_val_for_summary
                    elif isinstance(moving_date_val_for_summary, str):
                        try:
                            moving_date_obj_for_summary_display = datetime.strptime(moving_date_val_for_summary, '%Y-%m-%d').date()
                        except ValueError: pass

                    formatted_moving_date_summary = ""
                    if moving_date_obj_for_summary_display:
                        try:
                            weekday_str_summary = ["월", "화", "수", "목", "금", "토", "일"][moving_date_obj_for_summary_display.weekday()]
                            formatted_moving_date_summary = f"🗓️ 이사일: {moving_date_obj_for_summary_display.strftime('%Y-%m-%d')} ({weekday_str_summary})"
                        except Exception: 
                            formatted_moving_date_summary = f"🗓️ 이사일: {str(moving_date_obj_for_summary_display)}"
                    elif moving_date_val_for_summary:
                        formatted_moving_date_summary = f"🗓️ 이사일: {str(moving_date_val_for_summary)}"
                    else:
                        formatted_moving_date_summary = "🗓️ 이사일: 정보 없음"
                    summary_lines.append(formatted_moving_date_summary)

                    # 2. 주소 흐름 요약
                    address_flow_parts_summary = []
                    address_flow_parts_summary.append(from_addr_summary if from_addr_summary else "출발지 정보 없음")

                    if st.session_state.get('has_via_point', False):
                        via_location_summary_flow = st.session_state.get('via_point_location', '경유지 정보 없음')
                        address_flow_parts_summary.append(f"↪️ {via_location_summary_flow}")

                    if is_storage_move_summary and storage_details_text:
                        address_flow_parts_summary.append(f"📦 {storage_details_text}")
                    
                    address_flow_parts_summary.append(to_addr_summary if to_addr_summary else "도착지 정보 없음")
                    
                    vehicle_display_text_summary = f"({vehicle_tonnage_summary if vehicle_tonnage_summary else vehicle_type_summary})"
                    address_flow_parts_summary.append(vehicle_display_text_summary)

                    summary_lines.append(" ⏩ ".join(address_flow_parts_summary))
                    summary_lines.append("──────────────────────────────")

                    # 3. 고객 정보
                    if customer_name_summary: summary_lines.append(f"👤 고객명: {customer_name_summary}")
                    if phone_summary and phone_summary != '-': summary_lines.append(f"📞 전화번호: {phone_summary}")
                    if email_summary and email_summary != '-': summary_lines.append(f"📧 이메일: {email_summary}")
                    summary_lines.append("")

                    # 4. 상세 주소 목록
                    summary_lines.append("📍 출발지 주소:")
                    summary_lines.append(f"  {from_addr_summary if from_addr_summary else '정보 없음'}")

                    if st.session_state.get('has_via_point', False):
                        via_location_detail_summary = st.session_state.get('via_point_location', '정보 없음')
                        summary_lines.append("↪️ 경유지 주소:")
                        summary_lines.append(f"  {via_location_detail_summary}")

                    if is_storage_move_summary and storage_details_text:
                        summary_lines.append("📦 보관 정보:")
                        summary_lines.append(f"  {storage_details_text}")
                    
                    summary_lines.append("🏁 도착지 주소:")
                    summary_lines.append(f"  {to_addr_summary if to_addr_summary else '정보 없음'}")
                    summary_lines.append("──────────────────────────────")

                    # 5. 그 외 기존 정보
                    summary_lines.append(f"🚛 차량/인원: {vehicle_tonnage_summary if vehicle_tonnage_summary else vehicle_type_summary} / {ppl_summary}")
                    summary_lines.append("")
                    summary_lines.append(f"🛠️ 출발지 작업: {from_method_full}")
                    if st.session_state.get('has_via_point', False): # 경유지 작업 방법 추가
                        summary_lines.append(f"↪️ 경유지 작업: {via_method_full}")
                    summary_lines.append(f"🛠️ 도착지 작업: {to_method_full}")
                    summary_lines.append("")
                    summary_lines.append(f"💳 계약금 {deposit_for_summary:,.0f}원 / 잔금 {remaining_for_summary:,.0f}원")
                    if payment_options_summary:
                        summary_lines.append(f"  ({payment_options_summary})")
                    summary_lines.append("")
                    summary_lines.append(f"💰 총 {calculated_total_for_summary:,.0f}원 중:")

                    processed_for_summary_text = set()
                    cost_detail_lines = []
                    if isinstance(cost_items_display, list):
                        temp_cost_items = [item for item in cost_items_display if isinstance(item, (list, tuple)) and len(item) >=2]
                        for item_name_disp, item_cost_disp, _ in temp_cost_items:
                            if str(item_name_disp) == "기본 운임" and item_cost_disp != 0:
                                cost_detail_lines.append(f"  - 이사비: {int(item_cost_disp):,}")
                                processed_for_summary_text.add(str(item_name_disp))
                                break
                        for item_name_disp, item_cost_disp, _ in temp_cost_items:
                            name_str, cost_int = str(item_name_disp), int(item_cost_disp) if item_cost_disp is not None else 0
                            if name_str not in processed_for_summary_text and "사다리차" not in name_str and "스카이" not in name_str and "부가세" not in name_str and "카드" not in name_str and cost_int != 0 :
                                cost_detail_lines.append(f"  - {name_str}: {cost_int:,}")
                                processed_for_summary_text.add(name_str)
                        for item_name_disp, item_cost_disp, _ in temp_cost_items:
                            name_str, cost_int = str(item_name_disp), int(item_cost_disp) if item_cost_disp is not None else 0
                            if name_str not in processed_for_summary_text and ("사다리차" in name_str or "스카이" in name_str) and cost_int != 0:
                                cost_detail_lines.append(f"  - {name_str}: {cost_int:,}")
                                processed_for_summary_text.add(name_str)
                        for item_name_disp, item_cost_disp, _ in temp_cost_items:
                            name_str, cost_int = str(item_name_disp), int(item_cost_disp) if item_cost_disp is not None else 0
                            if name_str not in processed_for_summary_text and ("부가세" in name_str or "카드" in name_str) and cost_int != 0:
                                cost_detail_lines.append(f"  - {name_str}: {cost_int:,}")
                                processed_for_summary_text.add(name_str)
                    
                    if cost_detail_lines:
                        summary_lines.extend(cost_detail_lines)
                    elif calculated_total_for_summary != 0:
                         summary_lines.append(f"  - 기타 비용 합계: {calculated_total_for_summary:,}")
                    else:
                        summary_lines.append("  - 세부 비용 내역 없음")
                    summary_lines.append("")

                    if bask_summary_str and bask_summary_str != "포장자재 정보 없음":
                         summary_lines.append(f"📦 포장자재: {bask_summary_str}")
                         summary_lines.append("")
                    
                    if note_summary and note_summary.strip() and note_summary != '-':
                        summary_lines.append("📝 고객요구사항:")
                        summary_lines.extend([f"  - {note_line.strip()}" for note_line in note_summary.strip().replace('\r\n', '\n').split('\n') if note_line.strip()])

                    st.text_area("요약 정보", "\n".join(summary_lines), height=400, key="summary_text_area_readonly_tab3", disabled=True)

                except Exception as e_summary_direct:
                    st.error(f"❌ 요약 정보 생성 중 오류: {e_summary_direct}"); traceback.print_exc()
            elif not final_selected_vehicle_for_calc: # 차량 미선택 시 (유효성 검사 경고가 이미 표시될 수 있음)
                if not validation_messages or not any("차량 종류가 선택되지 않았습니다" in msg for msg in validation_messages): # 중복 메시지 방지
                    st.info("ℹ️ 견적 계산용 차량 미선택으로 요약 정보 표시 불가.")
            st.divider() # 요약 정보 섹션 끝
        except Exception as calc_err_outer_display: # 비용 계산 로직 전체를 감싸는 try-except
            st.error(f"최종 견적 표시 중 외부 오류 발생: {calc_err_outer_display}")
            traceback.print_exc()

    # --- 견적서 생성, 발송 및 다운로드 섹션 ---
    st.subheader("📄 견적서 생성, 발송 및 다운로드")

    # 파일 생성 가능 여부 확인
    can_generate_anything = bool(final_selected_vehicle_for_calc) and \
                          not has_cost_error and \
                          st.session_state.get("calculated_cost_items_for_pdf") and \
                          st.session_state.get("total_cost_for_pdf", 0) > 0 # 총 비용이 0보다 커야 의미 있음
    actions_disabled = not can_generate_anything

    # --- 고객용 파일 생성 (PDF & PDF 기반 이미지) ---
    with st.container(border=True):
        st.markdown("**고객 전달용 파일**")
        col_pdf_btn, col_pdf_img_btn = st.columns(2)

        # PDF 생성 관련 인자
        pdf_args_common = {
            "state_data": st.session_state.to_dict(),
            "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
            "total_cost": st.session_state.get("total_cost_for_pdf", 0),
            "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
        }
        pdf_generation_possible = hasattr(pdf_generator, "generate_pdf") and can_generate_anything
        pdf_to_image_possible = hasattr(pdf_generator, "generate_quote_image_from_pdf") and pdf_generation_possible

        with col_pdf_btn:
            if st.button("📄 고객용 PDF 생성", key="generate_customer_pdf_btn", disabled=actions_disabled or not pdf_generation_possible):
                with st.spinner("고객용 PDF 생성 중..."):
                    pdf_data = pdf_generator.generate_pdf(**pdf_args_common)
                if pdf_data:
                    st.session_state['customer_final_pdf_data'] = pdf_data # 세션에 PDF 데이터 저장
                    st.success("✅ 고객용 PDF 생성 완료!")
                    # PDF 기반 이미지도 함께 생성 시도
                    if pdf_to_image_possible:
                        with st.spinner("PDF 기반 고객용 이미지 생성 중..."):
                            poppler_bin_path = None # 필요한 경우 st.secrets 등에서 경로 지정
                            img_data_from_pdf = pdf_generator.generate_quote_image_from_pdf(pdf_data, poppler_path=poppler_bin_path)
                        if img_data_from_pdf:
                            st.session_state['customer_pdf_image_data'] = img_data_from_pdf
                            st.success("✅ PDF 기반 고객용 이미지 생성 완료!")
                        else:
                            st.warning("⚠️ PDF 기반 고객용 이미지 생성 실패. (PDF는 생성됨)")
                            if 'customer_pdf_image_data' in st.session_state: del st.session_state['customer_pdf_image_data']
                else:
                    st.error("❌ 고객용 PDF 생성 실패.")
                    if 'customer_final_pdf_data' in st.session_state: del st.session_state['customer_final_pdf_data']
                    if 'customer_pdf_image_data' in st.session_state: del st.session_state['customer_pdf_image_data']


            if st.session_state.get('customer_final_pdf_data'):
                fname_pdf_cust = f"견적서_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.pdf"
                st.download_button(
                    label="📥 고객용 PDF 다운로드",
                    data=st.session_state['customer_final_pdf_data'],
                    file_name=fname_pdf_cust, mime="application/pdf",
                    key='dl_btn_customer_final_pdf', disabled=actions_disabled # actions_disabled로 버튼 상태 관리
                )
            elif pdf_generation_possible and not actions_disabled:
                st.caption("PDF 생성 버튼을 눌러 준비하세요.")

        with col_pdf_img_btn:
            if st.session_state.get('customer_pdf_image_data'):
                fname_pdf_img_cust = f"견적서_PDF이미지_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.png"
                st.download_button(
                    label="🖼️ 고객용 견적서 이미지 다운로드 (PDF 기반)",
                    data=st.session_state['customer_pdf_image_data'],
                    file_name=fname_pdf_img_cust, mime="image/png",
                    key='dl_btn_customer_pdf_image', disabled=actions_disabled # actions_disabled로 버튼 상태 관리
                )
            elif pdf_to_image_possible and st.session_state.get('customer_final_pdf_data') and not actions_disabled :
                st.caption("PDF 생성 시 함께 생성됩니다.")
            elif pdf_to_image_possible and not actions_disabled :
                 st.caption("고객용 PDF를 먼저 생성하세요.")


        if not pdf_generation_possible and not actions_disabled:
             st.caption("고객용 파일 생성 불가 (견적 내용 또는 PDF 모듈 확인)")
        elif actions_disabled: # actions_disabled 가 True 이면 (즉, can_generate_anything 이 False 이면)
             st.caption("견적 내용을 먼저 완성해주세요.")

    st.divider()

    # --- 내부 검토용 파일 생성 (회사 양식 이미지 & Excel) ---
    with st.container(border=True):
        st.markdown("**내부 검토용 파일**")
        col_internal_img_btn, col_internal_excel_btn = st.columns(2)

        # 회사 양식 기반 이미지 생성 관련 인자
        company_form_image_args = {
            "state_data": st.session_state.to_dict(),
            "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
            "total_cost_overall": st.session_state.get("total_cost_for_pdf", 0),
            "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
        }
        company_image_possible = hasattr(image_generator, "create_quote_image") and can_generate_anything

        with col_internal_img_btn:
            if st.button("🖼️ 내부 검토용 양식 이미지 생성", key="generate_internal_form_image_btn", disabled=actions_disabled or not company_image_possible):
                with st.spinner("내부 검토용 양식 이미지 생성 중..."):
                    internal_image_data = image_generator.create_quote_image(**company_form_image_args)
                if internal_image_data:
                    st.session_state['internal_form_image_data'] = internal_image_data
                    st.success("✅ 내부 검토용 양식 이미지 생성 완료!")
                else:
                    st.error("❌ 내부 검토용 양식 이미지 생성 실패.")
                    if 'internal_form_image_data' in st.session_state: del st.session_state['internal_form_image_data']

            if st.session_state.get('internal_form_image_data'):
                fname_internal_img = f"내부양식_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.png"
                st.download_button(
                    label="📥 내부 검토용 양식 이미지 다운로드",
                    data=st.session_state['internal_form_image_data'],
                    file_name=fname_internal_img, mime="image/png",
                    key='dl_btn_internal_form_image', disabled=actions_disabled # actions_disabled로 버튼 상태 관리
                )
            elif company_image_possible and not actions_disabled:
                st.caption("생성 버튼을 눌러 내부 검토용 이미지를 준비하세요.")

        # 내부 관리용 Excel
        with col_internal_excel_btn:
            excel_possible = hasattr(excel_filler, "fill_final_excel_template") and can_generate_anything
            if st.button("📊 내부용 Excel 생성", key="generate_internal_excel_tab3", disabled=actions_disabled or not excel_possible):
                if excel_possible: # 다시 한번 확인
                    _current_state_for_excel = st.session_state.to_dict()
                    # Excel 생성용 비용 정보는 현재 상태로 다시 계산 (PDF용과 분리될 수 있으므로)
                    _total_cost_excel, _cost_items_excel, _personnel_info_excel = calculations.calculate_total_moving_cost(_current_state_for_excel)
                    with st.spinner("내부용 Excel 파일 생성 중..."):
                        filled_excel_data_dl = excel_filler.fill_final_excel_template(
                            _current_state_for_excel, _cost_items_excel, _total_cost_excel, _personnel_info_excel
                        )
                    if filled_excel_data_dl:
                        st.session_state['internal_excel_data_for_download'] = filled_excel_data_dl
                        st.success("✅ 내부용 Excel 생성 완료!")
                    else:
                        st.error("❌ 내부용 Excel 파일 생성 실패.")
                        if 'internal_excel_data_for_download' in st.session_state: del st.session_state['internal_excel_data_for_download']

            if st.session_state.get('internal_excel_data_for_download') and excel_possible: # excel_possible 조건 추가
                fname_excel_dl = f"내부견적_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.xlsx"
                st.download_button(label="📥 Excel 다운로드 (내부용)", data=st.session_state['internal_excel_data_for_download'], file_name=fname_excel_dl, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='dl_btn_excel_internal_section_tab3', disabled=actions_disabled) # actions_disabled로 버튼 상태 관리
            elif excel_possible and not actions_disabled: st.caption("생성 버튼을 눌러 내부용 Excel 파일을 준비하세요.")

        if not company_image_possible and not excel_possible and not actions_disabled:
             st.caption("내부 검토용 파일 생성 불가 (견적 내용 또는 관련 모듈 확인)")
        elif actions_disabled: # actions_disabled 가 True 이면
             st.caption("견적 내용을 먼저 완성해주세요.")

    st.divider()

    # 이메일 발송
    with st.container(border=True):
        st.markdown("**이메일 발송 (고객용 PDF 첨부)**")
        email_recipient_exists = bool(st.session_state.get("customer_email", "").strip())
        email_modules_ok = hasattr(email_utils, "send_quote_email") and hasattr(pdf_generator, "generate_pdf")
        email_possible = email_modules_ok and can_generate_anything and email_recipient_exists

        if st.button("📧 이메일 발송", key="email_send_button_main_tab3", disabled=actions_disabled or not email_possible):
            recipient_email_send = st.session_state.get("customer_email") # 이미 위에서 bool로 확인됨
            customer_name_send = st.session_state.get("customer_name", "고객")

            # 이메일 발송 시점에는 PDF가 이미 생성되어 세션에 있거나, 없다면 다시 생성
            pdf_email_bytes_send = st.session_state.get('customer_final_pdf_data')
            if not pdf_email_bytes_send and pdf_generation_possible: # PDF가 없으면 (그리고 생성 가능하면) 다시 생성
                with st.spinner("이메일 첨부용 PDF 생성 중..."):
                    pdf_email_bytes_send = pdf_generator.generate_pdf(**pdf_args_common)
                if pdf_email_bytes_send: # 성공 시 세션에 저장 (다음 사용 위해)
                     st.session_state['customer_final_pdf_data'] = pdf_email_bytes_send

            if pdf_email_bytes_send: # PDF 준비 완료
                subject_send = f"[{customer_name_send}님] 이삿날 이사 견적서입니다."
                body_send = f"{customer_name_send}님,\n\n요청하신 이사 견적서를 첨부 파일로 보내드립니다.\n\n감사합니다.\n이삿날 드림"
                pdf_filename_send = f"견적서_{customer_name_send}_{utils.get_current_kst_time_str('%Y%m%d')}.pdf"

                with st.spinner(f"{recipient_email_send}(으)로 이메일 발송 중..."):
                    email_sent_status = email_utils.send_quote_email(recipient_email_send, subject_send, body_send, pdf_email_bytes_send, pdf_filename_send)

                if email_sent_status: st.success(f"✅ 이메일 발송 성공!")
                else: st.error("❌ 이메일 발송 실패.") # email_utils 내부에서 상세 오류 표시
            else: # PDF 준비 실패
                st.error("❌ 첨부할 PDF 생성에 실패하여 이메일을 발송할 수 없습니다.")
        # 버튼 비활성화/캡션 조건 상세화
        elif actions_disabled:
            st.caption("견적 내용을 먼저 완성해주세요.")
        elif not email_recipient_exists:
            st.caption("고객 이메일 주소가 입력되지 않았습니다.")
        elif not email_modules_ok:
            st.caption("이메일 또는 PDF 생성 모듈에 문제가 있습니다.")
        elif not can_generate_anything : # 이 조건은 actions_disabled에 포함되지만, 명시적으로
            st.caption("견적 내용이 충분하지 않아 이메일을 발송할 수 없습니다.")
