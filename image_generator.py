# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date, datetime
import math
import traceback
import re

try:
    import data as app_data_for_img_gen
    # utils는 create_quote_image 함수 내에서 임포트 시도하도록 변경 (순환 참조 방지 목적일 수 있음)
except ImportError:
    app_data_for_img_gen = None
    print("Warning [image_generator.py]: data.py not found, some defaults might not be available.")


BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0, 0, 0) # 검은색 텍스트
TEXT_COLOR_BLUE = (20, 20, 180)
BASE_FONT_SIZE = 18

item_y_start_val = 334
item_y_spacing_val = 28.8
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491 # 중복되지만 명시적으로 둠
item_x_col3_val = 756

_y_from_floor_orig = 226
_y_to_floor_orig = 258
_y_sofa_3seater_orig = 549 # 소파(3인) Y
_y_living_room_cabinet_orig = 677 # 거실장 Y
_y_main_fee_yellow_box_orig = 775 # 총괄이사비용(노란박스) Y
_y_grand_total_orig = 861 # 총액 Y

# 실제 차량 선택 표시 Y값 조정 (기존값 - 10)
original_vehicle_y_calc = int(275 + item_y_spacing_val) # 약 303.8
vehicle_display_y_val = original_vehicle_y_calc - 2 - 10 # 요청: 10만큼 위로 (기존: 약 301 -> 조정 후: 약 291)
vehicle_number_x_val = 90
actual_vehicles_text_x_val = item_x_col2_others_val

# 작업비 관련 Y 좌표 (출발/도착)
from_work_fee_y_val = 805 # 출발지 작업비 Y
to_work_fee_y_val = 833   # 도착지 작업비 Y

# 계약금, 잔금 Y 좌표 조정
# 계약금: 이전 789에서 반 칸(item_y_spacing_val / 2) 아래로
deposit_y_val_adjusted = 789 + int(item_y_spacing_val / 2) # 약 789 + 14 = 803
# 잔금: 이전 826에서 한 칸(item_y_spacing_val) 아래로
remaining_balance_y_val_adjusted = 826 + int(item_y_spacing_val) # 약 826 + 29 = 855

storage_fee_y_val = _y_main_fee_yellow_box_orig # 보관료는 총괄 이사 비용과 같은 Y

grand_total_y_new = _y_grand_total_orig + 4 # 865 (총액 Y 최종 조정)

# 특이사항 Y
special_notes_start_y_val = int(grand_total_y_new + item_y_spacing_val * 1.5) # 약 908
special_notes_x_val = 80
special_notes_max_width_val = 700 # (이미지 가로폭 약 900 - X시작 80 - 우측여백 약 120)
special_notes_font_size_val = BASE_FONT_SIZE # 고객명과 동일 (18)

# 이사 종류 요약 표시 Y
quote_date_y_val = 130
move_type_summary_y_val = int(quote_date_y_val - (item_y_spacing_val * 0.7) - 20 - 50) # 약 39 (기존 약 89에서 -50)
move_type_summary_x_val = 640 + 100 # 740 (기존 640에서 +100)
move_type_summary_font_size_val = BASE_FONT_SIZE # 고객명과 동일 (18)
move_type_summary_max_width_val = 150 # (이미지 가로폭 약 900 - X시작 740 - 우측여백 약 10)

# 비용 섹션 X 좌표
costs_section_x_align_right_val = 410 # 총괄이사비용(노란박스), 총액 등 오른쪽 정렬 기준
work_method_fee_label_x_val = 35     # 출발/도착 작업비 레이블 X
work_method_text_display_x_val = int((item_x_col1_val + item_x_col2_baskets_val) / 2) # 상단 작업방법 표시 X
fees_x_val_right_aligned = item_x_col3_val # 계약금, 잔금 등 금액 오른쪽 정렬 X

# 경유지 요금 표시 좌표 (신규)
via_point_fee_y_val = int((from_work_fee_y_val + to_work_fee_y_val) / 2) # 출발지와 도착지 작업비의 중간 Y
via_point_fee_label_x_val = work_method_fee_label_x_val + 50 # 기존 레이블에서 50픽셀 오른쪽
via_point_fee_value_x_val = costs_section_x_align_right_val # 금액은 기존 오른쪽 정렬 X 사용


def get_adjusted_font_size(original_size_ignored, field_key):
    # ... (이전 답변과 동일하게 유지, 에어컨 설치비 관련 폰트 조정은 이미 제거됨) ...
    if field_key == "customer_name": return BASE_FONT_SIZE
    if field_key == "customer_phone": return BASE_FONT_SIZE - 2
    if field_key.startswith("item_") and field_key not in ["item_x_col1_val", "item_x_col2_baskets_val", "item_x_col2_others_val", "item_x_col3_val"]:
        return item_font_size_val
    if field_key in ["grand_total", "remaining_balance_display"]: return BASE_FONT_SIZE + 2
    if field_key in ["from_work_method_text_display", "to_work_method_text_display"]: return BASE_FONT_SIZE - 2
    if field_key in ["from_method_label", "to_method_label", "via_method_label",
                     "from_method_fee_value", "to_method_fee_value", "via_method_fee_value",
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
    "item_large_box":   {"x": item_x_col2_baskets_val, "y": int(581 + item_y_spacing_val * 0.45) - 3, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # Y 조정
    "item_book_box":    {"x": item_x_col2_baskets_val, "y": int(581 + item_y_spacing_val * 1.45), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_plant_box":   {"x": item_x_col2_others_val, "y": 680, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": item_x_col2_others_val, "y": 709, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": item_x_col2_others_val, "y": 738, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_styler":      {"x": item_x_col3_val, "y": item_y_start_val - 2, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # Y 조정
    "item_massage_chair":{"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 4), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 5), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 6), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 8.9) - 2, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # Y 조정
    "item_angle_shelf": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 10) - 2, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # Y 조정
    "item_partition":   {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 11.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 12.15), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 13.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": _y_main_fee_yellow_box_orig, "size": get_adjusted_font_size(0, "main_fee_yellow_box"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": costs_section_x_align_right_val, "y": int(grand_total_y_new), "size": get_adjusted_font_size(0, "grand_total"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "from_method_label":  {"x": work_method_fee_label_x_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "from_method_fee_value": {"x": costs_section_x_align_right_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},
    "to_method_label":    {"x": work_method_fee_label_x_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "to_method_fee_value":  {"x": costs_section_x_align_right_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},
    
    # 경유지 요금 표시 필드 추가
    "via_method_label":   {"x": via_point_fee_label_x_val, "y": int(via_point_fee_y_val), "size": get_adjusted_font_size(0, "via_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "via_method_fee_value": {"x": via_point_fee_value_x_val, "y": int(via_point_fee_y_val), "size": get_adjusted_font_size(0, "via_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "deposit_amount_display":   {"x": fees_x_val_right_aligned, "y": int(deposit_y_val_adjusted), "size": get_adjusted_font_size(0, "deposit_amount_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # Y 조정
    "storage_fee_display":      {"x": fees_x_val_right_aligned, "y": int(storage_fee_y_val), "size": get_adjusted_font_size(0, "storage_fee_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance_display":{"x": fees_x_val_right_aligned, "y": int(remaining_balance_y_val_adjusted), "size": get_adjusted_font_size(0, "remaining_balance_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # Y 조정
    "special_notes_display": {
        "x": special_notes_x_val, "y": special_notes_start_y_val,
        "size": get_adjusted_font_size(0, "special_notes_display"), "font": "regular",
        "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": special_notes_max_width_val, "line_spacing_factor": 1.3
    }
}

# ITEM_KEY_MAP은 이전과 동일하게 유지 (에어컨 설치비 관련 키는 없음)
ITEM_KEY_MAP = {
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장": "item_drawer_5dan",
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door",
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand",
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater", "식탁(4인)": "item_dining_table",
    "에어컨": "item_ac_left",
    "거실장": "item_living_room_cabinet",
    "피아노(디지털)": "item_piano_digital",
    "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer",
    "사무실책상": "item_executive_desk",
    "책상&의자": "item_desk",
    "책장": "item_bookshelf",
    "바구니": "item_basket",
    "중박스": "item_medium_box", # 중대박스(item_large_box)와 별도
    "중대박스": "item_large_box", # ITEM_KEY_MAP에 추가 (FIELD_MAP 키와 일치)
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box", # FIELD_MAP의 item_clothes_box와 매칭
    "이불박스": "item_duvet_box", # FIELD_MAP의 item_duvet_box와 매칭
    "스타일러": "item_styler",
    "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic",
    "복합기": "item_copier", # FIELD_MAP에 item_copier 추가됨
    "TV(45인치)": "item_tv_45",
    "TV(75인치)": "item_tv_stand", # FIELD_MAP의 item_tv_stand와 매칭 (TV 거치대 의미인지, 75인치 TV 자체인지 확인 필요)
    "벽걸이": "item_wall_mount_item", # FIELD_MAP에 item_wall_mount_item 추가됨
    "금고": "item_safe",
    "앵글": "item_angle_shelf",
    "파티션": "item_partition", # FIELD_MAP에 item_partition 추가됨
    "5톤진입": "item_5ton_access" # FIELD_MAP에 item_5ton_access 추가됨
    # 에어컨(우측)은 FIELD_MAP에 item_ac_right로 존재하나, ITEM_KEY_MAP에는 에어컨(좌측)만 있음. 필요시 추가.
}


def get_text_dimensions(text_string, font):
    # ... (이전 답변과 동일하게 유지) ...
    if not text_string: return 0,0
    if hasattr(font, 'getbbox'): # Pillow 9.2.0+
        try:
            bbox = font.getbbox(str(text_string))
            width = bbox[2] - bbox[0]
            # height = bbox[3] - bbox[1] # bbox 높이는 실제 렌더링 높이와 다를 수 있음
            ascent, descent = font.getmetrics() # 글꼴의 ascent/descent 사용
            height = ascent + descent
        except Exception: # Fallback for older versions or unexpected issues
            if hasattr(font, 'getlength'): # Pillow 10.0.0 에서 getsize 대신 사용 권장
                width = font.getlength(str(text_string))
            else: # 최후의 수단
                width = len(str(text_string)) * (font.size if hasattr(font, 'size') else 10) / 2
            ascent, descent = font.getmetrics()
            height = ascent + descent
    elif hasattr(font, 'getmask'): # Pillow < 9.2.0 에서 사용되던 방식 (getsize 내부 로직과 유사)
        try:
            width, height = font.getmask(str(text_string)).size
        except Exception: # getmask 실패 시
            ascent, descent = font.getmetrics()
            height = ascent + descent
            width = font.getlength(str(text_string)) if hasattr(font, 'getlength') else len(str(text_string)) * height / 2
    else: # 모든 주요 메소드 실패 시 (매우 드문 경우)
        ascent, descent = font.getmetrics()
        height = ascent + descent
        if hasattr(font, 'getlength'):
            width = font.getlength(str(text_string))
        else: # 정말 최후의 근사치
            width = len(str(text_string)) * height / 2 # 글자 수 기반 추정
    return width, height

def _get_font(font_type="regular", size=12):
    # ... (이전 답변과 동일하게 유지) ...
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD
        # else: print(f"Warning: Bold font file not found at {FONT_PATH_BOLD}. Using regular.")

    if not os.path.exists(font_path_to_use):
        print(f"ERROR [ImageGenerator]: Font file NOT FOUND at '{font_path_to_use}'. Falling back to PIL default.")
        try: return ImageFont.load_default(size=size) # Pillow 10.0.0 부터 size 인자 지원
        except TypeError: # 이전 버전 호환
            try: return ImageFont.load_default()
            except Exception as e_load_def_no_size:
                 print(f"CRITICAL: Error loading default PIL font (no size): {e_load_def_no_size}")
                 raise
        except Exception as e_pil_font:
            print(f"CRITICAL: Error loading default PIL font: {e_pil_font}")
            raise

    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError: # 파일은 있으나 Pillow가 읽을 수 없는 경우
        print(f"IOError [ImageGenerator]: Font '{font_path_to_use}' found but unreadable by Pillow. Falling back to default.")
        try: return ImageFont.load_default(size=size)
        except TypeError: return ImageFont.load_default()
        except Exception as e_pil_font_io:
            print(f"CRITICAL: Error loading default PIL font after IOError: {e_pil_font_io}")
            raise
    except Exception as e_font: # 그 외 폰트 로딩 에러
        print(f"General Error loading font {font_path_to_use}: {e_font}")
        raise


def _draw_text_with_alignment(draw, text, x, y, font, color, align="left", max_width=None, line_spacing_factor=1.2):
    # ... (이전 답변과 동일하게 유지) ...
    if text is None: text = ""
    text = str(text)
    lines = []

    if max_width:
        words = text.split(' ')
        current_line = ""
        for word in words:
            # 단어가 비어있으면 건너뛰기
            if not word:
                if current_line: # 이전 라인이 있으면 공백 추가 시도
                    current_line += " "
                continue

            word_width, _ = get_text_dimensions(word, font)

            # 단일 단어가 최대 너비보다 큰 경우 (예: 긴 URL), 해당 단어를 강제로 분할
            if word_width > max_width and len(word) > 1:
                if current_line.strip(): # 이전 라인이 있으면 먼저 추가
                    lines.append(current_line.strip())
                    current_line = ""

                temp_word_line = ""
                for char_in_word in word:
                    temp_word_line_plus_char_width, _ = get_text_dimensions(temp_word_line + char_in_word, font)
                    if temp_word_line_plus_char_width <= max_width:
                        temp_word_line += char_in_word
                    else:
                        lines.append(temp_word_line)
                        temp_word_line = char_in_word
                if temp_word_line: # 남은 글자들 추가
                    lines.append(temp_word_line)
                # current_line = "" # 이 단어는 이미 처리되었으므로 current_line은 비어있어야 함
                continue # 다음 단어로 넘어감

            # 현재 라인에 단어 추가 시 너비 계산
            # current_line이 비어있으면 word만, 아니면 current_line + " " + word
            test_line = (current_line + " " + word).strip() if current_line else word
            current_line_plus_word_width, _ = get_text_dimensions(test_line, font)

            if current_line_plus_word_width <= max_width:
                current_line = test_line
            else: # 현재 단어를 추가하면 최대 너비 초과
                if current_line: # 이전까지의 라인 추가
                    lines.append(current_line.strip())
                current_line = word # 새 라인은 현재 단어로 시작
        
        if current_line.strip(): # 마지막 라인 추가
            lines.append(current_line.strip())
        
        if not lines and text.strip(): # 분할되지 않은 경우 (예: 짧은 텍스트 또는 max_width가 매우 큰 경우)
            lines.append(text.strip())
    else: # max_width가 없는 경우, 기존처럼 \n 기준으로 분리
        lines.extend(text.split('\n'))

    current_y_draw = y
    first_line = True
    # Pillow 폰트 객체에서 직접 line spacing 정보를 가져오기 어려우므로,
    # 글꼴 높이(ascent + descent)를 기준으로 line_spacing_factor를 적용
    _, typical_char_height = get_text_dimensions("A", font) # 높이 계산용 (ascent+descent)
    
    actual_line_spacing = int(typical_char_height * line_spacing_factor)

    for i, line in enumerate(lines):
        line_to_draw = line.strip() # 각 줄의 앞뒤 공백 제거
        if not line_to_draw and not first_line and len(lines) > 1: # 빈 줄이고 첫 줄이 아니면 간격만
            current_y_draw += actual_line_spacing
            continue

        text_width_draw, _ = get_text_dimensions(line_to_draw, font)
        actual_x_draw = x
        if align == "right": actual_x_draw = x - text_width_draw
        elif align == "center": actual_x_draw = x - text_width_draw / 2
        
        # anchor='lt' (left-top) 사용 시 y는 텍스트 박스의 상단 경계가 됨
        draw.text((actual_x_draw, current_y_draw), line_to_draw, font=font, fill=color, anchor="lt")

        if i < len(lines) - 1 : # 마지막 줄이 아니면 줄 간격 추가
             current_y_draw += actual_line_spacing
        first_line = False # 첫 줄 그린 후 False로 설정

    return current_y_draw # 마지막으로 그려진 텍스트의 시작 Y 좌표 + 마지막 줄 높이 반환 (다음 요소 위치 잡기 위함)


def _format_currency(amount_val):
    # ... (이전 답변과 동일하게 유지) ...
    if amount_val is None or str(amount_val).strip() == "": return ""
    try:
        num_val = float(str(amount_val).replace(",", "").strip()) # 콤마 제거 후 float 변환
        num = int(num_val) # 정수 부분만 사용
        return f"{num:,}" # 천단위 콤마
    except ValueError: # 숫자 변환 실패 시 원본 반환
        return str(amount_val)

# create_quote_image 함수 정의 시작
def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    print("DEBUG [ImageGenerator]: create_quote_image function CALLED")
    utils_module = None
    try:
        import utils as local_utils # 함수 내에서 utils 임포트
        utils_module = local_utils
    except ImportError:
        print("ERROR [ImageGenerator]: utils.py not found inside create_quote_image. Item quantities will be missing.")


    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
        print("DEBUG [ImageGenerator]: Background image loaded.")
    except FileNotFoundError:
        print(f"ERROR [ImageGenerator]: Background image not found at {BACKGROUND_IMAGE_PATH}")
        return None # 배경 없으면 이미지 생성 불가
    except Exception as e_bg:
        print(f"ERROR [ImageGenerator]: Error loading background image: {e_bg}")
        return None

    if not os.path.exists(FONT_PATH_REGULAR): print(f"WARNING [ImageGenerator]: Regular font missing at {FONT_PATH_REGULAR}")
    if not os.path.exists(FONT_PATH_BOLD): print(f"WARNING [ImageGenerator]: Bold font missing at {FONT_PATH_BOLD}")

    # --- 데이터 추출 및 준비 ---
    move_type_summary_parts = []
    base_move_type_raw = state_data.get('base_move_type', "이사") # 예: "가정 이사 🏠"
    base_move_type = base_move_type_raw.split(" ")[0] # "가정" 또는 "사무실"

    move_type_summary_parts.append(base_move_type)

    if state_data.get('is_storage_move', False):
        storage_type_raw = state_data.get('storage_type', '') # 예: "컨테이너 보관 📦"
        storage_type = storage_type_raw.split(" ")[0]
        move_type_summary_parts.append(f"{storage_type}보관")
        if state_data.get('storage_use_electricity', False):
            move_type_summary_parts.append("(전기)") # 간결하게
    
    if state_data.get('apply_long_distance', False):
        move_type_summary_parts.append("장거리")
    
    if state_data.get('has_via_point', False): # 경유지 이사 표시 추가
        move_type_summary_parts.append("경유")

    move_type_summary_text = " ".join(list(dict.fromkeys(move_type_summary_parts))) + "이사" # 중복 제거 및 "이사" 추가


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

    # 작업 방법 텍스트 (이모티콘 제거)
    from_method_raw = state_data.get('from_method', '')
    from_method_text_for_label = "출발" + (from_method_raw.split(" ")[0] if from_method_raw else "작업")
    from_method_text_for_display_top = from_method_raw.split(" ")[0] if from_method_raw else ""

    to_method_raw = state_data.get('to_method', '')
    to_method_text_for_label = "도착" + (to_method_raw.split(" ")[0] if to_method_raw else "작업")
    to_method_text_for_display_top = to_method_raw.split(" ")[0] if to_method_raw else ""
    
    via_method_raw = state_data.get('via_point_method', '')
    via_method_text_for_label = "경유" + (via_method_raw.split(" ")[0] if via_method_raw else "작업")


    # 비용 항목 계산
    total_moving_expenses_val = 0 
    storage_fee_val = 0
    from_method_fee_val = 0
    to_method_fee_raw_val = 0
    regional_ladder_surcharge_val = 0
    via_point_surcharge_val = 0 # 경유지 추가요금

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, item_note_ignored in calculated_cost_items:
            label = str(item_l)
            try: amount = int(float(item_a or 0))
            except (ValueError, TypeError): amount = 0

            if label == '보관료':
                storage_fee_val += amount
            elif label.startswith('출발지 사다리차') or label.startswith('출발지 스카이 장비'): # 스카이 요금도 출발지 작업비로
                from_method_fee_val += amount
            elif label.startswith('도착지 사다리차') or label.startswith('도착지 스카이 장비'): # 스카이 요금도 도착지 작업비로
                to_method_fee_raw_val += amount
            elif label == '지방 사다리 추가요금':
                 regional_ladder_surcharge_val += amount
            elif label == '경유지 추가요금': # 경유지 요금
                 via_point_surcharge_val += amount
            elif label not in ['보관료', '지방 사다리 추가요금', '경유지 추가요금'] and \
                 not label.startswith('출발지 사다리차') and not label.startswith('출발지 스카이 장비') and \
                 not label.startswith('도착지 사다리차') and not label.startswith('도착지 스카이 장비') and \
                 "부가세" not in label and "카드결제" not in label: # 카드결제(VAT 및 수수료 포함)도 제외
                total_moving_expenses_val += amount
            
    final_to_method_fee_val = to_method_fee_raw_val + regional_ladder_surcharge_val


    deposit_amount_val = int(float(state_data.get('deposit_amount', 0) or 0))
    grand_total_num = int(float(total_cost_overall or 0))
    remaining_balance_num = grand_total_num - deposit_amount_val
    
    special_notes_content = state_data.get('special_notes', '')

    # 그릴 데이터 준비
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
        
        "main_fee_yellow_box": _format_currency(total_moving_expenses_val),
        "grand_total": _format_currency(grand_total_num),

        "from_method_label": from_method_text_for_label if from_method_fee_val > 0 else "", # 비용 있을 때만 레이블 표시
        "from_method_fee_value": _format_currency(from_method_fee_val) if from_method_fee_val > 0 else "",
        "to_method_label": to_method_text_for_label if final_to_method_fee_val > 0 else "", # 비용 있을 때만 레이블 표시
        "to_method_fee_value": _format_currency(final_to_method_fee_val) if final_to_method_fee_val > 0 else "",
        
        # 경유지 요금 데이터 추가
        "via_method_label": via_method_text_for_label if via_point_surcharge_val > 0 else "", # 비용 있을 때만
        "via_method_fee_value": _format_currency(via_point_surcharge_val) if via_point_surcharge_val > 0 else "",

        "deposit_amount_display": _format_currency(deposit_amount_val),
        "storage_fee_display": _format_currency(storage_fee_val),
        "remaining_balance_display": _format_currency(remaining_balance_num),
        "special_notes_display": special_notes_content
    }

    # 품목 수량 채우기
    print("DEBUG [ImageGenerator]: Populating item quantities...")
    try:
        current_move_type_for_items = state_data.get("base_move_type") # 예: "가정 이사 🏠"
        for field_map_key in ITEM_KEY_MAP.values():
            if field_map_key.startswith("item_") and field_map_key in FIELD_MAP:
                data_to_draw[field_map_key] = ""

        if utils_module and hasattr(utils_module, 'get_item_qty') and callable(utils_module.get_item_qty):
            for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
                if field_map_key_from_map in FIELD_MAP and field_map_key_from_map.startswith("item_"):
                    qty_int = utils_module.get_item_qty(state_data, data_py_item_name) # state_data와 품목명 전달
                    if qty_int > 0:
                        text_val = str(qty_int)
                        if data_py_item_name == "장롱":
                            try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                            except: text_val = str(qty_int)
                        data_to_draw[field_map_key_from_map] = text_val
        else:
            print("ERROR [ImageGenerator]: utils.get_item_qty function is not available. Cannot populate item quantities.")
    except Exception as e_item_qty:
        print(f"ERROR [ImageGenerator]: Error processing item quantities: {e_item_qty}")
        traceback.print_exc()

    # 텍스트 그리기
    print("DEBUG [ImageGenerator]: Starting to draw text elements on image.")
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
        
        # 작업비 관련 항목은 값이 0이거나 빈 문자열이면 그리지 않음 (레이블 포함)
        if key in ["from_method_label", "from_method_fee_value", 
                   "to_method_label", "to_method_fee_value",
                   "via_method_label", "via_method_fee_value"] and not final_text_to_draw.strip():
            continue


        if final_text_to_draw.strip() != "" or (key == "special_notes_display" and final_text_to_draw == ""):
            size_to_use = get_adjusted_font_size(M.get("size", BASE_FONT_SIZE), key)
            try:
                font_obj = _get_font(font_type=M.get("font", "regular"), size=size_to_use)
            except Exception as font_load_err_draw:
                print(f"ERROR [ImageGenerator]: Critical error loading font for key '{key}'. Skipping this text. Error: {font_load_err_draw}")
                continue 

            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width")
            line_spacing_factor = M.get("line_spacing_factor", 1.15)
            
            _draw_text_with_alignment(draw, final_text_to_draw, M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    print("DEBUG [ImageGenerator]: Text drawing complete. Saving image to bytes.")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    print("DEBUG [ImageGenerator]: Image generation successful.")
    return img_byte_arr.getvalue()

if __name__ == '__main__':
    print("image_generator.py test mode")
    # 테스트 데이터에 경유지 정보 및 비용 추가
    mock_state_test_via = {
        "customer_name": "박경유 테스트", "customer_phone": "010-3333-4444",
        "moving_date": date(2025, 2, 15),
        "from_location": "서울시 강남구 역삼동 출발지",
        "to_location": "경기도 수원시 영통구 도착지",
        "from_floor": "5", "to_floor": "12",
        "final_selected_vehicle": "5톤", "dispatched_5t": 1,
        "from_method": "사다리차 🪜", 
        "to_method": "스카이 🏗️", "sky_hours_final": 2, # 도착지 스카이 시간
        "has_via_point": True, # 경유지 있음
        "via_point_location": "경기도 성남시 분당구 경유지 아파트",
        "via_point_method": "승강기 🛗", # 경유지 작업 방법
        "via_point_surcharge": 50000,    # 경유지 추가 요금
        "deposit_amount": 150000,
        "base_move_type": "가정 이사 🏠",
        "special_notes": "경유지에서 일부 짐만 내립니다.\n도착지 작업 시간 엄수 부탁드립니다.",
        "qty_가정 이사 🏠_주요 품목_장롱": 3, # 1.0 칸
        "qty_가정 이사 🏠_주요 품목_소파(3인용)": 1,
        "qty_가정 이사 🏠_포장 자재 📦_바구니": 30,
    }
    mock_costs_test_via = [
        ("기본 운임", 1200000, "5톤 기준"),
        ("출발지 사다리차", 150000, "5층, 5톤 기준"),
        ("도착지 스카이 장비", 370000, "도착(2h): 기본 300,000 + 추가 70,000"), # (300000 + 70000 * (2-1))
        ("경유지 추가요금", 50000, "수동입력"),
    ]
    mock_total_cost_test_via = 1200000 + 150000 + 370000 + 50000
    mock_personnel_test_via = {"final_men": 3, "final_women": 1}

    try:
        image_bytes_test = create_quote_image(mock_state_test_via, mock_costs_test_via, mock_total_cost_test_via, mock_personnel_test_via)
        
        if image_bytes_test:
            timestamp_test = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_test = f"test_image_via_point_{timestamp_test}.png"
            with open(filename_test, "wb") as f:
                f.write(image_bytes_test)
            print(f"Test image '{filename_test}' saved successfully. Please verify all elements and positions.")
        else:
            print("Test image generation failed. Check logs above for [ImageGenerator] messages.")
    except Exception as e_main_test:
        print(f"Error in test run: {e_main_test}")
        traceback.print_exc()
