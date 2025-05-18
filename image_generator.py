# image_generator.py (수정 예시)
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
TEXT_COLOR_YELLOW_BG = (0,0,0) # 노란 배경 위의 검은색 텍스트
TEXT_COLOR_BLUE = (20, 20, 180)
BASE_FONT_SIZE = 18

# --- 품목 관련 기본 좌표 및 간격 ---
item_y_start_val = 334
item_y_spacing_val = 28.8
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491
item_x_col3_val = 756

# --- 기타 주요 Y 좌표 (기존 값 또는 "예전 값"으로 추정되는 값으로 설정) ---
# 사용자가 "예전 값"으로 돌리기를 원하므로, 이 부분의 값들을 이전 버전이나 원하는 값으로 설정해야 합니다.
# 아래 값들은 설명을 위한 임의의 "예전 스타일" 값일 수 있습니다. 정확한 값으로 수정해주세요.

_y_main_fee_yellow_box_orig = 775 # 메인 비용 (노란 박스) Y - 이 값은 유지될 가능성이 높음
_y_grand_total_orig = 861         # 총계 Y - 이 값도 유지될 가능성이 높음

# 출발/도착 사다리(작업) 요금 표시 위치 (텍스트 레이블과 금액 모두)
# 예시: 메인 비용 박스 아래 또는 특정 고정 Y 값
# "예전 값"에 따라 이 Y 좌표들을 조정해야 합니다.
# 여기서는 임의로 _y_main_fee_yellow_box_orig 아래로 배치하는 예시를 들겠습니다.
prev_from_work_fee_y_val = _y_main_fee_yellow_box_orig + item_y_spacing_val * 1.2  # 예시: 약 809
prev_to_work_fee_y_val = prev_from_work_fee_y_val + item_y_spacing_val      # 예시: 약 838

# 계약금 및 잔금 표시 위치 ("예전 값"으로)
# 예시: 총계 위 또는 특정 고정 Y 값
prev_deposit_y_val = _y_grand_total_orig - item_y_spacing_val * 2.5 # 예시: 약 789
prev_remaining_balance_y_val = _y_grand_total_orig - item_y_spacing_val * 1.2 # 예시: 약 826

# --- FIELD_MAP에서 사용할 최종 Y 좌표 변수 ---
# 사용자가 원하는 "예전 값" 또는 새로운 좌표로 이 변수들을 설정합니다.
from_work_fee_y_val = prev_from_work_fee_y_val # 예시 값 사용
to_work_fee_y_val = prev_to_work_fee_y_val     # 예시 값 사용
deposit_y_val = prev_deposit_y_val             # 예시 값 사용
remaining_balance_y_val = prev_remaining_balance_y_val # 예시 값 사용

# 나머지 좌표 변수들은 이전과 유사하게 유지될 수 있음
storage_fee_y_val = _y_main_fee_yellow_box_orig # 보관료는 메인 비용과 같은 Y (오른쪽 다른 컬럼)
grand_total_y_new = _y_grand_total_orig + 4

# 기타 X 좌표 등
costs_section_x_align_right_val = 410
work_method_fee_label_x_val = 35
fees_x_val_right_aligned = item_x_col3_val # 계약금, 잔금 등의 금액 X 좌표 (품목 3열과 유사한 위치)

# (이하 get_adjusted_font_size, FIELD_MAP, ITEM_KEY_MAP, _get_font, _draw_text_with_alignment, _format_currency, create_quote_image 함수 정의)
# ...

def get_adjusted_font_size(original_size_ignored, field_key):
    # ... (이전과 동일) ...
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

    # --- 품목 수량 (이전과 동일하게 유지) ---
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

    # --- 비용 표시 (Y 좌표 변경됨) ---
    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": _y_main_fee_yellow_box_orig, "size": get_adjusted_font_size(0, "main_fee_yellow_box"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": costs_section_x_align_right_val, "y": int(grand_total_y_new), "size": get_adjusted_font_size(0, "grand_total"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},

    "from_method_label":  {"x": work_method_fee_label_x_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "from_method_fee_value": {"x": costs_section_x_align_right_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "to_method_label":    {"x": work_method_fee_label_x_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "to_method_fee_value":  {"x": costs_section_x_align_right_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "deposit_amount_display":   {"x": fees_x_val_right_aligned, "y": int(deposit_y_val), "size": get_adjusted_font_size(0, "deposit_amount_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee_display":      {"x": fees_x_val_right_aligned, "y": int(storage_fee_y_val), "size": get_adjusted_font_size(0, "storage_fee_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance_display":{"x": fees_x_val_right_aligned, "y": int(remaining_balance_y_val), "size": get_adjusted_font_size(0, "remaining_balance_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "special_notes_display": {
        "x": special_notes_x_val, "y": special_notes_start_y_val,
        "size": get_adjusted_font_size(0, "special_notes_display"), "font": "regular",
        "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": special_notes_max_width_val, "line_spacing_factor": 1.3
    }
}
# ... (ITEM_KEY_MAP 정의는 이전과 동일하게 유지) ...
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
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box",
    "스타일러": "item_styler",
    "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic",
    "TV(45인치)": "item_tv_45",
    "TV(75인치)": "item_tv_stand",
    "금고": "item_safe",
    "앵글": "item_angle_shelf",
}


# ... (get_text_dimensions, _get_font, _draw_text_with_alignment, _format_currency 함수는 이전과 동일하게 유지) ...
def get_text_dimensions(text_string, font):
    if not text_string: return 0,0
    if hasattr(font, 'getbbox'):
        try:
            bbox = font.getbbox(str(text_string))
            width = bbox[2] - bbox[0]
            ascent, descent = font.getmetrics()
            height = ascent + descent
        except Exception:
            if hasattr(font, 'getlength'): width = font.getlength(str(text_string))
            else: width = len(str(text_string)) * (font.size if hasattr(font, 'size') else 10) / 2
            ascent, descent = font.getmetrics()
            height = ascent + descent
    elif hasattr(font, 'getmask'):
        try:
            width, height = font.getmask(str(text_string)).size
        except Exception:
            ascent, descent = font.getmetrics()
            height = ascent + descent
            width = font.getlength(str(text_string)) if hasattr(font, 'getlength') else len(str(text_string)) * height / 2
    else:
        ascent, descent = font.getmetrics()
        height = ascent + descent
        if hasattr(font, 'getlength'):
            width = font.getlength(str(text_string))
        else:
            width = len(str(text_string)) * height / 2
    return width, height

def _get_font(font_type="regular", size=12):
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD

    if not os.path.exists(font_path_to_use):
        print(f"ERROR [ImageGenerator]: Font file NOT FOUND at '{font_path_to_use}'. Falling back to PIL default.")
        try: return ImageFont.load_default(size=size)
        except TypeError: return ImageFont.load_default()
        except Exception as e_pil_font:
            print(f"CRITICAL: Error loading default PIL font: {e_pil_font}")
            raise

    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError:
        print(f"IOError [ImageGenerator]: Font '{font_path_to_use}' found but unreadable by Pillow. Falling back to default.")
        try: return ImageFont.load_default(size=size)
        except TypeError: return ImageFont.load_default()
        except Exception as e_pil_font_io:
            print(f"CRITICAL: Error loading default PIL font after IOError: {e_pil_font_io}")
            raise
    except Exception as e_font:
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
                for char_in_word in word: # 변수명 변경
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
    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1:
            current_y_draw += int(typical_char_height * line_spacing_factor)
            continue
        text_width_draw, _ = get_text_dimensions(line, font)
        actual_x_draw = x
        if align == "right": actual_x_draw = x - text_width_draw
        elif align == "center": actual_x_draw = x - text_width_draw / 2
        
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
    # ... (이미지 로드, 기본 정보 추출 로직은 이전과 동일) ...
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
    
    # 비용 항목 계산 (에어컨 비용은 option_ac_cost_val에만, main_fee_yellow_box에서는 제외)
    total_moving_expenses_val = 0
    storage_fee_val = 0
    option_ac_cost_val = 0
    from_method_fee_val = 0
    to_method_fee_raw_val = 0
    regional_ladder_surcharge_val = 0

    AC_COST_LABEL = "에어컨 이전설치비" # 이 레이블은 calculations.py와 일치해야 합니다.

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, item_note_ignored in calculated_cost_items:
            label = str(item_l)
            try: amount = int(float(item_a or 0))
            except (ValueError, TypeError): amount = 0

            if label == AC_COST_LABEL:
                option_ac_cost_val += amount # 에어컨 비용은 여기에만 할당
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
        
        # "fee_value_next_to_ac_right"는 FIELD_MAP에서 제거했으므로, 여기서 값을 할당해도 그려지지 않음
        # 만약 이 값을 다른 곳에 (예: main_fee_yellow_box 또는 grand_total) 포함시키려면
        # total_moving_expenses_val 또는 grand_total_num 계산 시 option_ac_cost_val을 더해야 함
        # 현재는 에어컨 비용을 별도로 표시하지 않고, main_fee에 포함시키지 않는 것으로 가정
        
        "main_fee_yellow_box": _format_currency(total_moving_expenses_val), # 에어컨 비용이 제외된 순수 이사비
        "grand_total": _format_currency(grand_total_num), # 총액 (에어컨 비용 포함된 전체 견적 금액)

        "from_method_label": from_method_text_for_label,
        "from_method_fee_value": _format_currency(from_method_fee_val),
        "to_method_label": to_method_text_for_label,
        "to_method_fee_value": _format_currency(final_to_method_fee_val),

        "deposit_amount_display": _format_currency(deposit_amount_val),
        "storage_fee_display": _format_currency(storage_fee_val),
        "remaining_balance_display": _format_currency(remaining_balance_num),
        "special_notes_display": special_notes_content
    }

    # 품목 수량 매핑 (이전과 동일)
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
            print("ERROR [image_generator]: utils.get_item_qty function is not available. Item quantities might be incorrect.")
    except Exception as e_item_qty:
        print(f"Error processing item quantities for image: {e_item_qty}")
        traceback.print_exc()

    # 텍스트 그리기 (이전과 동일)
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

# ... (if __name__ == '__main__': 블록은 이전과 동일하게 유지 또는 테스트 케이스 업데이트) ...
if __name__ == '__main__':
    print("image_generator.py test mode")
    # AC_COST_LABEL을 테스트용 mock_costs의 레이블과 일치시키거나,
    # mock_costs에 해당 레이블의 항목을 추가해야 테스트가 정확해짐
    AC_COST_LABEL_TEST = "에어컨 이전설치비" # 실제 레이블과 동일하게 설정

    mock_state_test = {
        "customer_name": "위치변경 고객", "customer_phone": "010-7777-8888",
        "moving_date": date(2025, 6, 20),
        "from_location": "경기도 수원시 영통구 이의동 광교", "to_location": "서울시 서초구 반포동 아크로리버파크",
        "from_floor": "25", "to_floor": "12",
        "final_selected_vehicle": "15톤", "dispatched_5t": 3, 
        "from_method": "사다리차 🪜", "to_method": "사다리차 🪜",
        "deposit_amount": 1000000, # 계약금 예시
        "base_move_type": "가정 이사 🏠",
        "special_notes": "피아노 운반 시 전문가 동행 필수.\n오후 1시 정각 작업 시작 희망.",
        "qty_가정 이사 🏠_주요 품목_장롱": 15, # 5칸
        "qty_가정 이사 🏠_주요 품목_더블침대": 2,
        "qty_가정 이사 🏠_기타_에어컨": 3,
        "qty_가정 이사 🏠_포장 자재 📦_바구니": 80,
    }
    mock_costs_test = [
        ("기본 운임", 3000000, "15톤 기준"),
        ("출발지 사다리차", 400000, "25층, 15톤급 기준"), # 예시 금액
        ("도착지 사다리차", 280000, "12층, 15톤급 기준"), # 예시 금액
        (AC_COST_LABEL_TEST, 300000, "에어컨 3대 설치"), 
        ("추가 인력", 400000, "남2")
    ]
    mock_total_cost_test = sum(c[1] for c in mock_costs_test) # 3000000 + 400000 + 280000 + 300000 + 400000 = 4380000
    mock_personnel_test = {"final_men": 7+2, "final_women": 2} # 기본인력 + 추가인력

    try:
        # utils.get_item_qty 모킹은 이전과 동일하게 유지 또는 실제 utils.get_item_qty가 mock_state_test를 읽을 수 있도록 함
        image_bytes_test = create_quote_image(mock_state_test, mock_costs_test, mock_total_cost_test, mock_personnel_test)
        
        if image_bytes_test:
            timestamp_test = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_test = f"test_fee_pos_changed_{timestamp_test}.png"
            with open(filename_test, "wb") as f:
                f.write(image_bytes_test)
            print(f"Test image '{filename_test}' saved successfully.")
        else:
            print("Test image generation failed.")
    except Exception as e_main_test:
        print(f"Error in test run: {e_main_test}")
        traceback.print_exc()
