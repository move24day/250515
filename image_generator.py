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
from_work_fee_y_val = 805  # 예: 이전 값 또는 원하는 값
to_work_fee_y_val = 833    # 예: from_work_fee_y_val + item_y_spacing_val

grand_total_y_new = _y_grand_total_orig + 4 # 865

deposit_y_val = 789        # 예: 이전 값 또는 원하는 값
remaining_balance_y_val = 826 # 예: 이전 값 또는 원하는 값

storage_fee_y_val = _y_main_fee_yellow_box_orig # 보관료는 메인 비용과 같은 Y

# 특이사항 Y
special_notes_start_y_val = int(grand_total_y_new + item_y_spacing_val * 1.5) # 약 908

# X 좌표 관련
vehicle_number_x_val = 90
actual_vehicles_text_x_val = item_x_col2_others_val
costs_section_x_align_right_val = 410
work_method_fee_label_x_val = 35
work_method_text_display_x_val = int((item_x_col1_val + item_x_col2_baskets_val) / 2)
fees_x_val_right_aligned = item_x_col3_val
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
    "에어컨": "item_ac_left",
    "거실장": "item_living_room_cabinet",
    "피아노(디지털)": "item_piano_digital",
    "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer",
    "사무실책상": "item_executive_desk",
    "책상&의자": "item_desk",
    "책장": "item_bookshelf",
    # "의자": "item_chair", # 양식에 따라 추가/제외
    # "테이블": "item_table", # 양식에 따라 추가/제외
    # "담요": "item_blanket", # 양식에 따라 추가/제외
    "바구니": "item_basket",
    "중박스": "item_medium_box", # data.py의 품목명과 일치하는지 확인 ("중자바구니"일 수도 있음)
    # "중대박스": "item_large_box", # data.py에 해당 품목이 정의되어 있고, FIELD_MAP에도 위치가 정의되어야 함
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box", # FIELD_MAP 키와 일치
    "스타일러": "item_styler",
    "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic",
    # "복합기": "item_copier", # data.py 및 FIELD_MAP에 정의 필요
    "TV(45인치)": "item_tv_45",
    "TV(75인치)": "item_tv_stand", # FIELD_MAP 키와 일치 (TV 스탠드가 아닌 TV 자체를 의미할 경우 주의)
    # "벽걸이": "item_wall_mount_item", # data.py 및 FIELD_MAP에 정의 필요
    "금고": "item_safe",
    "앵글": "item_angle_shelf",
    # "파티션": "item_partition", # data.py 및 FIELD_MAP에 정의 필요
    # "5톤진입": "item_5ton_access", # 품목인지, 조건인지 확인. FIELD_MAP에 정의 필요
    # "이불박스": "item_duvet_box" # data.py 및 FIELD_MAP에 정의 필요
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
    print("DEBUG [ImageGenerator]: create_quote_image function CALLED") # 함수 호출 확인
    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
        print("DEBUG [ImageGenerator]: Background image loaded.")
    except FileNotFoundError:
        print(f"ERROR [ImageGenerator]: Background image not found at {BACKGROUND_IMAGE_PATH}")
        # ... (에러 처리) ...
        return None
    except Exception as e_bg:
        print(f"ERROR [ImageGenerator]: Error loading background image: {e_bg}")
        return None

    if not os.path.exists(FONT_PATH_REGULAR): print(f"WARNING [ImageGenerator]: Regular font missing at {FONT_PATH_REGULAR}")
    if not os.path.exists(FONT_PATH_BOLD): print(f"WARNING [ImageGenerator]: Bold font missing at {FONT_PATH_BOLD}")

    # --- 데이터 추출 ---
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
    
    # --- 비용 항목 계산 ---
    total_moving_expenses_val = 0 
    storage_fee_val = 0
    option_ac_cost_val = 0 # 에어컨 비용은 계산하지만, FIELD_MAP에서 그리는 부분이 없으므로 표시 안됨
    from_method_fee_val = 0
    to_method_fee_raw_val = 0
    regional_ladder_surcharge_val = 0

    AC_COST_LABEL = "에어컨 이전설치비" # calculations.py의 레이블과 일치해야 함

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
    grand_total_num = int(float(total_cost_overall or 0)) # 함수 인자로 받은 전체 비용 사용
    remaining_balance_num = grand_total_num - deposit_amount_val
    
    special_notes_content = state_data.get('special_notes', '')

    # --- 그릴 데이터 준비 ---
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

    # 품목 수량 채우기
    print("DEBUG [ImageGenerator]: Populating item quantities...")
    try:
        current_move_type = state_data.get("base_move_type")
        # 모든 FIELD_MAP의 품목 키에 대해 빈 문자열로 초기화 (수량 없으면 안 그려지도록)
        for field_map_key in FIELD_MAP.keys(): # FIELD_MAP의 모든 키 순회
            if field_map_key.startswith("item_"): # 품목 관련 키라면
                data_to_draw[field_map_key] = "" # 기본적으로 빈 문자열 할당

        if utils and hasattr(utils, 'get_item_qty') and callable(utils.get_item_qty):
            for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
                # ITEM_KEY_MAP에 있는 키가 FIELD_MAP에도 정의되어 있는지 확인
                if field_map_key_from_map in FIELD_MAP and field_map_key_from_map.startswith("item_"):
                    qty_int = utils.get_item_qty(state_data, data_py_item_name)
                    # print(f"DEBUG [ImageGenerator]: Item: {data_py_item_name}, Mapped Key: {field_map_key_from_map}, Qty: {qty_int}") # 수량 확인 로그
                    if qty_int > 0:
                        text_val = str(qty_int)
                        if data_py_item_name == "장롱":
                            try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                            except: text_val = str(qty_int)
                        data_to_draw[field_map_key_from_map] = text_val
                        # print(f"DEBUG [ImageGenerator]: Added to data_to_draw: {field_map_key_from_map} = {text_val}")
        else:
            print("ERROR [ImageGenerator]: utils.get_item_qty function is not available. Cannot populate item quantities.")
    except Exception as e_item_qty:
        print(f"ERROR [ImageGenerator]: Error processing item quantities: {e_item_qty}")
        traceback.print_exc()
    print(f"DEBUG [ImageGenerator]: data_to_draw (items part sample): { {k:v for k,v in data_to_draw.items() if k.startswith('item_') and v} }")


    # --- 텍스트 그리기 ---
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
        
        if final_text_to_draw.strip() != "" or (key == "special_notes_display" and final_text_to_draw == ""): # 빈 특이사항도 그릴 수 있도록
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
            
            # print(f"DEBUG [ImageGenerator]: Drawing: Key='{key}', Text='{final_text_to_draw[:30]}...', X={M['x']}, Y={M['y']}") # 그리기 직전 로그
            _draw_text_with_alignment(draw, final_text_to_draw, M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    print("DEBUG [ImageGenerator]: Text drawing complete. Saving image to bytes.")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    print("DEBUG [ImageGenerator]: Image generation successful.")
    return img_byte_arr.getvalue()

# 테스트용 if __name__ == '__main__': 블록
if __name__ == '__main__':
    print("image_generator.py test mode")
    # (이전과 동일한 테스트 코드 유지 또는 필요에 따라 수정)
    AC_COST_LABEL_TEST = "에어컨 이전설치비" 

    mock_state_test_pos = {
        "customer_name": "위치조정 고객님", "customer_phone": "010-9999-0000",
        "moving_date": date(2025, 12, 25),
        "from_location": "경기도 수원시 영통구 이의동 광교", "to_location": "서울시 서초구 반포동 아크로리버파크",
        "from_floor": "5", "to_floor": "10",
        "final_selected_vehicle": "5톤", "dispatched_5t": 1, 
        "from_method": "사다리차 🪜", "to_method": "계단 🚶",
        "deposit_amount": 200000,
        "base_move_type": "가정 이사 🏠", # 이사 유형
        "special_notes": "계약금, 잔금, 사다리 요금 위치 확인용 테스트입니다.\n두 번째 줄 테스트입니다.",
        # utils.get_item_qty가 읽을 수 있도록 세션 상태 키 형식으로 품목 수량 설정
        "qty_가정 이사 🏠_주요 품목_장롱": 3, # 장롱 3칸 -> 이미지에 1.0으로 표시되어야 함
        "qty_가정 이사 🏠_주요 품목_더블침대": 1,
        "qty_가정 이사 🏠_기타_에어컨": 1, # 에어컨 수량 (이 값은 이미지에 직접 표시되지는 않음, 비용계산에만 사용)
        "qty_가정 이사 🏠_포장 자재 📦_바구니": 10,
    }
    mock_costs_test_pos = [
        ("기본 운임", 1200000, "5톤 기준"),
        ("출발지 사다리차", 150000, "5층, 5톤 기준"),
        (AC_COST_LABEL_TEST, 100000, "에어컨 1대 기본 설치"), # 에어컨 비용은 있지만, FIELD_MAP에서 해당 항목을 지웠으므로 그려지지 않음
    ]
    mock_total_cost_test_pos = 1200000 + 150000 + 100000 # 총계에는 에어컨 비용 포함
    mock_personnel_test_pos = {"final_men": 3, "final_women": 1}

    # utils.py의 get_item_qty를 모킹할 필요 없이, mock_state_test_pos에 올바른 키로 값을 넣어주면 됨
    # (단, utils.py가 정상적으로 임포트되고 data.py를 참조할 수 있어야 함)

    try:
        image_bytes_test = create_quote_image(mock_state_test_pos, mock_costs_test_pos, mock_total_cost_test_pos, mock_personnel_test_pos)
        
        if image_bytes_test:
            timestamp_test = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename_test = f"test_image_final_{timestamp_test}.png"
            with open(filename_test, "wb") as f:
                f.write(image_bytes_test)
            print(f"Test image '{filename_test}' saved successfully. Please check all elements.")
        else:
            print("Test image generation failed. Check logs above.")
    except Exception as e_main_test:
        print(f"Error in test run: {e_main_test}")
        traceback.print_exc()
