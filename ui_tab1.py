# ui_tab1.py
import streamlit as st
from datetime import datetime, date, timedelta 
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
except Exception as e_path:
    st.error(f"업로드 디렉토리 설정 중 오류 발생: {e_path}")
    UPLOAD_DIR = None

def render_tab1():
    if UPLOAD_DIR is None:
        st.warning("이미지 업로드 디렉토리 설정에 문제가 있어 이미지 관련 기능이 제한될 수 있습니다.")

    st.session_state.setdefault('image_uploader_key_counter', 0)
    st.session_state.setdefault('issue_tax_invoice', False)
    st.session_state.setdefault('card_payment', False)
    st.session_state.setdefault('move_time_option', "오전") # 기본 '오전'
    st.session_state.setdefault('afternoon_move_details', "")
    st.session_state.setdefault('contract_date', date.today()) # 계약일 기본값


    gdrive_folder_id_from_secrets = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")

    with st.container(border=True):
        st.subheader("Google Drive 연동") 
        # ... (Google Drive 연동 UI 로직은 이전 답변과 동일) ...
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
                        if 'uploaded_image_paths' not in loaded_content or \
                           not isinstance(loaded_content.get('uploaded_image_paths'), list):
                            loaded_content['uploaded_image_paths'] = [] 
                        
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
                        # prepare_state_for_save 호출 시 st.session_state.to_dict() 전달
                        state_data_to_save = prepare_state_for_save(st.session_state.to_dict()) 
                        if 'uploaded_image_paths' not in state_data_to_save or \
                           not isinstance(state_data_to_save.get('uploaded_image_paths'), list):
                             state_data_to_save['uploaded_image_paths'] = st.session_state.get('uploaded_image_paths', [])
                        
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

    st.text_input("고객명", key="customer_name")
    
    col_phone, col_email = st.columns(2)
    with col_phone:
        st.text_input("전화번호", key="customer_phone", placeholder="010-1234-5678 또는 01012345678")
    with col_email:
        st.text_input("이메일", key="customer_email", placeholder="email@example.com")

    st.markdown("---") 

    # --- 출발지 / 도착지 정보 가로 배치 수정 ---
    col_from_header, col_to_header = st.columns(2)
    with col_from_header:
        st.subheader("출발지 정보")
    with col_to_header:
        st.subheader("도착지 정보")

    # 주소 입력
    from_addr_col, to_addr_col = st.columns(2)
    with from_addr_col:
        st.text_input(" ", key="from_address_full", label_visibility="collapsed", placeholder="출발지 전체 주소") # label_visibility로 레이블 숨김
    with to_addr_col:
        st.text_input(" ", key="to_address_full", label_visibility="collapsed", placeholder="도착지 전체 주소")

    # 층수 입력
    from_floor_col, to_floor_col = st.columns(2)
    with from_floor_col:
        st.text_input(" ", key="from_floor", label_visibility="collapsed", placeholder="출발층 (예: 3, B1)")
    with to_floor_col:
        st.text_input(" ", key="to_floor", label_visibility="collapsed", placeholder="도착층 (예: 5, B2)")
    
    # 작업 방법 입력
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
        current_moving_date_val = st.session_state.get('moving_date')
        if not isinstance(current_moving_date_val, date):
             try: kst_def = pytz.timezone("Asia/Seoul"); default_date_def = datetime.now(kst_def).date()
             except Exception: default_date_def = datetime.now().date()
             st.session_state.moving_date = default_date_def
        st.date_input("이사 예정일 (출발일)", key="moving_date", on_change=getattr(callbacks, "set_default_times", None))
        
        # 계약일 추가
        current_contract_date_val = st.session_state.get('contract_date')
        if not isinstance(current_contract_date_val, date):
            st.session_state.contract_date = date.today()
        st.date_input("계약일", key="contract_date")

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
        if 'long_distance_selector' not in st.session_state: 
            st.session_state.long_distance_selector = ld_options[0] if ld_options else None
        current_ld_val = st.session_state.get('long_distance_selector')
        current_ld_index = 0 
        if ld_options and current_ld_val in ld_options:
            try: current_ld_index = ld_options.index(current_ld_val)
            except ValueError: st.session_state.long_distance_selector = ld_options[0] 
        st.selectbox("장거리 구간 선택", ld_options, index=current_ld_index, key="long_distance_selector") 

    with st.container(border=True):
        st.subheader("결제 관련 옵션") 
        col_pay_opt_tab1_1, col_pay_opt_tab1_2 = st.columns(2)
        with col_pay_opt_tab1_1:
            st.checkbox("계산서 발행 (견적가에 VAT 10% 추가)", key="issue_tax_invoice") # "세금계산서" -> "계산서"
        with col_pay_opt_tab1_2:
            st.checkbox("카드 결제 (VAT 및 수수료 포함하여 총 13% 추가)", key="card_payment") 
    st.divider()

    if UPLOAD_DIR: 
        st.subheader("관련 이미지 업로드") 
        # ... (이미지 업로드 UI 로직은 기존과 동일) ...
        uploader_widget_key = f"image_uploader_tab1_instance_{st.session_state.image_uploader_key_counter}"
        uploaded_files = st.file_uploader(
            "이미지 파일을 선택해주세요 (여러 파일 가능)", type=["png", "jpg", "jpeg"],
            accept_multiple_files=True, key=uploader_widget_key,
            help="파일을 선택하거나 여기에 드래그앤드롭 하세요."
        )
        if uploaded_files: 
            newly_saved_paths_this_run = [] 
            current_tracked_filenames = {os.path.basename(p) for p in st.session_state.get('uploaded_image_paths', []) if isinstance(p, str)}
            
            img_phone_prefix = st.session_state.get('customer_phone', 'unknown_phone').strip()
            if not img_phone_prefix: img_phone_prefix = 'no_phone_img' 
            img_phone_prefix = utils.sanitize_phone_number(img_phone_prefix) 

            for uploaded_file_obj in uploaded_files:
                original_filename_sanitized = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in uploaded_file_obj.name)
                name_part, ext_part = os.path.splitext(original_filename_sanitized)
                base_filename = f"{img_phone_prefix}_{name_part}{ext_part if ext_part else '.jpg'}" 
                
                counter = 1
                filename_to_save = base_filename
                prospective_save_path = os.path.join(UPLOAD_DIR, filename_to_save)
                while os.path.exists(prospective_save_path):
                    filename_to_save = f"{img_phone_prefix}_{name_part}_{counter}{ext_part if ext_part else '.jpg'}"
                    prospective_save_path = os.path.join(UPLOAD_DIR, filename_to_save)
                    counter += 1
                final_save_path = prospective_save_path 
                final_filename_to_save = os.path.basename(final_save_path) 

                if final_filename_to_save not in current_tracked_filenames and final_save_path not in newly_saved_paths_this_run :
                    try:
                        with open(final_save_path, "wb") as f: f.write(uploaded_file_obj.getbuffer())
                        newly_saved_paths_this_run.append(final_save_path) 
                    except Exception as e: st.error(f"'{uploaded_file_obj.name}' 저장 실패: {e}")

            if newly_saved_paths_this_run: 
                current_paths = st.session_state.get('uploaded_image_paths', [])
                current_paths.extend(newly_saved_paths_this_run) 
                st.session_state.uploaded_image_paths = sorted(list(set(current_paths))) 
                st.session_state.image_uploader_key_counter += 1 
                st.rerun() 
            elif uploaded_files and not newly_saved_paths_this_run: 
                 st.session_state.image_uploader_key_counter += 1
                 st.rerun()

        current_image_paths = st.session_state.get('uploaded_image_paths', [])
        if current_image_paths:
            st.markdown("**업로드된 이미지:**")
            def delete_image_action(image_path_to_delete): 
                try:
                    if os.path.exists(image_path_to_delete): 
                        os.remove(image_path_to_delete)
                        st.toast(f"삭제 성공: {os.path.basename(image_path_to_delete)}", icon="🗑️")
                    else: 
                        st.toast(f"파일 없음: {os.path.basename(image_path_to_delete)}", icon="⚠️")
                except Exception as e_del: 
                    st.error(f"파일 삭제 오류 ({os.path.basename(image_path_to_delete)}): {e_del}")

                paths_after_delete = st.session_state.get('uploaded_image_paths', [])
                if image_path_to_delete in paths_after_delete:
                    paths_after_delete.remove(image_path_to_delete)
                    st.session_state.uploaded_image_paths = paths_after_delete
                st.session_state.image_uploader_key_counter += 1 
                st.rerun() 

            paths_to_display_and_delete = list(current_image_paths) 
            valid_display_paths = [p for p in paths_to_display_and_delete if isinstance(p, str) and os.path.exists(p)]

            if len(valid_display_paths) != len(paths_to_display_and_delete): 
                st.session_state.uploaded_image_paths = valid_display_paths 
                if paths_to_display_and_delete: 
                    st.rerun()
            
            if valid_display_paths: 
                cols_per_row_display = 3 
                for i in range(0, len(valid_display_paths), cols_per_row_display):
                    image_paths_in_row = valid_display_paths[i:i+cols_per_row_display]
                    cols_display = st.columns(cols_per_row_display)
                    for col_idx, img_path_display in enumerate(image_paths_in_row):
                        with cols_display[col_idx]:
                            try:
                                st.image(img_path_display, caption=os.path.basename(img_path_display), use_container_width=True)
                                delete_btn_key = f"del_btn_{img_path_display.replace(os.sep, '_').replace('.', '_').replace(' ', '_')}_{i}_{col_idx}"
                                if st.button(f"삭제", key=delete_btn_key, type="secondary", help=f"{os.path.basename(img_path_display)} 삭제하기"):
                                    delete_image_action(img_path_display)
                            except Exception as img_display_err:
                                st.error(f"{os.path.basename(img_path_display)} 표시 오류: {img_display_err}")
            elif not current_image_paths : st.caption("업로드된 이미지가 없습니다.") 
            elif paths_to_display_and_delete and not valid_display_paths: st.caption("표시할 유효한 이미지가 없습니다. 경로를 확인해주세요.")
    else: 
        st.warning("이미지 업로드 디렉토리 설정 오류로 이미지 업로드 기능이 비활성화되었습니다.")

    kst_time_str = utils.get_current_kst_time_str() if hasattr(utils, 'get_current_kst_time_str') else ''
    st.caption(f"견적 생성/수정 시간: {kst_time_str}") 
    st.divider()

    if st.session_state.get('has_via_point'):
        with st.container(border=True):
            st.subheader("경유지 정보") 
            via_addr_cols = st.columns([3,1])
            with via_addr_cols[0]:
                 st.text_input("경유지 주소", key="via_point_address", label_visibility="collapsed", placeholder="경유지 전체 주소") # 키 이름 변경: via_point_location -> via_point_address
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
            storage_options_raw = data.STORAGE_TYPES if hasattr(data,'STORAGE_TYPES') else [] # STORAGE_TYPE_OPTIONS -> STORAGE_TYPES
            
            if 'storage_type' not in st.session_state: 
                st.session_state.storage_type = storage_options_raw[0] if storage_options_raw else None

            current_storage_type_val = st.session_state.get('storage_type') 
            current_storage_index = 0
            if storage_options_raw and current_storage_type_val in storage_options_raw:
                try: current_storage_index = storage_options_raw.index(current_storage_type_val)
                except ValueError: st.session_state.storage_type = storage_options_raw[0]
            elif not storage_options_raw:
                 st.warning("보관 유형 옵션을 불러올 수 없습니다.")
            
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
