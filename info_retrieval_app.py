# info_retrieval_app.py
import streamlit as st
import os
from datetime import date, datetime # datetime 추가
import pytz # 시간대 처리

# 기존 프로젝트 모듈 임포트
try:
    import google_drive_helper as gdrive
    import calculations
    import data # calculations 모듈이 data 모듈을 사용합니다.
    # state_manager의 일부 로직(기본값, 타입 변환 등)을 참조하여 단순화된 형태로 사용합니다.
    # from state_manager import MOVE_TYPE_OPTIONS # 필요시 사용
except ImportError as e:
    st.error(f"오류: 필요한 모듈(google_drive_helper, calculations, data)을 찾을 수 없습니다. 현재 디렉토리를 확인해주세요: {e}")
    st.stop()

# 시간대 설정 (state_manager.py 와 유사하게)
try:
    KST = pytz.timezone("Asia/Seoul")
except pytz.UnknownTimeZoneError:
    KST = pytz.utc

# state_manager.py의 MOVE_TYPE_OPTIONS 와 유사하게 정의 (calculations.py 내에서 필요할 수 있음)
if 'MOVE_TYPE_OPTIONS' not in globals() and hasattr(data, 'item_definitions'):
    MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if data.item_definitions and isinstance(data.item_definitions, dict) else ["가정 이사 🏠", "사무실 이사 🏢"]
elif 'MOVE_TYPE_OPTIONS' not in globals():
    MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]


def get_default_state_for_calc():
    """
    calculations.calculate_total_moving_cost 에 필요한 최소한의 기본값을 포함하는 딕셔너리를 반환합니다.
    실제 state_manager.py의 defaults와 유사하게 구성하되, 이 앱의 목적에 맞게 단순화합니다.
    """
    try: default_date = datetime.now(KST).date()
    except Exception: default_date = datetime.now().date()
    
    return {
        "base_move_type": MOVE_TYPE_OPTIONS[0],
        "is_storage_move": False,
        "apply_long_distance": False,
        "moving_date": default_date,
        "arrival_date": default_date,
        "from_floor": "1", "to_floor": "1",
        "from_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "계단 🚶",
        "to_method": data.METHOD_OPTIONS[0] if hasattr(data, 'METHOD_OPTIONS') and data.METHOD_OPTIONS else "계단 🚶",
        "final_selected_vehicle": "1톤", # 견적 계산을 위해 기본 차량 필요
        "add_men": 0, "add_women": 0,
        "remove_base_housewife": False, "remove_base_man": False,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "adjustment_amount": 0,
        "departure_ladder_surcharge_manual": 0,
        "arrival_ladder_surcharge_manual": 0,
        "storage_duration": 1, "storage_type": data.DEFAULT_STORAGE_TYPE if hasattr(data, 'DEFAULT_STORAGE_TYPE') else "컨테이너 보관 📦",
        "storage_use_electricity": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, 'long_distance_options') and data.long_distance_options else "선택 안 함",
        "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        "has_via_point": False, "via_point_surcharge": 0,
        "issue_tax_invoice": False, # 이 값을 False로 고정하여 "세금계산서 발행 전 이사비" 계산
        "card_payment": False,      # 이 값을 False로 고정
        # 여기에 calculations.py 가 참조하는 모든 st.session_state 키의 기본값을 넣어주어야 합니다.
        # (예: qty_이사유형_품목섹션_품목명 등) - 이것들은 견적마다 다르므로 로드된 데이터 사용
    }

def get_pre_vat_moving_cost(loaded_state_data):
    """
    로드된 견적 상태를 기반으로 '세금계산서 발행 전 이사비' (VAT 및 카드 수수료 제외 총액)를 계산합니다.
    """
    temp_state = get_default_state_for_calc() # 기본값으로 전체 상태 구조를 만듭니다.
    
    # 로드된 데이터로 기본값을 덮어씁니다.
    if loaded_state_data and isinstance(loaded_state_data, dict):
        for key, value in loaded_state_data.items():
            if key in temp_state or key.startswith("qty_"): # qty_ 항목들도 복사
                # 날짜 문자열을 date 객체로 변환
                if key in ["moving_date", "arrival_date"] and isinstance(value, str):
                    try:
                        temp_state[key] = date.fromisoformat(value)
                    except ValueError:
                        temp_state[key] = get_default_state_for_calc()[key] # 파싱 실패시 기본값
                # 숫자형 변환 (정수 또는 실수)
                elif isinstance(temp_state.get(key), (int, float)) and not isinstance(value, (int,float)):
                    try:
                        if isinstance(temp_state.get(key), float): temp_state[key] = float(value)
                        else: temp_state[key] = int(float(value))
                    except (ValueError, TypeError):
                         temp_state[key] = get_default_state_for_calc().get(key,0) # 변환 실패시 기본값
                else:
                    temp_state[key] = value
    
    # 세금/카드 옵션은 계산 목적상 강제로 False 설정
    temp_state['issue_tax_invoice'] = False
    temp_state['card_payment'] = False

    # calculate_total_moving_cost 함수는 (총비용, 비용항목리스트, 인원정보)를 반환
    # 이 때 issue_tax_invoice와 card_payment이 False이므로 반환되는 총비용이 
    # 세금계산서/카드결제 전 순수 이사비용이 됩니다.
    pre_vat_cost, _, _ = calculations.calculate_total_moving_cost(temp_state)
    return pre_vat_cost


st.set_page_config(page_title="이사 정보 간편 조회", layout="wide")
st.title("📞 이사 정보 간편 조회")
st.caption("저장된 견적 데이터에서 전화번호 끝 4자리로 이삿날, 연락처, 세금계산서 발행 전 이사비를 조회합니다.")

phone_last_4 = st.text_input("조회할 전화번호 끝 4자리를 입력하세요:", max_chars=4)

if st.button("정보 조회하기"):
    if len(phone_last_4) == 4 and phone_last_4.isdigit():
        with st.spinner("Google Drive에서 데이터 검색 중..."):
            gdrive_folder_id = st.secrets.get("gcp_service_account", {}).get("drive_folder_id")
            
            # 파일 이름에 전화번호가 포함되므로, 특정 쿼리 없이 모든 JSON을 가져와 필터링
            all_json_files = gdrive.find_files_by_name_contains(
                name_query="", 
                mime_types="application/json",
                folder_id=gdrive_folder_id
            )

            found_records_display = []
            if not all_json_files:
                st.warning("Google Drive에서 파일을 찾을 수 없거나 접근 권한이 없습니다.")
            else:
                for file_info in all_json_files:
                    file_name = file_info.get('name', '')
                    file_id = file_info.get('id')
                    if file_name and file_id:
                        # 파일명 (확장자 제외)이 전화번호이므로, 해당 전화번호가 끝 4자리로 끝나는지 확인
                        phone_part_in_filename = os.path.splitext(file_name)[0]
                        if phone_part_in_filename.endswith(phone_last_4):
                            loaded_data_dict = gdrive.load_json_file(file_id)
                            if loaded_data_dict:
                                pre_vat_moving_cost = get_pre_vat_moving_cost(loaded_data_dict)
                                
                                moving_date_str = loaded_data_dict.get("moving_date", "정보없음")
                                # 날짜 형식 변환 (YYYY-MM-DD -> MM-DD 또는 그대로)
                                try:
                                    parsed_moving_date = date.fromisoformat(moving_date_str)
                                    display_moving_date = parsed_moving_date.strftime("%m-%d")
                                except (ValueError, TypeError):
                                    display_moving_date = moving_date_str # 파싱 실패시 원본 표시

                                found_records_display.append({
                                    "filename": file_name,
                                    "moving_date": display_moving_date,
                                    "customer_phone": loaded_data_dict.get("customer_phone", "정보없음"),
                                    "pre_vat_cost": pre_vat_moving_cost
                                })
            if found_records_display:
                st.success(f"총 {len(found_records_display)}개의 일치하는 기록을 찾았습니다.")
                for record in found_records_display:
                    st.markdown("---")
                    st.markdown(f"##### 📝 파일명: `{record['filename']}`")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(label="🗓️ 이삿날", value=record['moving_date'])
                    with col2:
                        st.metric(label="📞 연락처", value=record['customer_phone'])
                    with col3:
                        st.metric(label="💰 이사비 (VAT/카드 전)", value=f"{record['pre_vat_cost']:,.0f} 원")
            else:
                st.info(f"'{phone_last_4}'로 끝나는 전화번호의 견적을 찾지 못했습니다.")
    else:
        st.error("전화번호 끝 4자리를 정확히 입력해주세요.")
