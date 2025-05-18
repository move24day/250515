# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math
import traceback
import re

try:
    import data as app_data_for_img_gen # data.py 임포트
except ImportError:
    app_data_for_img_gen = None
    print("Warning [image_generator.py]: data.py not found, some defaults might not be available.")


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)
TEXT_COLOR_BLUE = (20, 20, 180)

BASE_FONT_SIZE = 18
item_y_start_val = 334
item_y_spacing_val = 28.8
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491
item_x_col3_val = 756

original_vehicle_y_calc = int(275 + item_y_spacing_val)
vehicle_display_y_val = original_vehicle_y_calc - 2
vehicle_number_x_val = 90
actual_vehicles_text_x_val = item_x_col2_others_val

costs_section_x_align_right_val = 410
work_method_fee_label_x_val = 35

_y_from_floor_orig = 226
_y_to_floor_orig = 258
work_method_text_display_x_val = int((item_x_col1_val + item_x_col2_baskets_val) / 2)

_y_living_room_cabinet_orig = 677
_y_sofa_3seater_orig = 549
_y_main_fee_yellow_box_orig = 775
_y_grand_total_orig = 861

from_work_fee_y_val = _y_living_room_cabinet_orig + abs(_y_sofa_3seater_orig - _y_living_room_cabinet_orig) # 805
to_work_fee_y_val = from_work_fee_y_val + item_y_spacing_val # 833.8

fees_x_val_right_aligned = item_x_col3_val

deposit_y_val = from_work_fee_y_val
storage_fee_y_val = _y_main_fee_yellow_box_orig
remaining_balance_y_val = deposit_y_val + item_y_spacing_val + (item_y_spacing_val / 2) # 약 848.2

grand_total_y_new = _y_grand_total_orig + 4 # 865

special_notes_start_y_val = int(grand_total_y_new + item_y_spacing_val * 1.5) # 약 908
special_notes_x_val = 80
special_notes_max_width_val = 700
special_notes_font_size_val = BASE_FONT_SIZE

quote_date_y_val = 130
move_type_summary_y_val = int(quote_date_y_val - (item_y_spacing_val * 0.7) - 20 - 50)
move_type_summary_x_val = 640 + 100
move_type_summary_font_size_val = BASE_FONT_SIZE
move_type_summary_max_width_val = 150


def get_adjusted_font_size(original_size_ignored, field_key):
    if field_key == "customer_name": return BASE_FONT_SIZE
    if field_key == "customer_phone": return BASE_FONT_SIZE - 2
    if field_key.startswith("item_") and field_key not in ["item_x_col1_val", "item_x_col2_baskets_val", "item_x_col2_others_val", "item_x_col3_val"]:
        return item_font_size_val
    if field_key in ["grand_total", "remaining_balance_display"]: return BASE_FONT_SIZE + 2
    # "fee_value_next_to_ac_right" 키가 삭제되었으므로, 이 부분도 주석 처리 또는 삭제 가능 (만약 다른 곳에서 사용하지 않는다면)
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
        "x": move_type_summary_x_val,
        "y": move_type_summary_y_val,
        "size": get_adjusted_font_size(0, "move_type_summary_display"),
        "font": "bold",
        "color": TEXT_COLOR_BLUE,
        "align": "right",
        "max_width": move_type_summary_max_width_val,
        "line_spacing_factor": 1.1
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

    # "fee_value_next_to_ac_right" 항목 주석 처리 또는 삭제
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
        "x": special_notes_x_val,
        "y": special_notes_start_y_val,
        "size": get_adjusted_font_size(0, "special_notes_display"),
        "font": "regular",
        "color": TEXT_COLOR_DEFAULT,
        "align": "left",
        "max_width": special_notes_max_width_val,
        "line_spacing_factor": 1.3
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
    "의자": "item_chair",
    "테이블": "item_table",
    "담요": "item_blanket",
    "바구니": "item_basket",
    "중박스": "item_medium_box",
    "중대박스": "item_large_box", # 이 키가 '중자바구니' 또는 다른 실제 품목명과 매칭되는지 확인 필요
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box", # '옷행거'는 종종 'clothes_box'가 아닌 다른 키와 매칭될 수 있음 (예: item_hanger)
    "스타일러": "item_styler",
    "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic",
    "복합기": "item_copier", # '복합기' 또는 '프린터'
    "TV(45인치)": "item_tv_45",
    "TV(75인치)": "item_tv_stand", # TV 스탠드가 아닌 TV 자체를 의미할 수 있음 (키 이름 주의)
    "벽걸이": "item_wall_mount_item", # '벽걸이 TV' 또는 '벽걸이 에어컨' 등 구체화 필요
    "금고": "item_safe",
    "앵글": "item_angle_shelf",
    "파티션": "item_partition",
    "5톤진입": "item_5ton_access", # 이것이 품목인지, 아니면 작업 조건인지 확인 필요
    "이불박스": "item_duvet_box"
}

def get_text_dimensions(text_string, font):
    if not text_string: return 0,0
    if hasattr(font, 'getbbox'):
        try:
            bbox = font.getbbox(str(text_string))
            width = bbox[2] - bbox[0]
            ascent, descent = font.getmetrics()
            height = ascent + descent
        except Exception: # Fallback for some PIL/Pillow versions or font issues
            if hasattr(font, 'getlength'): width = font.getlength(str(text_string))
            else: width = len(str(text_string)) * (font.size if hasattr(font, 'size') else 10) / 2 # Rough estimate
            ascent, descent = font.getmetrics()
            height = ascent + descent
    elif hasattr(font, 'getmask'): # Older PIL method
        try:
            width, height = font.getmask(str(text_string)).size
        except Exception:
            ascent, descent = font.getmetrics()
            height = ascent + descent
            width = font.getlength(str(text_string)) if hasattr(font, 'getlength') else len(str(text_string)) * height / 2
    else: # Basic fallback
        ascent, descent = font.getmetrics()
        height = ascent + descent
        if hasattr(font, 'getlength'):
            width = font.getlength(str(text_string))
        else:
            width = len(str(text_string)) * height / 2 # Very rough estimate
    return width, height

def _get_font(font_type="regular", size=12):
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD
        # else: print(f"Warning: Bold font {FONT_PATH_BOLD} not found, using regular.")
    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError: # Font file not found or cannot be read
        # print(f"Warning: Font '{font_path_to_use}' not found or unreadable. Falling back to default.")
        try: return ImageFont.load_default(size=size) # Try to load default with size
        except TypeError: return ImageFont.load_default() # If size argument is not supported by default
        except Exception as e_pil_font:
            print(f"Error loading default PIL font: {e_pil_font}")
            raise # Re-raise if default also fails critically
    except Exception as e_font:
        print(f"Error loading font {font_path_to_use}: {e_font}")
        raise # Re-raise other font loading errors

def _draw_text_with_alignment(draw, text, x, y, font, color, align="left", max_width=None, line_spacing_factor=1.2):
    if text is None: text = ""
    text = str(text)
    lines = []

    if max_width:
        words = text.split(' ') # 공백 기준으로 단어 분리
        current_line = ""
        for word in words:
            word_width, _ = get_text_dimensions(word, font)
            # 단일 단어가 max_width를 초과하는 경우 (한글 등에서 발생 가능) - 글자 단위로 분리 시도
            if word_width > max_width and len(word) > 1: # 최소 2글자 이상일 때만 분리 시도
                if current_line: # 이전까지의 라인 추가
                    lines.append(current_line.strip())
                # 긴 단어 글자 단위 분리
                temp_word_line = ""
                for char_idx, char in enumerate(word):
                    temp_word_line_plus_char_width, _ = get_text_dimensions(temp_word_line + char, font)
                    if temp_word_line_plus_char_width <= max_width:
                        temp_word_line += char
                    else: # 현재 글자 추가 시 넘치면 이전까지의 부분 저장
                        lines.append(temp_word_line)
                        temp_word_line = char # 새 라인은 현재 글자로 시작
                if temp_word_line: # 남은 부분 추가
                    lines.append(temp_word_line)
                current_line = "" # 현재 라인 초기화
                continue # 다음 단어로

            # 현재 라인에 단어 추가 시 너비 확인 (단어 뒤 공백 포함)
            current_line_plus_word_width, _ = get_text_dimensions(current_line + word + " ", font) if current_line else get_text_dimensions(word + " ", font)

            if current_line_plus_word_width <= max_width:
                current_line += word + " "
            else: # 현재 단어 추가 시 넘치면
                if current_line: # 이전 라인이 있으면 추가
                    lines.append(current_line.strip())
                current_line = word + " " # 새 라인은 현재 단어로 시작
        
        if current_line.strip(): # 마지막 라인 추가
            lines.append(current_line.strip())
        
        if not lines and text: # max_width가 있으나 분리할 단어가 없는 짧은 텍스트
             lines.append(text)

    else: # max_width가 없으면 개행 문자로만 분리
        lines.extend(text.split('\n'))

    current_y = y
    first_line = True
    _, typical_char_height = get_text_dimensions("A", font) # 기준 높이 (한 줄 높이)

    for line in lines:
        # 빈 줄 처리: 첫 줄이 아니고, 여러 줄 중 빈 줄은 간격만 띄움
        if not line.strip() and not first_line and len(lines) > 1:
            current_y += int(typical_char_height * line_spacing_factor)
            continue
        
        text_width, _ = get_text_dimensions(line, font)
        actual_x = x
        if align == "right":
            actual_x = x - text_width
        elif align == "center":
            actual_x = x - text_width / 2
        
        draw.text((actual_x, current_y), line, font=font, fill=color, anchor="lt") # anchor='lt' (left-top)
        current_y += int(typical_char_height * line_spacing_factor)
        first_line = False
    return current_y # 마지막으로 그려진 Y 좌표 반환 (다음 요소 위치 잡는데 사용 가능)


def _format_currency(amount_val):
    if amount_val is None or str(amount_val).strip() == "": return ""
    try:
        # 쉼표 제거 후 float 변환, 그 다음 int 변환
        num_val = float(str(amount_val).replace(",", "").strip())
        num = int(num_val) # 소수점 이하 버림
        return f"{num:,}" # 천 단위 쉼표 포맷
    except ValueError: # 변환 실패 시 원본 문자열 반환
        return str(amount_val)

def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA") # RGBA로 열어 투명도 지원
        draw = ImageDraw.Draw(img)
    except FileNotFoundError:
        print(f"Error: Background image not found at {BACKGROUND_IMAGE_PATH}")
        # 대체 이미지 생성 또는 에러 반환
        img = Image.new('RGB', (900, 1400), color = 'white') # 임시 배경
        draw = ImageDraw.Draw(img)
        try: error_font = _get_font(size=24)
        except: error_font = ImageFont.load_default() # 최종 폴백
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, 480, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, 520, error_font, (255,0,0), "center")
        # return None # 여기서 중단하거나, 임시 이미지라도 반환할 수 있음
    except Exception as e_bg:
        print(f"Error loading background image: {e_bg}")
        return None # 배경 이미지 로드 실패 시 None 반환

    # 폰트 존재 여부 확인 (애플리케이션 시작 시점에 하는 것이 더 효율적일 수 있음)
    if not os.path.exists(FONT_PATH_REGULAR): print(f"Warning: Regular font missing at {FONT_PATH_REGULAR}")
    if not os.path.exists(FONT_PATH_BOLD): print(f"Warning: Bold font missing at {FONT_PATH_BOLD}")

    # --- 데이터 추출 및 준비 ---
    # (기존 데이터 추출 로직 유지)
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
    moving_date_obj = state_data.get('moving_date') # date 객체로 가정
    moving_date_str = moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj)
    quote_date_str = date.today().strftime('%Y-%m-%d') # 오늘 날짜
    from_location = state_data.get('from_location', '')
    to_location = state_data.get('to_location', '')
    from_floor = str(state_data.get('from_floor', '')) # 문자열로 통일
    to_floor = str(state_data.get('to_floor', ''))   # 문자열로 통일
    
    selected_vehicle_for_calc = state_data.get('final_selected_vehicle', '')
    vehicle_tonnage_display = ""
    if isinstance(selected_vehicle_for_calc, str):
        match = re.search(r'(\d+(\.\d+)?)', selected_vehicle_for_calc) # "X톤" 에서 숫자.숫자 또는 숫자 추출
        if match: vehicle_tonnage_display = match.group(1) # 예: "2.5" 또는 "5"
    elif isinstance(selected_vehicle_for_calc, (int, float)): # 숫자로 직접 올 경우
        vehicle_tonnage_display = str(selected_vehicle_for_calc)

    # 실제 투입 차량 정보
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

    # 작업 방법 텍스트 준비
    from_method_raw = state_data.get('from_method', '') # 예: "사다리차 🪜"
    from_method_text_for_label = "출발" + (from_method_raw.split(" ")[0] if from_method_raw else "작업") # 예: "출발사다리차"
    from_method_text_for_display_top = from_method_raw.split(" ")[0] if from_method_raw else "" # 예: "사다리차"

    to_method_raw = state_data.get('to_method', '')
    to_method_text_for_label = "도착" + (to_method_raw.split(" ")[0] if to_method_raw else "작업")
    to_method_text_for_display_top = to_method_raw.split(" ")[0] if to_method_raw else ""


    # 비용 항목 계산
    total_moving_expenses_val = 0 # 에어컨, 보관, VAT, 카드수수료 제외한 순수 이사비용 (노란 박스용)
    storage_fee_val = 0
    option_ac_cost_val = 0      # 에어컨 비용
    from_method_fee_val = 0     # 출발지 작업비 (사다리/스카이)
    to_method_fee_raw_val = 0   # 도착지 작업비 (사다리/스카이) - 지방할증 전
    regional_ladder_surcharge_val = 0 # 지방 사다리 추가요금

    # calculations.py에서 에어컨 비용에 사용하는 정확한 레이블로 설정해야 함
    AC_COST_LABEL = "에어컨 이전설치비" # <<--- 이 부분을 실제 사용하는 레이블로 변경하세요!

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
            # VAT, 카드수수료, 그리고 이미 별도로 처리된 비용들을 제외하고 합산
            elif label not in [AC_COST_LABEL, '보관료', '지방 사다리 추가요금'] and \
                 not label.startswith('출발지 사다리차') and not label.startswith('출발지 스카이') and \
                 not label.startswith('도착지 사다리차') and not label.startswith('도착지 스카이') and \
                 "부가세" not in label and "카드결제 수수료" not in label:
                total_moving_expenses_val += amount
            
    final_to_method_fee_val = to_method_fee_raw_val + regional_ladder_surcharge_val # 도착지 작업비 (지방할증 포함)

    # 계약금, 총액, 잔금
    deposit_amount_val = int(float(state_data.get('deposit_amount', 0) or 0)) # UI 직접 입력값 사용
    grand_total_num = int(float(total_cost_overall or 0)) # 함수 인자로 받은 전체 비용
    remaining_balance_num = grand_total_num - deposit_amount_val
    
    special_notes_content = state_data.get('special_notes', '')


    data_to_draw = {
        "move_type_summary_display": move_type_summary_text,
        "customer_name": customer_name, "customer_phone": customer_phone, "quote_date": quote_date_str,
        "moving_date": moving_date_str, "from_location": from_location, "to_location": to_location,
        "from_floor": from_floor, "to_floor": to_floor,
        "vehicle_type_numbers_only": vehicle_tonnage_display, # 예: "5" 또는 "7.5"
        "actual_dispatched_vehicles_display": actual_dispatched_vehicles_text, # 예: "5톤:1, 2.5톤:1"
        "workers_male": workers_male, "workers_female": workers_female,
        "from_work_method_text_display": from_method_text_for_display_top, # 예: "사다리차"
        "to_work_method_text_display": to_method_text_for_display_top,     # 예: "계단"
        
        # "fee_value_next_to_ac_right": _format_currency(option_ac_cost_val), # <<<--- 이 항목을 표시하지 않음
        
        "main_fee_yellow_box": _format_currency(total_moving_expenses_val), # 노란 박스 메인 비용
        "grand_total": _format_currency(grand_total_num), # 총액

        "from_method_label": from_method_text_for_label, # 예: "출발사다리차"
        "from_method_fee_value": _format_currency(from_method_fee_val),
        "to_method_label": to_method_text_for_label, # 예: "도착계단"
        "to_method_fee_value": _format_currency(final_to_method_fee_val),

        "deposit_amount_display": _format_currency(deposit_amount_val),
        "storage_fee_display": _format_currency(storage_fee_val),
        "remaining_balance_display": _format_currency(remaining_balance_num),
        "special_notes_display": special_notes_content
    }

    # 품목 수량 매핑
    try:
        current_move_type = state_data.get("base_move_type")
        item_defs_for_current_type = {}
        if app_data_for_img_gen and hasattr(app_data_for_img_gen, 'item_definitions') and current_move_type in app_data_for_img_gen.item_definitions:
            item_defs_for_current_type = app_data_for_img_gen.item_definitions[current_move_type]

        # 모든 ITEM_KEY_MAP의 값(FIELD_MAP 키)에 대해 빈 문자열로 초기화 (수량 없는 항목 빈칸 처리)
        for key_in_fieldmap_vals in ITEM_KEY_MAP.values():
            if key_in_fieldmap_vals.startswith("item_") and key_in_fieldmap_vals not in data_to_draw :
                 data_to_draw[key_in_fieldmap_vals] = "" # 또는 0

        # 실제 수량 채우기
        if utils.get_item_qty and callable(utils.get_item_qty): # utils.get_item_qty 사용
            for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
                qty_int = utils.get_item_qty(state_data, data_py_item_name) # utils 함수 사용
                if qty_int > 0:
                    text_val = str(qty_int)
                    if data_py_item_name == "장롱": # 장롱 칸 수 특별 처리
                        try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                        except: text_val = str(qty_int) # 실패 시 원본 수량
                    data_to_draw[field_map_key_from_map] = text_val
        else: # utils.get_item_qty 사용 불가 시, 기존 로직 (참고용, 실제로는 utils.get_item_qty가 있어야 함)
            print("Warning [image_generator]: utils.get_item_qty is not available. Item quantities might be incorrect.")
            # 기존 직접 접근 방식 (오류 가능성 높음, utils.get_item_qty가 올바른 방식)
            if isinstance(item_defs_for_current_type, dict):
                for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
                    found_section = None
                    for section_name, item_list_in_section in item_defs_for_current_type.items():
                        if isinstance(item_list_in_section, list) and data_py_item_name in item_list_in_section:
                            found_section = section_name; break
                    if found_section:
                        widget_key = f"qty_{current_move_type}_{found_section}_{data_py_item_name}"
                        qty_raw = state_data.get(widget_key, 0)
                        qty_int = 0
                        try:
                            if qty_raw is not None and str(qty_raw).strip() != "": qty_int = int(float(str(qty_raw)))
                        except ValueError: qty_int = 0
                        if qty_int > 0:
                            text_val = str(qty_int)
                            if data_py_item_name == "장롱":
                                try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                                except: text_val = str(qty_int)
                            data_to_draw[field_map_key_from_map] = text_val


    except Exception as e_item:
        print(f"Error processing item quantities for image: {e_item}")
        traceback.print_exc()


    # 텍스트 그리기
    for key, M_raw in FIELD_MAP.items():
        # 요청에 따라 "fee_value_next_to_ac_right" 키는 FIELD_MAP에서 삭제되었으므로,
        # 이 루프에서 해당 키를 만나지 않음.
        M = {} # M_raw를 정수형으로 변환 시도 (좌표, 크기 등)
        for k_map, v_map in M_raw.items():
            if k_map in ["x", "y", "size", "max_width"]: # 숫자여야 하는 속성들
                try: M[k_map] = int(v_map)
                except (ValueError, TypeError) : M[k_map] = v_map # 변환 실패 시 원본 유지
            else: M[k_map] = v_map # 나머지 속성은 그대로

        text_content_value = M.get("text_override", data_to_draw.get(key)) # 우선순위: text_override > data_to_draw[key]
        final_text_to_draw = ""

        if text_content_value is not None and str(text_content_value).strip() != "": # None이거나 공백 문자열이 아니면
            final_text_to_draw = str(text_content_value)
        
        # 그릴 내용이 있거나, special_notes_display처럼 내용이 없어도 빈칸으로 그려야 하는 경우
        if final_text_to_draw.strip() != "" or (key == "special_notes_display" and final_text_to_draw == ""):
            size_to_use = get_adjusted_font_size(M.get("size", BASE_FONT_SIZE), key) # 필드별 폰트 크기 조정
            try:
                font_obj = _get_font(font_type=M.get("font", "regular"), size=size_to_use)
            except Exception as font_load_err:
                print(f"Critical error loading font for key '{key}'. Skipping this text. Error: {font_load_err}")
                continue # 이 텍스트 그리기는 건너뜀

            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width") # 자동 줄바꿈을 위한 최대 너비
            line_spacing_factor = M.get("line_spacing_factor", 1.15) # 줄 간격 배수
            
            _draw_text_with_alignment(draw, final_text_to_draw, M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    # 이미지 바이트로 변환하여 반환
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG') # PNG로 저장
    img_byte_arr.seek(0) # 포인터 리셋
    return img_byte_arr.getvalue()

if __name__ == '__main__':
    print("image_generator.py test mode")
    # AC_COST_LABEL을 테스트용 mock_costs의 레이블과 일치시키거나,
    # mock_costs에 해당 레이블의 항목을 추가해야 테스트가 정확해짐
    # 예: AC_COST_LABEL_TEST = "에어컨 이전설치비" (실제 calculations.py와 동일하게)
    mock_state = {
        "customer_name": "김에어컨 테스트", "customer_phone": "010-3333-4444",
        "moving_date": date(2024, 9, 10),
        "from_location": "서울시 강남구 테헤란로 123",
        "to_location": "경기도 성남시 분당구 판교역로 456",
        "from_floor": "15", "to_floor": "3",
        "final_selected_vehicle": "5톤", "dispatched_5t": 1,
        "from_method": "사다리차 🪜", "to_method": "사다리차 🪜",
        "deposit_amount": 300000,
        "base_move_type": "가정 이사 🏠",
        "qty_가정 이사 🏠_주요 품목_에어컨": 2, # 에어컨 수량
        "special_notes": "에어컨 2대 이전 설치 (스탠드1, 벽걸이1)\n거실 스탠드 에어컨 배관 연장 필요할 수 있음."
    }
    mock_costs = [
        ("기본 운임", 1200000, "5톤 기준"),
        ("출발지 사다리차", 210000, "15층, 5톤 기준"),
        ("도착지 사다리차", 150000, "3층, 5톤 기준"),
        ("에어컨 이전설치비", 150000, "스탠드 1대, 벽걸이 1대 기본 설치") # AC_COST_LABEL과 일치하는 레이블
    ]
    mock_total_cost = 1200000 + 210000 + 150000 + 150000 # 1710000 (VAT, 카드수수료 등 미포함 순수 합계)
    mock_personnel = {"final_men": 3, "final_women": 1}

    try:
        image_bytes = create_quote_image(mock_state, mock_costs, mock_total_cost, mock_personnel)
        if image_bytes:
            # 파일명에 현재 날짜/시간 포함하여 중복 방지
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_quote_image_no_ac_fee_field_{timestamp}.png"
            with open(filename, "wb") as f:
                f.write(image_bytes)
            print(f"Test image '{filename}' saved successfully.")
        else:
            print("Test image generation failed.")
    except Exception as e_main:
        print(f"Error in test run: {e_main}")
        traceback.print_exc()
