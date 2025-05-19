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
    # utils는 create_quote_image 함수 내에서 임포트 시도합니다.
except ImportError:
    app_data_for_img_gen = None
    print("Warning [image_generator.py]: data.py not found, some defaults might not be available.")


BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0, 0, 0)
TEXT_COLOR_BLUE = (20, 20, 180)
BASE_FONT_SIZE = 18 # 전화번호 외 기본 폰트 크기

item_y_start_val = 334
item_y_spacing_val = 28.8
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491
item_x_col3_val = 756

# --- 수정된 부분: vehicle_number_x_val 및 actual_vehicles_text_x_val 정의 추가 ---
vehicle_number_x_val = 80  # 차량 번호(톤수) 표시 X 좌표 (예시 값, 레이아웃에 맞게 조정 필요)
actual_vehicles_text_x_val = 450 # 실제 투입 차량 텍스트 표시 X 좌표 (예시 값, 레이아웃에 맞게 조정 필요)
# --- 수정 끝 ---

_y_from_floor_orig = 226
_y_to_floor_orig = 258
_y_sofa_3seater_orig = 549
_y_living_room_cabinet_orig = 677
_y_main_fee_yellow_box_orig = 775
_y_grand_total_orig = 861

# Y 좌표 조정값 적용
vehicle_display_y_adjusted = int(275 + item_y_spacing_val) - 2 - 10 # 실제차량선택 표시: 10 위로
vehicle_number_y_adjusted = vehicle_display_y_adjusted + 1 # 선택된 차량 숫자: 1 아래로 (실제차량 기준에서)
actual_vehicles_text_y_adjusted = vehicle_display_y_adjusted + 1 # 실제투입차량 텍스트: 1 아래로 (실제차량 기준에서)

from_work_fee_y_val = 805
to_work_fee_y_val = 833
deposit_y_val_adjusted = 789 + int(item_y_spacing_val / 2)
remaining_balance_y_val_adjusted = 826 + int(item_y_spacing_val)
storage_fee_y_val = _y_main_fee_yellow_box_orig
grand_total_y_adjusted = _y_grand_total_orig + 4 + 1 # 합계금액: 1 아래로

special_notes_start_y_val = int(grand_total_y_adjusted + item_y_spacing_val * 1.5) # 조정된 합계금액 기준
special_notes_x_val = 80
special_notes_max_width_val = 700
special_notes_font_size_val = BASE_FONT_SIZE

quote_date_y_val = 130
move_type_summary_y_val = int(quote_date_y_val - (item_y_spacing_val * 0.7) - 20 - 50)
move_type_summary_x_val = 640 + 100
move_type_summary_font_size_val = BASE_FONT_SIZE
move_type_summary_max_width_val = 150

costs_section_x_align_right_val = 410
work_method_fee_label_x_val = 35
work_method_text_display_x_val = int((item_x_col1_val + item_x_col2_baskets_val) / 2)
fees_x_val_right_aligned = item_x_col3_val

via_point_fee_y_val = int((from_work_fee_y_val + to_work_fee_y_val) / 2)
via_point_fee_label_x_val = work_method_fee_label_x_val + 50
via_point_fee_value_x_val = costs_section_x_align_right_val

# 전화번호 폰트 크기 조정용 상수
CUSTOMER_PHONE_FONT_SIZE = BASE_FONT_SIZE - 3 # 기존 BASE_FONT_SIZE - 2 에서 1 더 줄임


def get_adjusted_font_size(original_size_ignored, field_key):
    if field_key == "customer_name": return BASE_FONT_SIZE
    if field_key == "customer_phone": return CUSTOMER_PHONE_FONT_SIZE # 조정된 폰트 크기 사용
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

    "vehicle_type_numbers_only": {"x": vehicle_number_x_val, "y": int(vehicle_number_y_adjusted), "size": get_adjusted_font_size(0, "vehicle_type_numbers_only"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": (item_x_col1_val - vehicle_number_x_val - 5)},
    "actual_dispatched_vehicles_display": {"x": actual_vehicles_text_x_val, "y": int(actual_vehicles_text_y_adjusted), "size": get_adjusted_font_size(0, "actual_dispatched_vehicles_display"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 220},

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
    "item_piano_digital": {"x": item_x_col1_val, "y": int(_y_living_room_cabinet_orig + item_y_spacing_val * 1) + 1, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # Y 조정 (+1 아래로)
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
    "item_large_box":   {"x": item_x_col2_baskets_val, "y": int(581 + item_y_spacing_val * 0.45) - 3, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_book_box":    {"x": item_x_col2_baskets_val, "y": int(581 + item_y_spacing_val * 1.45), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_plant_box":   {"x": item_x_col2_others_val, "y": 680, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": item_x_col2_others_val, "y": 709, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": item_x_col2_others_val, "y": 738, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_styler":      {"x": item_x_col3_val, "y": item_y_start_val - 2, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 4) + 1, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # Y 조정 (+1 아래로)
    "item_tv_stand":    {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 5) + 2, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # TV다이: Y 조정 (+2 아래로)
    "item_wall_mount_item": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 6), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 8.9) - 2, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_angle_shelf": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 10) - 2, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 11.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 12.15), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 13.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": _y_main_fee_yellow_box_orig, "size": get_adjusted_font_size(0, "main_fee_yellow_box"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": costs_section_x_align_right_val, "y": int(grand_total_y_adjusted), "size": get_adjusted_font_size(0, "grand_total"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # Y 조정
    "from_method_label":  {"x": work_method_fee_label_x_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "from_method_fee_value": {"x": costs_section_x_align_right_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},
    "to_method_label":    {"x": work_method_fee_label_x_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "to_method_fee_value":  {"x": costs_section_x_align_right_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "via_method_label":   {"x": via_point_fee_label_x_val, "y": int(via_point_fee_y_val), "size": get_adjusted_font_size(0, "via_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "via_method_fee_value": {"x": via_point_fee_value_x_val, "y": int(via_point_fee_y_val), "size": get_adjusted_font_size(0, "via_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "deposit_amount_display":   {"x": fees_x_val_right_aligned, "y": int(deposit_y_val_adjusted), "size": get_adjusted_font_size(0, "deposit_amount_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee_display":      {"x": fees_x_val_right_aligned, "y": int(storage_fee_y_val), "size": get_adjusted_font_size(0, "storage_fee_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance_display":{"x": fees_x_val_right_aligned, "y": int(remaining_balance_y_val_adjusted), "size": get_adjusted_font_size(0, "remaining_balance_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "special_notes_display": {
        "x": special_notes_x_val, "y": special_notes_start_y_val,
        "size": get_adjusted_font_size(0, "special_notes_display"), "font": "regular",
        "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": special_notes_max_width_val, "line_spacing_factor": 1.3
    }
}

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
    "중박스": "item_medium_box",
    "중대박스": "item_large_box", # "item_large_box" 키가 FIELD_MAP에 정의되어 있는지 확인 필요 (현재는 없음)
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box", # "item_clothes_box"로 변경됨 (기존: item_hanger_box)
    "이불박스": "item_duvet_box",   # "item_duvet_box"로 변경됨 (기존: item_bedding_box)
    "스타일러": "item_styler",
    "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic",
    "복합기": "item_copier", # "item_copier"로 변경됨 (기존: item_printer)
    "TV(45인치)": "item_tv_45",
    "TV(75인치)": "item_tv_stand", # 이 항목이 TV다이(TV Stand)를 의미한다고 가정
    "벽걸이": "item_wall_mount_item",
    "금고": "item_safe",
    "앵글": "item_angle_shelf",
    "파티션": "item_partition",
    "5톤진입": "item_5ton_access"
    # "의자": "item_chair", -> FIELD_MAP에 "item_chair" 정의 필요
    # "테이블": "item_table", -> FIELD_MAP에 "item_table" 정의 필요
    # "담요": "item_blanket", -> FIELD_MAP에 "item_blanket" 정의 필요
}


def get_text_dimensions(text_string, font):
    if not text_string: return 0,0
    try:
        if hasattr(font, 'getbbox'): # Pillow 9.2.0+
            bbox = font.getbbox(str(text_string))
            width = bbox[2] - bbox[0]
            ascent, descent = font.getmetrics()
            height = ascent + descent
        elif hasattr(font, 'getsize'): # Older Pillow
            width, height = font.getsize(str(text_string))
        else: # Fallback if methods are missing (should not happen with standard Pillow)
            ascent, descent = font.getmetrics()
            height = ascent + descent
            width = len(str(text_string)) * (font.size / 2 if hasattr(font, 'size') else 5) # Very rough estimate
        return width, height
    except Exception as e:
        print(f"Warning: Error in get_text_dimensions for '{text_string[:20]}...': {e}")
        # Fallback to a simple length based estimation if Pillow methods fail unexpectedly
        fallback_size = 10
        if hasattr(font, 'size'): fallback_size = font.size
        return len(str(text_string)) * fallback_size * 0.6, fallback_size * 1.2


def _get_font(font_type="regular", size=12):
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD

    if not os.path.exists(font_path_to_use):
        print(f"ERROR [ImageGenerator]: Font file NOT FOUND at '{font_path_to_use}'. Falling back to PIL default.")
        try: return ImageFont.load_default(size=size)
        except AttributeError: # 'size' argument for load_default might not be in very old Pillow
            return ImageFont.load_default()
        except Exception as e_pil_font:
            print(f"CRITICAL: Error loading default PIL font: {e_pil_font}")
            raise

    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError:
        print(f"IOError [ImageGenerator]: Font '{font_path_to_use}' found but unreadable. Falling back to default.")
        try: return ImageFont.load_default(size=size)
        except AttributeError: return ImageFont.load_default()
        except Exception as e_pil_font_io:
            print(f"CRITICAL: Error loading default PIL font after IOError: {e_pil_font_io}")
            raise
    except Exception as e_font:
        print(f"General Error loading font {font_path_to_use}: {e_font}")
        raise
# image_generator.py

# ... (다른 코드는 그대로 유지) ...

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
                for char_in_word in word:
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

    current_y_draw = y
    first_line = True
    _, typical_char_height = get_text_dimensions("A", font) 
    for line in lines: # line_to_draw 대신 line 사용
        if not line.strip() and not first_line and len(lines) > 1: 
            current_y_draw += int(typical_char_height * line_spacing_factor)
            continue

        text_width_draw, _ = get_text_dimensions(line, font) # line_to_draw 대신 line 사용
        actual_x_draw = x
        if align == "right": actual_x_draw = x - text_width_draw
        elif align == "center": actual_x_draw = x - text_width_draw / 2
        
        # 수정: draw.text() 호출 시 anchor 파라미터 제거
        draw.text((actual_x_draw, current_y_draw), line, font=font, fill=color) # line_to_draw 대신 line 사용, anchor 제거

        current_y_draw += int(typical_char_height * line_spacing_factor) 
        first_line = False
    return current_y_draw

# ... (create_quote_image 및 나머지 코드는 이전과 동일하게 유지) ...
def _format_currency(amount_val):
    if amount_val is None or str(amount_val).strip() == "": return ""
    try:
        num_val = float(str(amount_val).replace(",", "").strip()) # 쉼표 제거 후 float 변환
        num = int(num_val) # 정수 부분만 사용
        return f"{num:,}" # 천단위 쉼표 포맷
    except ValueError:
        return str(amount_val) # 변환 실패 시 원본 문자열 반환

def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    print("DEBUG [ImageGenerator]: create_quote_image function CALLED")
    utils_module = None
    try:
        import utils as local_utils # create_quote_image 함수 내에서 utils 임포트
        utils_module = local_utils
    except ImportError:
        print("ERROR [ImageGenerator]: utils.py not found inside create_quote_image. Item quantities will be missing.")
        # utils_module은 None으로 유지됨

    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
        print("DEBUG [ImageGenerator]: Background image loaded.")
    except FileNotFoundError:
        print(f"ERROR [ImageGenerator]: Background image not found at {BACKGROUND_IMAGE_PATH}")
        return None
    except Exception as e_bg:
        print(f"ERROR [ImageGenerator]: Error loading background image: {e_bg}")
        return None

    # 폰트 파일 존재 여부 확인 (필수 아님, _get_font에서 처리)
    if not os.path.exists(FONT_PATH_REGULAR): print(f"WARNING [ImageGenerator]: Regular font missing at {FONT_PATH_REGULAR}")
    if not os.path.exists(FONT_PATH_BOLD): print(f"WARNING [ImageGenerator]: Bold font missing at {FONT_PATH_BOLD}")


    # --- 데이터 준비 ---
    # 이사 유형 요약
    move_type_summary_parts = []
    base_move_type_raw = state_data.get('base_move_type', "이사") # 기본값 "이사"
    base_move_type = base_move_type_raw.split(" ")[0] # 이모티콘 제거 (예: "가정")
    move_type_summary_parts.append(base_move_type) # 예: "가정" 추가

    if state_data.get('is_storage_move', False):
        storage_type_raw = state_data.get('storage_type', '')
        storage_type = storage_type_raw.split(" ")[0] # 이모티콘 제거
        move_type_summary_parts.append(f"{storage_type}보관") # 예: "컨테이너보관" 추가
        if state_data.get('storage_use_electricity', False):
            move_type_summary_parts.append("(전기)")
    if state_data.get('apply_long_distance', False):
        move_type_summary_parts.append("장거리")
    if state_data.get('has_via_point', False):
        move_type_summary_parts.append("경유")
    move_type_summary_text = " ".join(list(dict.fromkeys(move_type_summary_parts))) + "이사" # 중복 제거 후 "이사" 추가


    customer_name = state_data.get('customer_name', '')
    customer_phone = state_data.get('customer_phone', '')
    moving_date_obj = state_data.get('moving_date')
    moving_date_str = moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj)
    quote_date_str = date.today().strftime('%Y-%m-%d') # 견적일은 항상 오늘
    from_location = state_data.get('from_location', '')
    to_location = state_data.get('to_location', '')
    from_floor = str(state_data.get('from_floor', ''))
    to_floor = str(state_data.get('to_floor', ''))

    # 차량 톤수 정보 (계산용으로 선택된 차량 기준)
    selected_vehicle_for_calc = state_data.get('final_selected_vehicle', '')
    vehicle_tonnage_display = ""
    if isinstance(selected_vehicle_for_calc, str):
        match = re.search(r'(\d+(\.\d+)?)', selected_vehicle_for_calc) # 숫자 부분 추출
        if match: vehicle_tonnage_display = match.group(1) # 예: "5"
    elif isinstance(selected_vehicle_for_calc, (int, float)): # 드물지만 숫자 타입일 경우 대비
        vehicle_tonnage_display = str(selected_vehicle_for_calc)

    # 실제 투입 차량 정보 (견적서 표시용)
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

    # 출발지/도착지/경유지 작업 방법 텍스트 준비
    from_method_raw = state_data.get('from_method', '')
    from_method_prefix = from_method_raw.split(" ")[0] if from_method_raw else "" # 이모티콘 제거
    from_method_text_for_label = "출발" + (from_method_prefix if from_method_prefix else "작업")
    from_method_text_for_display_top = from_method_prefix # 상단 표시용 (이모티콘 없이)

    to_method_raw = state_data.get('to_method', '')
    to_method_prefix = to_method_raw.split(" ")[0] if to_method_raw else ""
    to_method_text_for_label = "도착" + (to_method_prefix if to_method_prefix else "작업")
    to_method_text_for_display_top = to_method_prefix

    via_method_raw = state_data.get('via_point_method', '') # 경유지 작업 방법
    via_method_prefix = via_method_raw.split(" ")[0] if via_method_raw else ""
    via_method_text_for_label = "경유" + (via_method_prefix if via_method_prefix else "작업") # 경유지용 레이블

    # 비용 계산 (image_generator 내에서 직접 계산)
    total_moving_expenses_val = 0 # 이사 비용 (작업비, 보관료, VAT 제외)
    storage_fee_val = 0
    from_method_fee_val = 0
    to_method_fee_raw_val = 0 # 도착지 순수 작업비 (지방 사다리 추가금 제외)
    regional_ladder_surcharge_val = 0 # 지방 사다리 추가금 (별도)
    via_point_surcharge_val = 0 # 경유지 추가 요금

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, item_note_ignored in calculated_cost_items:
            label = str(item_l)
            try: amount = int(float(item_a or 0)) # 금액은 정수로 변환
            except (ValueError, TypeError): amount = 0

            if label == '보관료':
                storage_fee_val += amount
            elif label.startswith('출발지 사다리차') or label.startswith('출발지 스카이 장비'):
                from_method_fee_val += amount
                if label.startswith('출발지 스카이 장비'): from_method_text_for_label = "출발스카이" # 레이블 변경
            elif label.startswith('도착지 사다리차') or label.startswith('도착지 스카이 장비'):
                to_method_fee_raw_val += amount # 순수 도착 작업비에 합산
                if label.startswith('도착지 스카이 장비'): to_method_text_for_label = "도착스카이" # 레이블 변경
            elif label == '지방 사다리 추가요금':
                 regional_ladder_surcharge_val += amount # 별도 저장
            elif label == '경유지 추가요금':
                 via_point_surcharge_val += amount # 경유지 추가 요금 저장
            # 아래 조건에서 VAT 및 카드 수수료 항목 제외
            elif label not in ['보관료', '지방 사다리 추가요금', '경유지 추가요금'] and \
                 not label.startswith('출발지 사다리차') and not label.startswith('출발지 스카이 장비') and \
                 not label.startswith('도착지 사다리차') and not label.startswith('도착지 스카이 장비') and \
                 "부가세" not in label and "카드결제" not in label: # VAT 및 카드결제 항목 제외
                total_moving_expenses_val += amount

    # 도착지 최종 작업비 = 순수 도착 작업비 + 지방 사다리 추가금
    final_to_method_fee_val = to_method_fee_raw_val + regional_ladder_surcharge_val

    # 계약금, 총액, 잔금
    deposit_amount_val = int(float(state_data.get('deposit_amount', 0) or 0)) # state_data에서 직접 가져옴
    grand_total_num = int(float(total_cost_overall or 0)) # 전체 총액
    remaining_balance_num = grand_total_num - deposit_amount_val

    # 특이사항
    special_notes_content = state_data.get('special_notes', '')


    # 그릴 데이터 딕셔너리
    data_to_draw = {
        "move_type_summary_display": move_type_summary_text,
        "customer_name": customer_name, "customer_phone": customer_phone, "quote_date": quote_date_str,
        "moving_date": moving_date_str, "from_location": from_location, "to_location": to_location,
        "from_floor": from_floor, "to_floor": to_floor,
        "vehicle_type_numbers_only": vehicle_tonnage_display, # 계산용 차량 톤수
        "actual_dispatched_vehicles_display": actual_dispatched_vehicles_text, # 실제 투입 차량 텍스트
        "workers_male": workers_male, "workers_female": workers_female,
        "from_work_method_text_display": from_method_text_for_display_top, # 상단 출발 방법 (이모티콘X)
        "to_work_method_text_display": to_method_text_for_display_top,     # 상단 도착 방법 (이모티콘X)
        "main_fee_yellow_box": _format_currency(total_moving_expenses_val), # 노란 박스 안의 총 이사 비용
        "grand_total": _format_currency(grand_total_num),                # 최종 합계 금액 (VAT 등 포함)
        "from_method_label": from_method_text_for_label if from_method_fee_val > 0 else "", # 출발 작업비 레이블
        "from_method_fee_value": _format_currency(from_method_fee_val) if from_method_fee_val > 0 else "", # 출발 작업비
        "to_method_label": to_method_text_for_label if final_to_method_fee_val > 0 else "",     # 도착 작업비 레이블
        "to_method_fee_value": _format_currency(final_to_method_fee_val) if final_to_method_fee_val > 0 else "",   # 도착 작업비 (지방사다리 포함)
        "via_method_label": via_method_text_for_label if via_point_surcharge_val > 0 and state_data.get('has_via_point', False) else "", # 경유지 작업비 레이블
        "via_method_fee_value": _format_currency(via_point_surcharge_val) if via_point_surcharge_val > 0 and state_data.get('has_via_point', False) else "", # 경유지 작업비
        "deposit_amount_display": _format_currency(deposit_amount_val),          # 계약금
        "storage_fee_display": _format_currency(storage_fee_val),             # 보관료
        "remaining_balance_display": _format_currency(remaining_balance_num), # 잔금
        "special_notes_display": special_notes_content # 특이사항
    }

    # --- 품목 수량 채우기 (utils.get_item_qty 사용) ---
    print("DEBUG [ImageGenerator]: Populating item quantities...")
    try:
        current_move_type_for_items_img = state_data.get("base_move_type") # 현재 이사 유형 (이모티콘 포함)

        # 모든 품목 키에 대해 빈 문자열로 초기화 (값이 없는 경우 아무것도 안그리기 위함)
        for field_map_key_img in ITEM_KEY_MAP.values():
            if field_map_key_img.startswith("item_") and field_map_key_img in FIELD_MAP: # FIELD_MAP에 정의된 품목 키만
                data_to_draw[field_map_key_img] = ""

        if utils_module and hasattr(utils_module, 'get_item_qty') and callable(utils_module.get_item_qty):
            for data_py_item_name, field_map_key_from_map_img in ITEM_KEY_MAP.items():
                # ITEM_KEY_MAP의 키(field_map_key_from_map_img)가 FIELD_MAP에도 정의되어 있는지 확인
                if field_map_key_from_map_img in FIELD_MAP and field_map_key_from_map_img.startswith("item_"):
                    qty_int = utils_module.get_item_qty(state_data, data_py_item_name) # state_data와 실제품목명 전달
                    if qty_int > 0:
                        text_val = str(qty_int)
                        # 장롱 특별 처리 (칸 수 / 3.0)
                        if data_py_item_name == "장롱":
                            try: text_val = f"{(float(qty_int) / 3.0):.1f}" # 소수점 한자리까지
                            except: text_val = str(qty_int) # 오류 시 원래 수량
                        data_to_draw[field_map_key_from_map_img] = text_val
        else:
            print("ERROR [ImageGenerator]: utils.get_item_qty function is not available. Item quantities might be incorrect.")
    except Exception as e_item_qty_img:
        print(f"ERROR [ImageGenerator]: Error processing item quantities: {e_item_qty_img}")
        traceback.print_exc()


    # --- 텍스트 그리기 ---
    print("DEBUG [ImageGenerator]: Starting to draw text elements on image.")
    for key, M_raw in FIELD_MAP.items():
        # 좌표값 int 변환 (이미 위에서 처리되었어야 함, 안전장치)
        M = {}
        for k_map, v_map in M_raw.items():
            if k_map in ["x", "y", "size", "max_width"]: # 숫자여야 하는 속성들
                try: M[k_map] = int(v_map)
                except (ValueError, TypeError) : M[k_map] = v_map # 변환 실패시 원본 유지
            else: M[k_map] = v_map

        text_content_value = M.get("text_override", data_to_draw.get(key)) # text_override 우선
        final_text_to_draw = ""
        if text_content_value is not None and str(text_content_value).strip() != "": # 공백만 있는 경우도 제외
            final_text_to_draw = str(text_content_value)

        # 특정 레이블/값 쌍은 값이 있을 때만 그리도록 (예: 작업비)
        if key in ["from_method_label", "from_method_fee_value",
                   "to_method_label", "to_method_fee_value",
                   "via_method_label", "via_method_fee_value"] and not final_text_to_draw.strip():
            continue # 내용 없으면 다음 키로

        # 내용이 있거나, 특이사항처럼 내용 없어도 영역 표시해야 하는 경우
        if final_text_to_draw.strip() != "" or (key == "special_notes_display" and final_text_to_draw == ""):
            size_to_use = get_adjusted_font_size(M.get("size", BASE_FONT_SIZE), key)
            try:
                font_obj = _get_font(font_type=M.get("font", "regular"), size=size_to_use)
            except Exception as font_load_err_draw_img: # 폰트 로드 실패 시
                print(f"ERROR [ImageGenerator]: Font loading error for key '{key}'. Skipping. Error: {font_load_err_draw_img}")
                continue # 해당 텍스트 그리기는 건너뜀

            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width") # 자동 줄바꿈 최대 폭
            line_spacing_factor = M.get("line_spacing_factor", 1.15) # 기본 줄간격 (기존 1.2에서 약간 줄임)

            _draw_text_with_alignment(draw, final_text_to_draw, M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    print("DEBUG [ImageGenerator]: Text drawing complete. Saving image to bytes.")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    print("DEBUG [ImageGenerator]: Image generation successful.")
    return img_byte_arr.getvalue()


# --- 테스트용 코드 (선택적) ---
if __name__ == '__main__':
    print("image_generator.py test mode")

    # 테스트 데이터 (via_point 관련 정보 포함, 차량 및 비용 정보 수정)
    mock_state_test_via = {
        "customer_name": "박경유 스타일러", "customer_phone": "010-5555-6666",
        "moving_date": date(2025, 3, 20),
        "from_location": "서울시 용산구 한남동 빌라 한강대로123가길 45-6 101동 202호", "to_location": "경기도 하남시 미사강변도시 아파트 미사강변남로 789 XYZ타워 303동 1501호",
        "from_floor": "2", "to_floor": "15",
        "final_selected_vehicle": "6톤", # 차량 변경
        "dispatched_5t": 1, "dispatched_1t":1, # 투입 차량 변경
        "from_method": "계단 🚶",
        "to_method": "스카이 🏗️", "sky_hours_final": 3, # 스카이 시간 변경
        "has_via_point": True, # 경유지 있음
        "via_point_location": "서울시 송파구 잠실동 중간경유지 ABC빌딩 12층", # 경유지 주소
        "via_point_method": "사다리차 🪜", # 경유지 작업 변경
        "via_point_surcharge": 70000,    # 경유지 추가요금 (calculations에서 계산됨)
        "deposit_amount": 200000,
        "base_move_type": "가정 이사 🏠",
        "apply_long_distance": False, # 장거리 아님
        "is_storage_move": False,    # 보관 아님
        "special_notes": "스타일러 및 금고, 앵글 포함 견적 테스트 요청드립니다.\nTV다이 위치 확인 필요.\n전화번호 폰트 크기가 너무 작지 않은지 확인 부탁드립니다.\n여러 줄 메모 테스트입니다. 줄바꿈이 잘 되는지 확인해야 합니다. 이미지 생성 시 특이사항 란에 표시됩니다.",
        "qty_가정 이사 🏠_기타_스타일러": 1,
        "qty_가정 이사 🏠_기타_금고": 1,
        "qty_가정 이사 🏠_기타_앵글": 2,
        "qty_가정 이사 🏠_주요 품목_TV(75인치)": 1, # ITEM_KEY_MAP에서 'item_tv_stand'로 매핑됨
        "qty_가정 이사 🏠_기타_TV(45인치)": 1,    # 'item_tv_45'
        "qty_가정 이사 🏠_기타_피아노(디지털)": 1, # 'item_piano_digital'
        "qty_가정 이사 🏠_포장 자재 📦_중대박스": 5, # ITEM_KEY_MAP에서 'item_large_box'로 매핑됨
    }

    # 테스트용 비용 항목 (실제 calculations.py 결과와 유사하게)
    mock_costs_test_via = [
        ("기본 운임", 1350000, "6톤 기준"), # 6톤 가격으로 변경
        # 출발지 계단이므로 작업비 0 또는 없음 (표시 안됨)
        ("도착지 스카이 장비", 440000, "도착(3h): 기본 300,000 + 추가 140,000"), # 3시간
        ("경유지 추가요금", 70000, "수동입력 (사다리 가정)"), # 경유지 요금
        # 필요시 다른 비용 항목 추가 (예: 날짜 할증, 추가 인력 등)
    ]
    # 전체 총액 (위 비용들의 합계. 실제로는 VAT, 카드수수료 등 포함될 수 있음)
    mock_total_cost_test_via = 1350000 + 440000 + 70000 # 예시 합계

    # 테스트용 인원 정보 (6톤 기준)
    mock_personnel_test_via = {"final_men": 3, "final_women": 1}

    try:
        # 이미지 생성 함수 호출
        image_bytes_test = create_quote_image(mock_state_test_via, mock_costs_test_via, mock_total_cost_test_via, mock_personnel_test_via)

        if image_bytes_test:
            timestamp_test = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_test = f"test_image_final_coords_with_vars_{timestamp_test}.png"
            with open(filename_test, "wb") as f:
                f.write(image_bytes_test)
            print(f"Test image '{filename_test}' saved successfully.")
        else:
            print("Test image generation failed.")
    except Exception as e_main_test:
        print(f"Error in test run: {e_main_test}")
        traceback.print_exc()
