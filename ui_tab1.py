# ui_tab1.py (이미지 처리 로직 수정 후)
import streamlit as st
from datetime import datetime, date, timedelta
import pytz
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

def render_tab1():
    st.session_state.setdefault('image_uploader_key_counter', 0)
    st.session_state.setdefault('uploaded_images', [])
    st.session_state.setdefault('issue_tax_invoice', False)
    st.session_state.setdefault('card_payment', False)
    st.session_state.setdefault('move_time_option', "오전")
    st.session_state.setdefault('afternoon_move_details', "")
    st.session_state.setdefault('contract_date', date.today())
    
    update_basket_quantities_callback = getattr(callbacks, "update_basket_quantities", None)
    sync_move_type_callback = getattr(callbacks, 'sync_move_type', None)
    set_default_times_callback = getattr(callbacks, "set_default_times", None)

    gdrive_folder_id_from_secrets = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")

    with st.container(border=True):
        st.subheader("Google Drive 연동")
        if gdrive_folder_id_from_secrets:
            st.caption(f"Google Drive의 지정된 폴더에 견적 파일을 저장하고 불러옵니다.")
        else:
            st.caption("Google Drive의 루트 또는 기본 위치에 견적 파일을 저장하고 불러옵니다. (특정 폴더 미지정)")

        col_load, col_save = st.columns(2)

        with col_load:
            st.markdown("**견적 불러오기**")
            search_term = st.text_input("검색 (전화번호 전체 또는 끝 4자리)", key="gdrive_search_term_tab1", help="전체 전화번호 또는 전화번호 끝 4자리를 입력하세요.")

            if st.button("견적 검색", key="gdrive_search_button_tab1"):
                st.session_state.gdrive_search_results = []
                st.session_state.gdrive_file_options_map = {}
                st.session_state.gdrive_selected_file_id = None
                st.session_state.gdrive_selected_filename = None
                search_term_strip = search_term.strip()
                processed_results = []

                if search_term_strip:
                    with st.spinner("Google Drive에서 검색 중..."):
                        if len(search_term_strip) == 4 and search_term_strip.isdigit():
                            all_json_files_in_folder = gdrive.find_files_by_name_contains(
                                name_query="",
                                mime_types="application/json",
                                folder_id=gdrive_folder_id_from_secrets
                            )
                            if all_json_files_in_folder:
                                for r_item in all_json_files_in_folder:
                                    file_name = r_item.get('name', '')
                                    if file_name:
                                        try:
                                            file_name_stem = os.path.splitext(file_name)[0]
                                            if file_name_stem.isdigit() and file_name_stem.endswith(search_term_strip):
                                                processed_results.append(r_item)
                                        except Exception:
                                            pass
                        else:
                            all_gdrive_results = gdrive.find_files_by_name_contains(
                                name_query=search_term_strip,
                                mime_types="application/json",
                                folder_id=gdrive_folder_id_from_secrets
                            )
                            if all_gdrive_results:
                                processed_results = all_gdrive_results

                    if processed_results:
                        st.session_state.gdrive_search_results = processed_results
                        st.session_state.gdrive_file_options_map = {pr_item['name']: pr_item['id'] for pr_item in processed_results}
                        if processed_results:
                            st.session_state.gdrive_selected_filename = processed_results[0].get('name')
                            st.session_state.gdrive_selected_file_id = processed_results[0].get('id')
                        st.success(f"{len(processed_results)}개 검색 완료.")
                    else:
                        st.warning("해당 조건에 맞는 파일을 찾을 수 없습니다.")
                else:
                    st.warning("검색어를 입력하세요.")

            if st.session_state.get('gdrive_search_results'):
                file_options_display = list(st.session_state.gdrive_file_options_map.keys())
                current_selection_index = 0
                selected_filename_from_state = st.session_state.get('gdrive_selected_filename')

                if selected_filename_from_state in file_options_display:
                    try:
                        current_selection_index = file_options_display.index(selected_filename_from_state)
                    except ValueError:
                        current_selection_index = 0

                if not selected_filename_from_state and file_options_display:
                    st.session_state.gdrive_selected_filename = file_options_display[0]
                    st.session_state.gdrive_selected_file_id = st.session_state.gdrive_file_options_map.get(file_options_display[0])
                    current_selection_index = 0

                on_change_callback_gdrive = getattr(callbacks, 'update_selected_gdrive_id', None)
                st.selectbox(
                    "불러올 JSON 파일 선택:", file_options_display,
                    index=current_selection_index,
                    key="gdrive_selected_filename_widget_tab1",
                    on_change=on_change_callback_gdrive if callable(on_change_callback_gdrive) else None
                )

            load_button_disabled = not bool(st.session_state.get('gdrive_selected_file_id'))
            if st.button("선택 견적 불러오기", disabled=load_button_disabled, key="load_gdrive_btn_tab1"):
                json_file_id = st.session_state.get('gdrive_selected_file_id')
                selected_filename_display = st.session_state.get('gdrive_selected_filename', '선택된 파일')
                if json_file_id:
                    with st.spinner(f"'{selected_filename_display}' 로딩 중..."):
                        loaded_content = gdrive.load_json_file(json_file_id)
                    if loaded_content:
                        update_basket_callback_ref = getattr(callbacks, 'update_basket_quantities', lambda: None)
                        if 'uploaded_images' not in loaded_content or \
                           not isinstance(loaded_content.get('uploaded_images'), list):
                            loaded_content['uploaded_images'] = []

                        load_success = load_state_from_data(loaded_content, update_basket_callback_ref)
                        if load_success:
                            st.session_state.image_uploader_key_counter +=1
                            st.success("견적 데이터 로딩 완료.")
                            st.rerun()
                        else: st.error("저장된 데이터 형식 오류로 로딩 실패.")
                    else: st.error(f"'{selected_filename_display}' 파일 로딩 또는 JSON 파싱 실패.")
                else:
                    st.warning("불러올 파일을 선택해주세요.")

        with col_save:
            st.markdown("**현재 견적 저장**")
            with st.form(key="save_quote_form_tab1"):
                raw_phone_for_display = st.session_state.get('customer_phone', '').strip()
                example_sanitized_phone = utils.sanitize_phone_number(raw_phone_for_display)
                example_json_fname = f"{example_sanitized_phone}.json" if example_sanitized_phone else "전화번호입력후생성.json"
                st.caption(f"JSON 파일명 예시: `{example_json_fname}` (같은 번호로 저장 시 덮어쓰기)")

                submitted = st.form_submit_button("Google Drive에 저장")
                if submitted:
                    raw_customer_phone = st.session_state.get('customer_phone', '').strip()
                    sanitized_customer_phone = utils.sanitize_phone_number(raw_customer_phone)
                    st.session_state.customer_phone = sanitized_customer_phone

                    if not sanitized_customer_phone or not sanitized_customer_phone.isdigit() or len(sanitized_customer_phone) < 9:
                        st.error("저장 실패: 유효한 고객 전화번호를 입력해주세요 (예: 01012345678 또는 021234567).")
                    else:
                        json_filename = f"{sanitized_customer_phone}.json"
                        state_data_to_save = prepare_state_for_save(st.session_state.to_dict())
                        if 'uploaded_images' not in state_data_to_save or \
                           not isinstance(state_data_to_save.get('uploaded_images'), list):
                             state_data_to_save['uploaded_images'] = st.session_state.get('uploaded_images', [])

                        try:
                            with st.spinner(f"'{json_filename}' 저장 중..."):
                                save_json_result = gdrive.save_json_file(
                                    json_filename,
                                    state_data_to_save,
                                    folder_id=gdrive_folder_id_from_secrets
                                )
                            if save_json_result and save_json_result.get('id'):
                                st.success(f"'{json_filename}' 저장 완료.")
                            else: st.error(f"'{json_filename}' 저장 실패.")
                        except Exception as save_err:
                            st.error(f"'{json_filename}' 저장 중 예외 발생: {save_err}")
                            traceback.print_exc()
    st.divider()

    st.header("고객 기본 정보")

    current_base_move_type_value = st.session_state.get('base_move_type', MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "")
    try:
        current_index_tab1 = MOVE_TYPE_OPTIONS.index(current_base_move_type_value)
    except ValueError:
        current_index_tab1 = 0
        if MOVE_TYPE_OPTIONS:
            st.session_state.base_move_type = MOVE_TYPE_OPTIONS[0]

    sync_move_type_callback_ref = getattr(callbacks, 'sync_move_type', None)
    if MOVE_TYPE_OPTIONS:
        st.radio(
            "기본 이사 유형", options=MOVE_TYPE_OPTIONS,
            format_func=lambda x: x.split(" ")[0],
            index=current_index_tab1, horizontal=True,
            key="base_move_type_widget_tab1",
            on_change=sync_move_type_callback_ref if callable(sync_move_type_callback_ref) else None,
            args=("base_move_type_widget_tab1",) if callable(sync_move_type_callback_ref) else None
        )
    else: st.warning("이사 유형 옵션을 로드할 수 없습니다.")

    col_opts1, col_opts2, col_opts3 = st.columns(3)
    with col_opts1: st.checkbox("보관이사 여부", key="is_storage_move")
    with col_opts2: st.checkbox("장거리 이사 적용", key="apply_long_distance")
    with col_opts3: st.checkbox("경유지 이사 여부", key="has_via_point")
    st.write("")

    st.text_input("고객명", key="customer_name")

    col_phone, col_email = st.columns(2)
    with col_phone:
        st.text_input("전화번호", key="customer_phone", placeholder="010-1234-5678 또는 01012345678")
    with col_email:
        st.text_input("이메일", key="customer_email", placeholder="email@example.com")

    st.markdown("---")

    col_from_header, col_to_header = st.columns(2)
    with col_from_header:
        st.subheader("출발지 정보")
    with col_to_header:
        st.subheader("도착지 정보")

    from_addr_col, to_addr_col = st.columns(2)
    with from_addr_col:
        st.text_input("출발지 주소", key="from_address_full", label_visibility="visible", placeholder="출발지 전체 주소")
    with to_addr_col:
        st.text_input("도착지 주소", key="to_address_full", label_visibility="visible", placeholder="도착지 전체 주소")

    from_floor_col, to_floor_col = st.columns(2)
    with from_floor_col:
        st.text_input("출발지 층수", key="from_floor", label_visibility="visible", placeholder="예: 3, B1")
    with to_floor_col:
        st.text_input("도착지 층수", key="to_floor", label_visibility="visible", placeholder="예: 5, B2")

    from_method_col, to_method_col = st.columns(2)
    with from_method_col:
        from_method_options = data.METHOD_OPTIONS if hasattr(data,'METHOD_OPTIONS') else []
        current_from_method_val = st.session_state.get('from_method', from_method_options[0] if from_method_options else None)
        try: current_from_method_idx = from_method_options.index(current_from_method_val) if current_from_method_val in from_method_options else 0
        except ValueError: current_from_method_idx = 0
        st.selectbox("출발지 작업 방법", from_method_options,
                        format_func=lambda x: x.split(" ")[0] if x else "선택",
                        index=current_from_method_idx, key="from_method")
    with to_method_col:
        to_method_options = data.METHOD_OPTIONS if hasattr(data,'METHOD_OPTIONS') else []
        current_to_method_val = st.session_state.get('to_method', to_method_options[0] if to_method_options else None)
        try: current_to_method_idx = to_method_options.index(current_to_method_val) if current_to_method_val in to_method_options else 0
        except ValueError: current_to_method_idx = 0
        st.selectbox("도착지 작업 방법", to_method_options,
                        format_func=lambda x: x.split(" ")[0] if x else "선택",
                        index=current_to_method_idx, key="to_method")

    st.markdown("---")
    st.subheader("이사 날짜 및 시간")

    date_cols1, date_cols2 = st.columns(2)
    with date_cols1:
        current_contract_date_val = st.session_state.get('contract_date')
        if not isinstance(current_contract_date_val, date):
            st.session_state.contract_date = date.today()
        st.date_input("계약일", key="contract_date")

        current_moving_date_val = st.session_state.get('moving_date')
        if not isinstance(current_moving_date_val, date):
             try: kst_def = pytz.timezone("Asia/Seoul"); default_date_def = datetime.now(kst_def).date()
             except Exception: default_date_def = datetime.now().date()
             st.session_state.moving_date = default_date_def
        set_default_times_cb_ref = getattr(callbacks, "set_default_times", None)
        st.date_input("이사 예정일 (출발일)", key="moving_date", on_change=set_default_times_cb_ref if callable(set_default_times_cb_ref) else None)

    with date_cols2:
        move_time_options = ["미선택", "오전", "오후"]
        current_move_time_opt_val = st.session_state.get("move_time_option", move_time_options[0])
        try: move_time_index = move_time_options.index(current_move_time_opt_val)
        except ValueError: move_time_index = 0; st.session_state.move_time_option = move_time_options[0]

        st.selectbox("이사 시간대", options=move_time_options, index=move_time_index, key="move_time_option")
        if st.session_state.get("move_time_option") == "오후":
            st.text_input("오후이사 상세(시간 등)", key="afternoon_move_details", placeholder="예: 3시 시작, 13-16시")

        if st.session_state.get('is_storage_move'):
            st.markdown("보관 후 입고 정보")
            min_arrival_date_for_storage = st.session_state.get('moving_date', date.today())
            if not isinstance(min_arrival_date_for_storage, date): min_arrival_date_for_storage = date.today()
            min_arrival_date_for_storage = min_arrival_date_for_storage + timedelta(days=1)

            current_arrival_date_for_storage = st.session_state.get('arrival_date')
            if not isinstance(current_arrival_date_for_storage, date) or current_arrival_date_for_storage < min_arrival_date_for_storage:
                st.session_state.arrival_date = min_arrival_date_for_storage

            st.date_input("도착(입고) 예정일", key="arrival_date", min_value=min_arrival_date_for_storage)

            moving_dt_for_storage, arrival_dt_for_storage = st.session_state.get('moving_date'), st.session_state.get('arrival_date')
            calculated_duration_for_storage = 1
            if isinstance(moving_dt_for_storage,date) and isinstance(arrival_dt_for_storage,date) and arrival_dt_for_storage >= moving_dt_for_storage:
                 calculated_duration_for_storage = max(1, (arrival_dt_for_storage - moving_dt_for_storage).days +1)

            st.session_state.storage_duration = calculated_duration_for_storage
            st.markdown(f"**계산된 보관 기간:** **`{calculated_duration_for_storage}`** 일")

    if st.session_state.get('apply_long_distance'):
        ld_options = data.long_distance_options if hasattr(data,'long_distance_options') else []
        current_ld_val = st.session_state.get('long_distance_selector', ld_options[0] if ld_options else None)
        try: current_ld_index = ld_options.index(current_ld_val) if current_ld_val in ld_options else 0
        except ValueError: current_ld_index = 0
        st.selectbox("장거리 구간 선택", ld_options, index=current_ld_index, key="long_distance_selector")

    with st.container(border=True):
        st.subheader("결제 관련 옵션")
        col_pay_opt_tab1_1, col_pay_opt_tab1_2 = st.columns(2)
        with col_pay_opt_tab1_1:
            st.checkbox("계산서 발행 (견적가에 VAT 10% 추가)", key="issue_tax_invoice")
        with col_pay_opt_tab1_2:
            st.checkbox("카드 결제 (VAT 및 수수료 포함하여 총 13% 추가)", key="card_payment")
    st.divider()

    st.subheader("관련 이미지 업로드")
    
    uploader_widget_key = f"image_uploader_tab1_instance_{st.session_state.image_uploader_key_counter}"
    uploaded_files = st.file_uploader(
        "이미지 파일을 선택해주세요 (여러 파일 가능)", type=["png", "jpg", "jpeg"],
        accept_multiple_files=True, key=uploader_widget_key,
        help="파일을 선택하거나 여기에 드래그앤드롭 하세요."
    )
    if uploaded_files:
        with st.spinner('이미지를 Google Drive에 업로드 중...'):
            current_images = st.session_state.get('uploaded_images', [])
            current_filenames_in_drive = {img['name'] for img in current_images}

            img_phone_prefix = st.session_state.get('customer_phone', 'unknown_phone').strip()
            if not img_phone_prefix: img_phone_prefix = 'no_phone_img'
            img_phone_prefix = utils.sanitize_phone_number(img_phone_prefix)
            
            for uploaded_file_obj in uploaded_files:
                # 파일명 충돌 방지를 위해 타임스탬프와 고유 ID 추가
                timestamp = datetime.now().strftime("%y%m%d%H%M%S")
                original_filename_sanitized = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in uploaded_file_obj.name)
                name_part, ext_part = os.path.splitext(original_filename_sanitized)
                unique_filename = f"{img_phone_prefix}_{timestamp}_{name_part}{ext_part if ext_part else '.jpg'}"

                if unique_filename not in current_filenames_in_drive:
                    upload_result = gdrive.upload_image_to_drive(
                        file_name=unique_filename,
                        image_bytes=uploaded_file_obj.getbuffer(),
                        folder_id=gdrive_folder_id_from_secrets
                    )
                    if upload_result:
                        current_images.append(upload_result)
                        st.toast(f"'{uploaded_file_obj.name}' 업로드 성공!", icon="✅")
                    else:
                        st.error(f"'{uploaded_file_obj.name}' 업로드 실패.")
            
            st.session_state.uploaded_images = current_images
            st.session_state.image_uploader_key_counter += 1
            st.rerun()

    current_uploaded_images = st.session_state.get('uploaded_images', [])
    if current_uploaded_images:
        st.markdown("**업로드된 이미지:**")
        
        def delete_image_action(image_id_to_delete):
            with st.spinner("이미지 삭제 중..."):
                success = gdrive.delete_file_from_drive(image_id_to_delete)
            if success:
                st.session_state.uploaded_images = [img for img in st.session_state.uploaded_images if img['id'] != image_id_to_delete]
                st.toast("이미지 삭제 완료.", icon="🗑️")
                st.rerun()
            else:
                st.error("이미지 삭제에 실패했습니다.")

        cols_per_row_display = 3
        for i in range(0, len(current_uploaded_images), cols_per_row_display):
            image_info_in_row = current_uploaded_images[i:i+cols_per_row_display]
            cols_display = st.columns(cols_per_row_display)
            for col_idx, img_info in enumerate(image_info_in_row):
                with cols_display[col_idx]:
                    try:
                        with st.spinner(f"'{img_info['name']}' 로딩 중..."):
                            image_bytes = gdrive.download_file_bytes(img_info['id'])
                        
                        if image_bytes:
                            st.image(image_bytes, caption=img_info.get('name', '이름없음'), use_container_width=True)
                            delete_btn_key = f"del_btn_{img_info['id']}"
                            st.button(f"삭제", key=delete_btn_key, type="secondary", 
                                      help=f"{img_info.get('name', '')} 삭제하기", on_click=delete_image_action, args=(img_info['id'],))
                        else:
                            st.error(f"'{img_info.get('name', '이름없음')}'\n이미지를 불러올 수 없습니다.")
                    except Exception as img_display_err:
                        st.error(f"{img_info.get('name', '알수없음')} 표시 오류: {img_display_err}")

    kst_time_str = utils.get_current_kst_time_str() if hasattr(utils, 'get_current_kst_time_str') else ''
    st.caption(f"견적 생성/수정 시간: {kst_time_str}")
    st.divider()

    if st.session_state.get('has_via_point'):
        with st.container(border=True):
            st.subheader("경유지 정보")
            via_addr_cols = st.columns([3,1])
            with via_addr_cols[0]:
                 st.text_input("경유지 주소", key="via_point_address", label_visibility="collapsed", placeholder="경유지 전체 주소")
            with via_addr_cols[1]:
                st.text_input("층수", key="via_point_floor", label_visibility="collapsed", placeholder="경유층 (예: 1)")

            method_options_via = data.METHOD_OPTIONS if hasattr(data,'METHOD_OPTIONS') else []
            current_via_method_val = st.session_state.get('via_point_method', method_options_via[0] if method_options_via else None)
            try: current_via_method_idx = method_options_via.index(current_via_method_val) if current_via_method_val in method_options_via else 0
            except ValueError: current_via_method_idx = 0
            st.selectbox("경유지 작업 방법", options=method_options_via, index=current_via_method_idx, key="via_point_method", format_func=lambda x: x.split(" ")[0] if x else "선택")
        st.divider()

    if st.session_state.get('is_storage_move'): 
        with st.container(border=True):
            st.subheader("보관이사 추가 정보")
            storage_options_raw = data.STORAGE_TYPE_OPTIONS if data and hasattr(data,'STORAGE_TYPE_OPTIONS') and data.STORAGE_TYPE_OPTIONS else []

            if 'storage_type' not in st.session_state: 
                st.session_state.storage_type = storage_options_raw[0] if storage_options_raw else None

            current_storage_type_val = st.session_state.get('storage_type')
            current_storage_index = 0
            if storage_options_raw and current_storage_type_val in storage_options_raw:
                try: current_storage_index = storage_options_raw.index(current_storage_type_val)
                except ValueError:
                    st.session_state.storage_type = storage_options_raw[0] if storage_options_raw else \
                                                    (data.DEFAULT_STORAGE_TYPE if hasattr(data, "DEFAULT_STORAGE_TYPE") else None)
                    current_storage_index = 0
            elif not storage_options_raw:
                 st.warning("보관 유형 옵션을 불러올 수 없습니다. (data.py 확인 필요)")

            st.radio("보관 유형 선택:",
                      options=storage_options_raw,
                      format_func=lambda x: x.split(" ")[0] if x else "선택",
                      index=current_storage_index,
                      key="storage_type", horizontal=True)
            st.checkbox("보관 중 전기사용", key="storage_use_electricity")
        st.divider()


    with st.container(border=True):
        st.header("고객 요구사항")
        st.text_area("기타 특이사항이나 요청사항을 입력해주세요.", height=100, key="special_notes")
