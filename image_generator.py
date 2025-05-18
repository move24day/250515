# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date, datetime # datetime 임포트 확인
import math
import traceback
import re

try:
    import data as app_data_for_img_gen # data.py 임포트
    import utils # utils.py 임포트
except ImportError:
    app_data_for_img_gen = None
    utils = None # utils도 None으로 초기화
    print("Warning [image_generator.py]: data.py or utils.py not found, some defaults/functionalities might not be available.")


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
item_y_spacing_val = 28.8
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491
item_x_col3_val = 756

# --- Y 좌표 및 기타 계산 변수 정의 (FIELD_MAP 보다 반드시 먼저 와야 함) ---
# 기본 Y 좌표 값
_y_from_floor_orig = 226
_y_to_floor_orig = 258
_y_sofa_3seater_orig = 549
_y_living_room_cabinet_orig = 677
_y_main_fee_yellow_box_orig = 775
_y_grand_total_orig = 861

# 차량 정보 Y
original_vehicle_y_calc = int(275 + item_y_spacing_val) # 약 303.8
vehicle_display_y_val = original_vehicle_y_calc - 2 # 약 301

# 고객/날짜 정보 Y
quote_date_y_val = 130
move_type_summary_y_val = int(quote_date_y_val - (item_y_spacing_val * 0.7) - 20 - 50) # 약 39 (기존 약 89에서 -50)


# 비용 관련 Y 좌표 (사용자 요청에 따라 "예전 값" 또는 조정된 값으로 설정)
# 이 값들을 "처음 올린 파일"의 수치 또는 정확히 원하시는 값으로 설정해주세요.
# 예시 값입니다. 실제 값을 입력해야 합니다.
from_work_fee_y_val = 805
to_work_fee_y_val = 833

grand_total_y_new = _y_grand_total_orig + 4 # 865

deposit_y_val = 789
remaining_balance_y_val = 826

storage_fee_y_val = _y_main_fee_yellow_box_orig # 보관료는 메인 비용과 같은 Y

# 특이사항 Y
special_notes_start_y_val = int(grand_total_y_new + item_y_spacing_val * 1.5) # 약 908

# X 좌표 관련
vehicle_number_x_val = 90
actual_vehicles_text_x_val = item_x_col2_others_val
costs_section_x_align_right_val = 410
work_method_fee_label_x_val = 35
work_method_text_display_x_val = int((item_x_col1_val + item_x_col2_baskets_val) / 2)
fees_x_val_right_aligned = item_x_col3_val # 계약금, 잔금 등의 금액 X좌표
special_notes_x_val = 80
special_notes_max_width_val = 700
special_notes_font_size_val = BASE_FONT_SIZE
move_type_summary_x_val = 640 + 100
move_type_summary_font_size_val = BASE_FONT_SIZE
move_type_summary_max_width_val = 150


def get_adjusted_font_size(original_size_ignored, field_key):
    if field_key == "customer_name": return BASE_FONT_SIZE
    if field_key == "customer_phone": return BASE_FONT_SIZE - 2
    if field_key.startswith("item_") and field_key not in ["item_x_col1_val", "item_x_col2_baskets_val", "item_x_col2_others_val", "item_x_col3_val"]:
        return item_font_size_val
    if field_key in ["grand_total", "remaining_balance_display"]: return BASE_FONT_SIZE + 2
    # 에어컨 설치비 삭제: 아래 라인 주석 처리 또는 삭제
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

# FIELD_MAP 정의 (모든 필요한 전역 변수 정의 이후)
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

    # 에어컨 설치비 삭제: 아래 라인 주석 처리 또는 삭제
    # "fee_value_next_to_ac_right": {"x": costs_section_x_align_right_val, "y": 680, "size": get_adjusted_font_size(0, "fee_value_next_to_ac_right"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},
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

ITEM_KEY_MAP = {
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장": "item_drawer_5dan",
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door",
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand",
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater", "식탁(4인)": "item_dining_table",
    "에어컨": "item_ac_left", # 이 품목 자체는 유지
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
            if word_width > max_width and len(word) > 1: # 단어가 최대 너비보다 크고, 한 글자가 아닌 경우 (한 글자는 그냥 찍음)
                if current_line: lines.append(current_line.strip()) # 이전까지의 라인 추가
                # 긴 단어 자체를 글자 단위로 분할 시도
                temp_word_line = ""
                for char_in_word in word:
                    temp_word_line_plus_char_width, _ = get_text_dimensions(temp_word_line + char_in_word, font)
                    if temp_word_line_plus_char_width <= max_width:
                        temp_word_line += char_in_word
                    else: # 현재 char를 포함하면 너비 초과
                        lines.append(temp_word_line) # 이전까지의 char들로 만든 라인 추가
                        temp_word_line = char_in_word # 새 라인은 현재 char로 시작
                if temp_word_line: lines.append(temp_word_line) # 남은 char들로 라인 추가
                current_line = "" # 현재 라인 리셋
                continue

            # 현재 라인에 단어 추가 시 너비 계산
            current_line_plus_word_width, _ = get_text_dimensions(current_line + word + " ", font) if current_line else get_text_dimensions(word + " ", font)
            if current_line_plus_word_width <= max_width:
                current_line += word + " "
            else: # 현재 단어를 추가하면 최대 너비 초과
                if current_line: lines.append(current_line.strip()) # 이전까지의 라인 추가
                current_line = word + " " # 새 라인은 현재 단어로 시작
        if current_line.strip(): lines.append(current_line.strip()) # 마지막 라인 추가
        if not lines and text: lines.append(text) # 분할되지 않은 경우 (예: 짧은 텍스트)
    else: # max_width가 없는 경우, 기존처럼 \n 기준으로 분리
        lines.extend(text.split('\n'))

    current_y_draw = y
    first_line = True
    _, typical_char_height = get_text_dimensions("A", font) # 높이 계산용
    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1: # 빈 줄이고 첫 줄이 아니면 간격만
            current_y_draw += int(typical_char_height * line_spacing_factor)
            continue

        text_width_draw, _ = get_text_dimensions(line, font)
        actual_x_draw = x
        if align == "right": actual_x_draw = x - text_width_draw
        elif align == "center": actual_x_draw = x - text_width_draw / 2
        
        # PIL의 text 메소드는 기본적으로 baseline을 기준으로 y좌표를 인식하므로,
        # 여러 줄 텍스트를 그릴 때 수동으로 y좌표를 조정해야 함.
        # anchor="lt" (left-top) 또는 "la" (left-ascent)를 사용하여 y좌표 해석 방식을 변경 가능.
        # 여기서는 anchor를 사용하지 않고 수동으로 y를 관리.
        draw.text((actual_x_draw, current_y_draw), line, font=font, fill=color) # anchor 기본값 사용 (lt와 유사하게 동작하나, 폰트에 따라 다를 수 있음)

        current_y_draw += int(typical_char_height * line_spacing_factor) # 다음 줄 y좌표 업데이트
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

# create_quote_image 함수 정의 시작
def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    print("DEBUG [ImageGenerator]: create_quote_image function CALLED")
    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
        print("DEBUG [ImageGenerator]: Background image loaded.")
    except FileNotFoundError:
        print(f"ERROR [ImageGenerator]: Background image not found at {BACKGROUND_IMAGE_PATH}")
        img = Image.new('RGB', (900, 1400), color = 'white') # 예시 크기, 실제 배경에 맞춰야 함
        draw = ImageDraw.Draw(img)
        try: error_font = _get_font(size=24)
        except: error_font = ImageFont.load_default() # 최종 폴백
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, img.height / 2 - 20, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, img.height / 2 + 20, error_font, (255,0,0), "center")
        # 이 경우 None을 반환하거나, 혹은 이 임시 이미지를 반환할 수 있습니다.
        # 여기서는 None을 반환하여 호출부에서 처리하도록 합니다.
        return None
    except Exception as e_bg:
        print(f"ERROR [ImageGenerator]: Error loading background image: {e_bg}")
        return None # 배경 로드 실패 시 None 반환

    if not os.path.exists(FONT_PATH_REGULAR): print(f"WARNING [ImageGenerator]: Regular font missing at {FONT_PATH_REGULAR}")
    if not os.path.exists(FONT_PATH_BOLD): print(f"WARNING [ImageGenerator]: Bold font missing at {FONT_PATH_BOLD}")

    # --- 데이터 추출 ---
    move_type_summary_parts = []
    base_move_type = state_data.get('base_move_type', "이사")
    if "가정" in base_move_type: move_type_summary_parts.append("가정")
    elif "사무실" in base_move_type: move_type_summary_parts.append("사무실")
    else: move_type_summary_parts.append(base_move_type.split(" ")[0]) # 첫 단어만 사용

    if state_data.get('is_storage_move', False):
        storage_type = state_data.get('storage_type', '')
        if "컨테이너" in storage_type: move_type_summary_parts.append("컨테이너보관")
        elif "실내" in storage_type: move_type_summary_parts.append("실내보관")
        else: move_type_summary_parts.append("보관") # 일반적인 보관
        # 전기 사용 여부 추가
        if state_data.get('storage_use_electricity', False):
            move_type_summary_parts.append("(전기사용)")
    
    if state_data.get('apply_long_distance', False):
        move_type_summary_parts.append("장거리")
    # 최종 이사 유형 텍스트 생성
    move_type_summary_text = " ".join(move_type_summary_parts) + " 이사" if move_type_summary_parts else base_move_type


    customer_name = state_data.get('customer_name', '')
    customer_phone = state_data.get('customer_phone', '')
    moving_date_obj = state_data.get('moving_date')
    moving_date_str = moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj)
    quote_date_str = date.today().strftime('%Y-%m-%d') # 견적일은 항상 오늘
    from_location = state_data.get('from_location', '')
    to_location = state_data.get('to_location', '')
    from_floor = str(state_data.get('from_floor', '')) # 층수는 문자열로
    to_floor = str(state_data.get('to_floor', ''))
    
    selected_vehicle_for_calc = state_data.get('final_selected_vehicle', '')
    vehicle_tonnage_display = ""
    if isinstance(selected_vehicle_for_calc, str):
        match = re.search(r'(\d+(\.\d+)?)', selected_vehicle_for_calc) # 정규식으로 숫자(톤수) 부분만 추출
        if match: vehicle_tonnage_display = match.group(1)
    elif isinstance(selected_vehicle_for_calc, (int, float)): # 혹시 숫자형으로 들어올 경우 대비
        vehicle_tonnage_display = str(selected_vehicle_for_calc)

    # 실제 투입 차량 정보 구성
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

    from_method_raw = state_data.get('from_method', '') # 예: "사다리차 🪜"
    from_method_text_for_label = "출발" + (from_method_raw.split(" ")[0] if from_method_raw else "작업") # "출발사다리차"
    from_method_text_for_display_top = from_method_raw.split(" ")[0] if from_method_raw else "" # "사다리차"

    to_method_raw = state_data.get('to_method', '')
    to_method_text_for_label = "도착" + (to_method_raw.split(" ")[0] if to_method_raw else "작업")
    to_method_text_for_display_top = to_method_raw.split(" ")[0] if to_method_raw else ""
    
    # --- 비용 항목 계산 ---
    total_moving_expenses_val = 0 # 에어컨, 보관료, 작업비, 특정 할증 제외한 순수 이사 비용 + 조정금액 등
    storage_fee_val = 0
    # option_ac_cost_val = 0 # 에어컨 설치비 삭제: 이 변수 초기화 삭제 또는 주석 처리
    from_method_fee_val = 0
    to_method_fee_raw_val = 0 # 지방 사다리 추가금 제외한 도착지 작업비
    regional_ladder_surcharge_val = 0 # 지방 사다리 추가금

    AC_COST_LABEL = "에어컨 이전설치비" # 에어컨 비용 레이블 일치 확인

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, item_note_ignored in calculated_cost_items:
            label = str(item_l)
            try: amount = int(float(item_a or 0)) # 금액은 정수 처리
            except (ValueError, TypeError): amount = 0

            # 에어컨 설치비 삭제: 아래 조건문 블록 전체 주석 처리 또는 삭제
            # if label == AC_COST_LABEL:
            #     option_ac_cost_val += amount 
            if label == '보관료': # '보관료'로 정확히 일치하는지 확인
                storage_fee_val += amount
            elif label.startswith('출발지 사다리차') or label.startswith('출발지 스카이'): # 출발지 작업비
                from_method_fee_val += amount
            elif label.startswith('도착지 사다리차') or label.startswith('도착지 스카이'): # 도착지 작업비 (순수)
                to_method_fee_raw_val += amount
            elif label == '지방 사다리 추가요금': # 지방 사다리 할증
                 regional_ladder_surcharge_val += amount
            # 그 외 (부가세, 카드수수료 제외한) 모든 비용을 '총괄 이사 비용'으로 합산
            elif label not in [AC_COST_LABEL, '보관료', '지방 사다리 추가요금'] and \
                 not label.startswith('출발지 사다리차') and not label.startswith('출발지 스카이') and \
                 not label.startswith('도착지 사다리차') and not label.startswith('도착지 스카이') and \
                 "부가세" not in label and "카드결제 수수료" not in label:
                total_moving_expenses_val += amount
            
    # 도착지 작업비 최종 계산 (지방 사다리 추가금 포함)
    final_to_method_fee_val = to_method_fee_raw_val + regional_ladder_surcharge_val


    deposit_amount_val = int(float(state_data.get('deposit_amount', 0) or 0))
    grand_total_num = int(float(total_cost_overall or 0)) # 계산된 총액 (VAT, 카드수수료 등 모두 포함)
    remaining_balance_num = grand_total_num - deposit_amount_val
    
    special_notes_content = state_data.get('special_notes', '')


    # --- 그릴 데이터 준비 ---
    data_to_draw = {
        "move_type_summary_display": move_type_summary_text,
        "customer_name": customer_name, "customer_phone": customer_phone, "quote_date": quote_date_str,
        "moving_date": moving_date_str, "from_location": from_location, "to_location": to_location,
        "from_floor": from_floor, "to_floor": to_floor,
        "vehicle_type_numbers_only": vehicle_tonnage_display, # 선택 차량 톤수 (숫자만)
        "actual_dispatched_vehicles_display": actual_dispatched_vehicles_text, # 실제 투입 차량 텍스트
        "workers_male": workers_male, "workers_female": workers_female,
        "from_work_method_text_display": from_method_text_for_display_top, # 출발지 작업 방법 (상단 표시용)
        "to_work_method_text_display": to_method_text_for_display_top, # 도착지 작업 방법 (상단 표시용)
        
        # 에어컨 설치비 삭제: 아래 라인 주석 처리 또는 삭제
        # "fee_value_next_to_ac_right": _format_currency(option_ac_cost_val), # 에어컨 설치 비용 (오른쪽 항목 옆)
        
        "main_fee_yellow_box": _format_currency(total_moving_expenses_val), # 총괄 이사 비용 (노란색 박스)
        "grand_total": _format_currency(grand_total_num), # 총액 (VAT/카드 포함)

        # 작업비 레이블 및 값 (출발/도착)
        "from_method_label": from_method_text_for_label,
        "from_method_fee_value": _format_currency(from_method_fee_val),
        "to_method_label": to_method_text_for_label,
        "to_method_fee_value": _format_currency(final_to_method_fee_val),

        "deposit_amount_display": _format_currency(deposit_amount_val), # 계약금
        "storage_fee_display": _format_currency(storage_fee_val),      # 보관료
        "remaining_balance_display": _format_currency(remaining_balance_num), # 잔금
        "special_notes_display": special_notes_content # 특이사항
    }

    # 품목 수량 채우기
    print("DEBUG [ImageGenerator]: Populating item quantities...")
    try:
        current_move_type = state_data.get("base_move_type")
        # FIELD_MAP에 정의된 아이템 키만 초기화 (없는 키 접근 방지)
        for field_map_key in ITEM_KEY_MAP.values():
            if field_map_key.startswith("item_") and field_map_key in FIELD_MAP: # FIELD_MAP에 정의된 키만
                data_to_draw[field_map_key] = "" # 기본값 빈 문자열

        if utils and hasattr(utils, 'get_item_qty') and callable(utils.get_item_qty):
            for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
                # ITEM_KEY_MAP에 있는 아이템이 FIELD_MAP에도 정의되어 있는지 확인
                if field_map_key_from_map in FIELD_MAP and field_map_key_from_map.startswith("item_"):
                    # utils.get_item_qty는 state_data와 data.py의 품목 이름을 직접 사용
                    qty_int = utils.get_item_qty(state_data, data_py_item_name)
                    if qty_int > 0:
                        text_val = str(qty_int)
                        # 장롱의 경우 특별 처리 (예: 3칸당 1.0으로 표시)
                        if data_py_item_name == "장롱":
                            try: text_val = f"{(float(qty_int) / 3.0):.1f}" # 3으로 나누고 소수점 한자리
                            except: text_val = str(qty_int) # 계산 실패 시 원래 수량
                        data_to_draw[field_map_key_from_map] = text_val
        else:
            print("ERROR [ImageGenerator]: utils.get_item_qty function is not available. Cannot populate item quantities.")
    except Exception as e_item_qty:
        print(f"ERROR [ImageGenerator]: Error processing item quantities: {e_item_qty}")
        traceback.print_exc()
    # print(f"DEBUG [ImageGenerator]: data_to_draw (items part sample after population): { {k:v for k,v in data_to_draw.items() if k.startswith('item_') and v} }")


    # --- 텍스트 그리기 ---
    print("DEBUG [ImageGenerator]: Starting to draw text elements on image.")
    for key, M_raw in FIELD_MAP.items():
        M = {} # 각 필드 정의 복사 (원본 FIELD_MAP 변경 방지)
        for k_map, v_map in M_raw.items(): # x, y, size 등 숫자형으로 변환 시도
            if k_map in ["x", "y", "size", "max_width"]:
                try: M[k_map] = int(v_map)
                except (ValueError, TypeError) : M[k_map] = v_map # 변환 실패 시 원본 유지
            else: M[k_map] = v_map

        # 그릴 텍스트 내용 가져오기 (FIELD_MAP에 text_override가 있으면 그것 사용)
        text_content_value = M.get("text_override", data_to_draw.get(key))
        final_text_to_draw = "" # 최종적으로 그릴 텍스트 (None이나 공백 처리 후)

        if text_content_value is not None and str(text_content_value).strip() != "":
            final_text_to_draw = str(text_content_value)
        
        # 실제로 그릴 내용이 있거나, 특이사항처럼 빈칸이라도 그려야 하는 경우
        if final_text_to_draw.strip() != "" or (key == "special_notes_display" and final_text_to_draw == ""): # 특이사항은 내용 없어도 영역은 잡아야 할 수 있음
            size_to_use = get_adjusted_font_size(M.get("size", BASE_FONT_SIZE), key)
            try:
                font_obj = _get_font(font_type=M.get("font", "regular"), size=size_to_use)
            except Exception as font_load_err_draw:
                print(f"ERROR [ImageGenerator]: Critical error loading font for key '{key}'. Skipping this text. Error: {font_load_err_draw}")
                continue # 이 텍스트는 건너뛰고 다음으로

            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width") # 최대 너비 (줄바꿈용)
            line_spacing_factor = M.get("line_spacing_factor", 1.15) # 줄 간격 배수
            
            # print(f"DEBUG [ImageGenerator]: Drawing: Key='{key}', Text='{final_text_to_draw[:30]}...', X={M['x']}, Y={M['y']}")
            _draw_text_with_alignment(draw, final_text_to_draw, M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    print("DEBUG [ImageGenerator]: Text drawing complete. Saving image to bytes.")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG') # 이미지 포맷 PNG로 저장
    img_byte_arr.seek(0) # BytesIO 포인터 처음으로 이동
    print("DEBUG [ImageGenerator]: Image generation successful.")
    return img_byte_arr.getvalue()
# 함수 정의 끝

# 테스트용 if __name__ == '__main__': 블록
if __name__ == '__main__':
    print("image_generator.py test mode")
    AC_COST_LABEL_TEST = "에어컨 이전설치비" # 테스트용 레이블

    # 테스트 데이터 (에어컨 비용 포함 시나리오)
    mock_state_test_pos = {
        "customer_name": "최종 점검 고객", "customer_phone": "010-1234-5678",
        "moving_date": date(2025, 1, 10),
        "from_location": "서울특별시 테스트구 테스트동 123-45", "to_location": "경기도 테스트시 테스트로 789",
        "from_floor": "3", "to_floor": "7",
        "final_selected_vehicle": "2.5톤", "dispatched_2_5t": 1, # 실제 투입 차량
        "from_method": "계단 🚶", "to_method": "사다리차 🪜",
        "deposit_amount": 100000,
        "base_move_type": "가정 이사 🏠",
        "special_notes": "테스트 노트입니다.\n여러 줄 테스트입니다.\n마지막 줄입니다.",
        "qty_가정 이사 🏠_주요 품목_장롱": 6, # 2.0 칸으로 표시되어야 함
        "qty_가정 이사 🏠_주요 품목_4도어 냉장고": 1,
        "qty_가정 이사 🏠_기타_에어컨": 1, # 에어컨 품목 수량 (이것 자체는 비용 계산에 직접 사용 안됨)
        "qty_가정 이사 🏠_포장 자재 📦_바구니": 20,
        "qty_가정 이사 🏠_포장 자재 📦_중박스": 10,
    }
    mock_costs_test_pos = [
        ("기본 운임", 900000, "2.5톤 기준"),
        # 출발지는 계단이므로 작업비 항목 없을 수 있음 (또는 0원)
        ("도착지 사다리차", 180000, "7층, 5톤(기본) 기준"), # 2.5톤 차량이지만 사다리는 5톤 기준으로 계산될 수 있음
        # (AC_COST_LABEL_TEST, 50000, "에어컨 1대 기본"), # 에어컨 설치비 삭제: 테스트 데이터에서도 주석 처리
    ]
    # 에어컨 설치비 삭제: 총 비용 계산에서 해당 금액 제외
    mock_total_cost_test_pos = 900000 + 180000 # + 50000
    mock_personnel_test_pos = {"final_men": 2, "final_women": 1}

    try:
        # create_quote_image 함수 호출
        image_bytes_test = create_quote_image(mock_state_test_pos, mock_costs_test_pos, mock_total_cost_test_pos, mock_personnel_test_pos)
        
        if image_bytes_test:
            timestamp_test = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_test = f"test_image_final_check_{timestamp_test}.png"
            with open(filename_test, "wb") as f:
                f.write(image_bytes_test)
            print(f"Test image '{filename_test}' saved successfully. Please verify all elements and positions.")
        else:
            print("Test image generation failed. Check logs above for [ImageGenerator] messages.")
    except Exception as e_main_test:
        print(f"Error in test run: {e_main_test}")
        traceback.print_exc()
