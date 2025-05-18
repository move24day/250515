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
    import utils
except ImportError:
    app_data_for_img_gen = None
    utils = None
    print("Warning [image_generator.py]: data.py or utils.py not found.")

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

# --- 색상 및 기본 폰트 크기 ---
TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)
TEXT_COLOR_BLUE = (20, 20, 180)
BASE_FONT_SIZE = 18

# --- 품목 관련 기본 좌표 및 간격 ---
item_y_start_val = 334
item_y_spacing_val = 28.8 # 기본 Y 간격 (1칸에 해당)
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491
item_x_col3_val = 756

# --- 기타 주요 Y 좌표 ---
# "예전 값" 또는 원하시는 값으로 이 Y 좌표들을 직접 설정해주세요.
# "3칸 더 내려야 한다"는 것은 현재 값에서 item_y_spacing_val * 3 만큼 더해야 한다는 의미일 수 있습니다.
# 또는, 절대적인 "예전 Y 좌표 값"을 의미할 수도 있습니다.

# 예시: 현재 값에서 3칸 (item_y_spacing_val * 3) 만큼 내리는 경우
# 기존 from_work_fee_y_val, to_work_fee_y_val, deposit_y_val, remaining_balance_y_val 값에
# item_y_spacing_val * 3 (대략 86.4)을 더해줍니다.

# 만약 "예전의 절대적인 Y 좌표 값"을 알고 계시다면, 그 값으로 직접 설정합니다.
# 예: from_work_fee_y_val = 750 (예전 Y 값이 750이었다면)

# 여기서는 "현재 위치에서 3칸(약 86px) 내린다"는 의미로 해석하고,
# FIELD_MAP에서 직접 Y 값을 조정하는 방식을 보여드리겠습니다.
# 또는, 이전에 사용했던 Y 좌표 계산 로직이나 특정 기준값을 사용합니다.

# 참고용: 기존에 자주 사용되던 Y 좌표값 (수정 전의 값들일 수 있음)
_y_main_fee_yellow_box_orig = 775
_y_grand_total_orig = 861

# 출발/도착 작업(사다리) 요금 Y 좌표 ("예전 값" 또는 조정된 값)
# X 값은 유지, Y 값만 조정
# "예전 값"을 여기에 직접 숫자로 입력하거나, 계산식을 사용합니다.
# 예시 1: 특정 고정 Y값 사용 (예: 700, 728)
# from_work_fee_y_val = 700  # 사용자가 원하는 "예전" Y 좌표 또는 새 Y 좌표
# to_work_fee_y_val = from_work_fee_y_val + int(item_y_spacing_val * 1) # 출발지 아래 한 칸

# 예시 2: 다른 요소 기준으로 상대적 위치 (main_fee 박스 위)
from_work_fee_y_val = _y_main_fee_yellow_box_orig - int(item_y_spacing_val * 2.5) # 약 703
to_work_fee_y_val = from_work_fee_y_val + int(item_y_spacing_val * 1)         # 약 732

# 계약금 및 잔금 Y 좌표 ("예전 값" 또는 조정된 값)
# "예전 값"을 여기에 직접 숫자로 입력하거나, 계산식을 사용합니다.
# 예시 1: 특정 고정 Y값 사용 (예: 800, 828)
# deposit_y_val = 800
# remaining_balance_y_val = deposit_y_val + int(item_y_spacing_val * 1)

# 예시 2: 총계(grand_total) 기준으로 상대적 위치 (총계 위)
deposit_y_val = grand_total_y_new - int(item_y_spacing_val * 2.5)             # 약 797 (grand_total_y_new는 865)
remaining_balance_y_val = deposit_y_val + int(item_y_spacing_val * 1)       # 약 826


# !!!! 중요 !!!!
# 만약 "3칸 더 내려서 표시"가 *현재 기준에서* 3칸(약 86px)을 의미한다면,
# 아래 FIELD_MAP에서 각 항목의 y 값을 직접 수정하는 것이 더 명확할 수 있습니다.
# 예를 들어, from_method_label의 현재 y값이 703이고, 3칸 내리려면 703 + (28.8 * 3) = 789.4 -> int(789)
# 이 경우에는 위의 from_work_fee_y_val 등의 변수 계산 로직을 이전 것으로 되돌리거나,
# FIELD_MAP의 y 값을 직접 조정해야 합니다.

# --- FIELD_MAP에서 사용할 최종 Y 좌표 변수 (위에서 설정한 값 사용) ---
# 이 부분은 이전 답변에서 Y 좌표 계산 로직을 변경했던 부분입니다.
# "예전 값"을 반영하려면 이 변수들의 할당 방식을 "예전 방식"으로 되돌리거나,
# 아래 FIELD_MAP에서 y값을 직접 "예전 수치"로 지정해야 합니다.

# 이전에 Y 좌표 변수들이 어떻게 계산되었는지, 또는 "처음 올린 파일"의
# FIELD_MAP에서 해당 키들의 y값이 몇이었는지 확인이 필요합니다.

# 예시: "처음 올린 파일"에서 FIELD_MAP의 y값이 직접 숫자로 하드코딩 되어 있었다면,
# 그 숫자들을 아래 y 값에 직접 넣어주면 됩니다.
# from_work_fee_y_val = ??? (처음 올린 파일의 from_method_label y 값)
# to_work_fee_y_val = ??? (처음 올린 파일의 to_method_label y 값)
# deposit_y_val = ??? (처음 올린 파일의 deposit_amount_display y 값)
# remaining_balance_y_val = ??? (처음 올린 파일의 remaining_balance_display y 값)


# 나머지 좌표 변수들은 이전과 유사하게 유지될 수 있음
storage_fee_y_val = _y_main_fee_yellow_box_orig
grand_total_y_new = _y_grand_total_orig + 4

# 기타 X 좌표 등 (X값은 맞다고 하셨으므로 유지)
costs_section_x_align_right_val = 410
work_method_fee_label_x_val = 35
fees_x_val_right_aligned = item_x_col3_val

# (get_adjusted_font_size 함수는 이전과 동일)
def get_adjusted_font_size(original_size_ignored, field_key):
    if field_key == "customer_name": return BASE_FONT_SIZE
    if field_key == "customer_phone": return BASE_FONT_SIZE - 2
    if field_key.startswith("item_") and field_key not in ["item_x_col1_val", "item_x_col2_baskets_val", "item_x_col2_others_val", "item_x_col3_val"]:
        return item_font_size_val
    if field_key in ["grand_total", "remaining_balance_display"]: return BASE_FONT_SIZE + 2
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
    # ... (고객 정보, 차량 정보, 품목 정보 등은 이전과 동일하게 유지) ...
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

    # --- 비용 표시 (Y 좌표는 위에서 정의한 변수 사용) ---
    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": _y_main_fee_yellow_box_orig, "size": get_adjusted_font_size(0, "main_fee_yellow_box"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": costs_section_x_align_right_val, "y": int(grand_total_y_new), "size": get_adjusted_font_size(0, "grand_total"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},

    # 출발지 작업(사다리) 요금: Y 좌표 변경됨
    "from_method_label":  {"x": work_method_fee_label_x_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "from_method_fee_value": {"x": costs_section_x_align_right_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    # 도착지 작업(사다리) 요금: Y 좌표 변경됨
    "to_method_label":    {"x": work_method_fee_label_x_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "to_method_fee_value":  {"x": costs_section_x_align_right_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    # 계약금: Y 좌표 변경됨
    "deposit_amount_display":   {"x": fees_x_val_right_aligned, "y": int(deposit_y_val), "size": get_adjusted_font_size(0, "deposit_amount_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee_display":      {"x": fees_x_val_right_aligned, "y": int(storage_fee_y_val), "size": get_adjusted_font_size(0, "storage_fee_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # 보관료 위치는 그대로 유지
    # 잔금: Y 좌표 변경됨
    "remaining_balance_display":{"x": fees_x_val_right_aligned, "y": int(remaining_balance_y_val), "size": get_adjusted_font_size(0, "remaining_balance_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "special_notes_display": {
        "x": special_notes_x_val, "y": special_notes_start_y_val,
        "size": get_adjusted_font_size(0, "special_notes_display"), "font": "regular",
        "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": special_notes_max_width_val, "line_spacing_factor": 1.3
    }
}

# ... (ITEM_KEY_MAP 정의는 이전과 동일하게 유지) ...

# ... (create_quote_image 함수 정의는 이전과 동일하게 유지, 내부에서 FIELD_MAP을 사용하므로 변경된 Y 좌표가 반영됨) ...
# create_quote_image 함수 내 data_to_draw 채우는 부분 등은 이전 답변의 로직을 그대로 사용합니다.
# 중요한 것은 FIELD_MAP의 y값과, 파일 상단에서 이 y값에 영향을 주는 변수들 (from_work_fee_y_val 등)을
# "예전 값" 또는 원하시는 값으로 정확히 설정하는 것입니다.

# create_quote_image 함수 (이전 답변의 전체 코드에서 복사하여 붙여넣되, FIELD_MAP 변경사항이 반영되도록 함)
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
    
    total_moving_expenses_val = 0 
    storage_fee_val = 0
    option_ac_cost_val = 0 
    from_method_fee_val = 0
    to_method_fee_raw_val = 0
    regional_ladder_surcharge_val = 0

    AC_COST_LABEL = "에어컨 이전설치비" 

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, item_note_ignored in calculated_cost_items:
            label = str(item_l)
            try: amount = int(float(item_a or 0))
            except (ValueError, TypeError): amount = 0

            if label == AC_COST_LABEL:
                option_ac_cost_val += amount
            elif label == '보관료':
                storage_fee_val += amount
            elif label.startswith('출발지 사다리차') or label.startswith('출발지 스카이'):
                from_method_fee_val += amount
            elif label.startswith('도착지 사다리차') or label.startswith('도착지 스카이'):
                to_method_fee_raw_val += amount
            elif label == '지방 사다리 추가요금':
                 regional_ladder_surcharge_val += amount
            elif label not in [AC_COST_LABEL, '보관료', '지방 사다리 추가요금'] and \
                 not label.startswith('출발지 사다리차') and not label.startswith('출발지 스카이') and \
                 not label.startswith('도착지 사다리차') and not label.startswith('도착지 스카이') and \
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

    try:
        current_move_type = state_data.get("base_move_type")
        for field_map_key in ITEM_KEY_MAP.values():
            if field_map_key.startswith("item_") and field_map_key in FIELD_MAP:
                data_to_draw[field_map_key] = ""

        if utils and hasattr(utils, 'get_item_qty') and callable(utils.get_item_qty):
            for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
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
    except Exception as e_item_qty:
        print(f"Error processing item quantities for image: {e_item_qty}")
        traceback.print_exc()

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


# (if __name__ == '__main__': 블록은 이전 답변의 테스트 코드를 참고하여 필요에 따라 수정/사용하세요.)
if __name__ == '__main__':
    print("image_generator.py test mode - 위치 변경 테스트")

    # 이 테스트 케이스는 Y 좌표가 변경되었는지 확인하는 데 중점을 둡니다.
    # 실제 "예전 값"을 위의 Y 좌표 변수에 적용한 후 테스트해야 정확합니다.
    
    mock_state_test_pos = {
        "customer_name": "위치조정 고객님", "customer_phone": "010-9999-0000",
        "moving_date": date(2025, 12, 25),
        "from_location": "서울시 강동구 고덕동", "to_location": "경기도 하남시 미사동",
        "from_floor": "5", "to_floor": "10",
        "final_selected_vehicle": "5톤", "dispatched_5t": 1, 
        "from_method": "사다리차 🪜", "to_method": "계단 🚶",
        "deposit_amount": 200000,
        "base_move_type": "가정 이사 🏠",
        "special_notes": "계약금, 잔금, 사다리 요금 위치 확인용 테스트입니다.",
        "qty_가정 이사 🏠_주요 품목_장롱": 3, # 1칸
    }
    mock_costs_test_pos = [
        ("기본 운임", 1200000, "5톤 기준"),
        ("출발지 사다리차", 150000, "5층, 5톤 기준"),
        # 도착지는 계단이므로 사다리 비용 없음
        ("에어컨 이전설치비", 0, "해당 없음"), # 에어컨 비용은 없다고 가정 (표시 안함)
    ]
    mock_total_cost_test_pos = 1200000 + 150000 
    mock_personnel_test_pos = {"final_men": 3, "final_women": 1}

    try:
        image_bytes_test = create_quote_image(mock_state_test_pos, mock_costs_test_pos, mock_total_cost_test_pos, mock_personnel_test_pos)
        
        if image_bytes_test:
            timestamp_test = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_test = f"test_y_pos_changed_{timestamp_test}.png"
            with open(filename_test, "wb") as f:
                f.write(image_bytes_test)
            print(f"Test image '{filename_test}' saved successfully. Please check the Y positions.")
        else:
            print("Test image generation failed.")
    except Exception as e_main_test:
        print(f"Error in test run: {e_main_test}")
        traceback.print_exc()
