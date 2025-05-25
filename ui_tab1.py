# ui_tab1.py
import streamlit as st
from datetime import datetime, date
import pytz
import json
import os
import traceback
import re

try:
    import data
    import utils
    import google_drive_helper as gdrive 
    from state_manager import (
        MOVE_TYPE_OPTIONS, 
        prepare_state_for_save,
        load_state_from_data
    )
    import callbacks
except ImportError as ie:
    st.error(f"UI Tab 1: 필수 모듈 로딩 실패 - {ie}")
    if hasattr(ie, 'name') and ie.name:
        st.error(f"실패한 모듈: {ie.name}")
    st.stop() 
except Exception as e:
    st.error(f"UI Tab 1: 모듈 로딩 중 오류 - {e}")
    traceback.print_exc()
    st.stop()

try:
    if "__file__" in locals(): 
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    else: 
        BASE_DIR = os.getcwd()
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "images")
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR, exist_ok=True)
except Exception as e:
    st.error(f"업로드 디렉토리 설정 중 오류 발생: {e}")
    UPLOAD_DIR = None


def render_tab1():
    """Renders the UI for Tab 1: Customer Information and Moving Details."""
    update_basket_quantities_callback = getattr(callbacks, "update_basket_quantities", None)
    sync_move_type_callback = getattr(callbacks, "sync_move_type", None)
    handle_item_update_callback = getattr(callbacks, "handle_item_update", None)
    set_default_times_callback = getattr(callbacks, "set_default_times", None)


    if not all(callable(cb) for cb in [update_basket_quantities_callback, sync_move_type_callback, handle_item_update_callback, set_default_times_callback]):
        st.error("UI Tab 1: 일부 콜백 함수 로드 실패.")


    st.header("👤 고객 및 이사 정보")
    
    col_search_load, col_save = st.columns([3,1])
    with col_search_load:
        search_phone_tab1 = st.text_input("전화번호 끝 4자리로 견적 검색:", max_chars=4, key="search_phone_input_tab1")
        if st.button("견적 검색", key="search_button_tab1"):
            if search_phone_tab1.isdigit() and len(search_phone_tab1) == 4:
                callbacks.search_and_load_quote_by_phone_suffix(search_phone_tab1)
            else:
                st.warning("전화번호 끝 4자리를 숫자로 입력해주세요.")
    with col_save:
        st.write("") # 줄 맞춤용
        st.write("")
        if st.button("💾 현재 견적 저장", key="save_quote_button_tab1", type="primary", help="현재 입력된 모든 정보를 Google Drive에 저장합니다."):
            if not st.session_state.get('customer_phone', ''):
                st.error("고객 전화번호를 입력해야 저장이 가능합니다.")
            else:
                try:
                    state_to_save = prepare_state_for_save(st.session_state.to_dict())
                    filename = f"{state_to_save.get('customer_phone', '견적')}.json" # 전화번호로 파일명 지정
                    
                    with st.spinner(f"'{filename}' 저장 중..."):
                        gdrive.upload_or_update_json_to_drive(filename, state_to_save)
                    st.success(f"'{filename}' 견적이 Google Drive에 성공적으로 저장되었습니다!")
                except Exception as e_save:
                    st.error(f"견적 저장 중 오류 발생: {e_save}")
                    traceback.print_exc()
    st.divider()
    
    with st.container(border=True):
        st.subheader("기본 정보")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("고객명", key="customer_name")
            
            # 이사 유형 선택 (ui_tab3와 동기화)
            current_move_type_from_state = st.session_state.get("base_move_type", MOVE_TYPE_OPTIONS[0])
            current_index = 0
            if MOVE_TYPE_OPTIONS:
                try:
                    current_index = MOVE_TYPE_OPTIONS.index(current_move_type_from_state)
                except ValueError: # 로드된 값이 옵션에 없을 경우 첫번째 옵션으로
                    current_index = 0
                    st.session_state.base_move_type = MOVE_TYPE_OPTIONS[0]
                    if callable(handle_item_update_callback): handle_item_update_callback() # 품목 업데이트
            else:
                st.error("이사 유형 옵션 정의를 찾을 수 없습니다 (data.py 확인 필요).")
                
            st.radio("이사 유형", options=MOVE_TYPE_OPTIONS, index=current_index, key="base_move_type_widget_tab1", horizontal=True, on_change=sync_move_type_callback, args=("base_move_type_widget_tab1",))
        with col2:
            st.text_input("연락처", key="customer_phone", help="'-' 없이 숫자만 입력해주세요. 예: 01012345678")
            st.text_input("이메일 (선택)", key="customer_email")

        st.write("")
        st.checkbox("🅿️ 주차 지원 가능 (양쪽 모두)", key="parking_available")
        st.checkbox("🧊 냉장고 문 분리 필요", key="fridge_disassembly")
        st.checkbox("💨 에어컨 이전 설치 필요", key="ac_transfer_install")
        st.write("")
        st.text_area("특이사항 및 고객 요청사항", key="special_notes", height=100)
    st.divider()

    with st.container(border=True):
        st.subheader("🗓️ 날짜 및 시간")
        col_date1, col_date2, col_time = st.columns(3)
        with col_date1:
            st.date_input("이사 예정일", key="moving_date", on_change=set_default_times_callback) # 시간 기본값 설정 콜백 연결
        with col_date2:
            # --- 계약일 입력 필드 추가 ---
            st.date_input("계약일", key="contract_date", value=st.session_state.get("contract_date", date.today()))
        with col_time:
            st.selectbox("이사 시간 선택", options=["오전", "오후", "미선택"], key="move_time_option", index=0) # 기본 '오전'

        if st.session_state.get("move_time_option") == "오후":
            st.text_input("오후 이사 상세 (예: 2시, 3시 시작 등)", key="afternoon_move_details")
            
        st.checkbox("☀️ 장거리 이사", key="apply_long_distance")
        if st.session_state.get("apply_long_distance"):
            current_ld_option = st.session_state.get("long_distance_selector", data.long_distance_options[0] if hasattr(data, "long_distance_options") else "선택 안 함")
            try:
                ld_index = data.long_distance_options.index(current_ld_option) if hasattr(data, "long_distance_options") else 0
            except ValueError:
                ld_index = 0 # 옵션에 없으면 첫번째로
            st.selectbox("장거리 구간 선택", options=data.long_distance_options if hasattr(data, "long_distance_options") else ["선택 안 함"], index=ld_index, key="long_distance_selector")

    st.divider()
    
    # --- 출발지 정보 ---
    with st.container(border=True):
        st.subheader("📍 출발지 정보")
        st.text_input("출발지 주소", key="from_address_full", placeholder="예: 서울시 강남구 테헤란로 123, 현대아파트 101동 202호")
        col_from1, col_from2 = st.columns(2)
        with col_from1:
            st.text_input("출발지 층수", key="from_floor", placeholder="예: 3, 1층, 반지하")
        with col_from2:
            # 작업 방식 선택 (이모티콘 제거된 옵션 사용, 저장은 이모티콘 포함된 원본값)
            method_options_raw_from = data.METHOD_OPTIONS if hasattr(data, "METHOD_OPTIONS") else ["선택"]
            method_options_display_from = [opt.split(" ")[0] for opt in method_options_raw_from]
            current_method_from = st.session_state.get("from_method", method_options_raw_from[0])
            try:
                current_method_index_from = method_options_raw_from.index(current_method_from)
            except ValueError:
                current_method_index_from = 0
            st.selectbox("출발지 작업 방식", 
                         options=method_options_raw_from, 
                         format_func=lambda x: x.split(" ")[0] if x else "선택",
                         index=current_method_index_from, 
                         key="from_method", 
                         on_change=update_basket_quantities_callback) # 콜백 연결

        st.checkbox("수동 사다리 추가 (출발지)", key="manual_ladder_from_check", help=f"사다리차 사용 불가 시, 수동 작업 추가 비용: {getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0):,}원")
        if st.session_state.get("manual_ladder_from_check"):
             st.number_input("출발지 수동 사다리 추가금액", 
                             min_value=0, 
                             value=st.session_state.get("departure_ladder_surcharge_manual", getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0)), 
                             step=10000, 
                             key="departure_ladder_surcharge_manual", 
                             format="%d")

    # --- 도착지 정보 ---
    with st.container(border=True):
        st.subheader("🏁 도착지 정보")
        st.text_input("도착지 주소", key="to_address_full", placeholder="예: 경기도 성남시 분당구 판교역로 456, SK아파트 202동 303호")
        col_to1, col_to2 = st.columns(2)
        with col_to1:
            st.text_input("도착지 층수", key="to_floor", placeholder="예: 10, 1층, 주택")
        with col_to2:
            method_options_raw_to = data.METHOD_OPTIONS if hasattr(data, "METHOD_OPTIONS") else ["선택"]
            method_options_display_to = [opt.split(" ")[0] for opt in method_options_raw_to]
            current_method_to = st.session_state.get("to_method", method_options_raw_to[0])
            try:
                current_method_index_to = method_options_raw_to.index(current_method_to)
            except ValueError:
                current_method_index_to = 0
            st.selectbox("도착지 작업 방식", 
                         options=method_options_raw_to, 
                         format_func=lambda x: x.split(" ")[0] if x else "선택",
                         index=current_method_index_to, 
                         key="to_method", 
                         on_change=update_basket_quantities_callback)

        st.checkbox("수동 사다리 추가 (도착지)", key="manual_ladder_to_check", help=f"사다리차 사용 불가 시, 수동 작업 추가 비용: {getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0):,}원")
        if st.session_state.get("manual_ladder_to_check"):
            st.number_input("도착지 수동 사다리 추가금액", 
                            min_value=0, 
                            value=st.session_state.get("arrival_ladder_surcharge_manual", getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0)), 
                            step=10000, 
                            key="arrival_ladder_surcharge_manual", 
                            format="%d")
    st.divider()

    # --- 경유지 정보 (선택적) ---
    with st.container(border=True):
        st.subheader("↪️ 경유지 정보 (선택)")
        st.checkbox("경유지 있음", key="has_via_point")
        if st.session_state.get("has_via_point"):
            st.text_input("경유지 주소", key="via_point_address", placeholder="예: 서울시 서초구 반포대로 789, 삼성빌딩")
            col_via1, col_via2 = st.columns(2)
            with col_via1:
                st.text_input("경유지 층수", key="via_point_floor", placeholder="예: 2, 1층")
            with col_via2:
                method_options_raw_via = data.METHOD_OPTIONS if hasattr(data, "METHOD_OPTIONS") else ["선택"]
                method_options_display_via = [opt.split(" ")[0] for opt in method_options_raw_via]
                current_method_via = st.session_state.get("via_point_method", method_options_raw_via[0])
                try:
                    current_method_index_via = method_options_raw_via.index(current_method_via)
                except ValueError:
                    current_method_index_via = 0

                st.selectbox("경유지 작업 방식", 
                             options=method_options_raw_via, 
                             format_func=lambda x: x.split(" ")[0] if x else "선택",
                             index=current_method_index_via, 
                             key="via_point_method")
            st.number_input("경유지 추가 요금", min_value=0, step=10000, key="via_point_surcharge", format="%d", help="경유로 인한 추가 비용이 있다면 입력합니다.")


    # --- 보관 이사 정보 (선택적) ---
    with st.container(border=True):
        st.subheader("📦 보관 이사 정보 (선택)")
        st.checkbox("보관 이사", key="is_storage_move")
        if st.session_state.get("is_storage_move"):
            storage_options_raw = data.STORAGE_TYPES if hasattr(data, "STORAGE_TYPES") else ["선택"]
            current_storage_type = st.session_state.get("storage_type", storage_options_raw[0])
            try:
                current_storage_index = storage_options_raw.index(current_storage_type)
            except ValueError:
                current_storage_index = 0

            st.radio("보관 유형", 
                      options=storage_options_raw, 
                      format_func=lambda x: x.split(" ")[0] if x else "선택", 
                      index=current_storage_index, 
                      key="storage_type", horizontal=True)
            st.checkbox("보관 중 전기사용", key="storage_use_electricity") 

            min_arrival_date = st.session_state.get('moving_date', date.today())
            if not isinstance(min_arrival_date, date): min_arrival_date = date.today() 

            current_arrival_date = st.session_state.get('arrival_date')
            if not isinstance(current_arrival_date, date) or current_arrival_date < min_arrival_date:
                st.session_state.arrival_date = min_arrival_date 

            st.date_input("도착 예정일 (보관 후)", key="arrival_date", min_value=min_arrival_date) 

            moving_dt, arrival_dt = st.session_state.get('moving_date'), st.session_state.get('arrival_date')
            calculated_duration = max(1, (arrival_dt - moving_dt).days + 1) if isinstance(moving_dt,date) and isinstance(arrival_dt,date) and arrival_dt >= moving_dt else 1
            st.session_state.storage_duration = calculated_duration 
            st.info(f"예상 보관 기간: {st.session_state.storage_duration} 일")

    st.divider()
    with st.container(border=True):
        st.subheader("🖼️ 현장 사진 업로드 (선택)")
        uploaded_files = st.file_uploader("출발지, 도착지, 주요 물품 사진 등을 업로드할 수 있습니다.", 
                                          accept_multiple_files=True, 
                                          type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
                                          key="field_photos_uploader")
        if uploaded_files and UPLOAD_DIR:
            st.session_state.uploaded_image_paths = []
            for uploaded_file in uploaded_files:
                try:
                    # 파일명 고유화 (타임스탬프 사용)
                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
                    unique_filename = f"{timestamp}_{uploaded_file.name}"
                    
                    # 정규화된 경로 사용
                    save_path = os.path.join(UPLOAD_DIR, unique_filename)
                    
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.session_state.uploaded_image_paths.append(save_path) # 저장된 파일 경로 리스트에 추가
                    st.success(f"'{uploaded_file.name}' 업로드 및 저장 완료: {unique_filename}")
                except Exception as e_upload:
                    st.error(f"'{uploaded_file.name}' 업로드 중 오류 발생: {e_upload}")
                    traceback.print_exc()
        elif uploaded_files and not UPLOAD_DIR:
            st.error("이미지 업로드 디렉토리가 올바르게 설정되지 않았습니다.")

        # 저장된 이미지 경로가 있다면 표시 (선택적)
        if st.session_state.get("uploaded_image_paths"):
            with st.expander("업로드된 이미지 보기", expanded=False):
                for img_path in st.session_state.uploaded_image_paths:
                    try:
                        st.image(img_path, caption=os.path.basename(img_path), width=150)
                    except Exception as e_img_display:
                        st.warning(f"이미지 표시 오류 ({os.path.basename(img_path)}): {e_img_display}")
