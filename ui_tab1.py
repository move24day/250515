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
    import google_drive_helper as gdrive # google_drive_helper.py 임포트
    from state_manager import (
        MOVE_TYPE_OPTIONS, # 이모티콘 제거된 버전 사용
        prepare_state_for_save,
        load_state_from_data
    )
    import callbacks
except ImportError as ie:
    st.error(f"UI Tab 1: 필수 모듈 로딩 실패 - {ie}")
    if hasattr(ie, 'name') and ie.name:
        st.error(f"실패한 모듈: {ie.name}")
    st.stop() # 필수 모듈 없으면 중단
except Exception as e:
    st.error(f"UI Tab 1: 모듈 로딩 중 오류 - {e}")
    traceback.print_exc()
    st.stop()

# 이미지 업로드 디렉토리 설정
try:
    if "__file__" in locals(): # 스크립트 실행 환경
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    else: # 인터랙티브 환경 (예: Jupyter notebook)
        BASE_DIR = os.getcwd()
    UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "images")
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR) # 하위 디렉토리까지 생성
except PermissionError:
    st.error(f"권한 오류: 업로드 디렉토리({UPLOAD_DIR}) 생성 권한이 없습니다.")
    UPLOAD_DIR = None # 업로드 기능 비활성화
except Exception as e_path:
    st.error(f"오류: UPLOAD_DIR 경로 설정 중 문제 발생: {e_path}")
    UPLOAD_DIR = None

def render_tab1():
    if UPLOAD_DIR is None:
        st.warning("이미지 업로드 디렉토리 설정에 문제가 있어 이미지 관련 기능이 제한될 수 있습니다.")

    # 세션 상태 초기화 (이미지 업로더 키, 결제 옵션)
    if 'image_uploader_key_counter' not in st.session_state:
        st.session_state.image_uploader_key_counter = 0
    if 'issue_tax_invoice' not in st.session_state: # state_manager에서 초기화되지만, UI와 직접 연결되므로 확인
        st.session_state.issue_tax_invoice = False
    if 'card_payment' not in st.session_state:
        st.session_state.card_payment = False

    # Google Drive 폴더 ID (secrets.toml 에서 가져옴)
    gdrive_folder_id_from_secrets = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")

    with st.container(border=True):
        st.subheader("Google Drive 연동") # 이모티콘 제거
        if gdrive_folder_id_from_secrets:
            st.caption(f"Google Drive의 지정된 폴더에 견적 파일을 저장하고 불러옵니다.")
        else:
            st.caption("Google Drive의 루트 또는 기본 위치에 견적 파일을 저장하고 불러옵니다. (특정 폴더 미지정)")

        col_load, col_save = st.columns(2)

        with col_load:
            st.markdown("**견적 불러오기**")
            search_term = st.text_input("검색 (전화번호 전체 또는 끝 4자리)", key="gdrive_search_term_tab1", help="전체 전화번호 또는 전화번호 끝 4자리를 입력하세요.")

            if st.button("견적 검색", key="gdrive_search_button_tab1"): # 이모티콘 제거
                st.session_state.gdrive_search_results = [] # 이전 결과 초기화
                st.session_state.gdrive_file_options_map = {} # 맵 초기화
                st.session_state.gdrive_selected_file_id = None # 선택 ID 초기화
                st.session_state.gdrive_selected_filename = None # 선택 파일명 초기화
                search_term_strip = search_term.strip()
                processed_results = []

                if search_term_strip: # 검색어가 있을 때만 실행
                    with st.spinner("Google Drive에서 검색 중..."): # 이모티콘 제거
                        # 전화번호 끝 4자리로 검색하는 경우 (숫자 4자리)
                        if len(search_term_strip) == 4 and search_term_strip.isdigit():
                            # 폴더 내 모든 JSON 파일을 우선 가져옴 (이름 필터링은 Drive API에서 한계가 있을 수 있음)
                            all_json_files_in_folder = gdrive.find_files_by_name_contains(
                                name_query="", # 이름 쿼리는 비워두고
                                mime_types="application/json", # JSON 파일만
                                folder_id=gdrive_folder_id_from_secrets
                            )
                            if all_json_files_in_folder:
                                for r_item in all_json_files_in_folder:
                                    file_name = r_item.get('name', '')
                                    if file_name:
                                        try: # 파일명에서 확장자 제외하고 숫자 부분만 비교
                                            file_name_stem = os.path.splitext(file_name)[0]
                                            if file_name_stem.isdigit() and file_name_stem.endswith(search_term_strip):
                                                processed_results.append(r_item)
                                        except Exception: # 파싱 오류 시 무시
                                            pass
                        else: # 전체 전화번호 또는 다른 텍스트로 검색
                            all_gdrive_results = gdrive.find_files_by_name_contains(
                                name_query=search_term_strip,
                                mime_types="application/json", # JSON 파일만 검색
                                folder_id=gdrive_folder_id_from_secrets
                            )
                            if all_gdrive_results:
                                processed_results = all_gdrive_results
                    
                    if processed_results:
                        st.session_state.gdrive_search_results = processed_results
                        # 파일명: ID 맵 생성
                        st.session_state.gdrive_file_options_map = {pr_item['name']: pr_item['id'] for pr_item in processed_results}
                        if processed_results: # 검색 결과가 있으면 첫번째 항목을 기본 선택
                            st.session_state.gdrive_selected_filename = processed_results[0].get('name')
                            st.session_state.gdrive_selected_file_id = processed_results[0].get('id')
                        st.success(f"{len(processed_results)}개 검색 완료.") # 이모티콘 제거
                    else:
                        st.warning("해당 조건에 맞는 파일을 찾을 수 없습니다.") # 이모티콘 제거
                else: # 검색어가 없을 때
                    st.warning("검색어를 입력하세요.") # 이모티콘 제거

            # 검색 결과가 세션에 있을 경우 파일 선택 selectbox 표시
            if st.session_state.get('gdrive_search_results'):
                file_options_display = list(st.session_state.gdrive_file_options_map.keys())
                current_selection_index = 0 # 기본 인덱스
                selected_filename_from_state = st.session_state.get('gdrive_selected_filename')

                if selected_filename_from_state in file_options_display:
                    try:
                        current_selection_index = file_options_display.index(selected_filename_from_state)
                    except ValueError: # 현재 선택된 파일명이 옵션에 없을 경우 (예: 다른 검색 후)
                        current_selection_index = 0 
                
                # 이전에 선택된 파일이 없거나 유효하지 않으면, 옵션이 있을 경우 첫번째로 설정
                if not selected_filename_from_state and file_options_display:
                    st.session_state.gdrive_selected_filename = file_options_display[0]
                    st.session_state.gdrive_selected_file_id = st.session_state.gdrive_file_options_map.get(file_options_display[0])
                    current_selection_index = 0

                on_change_callback_gdrive = getattr(callbacks, 'update_selected_gdrive_id', None)
                st.selectbox(
                    "불러올 JSON 파일 선택:", file_options_display,
                    index=current_selection_index,
                    key="gdrive_selected_filename_widget_tab1", # 위젯 키 유지
                    on_change=on_change_callback_gdrive if callable(on_change_callback_gdrive) else None
                )
            
            # 불러오기 버튼 (선택된 파일 ID가 있을 때만 활성화)
            load_button_disabled = not bool(st.session_state.get('gdrive_selected_file_id'))
            if st.button("선택 견적 불러오기", disabled=load_button_disabled, key="load_gdrive_btn_tab1"): # 이모티콘 제거
                json_file_id = st.session_state.get('gdrive_selected_file_id')
                selected_filename_display = st.session_state.get('gdrive_selected_filename', '선택된 파일')
                if json_file_id:
                    with st.spinner(f"'{selected_filename_display}' 로딩 중..."): # 이모티콘 제거
                        loaded_content = gdrive.load_json_file(json_file_id) # gdrive_helper 사용
                    if loaded_content:
                        update_basket_callback_ref = getattr(callbacks, 'update_basket_quantities', lambda: None)
                        # 로드 시 uploaded_image_paths 키 확인 및 기본값 처리
                        if 'uploaded_image_paths' not in loaded_content or \
                           not isinstance(loaded_content.get('uploaded_image_paths'), list):
                            loaded_content['uploaded_image_paths'] = [] # 없거나 리스트 아니면 빈 리스트로
                        
                        load_success = load_state_from_data(loaded_content, update_basket_callback_ref)
                        if load_success:
                            st.session_state.image_uploader_key_counter +=1 # 이미지 업로더 리셋
                            st.success("견적 데이터 로딩 완료.") # 이모티콘 제거
                            st.rerun() # UI 전체 새로고침하여 반영
                        else: st.error("저장된 데이터 형식 오류로 로딩 실패.") # 이모티콘 제거
                    else: st.error(f"'{selected_filename_display}' 파일 로딩 또는 JSON 파싱 실패.") # 이모티콘 제거
                else: # 파일 ID가 없는 경우 (이론상 selectbox에서 처리되어야 함)
                    st.warning("불러올 파일을 선택해주세요.") # 이모티콘 제거
        
        with col_save:
            st.markdown("**현재 견적 저장**")
            with st.form(key="save_quote_form_tab1"):
                raw_phone_for_display = st.session_state.get('customer_phone', '').strip()
                example_sanitized_phone = utils.sanitize_phone_number(raw_phone_for_display) # utils.py 함수 사용
                example_json_fname = f"{example_sanitized_phone}.json" if example_sanitized_phone else "전화번호입력후생성.json"
                st.caption(f"JSON 파일명 예시: `{example_json_fname}` (같은 번호로 저장 시 덮어쓰기)")

                submitted = st.form_submit_button("Google Drive에 저장") # 이모티콘 제거
                if submitted:
                    raw_customer_phone = st.session_state.get('customer_phone', '').strip()
                    sanitized_customer_phone = utils.sanitize_phone_number(raw_customer_phone)
                    st.session_state.customer_phone = sanitized_customer_phone # 정제된 번호로 세션 업데이트

                    if not sanitized_customer_phone or not sanitized_customer_phone.isdigit() or len(sanitized_customer_phone) < 9: # 최소 길이 검사 (예시)
                        st.error("저장 실패: 유효한 고객 전화번호를 입력해주세요 (예: 01012345678 또는 021234567).") # 이모티콘 제거
                    else:
                        json_filename = f"{sanitized_customer_phone}.json"
                        state_data_to_save = prepare_state_for_save() # state_manager.py 함수 사용
                        # 저장 시점의 uploaded_image_paths를 다시 한번 확인하여 포함
                        if 'uploaded_image_paths' not in state_data_to_save or \
                           not isinstance(state_data_to_save.get('uploaded_image_paths'), list):
                             state_data_to_save['uploaded_image_paths'] = st.session_state.get('uploaded_image_paths', [])
                        
                        try:
                            with st.spinner(f"'{json_filename}' 저장 중..."): # 이모티콘 제거
                                save_json_result = gdrive.save_json_file( # gdrive_helper.py 함수 사용
                                    json_filename,
                                    state_data_to_save,
                                    folder_id=gdrive_folder_id_from_secrets
                                )
                            if save_json_result and save_json_result.get('id'): # 성공 시 ID 반환됨
                                st.success(f"'{json_filename}' 저장 완료.") # 이모티콘 제거
                            else: st.error(f"'{json_filename}' 저장 실패.") # 이모티콘 제거 (gdrive_helper 내부 오류 메시지 있을 수 있음)
                        except Exception as save_err: # 예외 처리
                            st.error(f"'{json_filename}' 저장 중 예외 발생: {save_err}") # 이모티콘 제거
                            traceback.print_exc()
    st.divider()

    st.header("고객 기본 정보") # 이모티콘 제거
    
    # 이모티콘 제거된 MOVE_TYPE_OPTIONS 사용
    move_type_options_tab1_display = [opt.split(" ")[0] for opt in MOVE_TYPE_OPTIONS]
    current_base_move_type_display = st.session_state.get('base_move_type').split(" ")[0]

    sync_move_type_callback_ref = getattr(callbacks, 'sync_move_type', None)
    if MOVE_TYPE_OPTIONS: # 옵션이 있을 때만
        try: 
            current_index_tab1 = move_type_options_tab1_display.index(current_base_move_type_display)
        except ValueError: 
            current_index_tab1 = 0 # 옵션에 현재 값 없으면 기본 선택
            # 이 경우 state_manager의 base_move_type을 옵션의 첫번째 값으로 설정하는 로직 추가 가능
            if MOVE_TYPE_OPTIONS:
                st.session_state.base_move_type = MOVE_TYPE_OPTIONS[0]


        st.radio(
            "기본 이사 유형", options=MOVE_TYPE_OPTIONS, # 실제 값은 이모티콘 포함된 원본 사용
            format_func=lambda x: x.split(" ")[0],      # UI 표시는 이모티콘 제거
            index=current_index_tab1, horizontal=True,
            key="base_move_type_widget_tab1", # state_manager와 키 일치
            on_change=sync_move_type_callback_ref if callable(sync_move_type_callback_ref) else None,
            args=("base_move_type_widget_tab1",) if callable(sync_move_type_callback_ref) else None
        )
    else: st.warning("이사 유형 옵션을 로드할 수 없습니다.") # 이모티콘 제거

    # 옵션 체크박스 (보관, 장거리, 경유지)
    col_opts1, col_opts2, col_opts3 = st.columns(3)
    with col_opts1: st.checkbox("보관이사 여부", key="is_storage_move") # 이모티콘 제거
    with col_opts2: st.checkbox("장거리 이사 적용", key="apply_long_distance") # 이모티콘 제거
    with col_opts3: st.checkbox("경유지 이사 여부", key="has_via_point") # 이모티콘 제거

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("고객명", key="customer_name") # 이모티콘 제거
        st.text_input("출발지 주소", key="from_location") # 이모티콘 제거
        if st.session_state.get('apply_long_distance'): # 장거리 선택 시 구간 선택
            ld_options = data.long_distance_options if hasattr(data,'long_distance_options') else []
            if 'long_distance_selector' not in st.session_state: # 초기화
                st.session_state.long_distance_selector = ld_options[0] if ld_options else None
            
            current_ld_val = st.session_state.get('long_distance_selector')
            current_ld_index = 0 # 기본 인덱스
            if ld_options and current_ld_val in ld_options:
                try: current_ld_index = ld_options.index(current_ld_val)
                except ValueError: st.session_state.long_distance_selector = ld_options[0] # 오류 시 기본값

            st.selectbox("장거리 구간 선택", ld_options, index=current_ld_index, key="long_distance_selector") # 이모티콘 제거
        
        st.text_input("출발지 층수", key="from_floor", placeholder="예: 3, B1, -1") # 이모티콘 제거
        
        method_options_from = data.METHOD_OPTIONS if hasattr(data,'METHOD_OPTIONS') else []
        if 'from_method' not in st.session_state: # 초기화
            st.session_state.from_method = method_options_from[0] if method_options_from else None
        
        current_from_method_val = st.session_state.get('from_method')
        current_from_method_index = 0
        if method_options_from and current_from_method_val in method_options_from:
            try: current_from_method_index = method_options_from.index(current_from_method_val)
            except ValueError: st.session_state.from_method = method_options_from[0]
        
        st.selectbox("출발지 작업 방법", method_options_from, 
                      format_func=lambda x: x.split(" ")[0] if x else "선택", # 이모티콘 제거된 텍스트 표시
                      index=current_from_method_index, key="from_method") # 이모티콘 제거
        
        current_moving_date_val = st.session_state.get('moving_date')
        # moving_date가 date 객체가 아니면 오늘 날짜로 설정 (state_manager에서 이미 처리)
        if not isinstance(current_moving_date_val, date):
             try: kst_def = pytz.timezone("Asia/Seoul"); default_date_def = datetime.now(kst_def).date()
             except Exception: default_date_def = datetime.now().date()
             st.session_state.moving_date = default_date_def
             
        st.date_input("이사 예정일 (출발일)", key="moving_date") # 이모티콘 제거
    
    with col2:
        st.text_input("전화번호", key="customer_phone", placeholder="010-1234-5678 또는 01012345678") # 이모티콘 제거
        st.text_input("이메일", key="customer_email", placeholder="email@example.com") # 이모티콘 제거
        st.text_input("도착지 주소", key="to_location") # 이모티콘 제거
        st.text_input("도착지 층수", key="to_floor", placeholder="예: 5, B2, -2") # 이모티콘 제거

        method_options_to = data.METHOD_OPTIONS if hasattr(data,'METHOD_OPTIONS') else []
        if 'to_method' not in st.session_state: # 초기화
            st.session_state.to_method = method_options_to[0] if method_options_to else None
        
        current_to_method_val = st.session_state.get('to_method')
        current_to_method_index = 0
        if method_options_to and current_to_method_val in method_options_to:
            try: current_to_method_index = method_options_to.index(current_to_method_val)
            except ValueError: st.session_state.to_method = method_options_to[0]

        st.selectbox("도착지 작업 방법", method_options_to, 
                      format_func=lambda x: x.split(" ")[0] if x else "선택", # 이모티콘 제거된 텍스트 표시
                      index=current_to_method_index, key="to_method") # 이모티콘 제거

    with st.container(border=True):
        st.subheader("결제 관련 옵션") # 이모티콘 제거
        col_pay_opt_tab1_1, col_pay_opt_tab1_2 = st.columns(2)
        with col_pay_opt_tab1_1:
            st.checkbox("세금계산서 발행 (견적가에 VAT 10% 추가)", key="issue_tax_invoice")
        with col_pay_opt_tab1_2:
            st.checkbox("카드 결제 (VAT 및 수수료 포함하여 총 13% 추가)", key="card_payment") # 문구 수정
            # st.caption("카드 수수료는 VAT 포함 금액에 부과될 수 있습니다.") # 문구 변경으로 불필요 또는 수정 필요
    st.divider()

    if UPLOAD_DIR: # 이미지 업로드 디렉토리 유효할 때만 기능 활성화
        st.subheader("관련 이미지 업로드") # 이모티콘 제거
        # 업로더 위젯 키를 카운터로 관리하여 파일 업로드 후 위젯 리셋 (선택된 파일 목록 초기화)
        uploader_widget_key = f"image_uploader_tab1_instance_{st.session_state.image_uploader_key_counter}"
        uploaded_files = st.file_uploader(
            "이미지 파일을 선택해주세요 (여러 파일 가능)", type=["png", "jpg", "jpeg"],
            accept_multiple_files=True, key=uploader_widget_key,
            help="파일을 선택하거나 여기에 드래그앤드롭 하세요."
        )
        if uploaded_files: # 새 파일이 업로드된 경우
            newly_saved_paths_this_run = [] # 이번 실행에서 새로 저장된 파일 경로
            # 현재 세션에 저장된 이미지 파일명 목록 (중복 저장 방지용)
            current_tracked_filenames = {os.path.basename(p) for p in st.session_state.get('uploaded_image_paths', []) if isinstance(p, str)}
            
            img_phone_prefix = st.session_state.get('customer_phone', 'unknown_phone').strip()
            if not img_phone_prefix: img_phone_prefix = 'no_phone_img' # 전화번호 없으면 기본 접두사
            img_phone_prefix = utils.sanitize_phone_number(img_phone_prefix) # 숫자만 남김

            for uploaded_file_obj in uploaded_files:
                # 파일명 정제 (허용 문자 외에는 '_'로 변경)
                original_filename_sanitized = "".join(c if c.isalnum() or c in ['.', '_'] else '_' for c in uploaded_file_obj.name)
                name_part, ext_part = os.path.splitext(original_filename_sanitized)
                # 전화번호_파일명.확장자 형식으로 기본 파일명 설정
                base_filename = f"{img_phone_prefix}_{name_part}{ext_part if ext_part else '.jpg'}" # 확장자 없으면 .jpg 기본
                
                counter = 1
                filename_to_save = base_filename
                prospective_save_path = os.path.join(UPLOAD_DIR, filename_to_save)
                # 동일한 이름의 파일이 존재하면 카운터 추가 (덮어쓰기 방지)
                while os.path.exists(prospective_save_path):
                    filename_to_save = f"{img_phone_prefix}_{name_part}_{counter}{ext_part if ext_part else '.jpg'}"
                    prospective_save_path = os.path.join(UPLOAD_DIR, filename_to_save)
                    counter += 1
                final_save_path = prospective_save_path # 최종 저장 경로
                final_filename_to_save = os.path.basename(final_save_path) # 최종 저장 파일명

                # 현재 추적 목록에 없거나 이번 실행에서 아직 저장 안된 파일만 처리
                if final_filename_to_save not in current_tracked_filenames and final_save_path not in newly_saved_paths_this_run :
                    try:
                        with open(final_save_path, "wb") as f: f.write(uploaded_file_obj.getbuffer())
                        newly_saved_paths_this_run.append(final_save_path) # 저장 성공 시 경로 추가
                    except Exception as e: st.error(f"'{uploaded_file_obj.name}' 저장 실패: {e}")

            if newly_saved_paths_this_run: # 새로 저장된 파일이 있으면
                current_paths = st.session_state.get('uploaded_image_paths', [])
                current_paths.extend(newly_saved_paths_this_run) # 기존 목록에 추가
                st.session_state.uploaded_image_paths = sorted(list(set(current_paths))) # 중복 제거 및 정렬
                st.session_state.image_uploader_key_counter += 1 # 업로더 키 변경하여 리셋
                st.rerun() # UI 새로고침하여 반영
            elif uploaded_files and not newly_saved_paths_this_run: # 파일은 업로드했지만 새로 저장된게 없는 경우 (중복 등)
                 # 이 경우에도 업로더는 리셋하여 사용자가 다시 시도할 수 있도록 함
                 st.session_state.image_uploader_key_counter += 1
                 st.rerun()

        # 업로드된 이미지 목록 표시 및 삭제 기능
        current_image_paths = st.session_state.get('uploaded_image_paths', [])
        if current_image_paths:
            st.markdown("**업로드된 이미지:**")
            def delete_image_action(image_path_to_delete): # 이미지 삭제 콜백
                try:
                    if os.path.exists(image_path_to_delete): 
                        os.remove(image_path_to_delete)
                        st.toast(f"삭제 성공: {os.path.basename(image_path_to_delete)}", icon="🗑️")
                    else: 
                        st.toast(f"파일 없음: {os.path.basename(image_path_to_delete)}", icon="⚠️")
                except Exception as e_del: 
                    st.error(f"파일 삭제 오류 ({os.path.basename(image_path_to_delete)}): {e_del}")

                # 세션 상태에서도 해당 경로 제거
                paths_after_delete = st.session_state.get('uploaded_image_paths', [])
                if image_path_to_delete in paths_after_delete:
                    paths_after_delete.remove(image_path_to_delete)
                    st.session_state.uploaded_image_paths = paths_after_delete
                st.session_state.image_uploader_key_counter += 1 # 업로더 키 변경
                st.rerun() # UI 새로고침

            paths_to_display_and_delete = list(current_image_paths) # 복사본 사용
            # 실제 존재하는 파일 경로만 필터링 (로드 후 파일이 삭제되었을 경우 대비)
            valid_display_paths = [p for p in paths_to_display_and_delete if isinstance(p, str) and os.path.exists(p)]

            if len(valid_display_paths) != len(paths_to_display_and_delete): # 유효하지 않은 경로가 있었으면
                st.session_state.uploaded_image_paths = valid_display_paths # 세션 상태 업데이트
                if paths_to_display_and_delete: # 이전 목록이 있었는데 변경됐으면 새로고침
                    st.rerun()
            
            if valid_display_paths: # 유효한 이미지만 표시
                cols_per_row_display = 3 # 한 줄에 표시할 이미지 수
                for i in range(0, len(valid_display_paths), cols_per_row_display):
                    image_paths_in_row = valid_display_paths[i:i+cols_per_row_display]
                    cols_display = st.columns(cols_per_row_display)
                    for col_idx, img_path_display in enumerate(image_paths_in_row):
                        with cols_display[col_idx]:
                            try:
                                st.image(img_path_display, caption=os.path.basename(img_path_display), use_container_width=True)
                                # 각 이미지별 삭제 버튼 (고유 키 사용)
                                delete_btn_key = f"del_btn_{img_path_display.replace(os.sep, '_').replace('.', '_').replace(' ', '_')}_{i}_{col_idx}"
                                if st.button(f"삭제", key=delete_btn_key, type="secondary", help=f"{os.path.basename(img_path_display)} 삭제하기"):
                                    delete_image_action(img_path_display)
                            except Exception as img_display_err:
                                st.error(f"{os.path.basename(img_path_display)} 표시 오류: {img_display_err}")
            elif not current_image_paths : st.caption("업로드된 이미지가 없습니다.") # 처음부터 업로드된 이미지 없는 경우
            elif paths_to_display_and_delete and not valid_display_paths: st.caption("표시할 유효한 이미지가 없습니다. 경로를 확인해주세요.")
    else: # UPLOAD_DIR 설정 실패 시
        st.warning("이미지 업로드 디렉토리 설정 오류로 이미지 업로드 기능이 비활성화되었습니다.")

    # 현재 시간 표시
    kst_time_str = utils.get_current_kst_time_str() if hasattr(utils, 'get_current_kst_time_str') else ''
    st.caption(f"견적 생성/수정 시간: {kst_time_str}") # 이모티콘 제거
    st.divider()

    # 경유지 정보 입력 섹션 (has_via_point 선택 시 표시)
    if st.session_state.get('has_via_point'):
        with st.container(border=True):
            st.subheader("경유지 정보") # 이모티콘 제거
            st.text_input("경유지 주소", key="via_point_location") # 이모티콘 제거
            st.text_input("경유지 층수", key="via_point_floor", placeholder="예: 3, B1, -1") # 이모티콘 제거, 신규 추가
            
            method_options_via = data.METHOD_OPTIONS if hasattr(data,'METHOD_OPTIONS') else []
            if 'via_point_method' not in st.session_state: # 초기화
                st.session_state.via_point_method = method_options_via[0] if method_options_via else None
            
            current_via_method_val = st.session_state.get('via_point_method')
            current_via_method_index = 0
            if method_options_via and current_via_method_val in method_options_via:
                try: current_via_method_index = method_options_via.index(current_via_method_val)
                except ValueError: st.session_state.via_point_method = method_options_via[0]
            elif not method_options_via:
                st.warning("경유지 작업 방법 옵션을 불러올 수 없습니다.")

            st.selectbox("경유지 작업 방법", 
                         options=method_options_via, 
                         index=current_via_method_index, 
                         key="via_point_method",
                         format_func=lambda x: x.split(" ")[0] if x else "선택" # 이모티콘 제거된 텍스트 표시
                        ) # 이모티콘 제거
        st.divider()

    # 보관이사 정보 입력 섹션 (is_storage_move 선택 시 표시)
    if st.session_state.get('is_storage_move'):
        with st.container(border=True):
            st.subheader("보관이사 추가 정보") # 이모티콘 제거
            
            storage_options_raw = data.STORAGE_TYPE_OPTIONS if hasattr(data,'STORAGE_TYPE_OPTIONS') else []
            # UI 표시용 (이모티콘 제거), 실제 값은 원본 사용
            storage_options_display = [opt.split(" ")[0] for opt in storage_options_raw]
            
            if 'storage_type' not in st.session_state: # 초기화
                st.session_state.storage_type = storage_options_raw[0] if storage_options_raw else None

            current_storage_type_val = st.session_state.get('storage_type') # 원본 값 (이모티콘 포함)
            current_storage_index = 0
            if storage_options_raw and current_storage_type_val in storage_options_raw:
                try: current_storage_index = storage_options_raw.index(current_storage_type_val)
                except ValueError: st.session_state.storage_type = storage_options_raw[0]
            elif not storage_options_raw:
                 st.warning("보관 유형 옵션을 불러올 수 없습니다.")
            
            st.radio("보관 유형 선택:", 
                      options=storage_options_raw, # 실제 선택값은 이모티콘 포함 원본
                      format_func=lambda x: x.split(" ")[0] if x else "선택", # 표시는 이모티콘 제거
                      index=current_storage_index, 
                      key="storage_type", horizontal=True)
            st.checkbox("보관 중 전기사용", key="storage_use_electricity") # 이모티콘 제거

            min_arrival_date = st.session_state.get('moving_date', date.today())
            if not isinstance(min_arrival_date, date): min_arrival_date = date.today() 

            current_arrival_date = st.session_state.get('arrival_date')
            if not isinstance(current_arrival_date, date) or current_arrival_date < min_arrival_date:
                st.session_state.arrival_date = min_arrival_date 

            st.date_input("도착 예정일 (보관 후)", key="arrival_date", min_value=min_arrival_date) # 이모티콘 제거

            moving_dt, arrival_dt = st.session_state.get('moving_date'), st.session_state.get('arrival_date')
            calculated_duration = max(1, (arrival_dt - moving_dt).days + 1) if isinstance(moving_dt,date) and isinstance(arrival_dt,date) and arrival_dt >= moving_dt else 1
            st.session_state.storage_duration = calculated_duration # 계산된 기간 세션에 저장
            st.markdown(f"**계산된 보관 기간:** **`{calculated_duration}`** 일")
        st.divider()

    with st.container(border=True):
        st.header("고객 요구사항") # 이모티콘 제거
        st.text_area("기타 특이사항이나 요청사항을 입력해주세요.", height=100, key="special_notes")
