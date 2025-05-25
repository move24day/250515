# state_manager.py

import streamlit as st
from datetime import datetime, date
import pytz

try:
    import data
except ImportError as e:
    st.error(f"State Manager: 필수 모듈 data.py 로딩 실패 - {e}")
    st.stop()

try:
    MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions else ["가정 이사 🏠", "사무실 이사 🏢"]
except Exception as e:
    MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"] 
    st.warning(f"data.py에서 이사 유형 로딩 중 오류 발생: {e}. 기본값을 사용합니다.")

# 저장할 상태 키 목록 정의
STATE_KEYS_TO_SAVE = [
    "base_move_type", "is_storage_move", "storage_type", "apply_long_distance", "long_distance_selector",
    "customer_name", "customer_phone", "customer_email", 
    "moving_date", "arrival_date", "storage_duration", "storage_use_electricity",
    "contract_date", # 계약일 추가
    "from_address_full", "from_floor", "from_method", 
    "to_address_full", "to_floor", "to_method", 
    "has_via_point", "via_point_address", "via_point_floor", "via_point_method", "via_point_surcharge",
    "parking_available", "fridge_disassembly", "ac_transfer_install", "special_notes",
    "vehicle_select_radio", "manual_vehicle_select_value", "final_selected_vehicle",
    "add_men", "add_women", "remove_base_housewife", "remove_base_man",
    "sky_hours_from", "sky_hours_final",
    "dispatched_1t", "dispatched_2_5t","dispatched_3_5t", "dispatched_5t",
    "has_waste_check", "waste_tons_input",
    "date_opt_0_widget", "date_opt_1_widget", "date_opt_2_widget", "date_opt_3_widget", "date_opt_4_widget", # 날짜 옵션 위젯 상태
    "manual_ladder_from_check", "departure_ladder_surcharge_manual", # 출발지 수동 사다리
    "manual_ladder_to_check", "arrival_ladder_surcharge_manual",       # 도착지 수동 사다리
    "deposit_amount", "adjustment_amount", # tab3 에서 직접 입력받는 값들
    "issue_tax_invoice", "card_payment", # 결제 옵션
    "move_time_option", "afternoon_move_details", # 이사 시간 옵션
    # "uploaded_image_paths" # 이미지 경로는 로컬 시스템에 따라 달라지므로 직접 저장/로드는 부적합할 수 있음
]

# 품목 수량 키는 동적으로 추가 (qty_ 접두사 사용)

def get_default_times_for_date(selected_date):
    if not isinstance(selected_date, date):
        selected_date = date.today()
    return selected_date.strftime("%H:%M") # 현재는 날짜만 사용, 시간은 별도 입력

def initialize_session_state(update_basket_callback=None):
    try:
        KST = pytz.timezone("Asia/Seoul")
    except pytz.UnknownTimeZoneError:
        KST = pytz.utc
    
    today_kst = datetime.now(KST).date()
    
    defaults = {
        "base_move_type": MOVE_TYPE_OPTIONS[0],
        "is_storage_move": False,
        "storage_type": data.STORAGE_TYPES[0] if hasattr(data, "STORAGE_TYPES") and data.STORAGE_TYPES else "컨테이너 보관 📦",
        "apply_long_distance": False,
        "long_distance_selector": data.long_distance_options[0] if hasattr(data, "long_distance_options") and data.long_distance_options else "선택 안 함",
        "customer_name": "", "customer_phone": "", "customer_email": "",
        "moving_date": today_kst,
        "arrival_date": today_kst, # 보관이사 아닐 시 moving_date와 동일하게 시작
        "contract_date": today_kst, # 계약일 기본값 오늘
        "storage_duration": 1, "storage_use_electricity": False,
        "from_address_full": "", "from_floor": "", 
        "from_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "계단 🚶",
        "to_address_full": "", "to_floor": "", 
        "to_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "계단 🚶",
        "has_via_point": False, "via_point_address": "", "via_point_floor": "", 
        "via_point_method": data.METHOD_OPTIONS[0] if hasattr(data, "METHOD_OPTIONS") and data.METHOD_OPTIONS else "계단 🚶",
        "via_point_surcharge": 0,
        "parking_available": False, "fridge_disassembly": False, "ac_transfer_install": False,
        "special_notes": "",
        "vehicle_select_radio": "자동 추천 차량 사용",
        "manual_vehicle_select_value": None, # data.py의 차량 목록 첫번째로 설정될 수 있음
        "final_selected_vehicle": None,
        "recommended_vehicle_auto": None, "recommended_base_price_auto": 0.0,
        "total_volume": 0.0, "total_weight": 0.0,
        "add_men": 0, "add_women": 0,
        "remove_base_housewife": False, "remove_base_man": False,
        "sky_hours_from": 1, "sky_hours_final": 1,
        "dispatched_1t":0, "dispatched_2_5t":0, "dispatched_3_5t":0, "dispatched_5t":0,
        "has_waste_check": False, "waste_tons_input": 0.5,
        "date_opt_0_widget": False, "date_opt_1_widget": False, "date_opt_2_widget": False,
        "date_opt_3_widget": False, "date_opt_4_widget": False,
        "manual_ladder_from_check": False, "departure_ladder_surcharge_manual": getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0),
        "manual_ladder_to_check": False, "arrival_ladder_surcharge_manual": getattr(data, 'MANUAL_LADDER_SURCHARGE_DEFAULT', 0),
        "deposit_amount": 0, "adjustment_amount": 0, 
        "issue_tax_invoice": False, "card_payment": False,
        "pdf_ready": False, "pdf_bytes": None,
        "selected_items": {}, # 물품 선택용 (Tab2)
        "move_time_option": "오전", "afternoon_move_details": "",
        "customer_final_pdf_data": None, # 이메일 발송 및 재다운로드용
        "uploaded_image_paths": [], # 업로드된 이미지 경로 리스트
        # Tab3의 수기 입력 필드용 (저장/로드 대상)
        "tab3_deposit_amount": 0, # load_state_from_data에서 deposit_amount로 매핑
        "tab3_adjustment_amount": 0, # load_state_from_data에서 adjustment_amount로 매핑
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    # 품목 수량 초기화 (data.py 기반)
    if hasattr(data, 'item_definitions') and data.item_definitions:
        for move_type_key, sections in data.item_definitions.items():
            if isinstance(sections, dict):
                for section_key, items_in_section in sections.items():
                    if isinstance(items_in_section, list):
                        for item_name_key in items_in_section:
                            state_key = f"qty_{move_type_key}_{section_key}_{item_name_key}"
                            if state_key not in st.session_state:
                                st.session_state[state_key] = 0
    
    # 동기화 콜백이 있다면 최초 1회 실행 (부피/무게 및 추천 차량 계산 등)
    if callable(update_basket_callback):
        update_basket_callback()


def prepare_state_for_save(current_state_dict):
    state_to_save = {}
    for key in STATE_KEYS_TO_SAVE:
        if key in current_state_dict:
            value = current_state_dict[key]
            # 날짜 객체는 ISO 문자열로 변환
            if isinstance(value, date):
                state_to_save[key] = value.isoformat()
            else:
                state_to_save[key] = value
    
    # 품목 수량(qty_ 접두사) 동적 저장
    for key, value in current_state_dict.items():
        if key.startswith("qty_"):
            state_to_save[key] = value
            
    # Tab3의 수기 입력 필드 값들도 명시적으로 저장 (STATE_KEYS_TO_SAVE에 이미 포함됨)
    # "deposit_amount", "adjustment_amount"는 UI 위젯과 직접 연결되므로 session_state에서 바로 가져옴
    # "regional_ladder_surcharge"는 사용되지 않으므로 제외 또는 검토 필요

    # 버전 정보 추가 (선택적)
    state_to_save["app_version"] = "1.1.0" # 예시 버전
    state_to_save["saved_at_kst"] = utils.get_current_kst_time_str() if hasattr(utils, "get_current_kst_time_str") else datetime.now(pytz.timezone("Asia/Seoul") if "pytz" in globals() else None).isoformat()

    return state_to_save


def load_state_from_data(loaded_data_dict, update_basket_callback=None):
    if not isinstance(loaded_data_dict, dict):
        st.error("로드할 데이터 형식이 올바르지 않습니다.")
        return

    # 먼저 기본값으로 현재 세션 상태를 한번 정리 (선택적: 누락된 키에 대한 기본값 보장)
    # initialize_session_state(update_basket_callback) # 이렇게 하면 기존 입력이 초기화될 수 있으므로 주의

    # 날짜 객체 변환을 위한 필드 목록
    date_fields = ["moving_date", "arrival_date", "contract_date"] # contract_date 추가

    for key_from_save_file, value_from_file in loaded_data_dict.items():
        if key_from_save_file in STATE_KEYS_TO_SAVE or key_from_save_file.startswith("qty_"):
            target_value = value_from_file
            if key_from_save_file in date_fields and isinstance(value_from_file, str):
                try:
                    target_value = date.fromisoformat(value_from_file)
                except ValueError:
                    st.warning(f"날짜 형식 오류 ({key_from_save_file}: {value_from_file}). 오늘 날짜로 설정합니다.")
                    target_value = date.today() 
            
            # 숫자형으로 변환 시도 (로드된 JSON은 모두 문자열일 수 있음)
            # Tab3의 특정 금액 필드들은 UI 위젯과 직접 연결되므로, state_manager의 기본값 설정을 따름
            if key_from_save_file in ["deposit_amount", "adjustment_amount", "via_point_surcharge", 
                                     "departure_ladder_surcharge_manual", "arrival_ladder_surcharge_manual",
                                     "add_men", "add_women", "storage_duration", 
                                     "sky_hours_from", "sky_hours_final",
                                     "dispatched_1t", "dispatched_2_5t","dispatched_3_5t", "dispatched_5t",
                                     "waste_tons_input"] or key_from_save_file.startswith("qty_") :
                try:
                    if isinstance(target_value, str) and not target_value: # 빈 문자열은 0으로
                        target_value = 0
                    
                    if key_from_save_file == "waste_tons_input": # 소수점 허용
                        target_value = float(target_value or 0)
                    else: # 정수형으로
                        target_value = int(float(target_value or 0)) # None 또는 빈 문자열 방지
                except (ValueError, TypeError):
                    st.warning(f"숫자 형식 오류 ({key_from_save_file}: {value_from_file}). 0으로 설정합니다.")
                    target_value = 0 if key_from_save_file != "waste_tons_input" else 0.0
            
            st.session_state[key_from_save_file] = target_value
        elif key_from_save_file in ["tab3_deposit_amount", "tab3_adjustment_amount"]: # 이전 버전 호환성
            ui_key = key_from_save_file.replace("tab3_", "")
            try: st.session_state[ui_key] = int(float(value_from_file or 0))
            except: st.session_state[ui_key] = 0


    # 로드 후 콜백 실행 (예: 부피/무게 재계산, 차량 추천)
    if callable(update_basket_callback):
        update_basket_callback()
    
    st.toast("견적 정보가 성공적으로 로드되었습니다!")
