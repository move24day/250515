# batch_quote_retriever.py
import streamlit as st
import pandas as pd
import os
from datetime import date, datetime, timedelta
import pytz
import math # math.floor, math.ceil 등 사용

# 기존 프로젝트 모듈 임포트
try:
    import google_drive_helper as gdrive
    import calculations
    import data 
    # state_manager는 직접 임포트보다 필요한 기본값/로직을 가져오는 형태로 단순화
except ImportError as e:
    st.error(f"오류: 필요한 모듈(google_drive_helper, calculations, data)을 찾을 수 없습니다: {e}")
    st.stop()

# 시간대 및 기본값 (기존 앱과 유사하게)
try:
    KST = pytz.timezone("Asia/Seoul")
except pytz.UnknownTimeZoneError:
    KST = pytz.utc
TODAY_DATE_OBJECT = datetime.now(KST).date()

if 'MOVE_TYPE_OPTIONS_BR' not in globals() and hasattr(data, 'item_definitions'): # BR: Batch Retriever
    MOVE_TYPE_OPTIONS_BR = list(data.item_definitions.keys()) if data.item_definitions and isinstance(data.item_definitions, dict) else ["가정 이사 🏠", "사무실 이사 🏢"]
elif 'MOVE_TYPE_OPTIONS_BR' not in globals():
    MOVE_TYPE_OPTIONS_BR = ["가정 이사 🏠", "사무실 이사 🏢"]

DEFAULT_METHOD_BR = data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "계단 🚶"
DEFAULT_STORAGE_TYPE_BR = data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦"


def get_minimal_default_state_for_calc():
    """calculations.py가 요구하는 최소한의 기본 상태값 반환"""
    return {
        "base_move_type": MOVE_TYPE_OPTIONS_BR[0],
        "is_storage_move": False, "apply_long_distance": False, "has_via_point": False,
        "moving_date": TODAY_DATE_OBJECT, "arrival_date": TODAY_DATE_OBJECT,
        "from_floor": "1", "to_floor": "1",
        "from_method": DEFAULT_METHOD_BR, "to_method": DEFAULT_METHOD_BR,
        "via_point_method": DEFAULT_METHOD_BR,
        "final_selected_vehicle": "1톤", # 가장 기본적인 차량으로 설정
        "add_men": 0, "add_women": 0,
        "remove_base_housewife": False, "remove_base_man": False,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "adjustment_amount": 0,
        "departure_ladder_surcharge_manual": 0, "arrival_ladder_surcharge_manual": 0,
        "storage_duration": 1, "storage_type": DEFAULT_STORAGE_TYPE_BR,
        "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        "via_point_surcharge": 0,
        "issue_tax_invoice": False, # VAT 계산 전 비용을 얻기 위해 False로 고정
        "card_payment": False,      # VAT 계산 전 비용을 얻기 위해 False로 고정
    }

def get_relevant_costs_from_state(loaded_state_data):
    """
    로드된 견적 상태를 기반으로, VAT/카드 수수료 전의 총 이사비용과
    보관이사시 각 레그별 비용요소를 계산합니다.
    """
    temp_state = get_minimal_default_state_for_calc()
    
    # 로드된 데이터로 기본값 덮어쓰기 및 타입 변환
    if loaded_state_data and isinstance(loaded_state_data, dict):
        for key, value in loaded_state_data.items():
            # 날짜 문자열 -> date 객체
            if key in ["moving_date", "arrival_date"] and isinstance(value, str):
                try: temp_state[key] = date.fromisoformat(value)
                except ValueError: temp_state[key] = TODAY_DATE_OBJECT
            # 숫자형 필드 변환 (정수 또는 실수)
            elif key in temp_state and isinstance(temp_state[key], (int, float)) and not isinstance(value, (int, float)):
                try:
                    if isinstance(temp_state[key], float): temp_state[key] = float(value or 0.0)
                    else: temp_state[key] = int(float(value or 0))
                except (ValueError, TypeError):
                     pass # 기본값 유지
            elif key.startswith("qty_") or key in temp_state : # qty_ 항목 및 기타 상태값 복사
                temp_state[key] = value
            
    # VAT/카드결제 플래그는 항상 False로 설정하여 순수 서비스 비용 계산
    temp_state['issue_tax_invoice'] = False
    temp_state['card_payment'] = False

    overall_pre_vat_total_cost, cost_items_pre_vat, _ = calculations.calculate_total_moving_cost(temp_state)

    # 비용 항목 분류
    departure_specific_sum = 0
    arrival_specific_sum = 0
    storage_fee_sum = 0
    common_splitable_sum = 0

    DEPARTURE_COST_LABELS = ["출발지 사다리차", "출발지 스카이 장비", "출발지 수동 사다리 추가"]
    ARRIVAL_COST_LABELS = ["도착지 사다리차", "도착지 스카이 장비", "도착지 수동 사다리 추가"]
    STORAGE_COST_LABEL = "보관료"
    # VAT, 카드결제 항목은 cost_items_pre_vat에 없을 것이므로 제외 목록 불필요
    EXCLUDE_LABELS_FOR_COMMON = DEPARTURE_COST_LABELS + ARRIVAL_COST_LABELS + [STORAGE_COST_LABEL, "오류"]

    for name, cost, _note in cost_items_pre_vat:
        cost_int = 0
        try: cost_int = int(float(cost or 0))
        except: pass

        if name in DEPARTURE_COST_LABELS:
            departure_specific_sum += cost_int
        elif name in ARRIVAL_COST_LABELS:
            arrival_specific_sum += cost_int
        elif name == STORAGE_COST_LABEL:
            storage_fee_sum = cost_int # 보관료는 하나만 있어야 함
        elif name not in EXCLUDE_LABELS_FOR_COMMON:
            common_splitable_sum += cost_int
            
    return {
        "overall_pre_vat_total": overall_pre_vat_total_cost,
        "common_splitable": common_splitable_sum,
        "departure_specific": departure_specific_sum,
        "arrival_specific": arrival_specific_sum,
        "storage_fee": storage_fee_sum,
        "is_storage_move": temp_state.get("is_storage_move", False), # 보관이사 여부도 반환
        "moving_date": temp_state.get("moving_date"),
        "arrival_date": temp_state.get("arrival_date"),
        "customer_phone": temp_state.get("customer_phone", "정보없음")
    }


st.set_page_config(page_title="이사 정보 일괄 조회", layout="wide")
st.title("🚚 이사 정보 일괄 조회 및 Excel 변환")
st.caption("텍스트 또는 Excel로 여러 전화번호 끝 4자리를 입력받아, 저장된 견적에서 이삿날, 연락처, 세금계산서 발행 전 이사비를 조회하여 Excel로 다운로드합니다.")

input_method = st.radio("입력 방식:", ("텍스트로 여러 번호 입력", "Excel 파일 업로드"), horizontal=True)
phone_numbers_input_str = ""
uploaded_excel_file = None
excel_column_name = "전화번호끝4자리" # 기본값

if input_method == "텍스트로 여러 번호 입력":
    phone_numbers_input_str = st.text_area("조회할 전화번호 끝 4자리를 한 줄에 하나씩 입력하세요:", height=150)
else:
    uploaded_excel_file = st.file_uploader("전화번호 끝 4자리가 포함된 Excel 파일을 업로드하세요.", type=["xlsx", "xls"])
    excel_column_name = st.text_input("전화번호 끝 4자리 정보가 있는 컬럼명을 입력하세요:", value=excel_column_name)

if st.button("📊 일괄 조회 및 Excel 생성"):
    phone_list_to_process = []
    if input_method == "텍스트로 여러 번호 입력":
        if phone_numbers_input_str.strip():
            phone_list_to_process = [num.strip() for num in phone_numbers_input_str.strip().split('\n') if num.strip().isdigit() and len(num.strip()) == 4]
            if not phone_list_to_process:
                st.warning("유효한 전화번호 끝 4자리가 입력되지 않았습니다.")
        else:
            st.warning("조회할 전화번호를 입력해주세요.")
    elif input_method == "Excel 파일 업로드":
        if uploaded_excel_file and excel_column_name.strip():
            try:
                df = pd.read_excel(uploaded_excel_file)
                if excel_column_name.strip() in df.columns:
                    phone_list_to_process = [str(num).strip() for num in df[excel_column_name.strip()].dropna() if str(num).strip().isdigit() and len(str(num).strip()) == 4]
                    if not phone_list_to_process:
                        st.warning(f"Excel 파일의 '{excel_column_name}' 컬럼에서 유효한 전화번호 끝 4자리를 찾을 수 없습니다.")
                else:
                    st.error(f"Excel 파일에 '{excel_column_name}' 컬럼이 없습니다. 컬럼명을 확인해주세요.")
            except Exception as e:
                st.error(f"Excel 파일 처리 중 오류 발생: {e}")
        elif not uploaded_excel_file:
            st.warning("Excel 파일을 업로드해주세요.")
        else:
            st.warning("전화번호가 포함된 Excel 컬럼명을 입력해주세요.")

    if phone_list_to_process:
        results_data = []
        gdrive_folder_id = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")
        
        with st.spinner(f"{len(phone_list_to_process)}개의 번호에 대해 데이터 조회 및 처리 중..."):
            all_json_files_cache = {} # 전체 파일 목록 캐시 (선택적 최적화)
            # 최적화를 위해 한번만 모든 JSON 파일 목록을 가져올 수 있으나, 파일 수가 매우 많으면 비효율적일 수 있음
            # 여기서는 각 번호마다 검색 (기존 로직과 유사)

            for idx, last_4_digits in enumerate(phone_list_to_process):
                st.progress((idx + 1) / len(phone_list_to_process), text=f"처리중: {last_4_digits} ({idx+1}/{len(phone_list_to_process)})")
                
                # 해당 번호로 끝나는 파일 검색
                # 실제로는 파일명이 전체 전화번호이므로, name contains 대신 로컬 필터링 필요
                # name_query에 last_4_digits를 넣으면 해당 문자열을 포함하는 모든 파일이 검색되므로 주의
                # 모든 JSON 파일을 가져와서 파일명으로 필터링하는 것이 더 정확함
                
                found_files_for_current_digits = []
                # 모든 JSON 파일을 한 번만 로드하도록 수정 (성능 개선)
                if not all_json_files_cache: # 처음 한 번만 실행
                    temp_all_files = gdrive.find_files_by_name_contains(name_query=".json", mime_types="application/json", folder_id=gdrive_folder_id)
                    if temp_all_files:
                        all_json_files_cache = {os.path.splitext(f['name'])[0]: f['id'] for f in temp_all_files if f.get('name','').endswith('.json')}

                
                matched_phone_files = {phone: file_id for phone, file_id in all_json_files_cache.items() if phone.endswith(last_4_digits)}

                if not matched_phone_files:
                    results_data.append({
                        "조회번호(끝4자리)": last_4_digits, "구분": "오류", 
                        "이삿날": "", "연락처": "", "이사비(VAT전)": "", 
                        "파일명": "", "상태": "해당 번호의 견적 파일 없음"
                    })
                    continue

                for full_phone_filename_stem, file_id in matched_phone_files.items():
                    loaded_state = gdrive.load_json_file(file_id)
                    if not loaded_state:
                        results_data.append({
                            "조회번호(끝4자리)": last_4_digits, "구분": "오류", 
                            "이삿날": "", "연락처": full_phone_filename_stem, 
                            "이사비(VAT전)": "", "파일명": f"{full_phone_filename_stem}.json", 
                            "상태": "파일 로드 또는 JSON 파싱 실패"
                        })
                        continue

                    try:
                        costs_info = get_relevant_costs_from_state(loaded_state)
                        moving_date_obj = costs_info["moving_date"]
                        customer_phone_val = costs_info["customer_phone"]

                        if costs_info["is_storage_move"]:
                            arrival_date_obj = costs_info["arrival_date"]
                            
                            # 비용 분할
                            common_leg_cost = round(costs_info["common_splitable"] / 2)
                            cost_leg1 = common_leg_cost + costs_info["departure_specific"]
                            cost_leg2 = (costs_info["common_splitable"] - common_leg_cost) + \
                                        costs_info["arrival_specific"] + costs_info["storage_fee"]

                            results_data.append({
                                "조회번호(끝4자리)": last_4_digits, "구분": "출발일(보관)",
                                "이삿날": moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj),
                                "연락처": customer_phone_val,
                                "이사비(VAT전)": cost_leg1,
                                "파일명": f"{full_phone_filename_stem}.json", "상태": "성공"
                            })
                            results_data.append({
                                "조회번호(끝4자리)": last_4_digits, "구분": "도착일(보관)",
                                "이삿날": arrival_date_obj.strftime('%Y-%m-%d') if isinstance(arrival_date_obj, date) else str(arrival_date_obj),
                                "연락처": customer_phone_val,
                                "이사비(VAT전)": cost_leg2,
                                "파일명": f"{full_phone_filename_stem}.json", "상태": "성공"
                            })
                        else: # 일반 이사
                            results_data.append({
                                "조회번호(끝4자리)": last_4_digits, "구분": "일반",
                                "이삿날": moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj),
                                "연락처": customer_phone_val,
                                "이사비(VAT전)": costs_info["overall_pre_vat_total"],
                                "파일명": f"{full_phone_filename_stem}.json", "상태": "성공"
                            })
                    except Exception as e_proc:
                        results_data.append({
                            "조회번호(끝4자리)": last_4_digits, "구분": "오류", 
                            "이삿날": loaded_state.get("moving_date", ""), "연락처": loaded_state.get("customer_phone", full_phone_filename_stem),
                            "이사비(VAT전)": "", "파일명": f"{full_phone_filename_stem}.json", 
                            "상태": f"데이터 처리 중 오류: {str(e_proc)[:50]}" # 오류 메시지 일부만
                        })
        
        if results_data:
            df_results = pd.DataFrame(results_data)
            # 컬럼 순서 지정
            excel_columns = ["조회번호(끝4자리)", "구분", "이삿날", "연락처", "이사비(VAT전)", "파일명", "상태"]
            df_results = df_results.reindex(columns=excel_columns)

            # Excel 파일로 변환 (메모리 내에서)
            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='xlsxwriter') as writer:
                df_results.to_excel(writer, index=False, sheet_name='조회결과')
                # 추가적인 서식 지정 가능 (예: 컬럼 너비 자동 조절)
                worksheet = writer.sheets['조회결과']
                for idx, col in enumerate(df_results):  # loop through all columns
                    series = df_results[col]
                    max_len = max((
                        series.astype(str).map(len).max(),  # len of largest item
                        len(str(series.name))  # len of column name/header
                        )) + 1  # adding a little extra space
                    worksheet.set_column(idx, idx, max_len)  # set column width
            
            excel_bytes = output_excel.getvalue()
            st.success("모든 번호 처리가 완료되었습니다! 아래 버튼으로 Excel 파일을 다운로드하세요.")
            st.download_button(
                label="📥 조회 결과 Excel 다운로드",
                data=excel_bytes,
                file_name=f"이사정보_조회결과_{datetime.now(KST).strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("처리할 데이터가 없거나 조회된 결과가 없습니다.")