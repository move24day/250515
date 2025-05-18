# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date, datetime # datetime 추가
import math
import traceback
import re

try:
    import data as app_data_for_img_gen # data.py 임포트
    import utils # utils.py 임포트 (get_item_qty 사용 위함)
except ImportError:
    app_data_for_img_gen = None
    utils = None
    print("Warning [image_generator.py]: data.py or utils.py not found, some defaults/functionalities might not be available.")


BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
# 시스템에 설치된 나눔고딕 폰트 경로 또는 프로젝트 내 폰트 파일 경로로 지정해야 합니다.
# 예시: FONT_PATH_REGULAR = "NanumGothic.ttf" (Streamlit Cloud에 폰트 포함 시)
# 로컬 환경에서는 전체 경로 또는 상대 경로를 정확히 지정해야 합니다.
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf") 
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")


TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)
TEXT_COLOR_BLUE = (20, 20, 180)

BASE_FONT_SIZE = 18
item_y_start_val = 334
item_y_spacing_val = 28.8 # Y 간격 미세 조정 가능
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491 # 바구니류 X 좌표
item_x_col2_others_val = 491  # 기타 품목 (2열) X 좌표
item_x_col3_val = 756

original_vehicle_y_calc = int(275 + item_y_spacing_val)
vehicle_display_y_val = original_vehicle_y_calc - 2 # 차량정보 Y 위치
vehicle_number_x_val = 90 # 차량 톤수 X 위치
actual_vehicles_text_x_val = item_x_col2_others_val # 실제 투입 차량 X 위치

costs_section_x_align_right_val = 410 # 비용 항목 우측 정렬 기준 X
work_method_fee_label_x_val = 35    # 작업 방법 레이블 X 위치

_y_from_floor_orig = 226
_y_to_floor_orig = 258
work_method_text_display_x_val = int((item_x_col1_val + item_x_col2_baskets_val) / 2) # 출발/도착 작업 방법 텍스트 중앙 X

# 기존 Y 좌표값 (참고용)
_y_living_room_cabinet_orig = 677
_y_sofa_3seater_orig = 549
_y_main_fee_yellow_box_orig = 775 # 메인 비용 (노란 박스) Y
_y_grand_total_orig = 861         # 총계 Y

# 비용 섹션 Y 좌표 재조정
from_work_fee_y_val = _y_main_fee_yellow_box_orig - item_y_spacing_val * 2.5 # 메인 비용 박스 위로 조정
to_work_fee_y_val = from_work_fee_y_val + item_y_spacing_val
# option_fee_y_val = to_work_fee_y_val + item_y_spacing_val # 옵션 비용 (예: 에어컨)을 표시할 경우 Y

fees_x_val_right_aligned = item_x_col3_val # 이삿짐 항목 3열과 비슷한 X 위치 (우측 정렬된 금액용)

deposit_y_val = from_work_fee_y_val # 계약금 Y 위치를 출발지 작업비와 동일 선상에 (조정 가능)
storage_fee_y_val = _y_main_fee_yellow_box_orig # 보관료는 메인 비용과 같은 Y (오른쪽 다른 컬럼)
remaining_balance_y_val = deposit_y_val + item_y_spacing_val * 1.2 # 잔금 Y 위치

grand_total_y_new = _y_grand_total_orig + 4 # 총계 Y 위치 (기존 값 기반)

special_notes_start_y_val = int(grand_total_y_new + item_y_spacing_val * 1.5) # 고객 요구사항 시작 Y
special_notes_x_val = 80
special_notes_max_width_val = 700 # 고객 요구사항 텍스트 최대 너비
special_notes_font_size_val = BASE_FONT_SIZE # 고객명과 동일 크기

quote_date_y_val = 130 # 견적일 Y
move_type_summary_y_val = int(quote_date_y_val - (item_y_spacing_val * 0.7) - 20 - 50) # 이사 종류 요약 Y
move_type_summary_x_val = 640 + 100 # 이사 종류 요약 X
move_type_summary_font_size_val = BASE_FONT_SIZE
move_type_summary_max_width_val = 150 # 이사 종류 요약 최대 너비


def get_adjusted_font_size(original_size_ignored, field_key):
    # ... (이 함수는 이전과 동일하게 유지)
    if field_key == "customer_name": return BASE_FONT_SIZE
    if field_key == "customer_phone": return BASE_FONT_SIZE - 2
    if field_key.startswith("item_") and field_key not in ["item_x_col1_val", "item_x_col2_baskets_val", "item_x_col2_others_val", "item_x_col3_val"]:
        return item_font_size_val
    if field_key in ["grand_total", "remaining_balance_display"]: return BASE_FONT_SIZE + 2
    # "fee_value_next_to_ac_right"는 FIELD_MAP에서 제거했으므로, 이 조건도 불필요
    # if field_key in ["fee_value_next_to_ac_right"]: return 14
    if field_key in ["from_work_method_text_display", "to_work_method_text_display"]: return BASE_FONT_SIZE - 2
    if field_key in ["from_method_label", "to_method_label",
                     "from_method_fee_value", "to_method_fee_value",
                     "deposit_amount_display", "storage_fee_display"]:
        return BASE_FONT_SIZE
    if field_key in ["vehicle_type_numbers_only", "actual_dispatched_vehicles_display"]: return BASE_FONT_SIZE -2
    if field_key == "special_notes_display": return special_notes_font_size_val
    if field_key == "move_type_summary_display": return move_type_summary_font_size_val
    return BASE_FONT_SIZE

FIELD_MAP = {
    "move_type_summary_display": {
        "x": move_type_summary_x_val, "y": move_type_summary_y_val,
        "size": get_adjusted_font_size(0, "move_type_summary_display"), "font": "bold",
        "color": TEXT_COLOR_BLUE, "align": "right", "max_width": move_type_summary_max_width_val, "line_spacing_factor": 1.1
    },
    "customer_name":  {"x": 175, "y": 130, "size": get_adjusted_font_size(0, "customer_name"), "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "customer_phone": {"x": 412, "y": 130, "size": get_adjusted_font_size(0, "customer_phone"), "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "quote_date":     {"x": 640, "y": quote_date_y_val, "size": get_adjusted_font_size(0, "quote_date"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "moving_date":    {"x": 640, "y": 161, "size": get_adjusted_font_size(0, "moving_date"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "from_location":  {"x": 175, "y": 161, "size": get_adjusted_font_size(0, "from_location"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},
    "to_location":    {"x": 175, "y": 192, "size": get_adjusted_font_size(0, "to_location"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},
    "from_floor":     {"x": 180, "y": _y_from_floor_orig, "size": get_adjusted_font_size(0, "from_floor"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "to_floor":       {"x": 180, "y": _y_to_floor_orig, "size": get_adjusted_font_size(0, "to_floor"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "vehicle_type_numbers_only": {"x": vehicle_number_x_val, "y": int(vehicle_display_y_val), "size": get_adjusted_font_size(0, "vehicle_type_numbers_only"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": (item_x_col1_val - vehicle_number_x_val - 5)},
    "actual_dispatched_vehicles_display": {"x": actual_vehicles_text_x_val, "y": int(vehicle_display_y_val), "size": get_adjusted_font_size(0, "actual_dispatched_vehicles_display"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 220},

    "workers_male":   {"x": 758, "y": 228, "size": get_adjusted_font_size(0, "workers_male"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "workers_female": {"x": 758, "y": 258, "size": get_adjusted_font_size(0, "workers_female"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "from_work_method_text_display": {"x": work_method_text_display_x_val, "y": _y_from_floor_orig, "size": get_adjusted_font_size(0, "from_work_method_text_display"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "to_work_method_text_display":   {"x": work_method_text_display_x_val, "y": _y_to_floor_orig,   "size": get_adjusted_font_size(0, "to_work_method_text_display"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    # --- 품목 수량 표시 위치 정의 (ITEM_KEY_MAP과 연동) ---
    "item_jangrong":    {"x": item_x_col1_val, "y": item_y_start_val, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_double_bed":  {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_3dan": {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 4.2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_normal": {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 5.3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 6.4), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": item_x_col1_val, "y": _y_sofa_3seater_orig, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_1seater":{"x": item_x_col1_val, "y": int(_y_sofa_3seater_orig + item_y_spacing_val * 1.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_dining_table":{"x": item_x_col1_val, "y": int(_y_sofa_3seater_orig + item_y_spacing_val * 2.2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": item_x_col1_val, "y": int(_y_sofa_3seater_orig + item_y_spacing_val * 3.3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": item_x_col1_val, "y": _y_living_room_cabinet_orig, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_digital": {"x": item_x_col1_val, "y": int(_y_living_room_cabinet_orig + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_washing_machine": {"x": item_x_col1_val, "y": int(_y_living_room_cabinet_orig + item_y_spacing_val * 2.2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_computer":    {"x": item_x_col2_others_val, "y": item_y_start_val, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_executive_desk": {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_bookshelf":   {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 4), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 5), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 6), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_basket":      {"x": item_x_col2_baskets_val, "y": 549, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_medium_box":  {"x": item_x_col2_baskets_val, "y": 581, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_large_box":   {"x": item_x_col2_baskets_val, "y": int(581 + item_y_spacing_val * 0.45), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_book_box":    {"x": item_x_col2_baskets_val, "y": int(581 + item_y_spacing_val * 1.45), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_plant_box":   {"x": item_x_col2_others_val, "y": 680, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": item_x_col2_others_val, "y": 709, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": item_x_col2_others_val, "y": 738, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_styler":      {"x": item_x_col3_val, "y": item_y_start_val, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 4), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 5), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 6), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 8.9), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_angle_shelf": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 10), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 11.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 12.15), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 13.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    # --- 품목 정의 끝 ---

    # --- 비용 표시 위치 정의 ---
    # "fee_value_next_to_ac_right" 항목 삭제됨 (Y:680 위치)
    
    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": _y_main_fee_yellow_box_orig, "size": get_adjusted_font_size(0, "main_fee_yellow_box"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": costs_section_x_align_right_val, "y": int(grand_total_y_new), "size": get_adjusted_font_size(0, "grand_total"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},

    "from_method_label":  {"x": work_method_fee_label_x_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "from_method_fee_value": {"x": costs_section_x_align_right_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "to_method_label":    {"x": work_method_fee_label_x_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "to_method_fee_value":  {"x": costs_section_x_align_right_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "deposit_amount_display":   {"x": fees_x_val_right_aligned, "y": int(deposit_y_val), "size": get_adjusted_font_size(0, "deposit_amount_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee_display":      {"x": fees_x_val_right_aligned, "y": int(storage_fee_y_val), "size": get_adjusted_font_size(0, "storage_fee_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # 보관료 위치 (메인비용과 같은 Y, 다른 X)
    "remaining_balance_display":{"x": fees_x_val_right_aligned, "y": int(remaining_balance_y_val), "size": get_adjusted_font_size(0, "remaining_balance_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "special_notes_display": {
        "x": special_notes_x_val, "y": special_notes_start_y_val,
        "size": get_adjusted_font_size(0, "special_notes_display"), "font": "regular",
        "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": special_notes_max_width_val, "line_spacing_factor": 1.3
    }
}

ITEM_KEY_MAP = {
    # data.py의 품목명과 FIELD_MAP의 item_XXX 키를 정확히 매칭
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장": "item_drawer_5dan",
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door",
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand",
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater", "식탁(4인)": "item_dining_table",
    "에어컨": "item_ac_left", # 에어컨 수량은 여기에 표시됨
    "거실장": "item_living_room_cabinet", # data.py에 "장식장" 대신 "거실장"으로 변경된 것 반영
    "피아노(디지털)": "item_piano_digital",
    "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer", # data.py에 "오디오 및 스피커" 대신 사용
    "사무실책상": "item_executive_desk",
    "책상&의자": "item_desk", # "사무실 책상"과 "책상&의자" 구분
    "책장": "item_bookshelf",
    # "의자": "item_chair", # "책상&의자"에 포함될 수도, 단독 의자일 수도 있음. 양식에 "의자" 항목 없으면 주석 처리.
    # "테이블": "item_table", # "소파 테이블" 또는 "식탁"과 구분 필요. 양식에 "테이블" 항목 없으면 주석 처리.
    # "담요": "item_blanket", # 포장 자재인지, 이사짐인지. 양식에 없으면 주석.
    "바구니": "item_basket",
    "중박스": "item_medium_box", # "중자바구니"와 data.py 및 FIELD_MAP 일관성 확인
    # "중대박스": "item_large_box", # data.py에 '중대박스' 품목 및 FIELD_MAP에 'item_large_box' 정의 필요
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box", # FIELD_MAP에 'item_clothes_box' 사용
    "스타일러": "item_styler",
    "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic",
    # "복합기": "item_copier", # data.py에 '복합기' 품목 정의 필요
    "TV(45인치)": "item_tv_45",
    "TV(75인치)": "item_tv_stand", # FIELD_MAP 키가 'item_tv_stand'임. TV 자체를 의미하는지, 스탠드를 의미하는지 명확히.
    # "벽걸이": "item_wall_mount_item", # data.py에 '벽걸이' 품목 정의 및 종류(TV, 에어컨 등) 명시 필요
    "금고": "item_safe",
    "앵글": "item_angle_shelf",
    # "파티션": "item_partition", # data.py에 '파티션' 품목 정의 필요
    # "5톤진입": "item_5ton_access", # 품목이 아닌 조건일 가능성. FIELD_MAP 키 확인.
    # "이불박스": "item_duvet_box" # data.py에 '이불박스' 품목 정의 필요
}

# ... (get_text_dimensions, _get_font, _draw_text_with_alignment, _format_currency 함수는 이전과 동일)
def get_text_dimensions(text_string, font):
    if not text_string: return 0,0
    if hasattr(font, 'getbbox'): # Preferred method for modern Pillow
        try:
            bbox = font.getbbox(str(text_string))
            width = bbox[2] - bbox[0]
            ascent, descent = font.getmetrics()
            height = ascent + descent # metrics sum for total line height
        except Exception: # Fallback for some PIL/Pillow versions or font issues
            if hasattr(font, 'getlength'): width = font.getlength(str(text_string))
            else: width = len(str(text_string)) * (font.size if hasattr(font, 'size') else 10) / 2 # Rough estimate
            ascent, descent = font.getmetrics()
            height = ascent + descent
    elif hasattr(font, 'getmask'): # Older PIL method
        try:
            width, height = font.getmask(str(text_string)).size
        except Exception: # Fallback if getmask fails
            ascent, descent = font.getmetrics()
            height = ascent + descent
            width = font.getlength(str(text_string)) if hasattr(font, 'getlength') else len(str(text_string)) * height / 2
    else: # Basic fallback if no advanced methods are available
        ascent, descent = font.getmetrics()
        height = ascent + descent
        if hasattr(font, 'getlength'):
            width = font.getlength(str(text_string))
        else: # Very rough estimate if no length method
            width = len(str(text_string)) * height / 2
    return width, height

def _get_font(font_type="regular", size=12):
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD
        # else: print(f"Warning: Bold font {FONT_PATH_BOLD} not found, using regular.")

    # 폰트 파일 존재 여부 최종 확인
    if not os.path.exists(font_path_to_use):
        print(f"ERROR [ImageGenerator]: Font file NOT FOUND at '{font_path_to_use}'. Falling back to PIL default.")
        try:
            return ImageFont.load_default(size=size)
        except TypeError: # Older PIL version might not support size for load_default
            return ImageFont.load_default()
        except Exception as e_pil_font:
            print(f"CRITICAL: Error loading default PIL font: {e_pil_font}")
            raise # Re-raise if default also fails, as it's a critical issue

    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError: # Font file not found or cannot be read by Pillow
        print(f"IOError [ImageGenerator]: Font '{font_path_to_use}' found but unreadable by Pillow. Falling back to default.")
        try: return ImageFont.load_default(size=size)
        except TypeError: return ImageFont.load_default()
        except Exception as e_pil_font_io:
            print(f"CRITICAL: Error loading default PIL font after IOError: {e_pil_font_io}")
            raise
    except Exception as e_font: # Other font loading errors
        print(f"General Error loading font {font_path_to_use}: {e_font}")
        raise

def _draw_text_with_alignment(draw, text, x, y, font, color, align="left", max_width=None, line_spacing_factor=1.2):
    if text is None: text = ""
    text = str(text)
    lines = []

    if max_width:
        words = text.split(' ')
        current_line = ""
        for word in words:
            word_width, _ = get_text_dimensions(word, font)
            if word_width > max_width and len(word) > 1:
                if current_line: lines.append(current_line.strip())
                temp_word_line = ""
                for char_idx, char_in_word in enumerate(word): # 변수명 충돌 방지
                    temp_word_line_plus_char_width, _ = get_text_dimensions(temp_word_line + char_in_word, font)
                    if temp_word_line_plus_char_width <= max_width:
                        temp_word_line += char_in_word
                    else:
                        lines.append(temp_word_line)
                        temp_word_line = char_in_word
                if temp_word_line: lines.append(temp_word_line)
                current_line = ""
                continue
            current_line_plus_word_width, _ = get_text_dimensions(current_line + word + " ", font) if current_line else get_text_dimensions(word + " ", font)
            if current_line_plus_word_width <= max_width:
                current_line += word + " "
            else:
                if current_line: lines.append(current_line.strip())
                current_line = word + " "
        if current_line.strip(): lines.append(current_line.strip())
        if not lines and text: lines.append(text)
    else:
        lines.extend(text.split('\n'))

    current_y_draw = y # 변수명 변경 current_y -> current_y_draw
    first_line = True
    _, typical_char_height = get_text_dimensions("A", font)
    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1:
            current_y_draw += int(typical_char_height * line_spacing_factor)
            continue
        text_width_draw, _ = get_text_dimensions(line, font) # 변수명 변경
        actual_x_draw = x # 변수명 변경
        if align == "right": actual_x_draw = x - text_width_draw
        elif align == "center": actual_x_draw = x - text_width_draw / 2
        
        # anchor='lt' (left-top)를 기본으로 사용. Pillow 최신 버전은 getbbox 등으로 더 정확한 위치 계산 가능.
        # 여기서는 단순 top-left 기준으로 그림.
        draw.text((actual_x_draw, current_y_draw), line, font=font, fill=color) 
        current_y_draw += int(typical_char_height * line_spacing_factor)
        first_line = False
    return current_y_draw


def _format_currency(amount_val):
    if amount_val is None or str(amount_val).strip() == "": return ""
    try:
        num_val = float(str(amount_val).replace(",", "").strip())
        num = int(num_val)
        return f"{num:,}"
    except ValueError:
        return str(amount_val)

def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
    except FileNotFoundError:
        print(f"Error: Background image not found at {BACKGROUND_IMAGE_PATH}")
        img = Image.new('RGB', (900, 1400), color = 'white')
        draw = ImageDraw.Draw(img)
        try: error_font = _get_font(size=24)
        except: error_font = ImageFont.load_default()
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, 480, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, 520, error_font, (255,0,0), "center")
    except Exception as e_bg:
        print(f"Error loading background image: {e_bg}")
        return None

    if not os.path.exists(FONT_PATH_REGULAR): print(f"Warning: Regular font missing at {FONT_PATH_REGULAR}")
    if not os.path.exists(FONT_PATH_BOLD): print(f"Warning: Bold font missing at {FONT_PATH_BOLD}")

    move_type_summary_parts = []
    base_move_type = state_data.get('base_move_type', "이사")
    if "가정" in base_move_type: move_type_summary_parts.append("가정")
    elif "사무실" in base_move_type: move_type_summary_parts.append("사무실")
    else: move_type_summary_parts.append(base_move_type.split(" ")[0])

    if state_data.get('is_storage_move', False):
        storage_type = state_data.get('storage_type', '')
        if "컨테이너" in storage_type: move_type_summary_parts.append("컨테이너보관")
        elif "실내" in storage_type: move_type_summary_parts.append("실내보관")
        else: move_type_summary_parts.append("보관")
        if state_data.get('storage_use_electricity', False):
            move_type_summary_parts.append("(전기사용)")
    if state_data.get('apply_long_distance', False):
        move_type_summary_parts.append("장거리")
    move_type_summary_text = " ".join(move_type_summary_parts) + " 이사" if move_type_summary_parts else base_move_type

    customer_name = state_data.get('customer_name', '')
    customer_phone = state_data.get('customer_phone', '')
    moving_date_obj = state_data.get('moving_date')
    moving_date_str = moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj)
    quote_date_str = date.today().strftime('%Y-%m-%d')
    from_location = state_data.get('from_location', '')
    to_location = state_data.get('to_location', '')
    from_floor = str(state_data.get('from_floor', ''))
    to_floor = str(state_data.get('to_floor', ''))
    
    selected_vehicle_for_calc = state_data.get('final_selected_vehicle', '')
    vehicle_tonnage_display = ""
    if isinstance(selected_vehicle_for_calc, str):
        match = re.search(r'(\d+(\.\d+)?)', selected_vehicle_for_calc)
        if match: vehicle_tonnage_display = match.group(1)
    elif isinstance(selected_vehicle_for_calc, (int, float)):
        vehicle_tonnage_display = str(selected_vehicle_for_calc)

    dispatched_1t = state_data.get('dispatched_1t', 0)
    dispatched_2_5t = state_data.get('dispatched_2_5t', 0)
    dispatched_3_5t = state_data.get('dispatched_3_5t', 0)
    dispatched_5t = state_data.get('dispatched_5t', 0)
    actual_dispatched_vehicles_parts = []
    if dispatched_1t > 0: actual_dispatched_vehicles_parts.append(f"1톤:{dispatched_1t}")
    if dispatched_2_5t > 0: actual_dispatched_vehicles_parts.append(f"2.5톤:{dispatched_2_5t}")
    if dispatched_3_5t > 0: actual_dispatched_vehicles_parts.append(f"3.5톤:{dispatched_3_5t}")
    if dispatched_5t > 0: actual_dispatched_vehicles_parts.append(f"5톤:{dispatched_5t}")
    actual_dispatched_vehicles_text = ", ".join(actual_dispatched_vehicles_parts) if actual_dispatched_vehicles_parts else ""

    workers_male = str(personnel_info.get('final_men', '0'))
    workers_female = str(personnel_info.get('final_women', '0'))

    from_method_raw = state_data.get('from_method', '')
    from_method_text_for_label = "출발" + (from_method_raw.split(" ")[0] if from_method_raw else "작업")
    from_method_text_for_display_top = from_method_raw.split(" ")[0] if from_method_raw else ""

    to_method_raw = state_data.get('to_method', '')
    to_method_text_for_label = "도착" + (to_method_raw.split(" ")[0] if to_method_raw else "작업")
    to_method_text_for_display_top = to_method_raw.split(" ")[0] if to_method_raw else ""

    # 비용 항목 계산
    total_moving_expenses_val = 0 # 순수 이사 비용 (노란 박스)
    storage_fee_val = 0           # 보관료
    option_ac_cost_val = 0      # 에어컨 설치비 (표시 안 함으로 변경됨)
    from_method_fee_val = 0     # 출발지 작업비
    to_method_fee_raw_val = 0   # 도착지 작업비 (지방할증 전)
    regional_ladder_surcharge_val = 0 # 지방 사다리 추가요금

    # *** 매우 중요: AC_COST_LABEL은 calculations.py에서 사용하는 에어컨 비용의 정확한 문자열 레이블이어야 합니다. ***
    AC_COST_LABEL = "에어컨 이전설치비" # 예시 레이블, 실제 사용하는 레이블로 변경하세요.
                                     # 만약 에어컨 비용이 여러 항목으로 나뉘어 있다면, 해당 레이블들을 리스트로 관리하고 확인해야 합니다.

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, item_note_ignored in calculated_cost_items:
            label = str(item_l)
            try: amount = int(float(item_a or 0))
            except (ValueError, TypeError): amount = 0

            if label == AC_COST_LABEL: # 에어컨 비용은 option_ac_cost_val에만 누적 (표시는 안 함)
                option_ac_cost_val += amount
            elif label == '보관료':
                storage_fee_val += amount
            elif label.startswith('출발지 사다리차') or label.startswith('출발지 스카이'):
                from_method_fee_val += amount
            elif label.startswith('도착지 사다리차') or label.startswith('도착지 스카이'):
                to_method_fee_raw_val += amount
            elif label == '지방 사다리 추가요금':
                 regional_ladder_surcharge_val += amount
            # VAT, 카드수수료, 그리고 'AC_COST_LABEL'을 제외한 나머지를 main_fee로 합산
            elif label != AC_COST_LABEL and \
                 label != '보관료' and \
                 not label.startswith('출발지 사다리차') and not label.startswith('출발지 스카이') and \
                 not label.startswith('도착지 사다리차') and not label.startswith('도착지 스카이') and \
                 label != '지방 사다리 추가요금' and \
                 "부가세" not in label and "카드결제 수수료" not in label:
                total_moving_expenses_val += amount
            
    final_to_method_fee_val = to_method_fee_raw_val + regional_ladder_surcharge_val

    deposit_amount_val = int(float(state_data.get('deposit_amount', 0) or 0))
    grand_total_num = int(float(total_cost_overall or 0))
    remaining_balance_num = grand_total_num - deposit_amount_val
    
    special_notes_content = state_data.get('special_notes', '')

    data_to_draw = {
        "move_type_summary_display": move_type_summary_text,
        "customer_name": customer_name, "customer_phone": customer_phone, "quote_date": quote_date_str,
        "moving_date": moving_date_str, "from_location": from_location, "to_location": to_location,
        "from_floor": from_floor, "to_floor": to_floor,
        "vehicle_type_numbers_only": vehicle_tonnage_display,
        "actual_dispatched_vehicles_display": actual_dispatched_vehicles_text,
        "workers_male": workers_male, "workers_female": workers_female,
        "from_work_method_text_display": from_method_text_for_display_top,
        "to_work_method_text_display": to_method_text_for_display_top,
        
        # "fee_value_next_to_ac_right" 키는 FIELD_MAP에서 제거했으므로, 여기서 값을 할당해도 그려지지 않음.
        # option_ac_cost_val 값은 계산되었지만, 이미지에는 표시되지 않음.
        # 만약 다른 곳(예: main_fee_yellow_box나 grand_total)에 에어컨 비용을 포함시키려면
        # total_moving_expenses_val 또는 grand_total_num 계산 시 option_ac_cost_val을 더해야 함.
        # 현재 로직은 에어컨 비용을 main_fee에서 명시적으로 제외하고, 별도 필드도 없애는 방향임.

        "main_fee_yellow_box": _format_currency(total_moving_expenses_val),
        "grand_total": _format_currency(grand_total_num),

        "from_method_label": from_method_text_for_label,
        "from_method_fee_value": _format_currency(from_method_fee_val),
        "to_method_label": to_method_text_for_label,
        "to_method_fee_value": _format_currency(final_to_method_fee_val),

        "deposit_amount_display": _format_currency(deposit_amount_val),
        "storage_fee_display": _format_currency(storage_fee_val),
        "remaining_balance_display": _format_currency(remaining_balance_num),
        "special_notes_display": special_notes_content
    }

    # 품목 수량 매핑 로직
    try:
        current_move_type = state_data.get("base_move_type")
        # 모든 ITEM_KEY_MAP의 값(FIELD_MAP 키)에 대해 빈 문자열로 초기화
        for field_map_key in ITEM_KEY_MAP.values():
            # FIELD_MAP에 해당 키가 정의되어 있는지 확인 (품목 표시에만 해당)
            if field_map_key.startswith("item_") and field_map_key in FIELD_MAP:
                data_to_draw[field_map_key] = "" # 기본값은 빈 문자열 (수량 없으면 안 그림)

        # utils.get_item_qty 함수가 로드되었는지 확인
        if utils and hasattr(utils, 'get_item_qty') and callable(utils.get_item_qty):
            for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
                # FIELD_MAP에 해당 품목을 그릴 위치가 정의되어 있는지 확인
                if field_map_key_from_map in FIELD_MAP and field_map_key_from_map.startswith("item_"):
                    qty_int = utils.get_item_qty(state_data, data_py_item_name)
                    if qty_int > 0:
                        text_val = str(qty_int)
                        if data_py_item_name == "장롱":
                            try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                            except: text_val = str(qty_int)
                        data_to_draw[field_map_key_from_map] = text_val
        else:
            print("ERROR [image_generator]: utils.get_item_qty function is not available. Cannot populate item quantities.")
            # 여기에 utils.get_item_qty가 없을 경우의 대체 로직을 넣거나, 에러를 명확히 할 수 있음
            # 예를 들어, 모든 품목 수량을 '?' 등으로 표시하거나, 경고 메시지를 이미지에 넣을 수도 있음

    except Exception as e_item_qty:
        print(f"Error processing item quantities for image: {e_item_qty}")
        traceback.print_exc()


    # 텍스트 그리기
    for key, M_raw in FIELD_MAP.items():
        M = {}
        for k_map, v_map in M_raw.items():
            if k_map in ["x", "y", "size", "max_width"]:
                try: M[k_map] = int(v_map)
                except (ValueError, TypeError) : M[k_map] = v_map
            else: M[k_map] = v_map

        text_content_value = M.get("text_override", data_to_draw.get(key))
        final_text_to_draw = ""

        if text_content_value is not None and str(text_content_value).strip() != "":
            final_text_to_draw = str(text_content_value)
        
        if final_text_to_draw.strip() != "" or (key == "special_notes_display" and final_text_to_draw == ""):
            size_to_use = get_adjusted_font_size(M.get("size", BASE_FONT_SIZE), key)
            try:
                font_obj = _get_font(font_type=M.get("font", "regular"), size=size_to_use)
            except Exception as font_load_err_draw:
                print(f"Critical error loading font for key '{key}' during drawing. Skipping. Error: {font_load_err_draw}")
                continue 

            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width")
            line_spacing_factor = M.get("line_spacing_factor", 1.15)
            
            _draw_text_with_alignment(draw, final_text_to_draw, M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

if __name__ == '__main__':
    print("image_generator.py test mode")
    # 테스트 시나리오: 에어컨 비용이 있지만, "fee_value_next_to_ac_right" 필드가 FIELD_MAP에 없으므로
    # 해당 위치에는 그려지지 않아야 함. 다른 품목들은 정상적으로 보여야 함.
    AC_COST_LABEL_TEST = "에어컨 이전설치비" # 실제 레이블과 동일하게 설정

    mock_state_test = {
        "customer_name": "물품확인 고객", "customer_phone": "010-5555-6666",
        "moving_date": date(2024, 10, 15),
        "from_location": "부산시 해운대구 마린시티", "to_location": "서울시 용산구 한남동",
        "from_floor": "20", "to_floor": "5",
        "final_selected_vehicle": "10톤", "dispatched_5t": 2, # 예시 투입 차량
        "from_method": "스카이 🏗️", "sky_hours_from": 3, "to_method": "사다리차 🪜",
        "deposit_amount": 500000,
        "base_move_type": "가정 이사 🏠",
        "special_notes": "모든 물품 파손주의.\n특히 유리 장식장 안전 포장 요청.",
        # 품목 수량 (utils.get_item_qty가 올바르게 동작하도록 세션 키 형식으로)
        "qty_가정 이사 🏠_주요 품목_장롱": 12, # 4칸
        "qty_가정 이사 🏠_주요 품목_4도어 냉장고": 1,
        "qty_가정 이사 🏠_주요 품목_TV(75인치)": 1,
        "qty_가정 이사 🏠_기타_에어컨": 2, # 에어컨 수량 (ITEM_KEY_MAP['에어컨']과 연결)
        "qty_가정 이사 🏠_포장 자재 📦_바구니": 50,
        "qty_가정 이사 🏠_포장 자재 📦_중박스": 30
    }
    mock_costs_test = [
        ("기본 운임", 2300000, "10톤 기준"),
        ("출발지 스카이 장비", 440000, "출발지(3h): 기본 300,000 + 추가 140,000"), # (300000 + 70000 * 2)
        ("도착지 사다리차", 240000, "5층, 10톤 기준"),
        (AC_COST_LABEL_TEST, 200000, "에어컨 2대 설치"), # 테스트용 에어컨 비용
        ("정리정돈 서비스", 300000, "프리미엄 옵션") # 기타 비용 예시
    ]
    # total_cost_overall은 모든 비용(에어컨 포함)의 합계여야 함
    mock_total_cost_test = sum(c[1] for c in mock_costs_test) # 2300000 + 440000 + 240000 + 200000 + 300000 = 3480000
    mock_personnel_test = {"final_men": 5, "final_women": 1}

    try:
        # utils.py의 get_item_qty를 모킹하거나, 실제 state_data 구조에 맞게 mock_state_test를 구성해야 함
        # 여기서는 utils.get_item_qty가 직접 mock_state_test를 사용한다고 가정하고 테스트
        if utils: # utils 모듈이 임포트되었는지 확인
            original_get_item_qty = utils.get_item_qty
            def mock_get_item_qty(state_data_mock, item_name_mock):
                # ITEM_KEY_MAP을 사용하여 state_data_mock의 실제 키를 찾음
                # 이 방식은 utils.get_item_qty의 내부 로직을 모방하는 것이므로,
                # 실제 utils.get_item_qty가 정확히 어떻게 동작하는지에 따라 달라질 수 있음
                # 가장 간단한 방법은 mock_state_test에 'qty_이사유형_섹션_품목명' 형태로 키를 다 넣어주는 것임 (위 예제에서 이미 그렇게 함)
                
                # ITEM_KEY_MAP을 순회하며 item_name_mock과 일치하는 data.py 품목명을 찾고,
                # 이를 기반으로 state_data_mock에서 session_state 키를 구성하여 값을 가져옴.
                # 이 테스트는 utils.get_item_qty의 정확한 구현에 의존함.
                # 위 mock_state_test는 이미 session_state 키 형식으로 값을 가지고 있으므로,
                # utils.get_item_qty가 이 키들을 잘 읽을 수 있다면 문제가 없음.
                
                # 임시로 utils.get_item_qty의 가장 기본적인 동작만 모방
                # (실제로는 utils.get_item_qty가 data.item_definitions를 참조해야 함)
                if item_name_mock == "장롱": return state_data_mock.get("qty_가정 이사 🏠_주요 품목_장롱",0)
                if item_name_mock == "4도어 냉장고": return state_data_mock.get("qty_가정 이사 🏠_주요 품목_4도어 냉장고",0)
                if item_name_mock == "TV(75인치)": return state_data_mock.get("qty_가정 이사 🏠_주요 품목_TV(75인치)",0)
                if item_name_mock == "에어컨": return state_data_mock.get("qty_가정 이사 🏠_기타_에어컨",0)
                if item_name_mock == "바구니": return state_data_mock.get("qty_가정 이사 🏠_포장 자재 📦_바구니",0)
                if item_name_mock == "중박스": return state_data_mock.get("qty_가정 이사 🏠_포장 자재 📦_중박스",0)
                return 0
            utils.get_item_qty = mock_get_item_qty # utils.get_item_qty를 임시 모의 함수로 교체

        image_bytes_test = create_quote_image(mock_state_test, mock_costs_test, mock_total_cost_test, mock_personnel_test)
        
        if utils: utils.get_item_qty = original_get_item_qty # 모의 함수 원복

        if image_bytes_test:
            timestamp_test = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_test = f"test_final_image_items_visible_{timestamp_test}.png"
            with open(filename_test, "wb") as f:
                f.write(image_bytes_test)
            print(f"Test image '{filename_test}' saved successfully.")
        else:
            print("Test image generation failed.")
    except Exception as e_main_test:
        print(f"Error in test run: {e_main_test}")
        traceback.print_exc()
