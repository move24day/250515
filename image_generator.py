# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)

# --- 기준값 정의 ---
# 기본 폰트 크기 (고객명 기준)
BASE_FONT_SIZE = 18 # 요청사항: 전체 폰트를 이름 폰트(18)에 맞춰줌

# 기존 품목 관련 기준값 (일부는 BASE_FONT_SIZE에 맞춰 조정될 수 있음)
item_y_start_val = 334
item_y_spacing_val = 28.8 # 항목 간 Y 간격
item_font_size_val = 15    # 품목 수량 폰트 크기 (요청에 따라 BASE_FONT_SIZE로 변경 가능하나, 가독성 위해 유지 또는 별도 조정 고려)
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491
item_x_col3_val = 756

vehicle_x_val = 90
vehicle_y_val = int(275 + item_y_spacing_val)

costs_section_x_align_right_val = 326 # 오른쪽 정렬 기준 X (총액, 이사비용 등)

# --- 동적 좌표 계산 ---
# 이전 FIELD_MAP 값 참조 (계산에 필요한 원본 Y값들)
_y_living_room_cabinet_orig = 677
_y_sofa_3seater_orig = 549
_y_main_fee_yellow_box_orig = 775 # 이사비용(노란박스)의 기존 Y

# 1. 사다리 요금 Y 좌표
from_ladder_fee_y_val = _y_living_room_cabinet_orig + abs(_y_sofa_3seater_orig - _y_living_room_cabinet_orig) # 805
to_ladder_fee_y_val = from_ladder_fee_y_val + item_y_spacing_val # 805 + 28.8 = 833.8
regional_ladder_surcharge_y_val = to_ladder_fee_y_val + item_y_spacing_val # 833.8 + 28.8 = 862.6

# 2. 계약금 X, Y 좌표
_x_item_book_box = item_x_col2_baskets_val # 491 (책바구니 X)
_x_item_safe = item_x_col3_val            # 756 (금고 X)
deposit_x_val = int((_x_item_book_box + _x_item_safe) / 2) # (491 + 756) / 2 = 623.5 -> 624
deposit_y_val = from_ladder_fee_y_val # 출발지 사다리 비용 Y와 동일 (805)

# 3. 보관료 X, Y 좌표
storage_fee_x_val = deposit_x_val # 계약금 X와 동일 (624)
storage_fee_y_val = _y_main_fee_yellow_box_orig # 이사비용(노란박스) Y와 동일 (775)

# 4. 잔금 Y 좌표
remaining_balance_y_val = deposit_y_val + item_y_spacing_val # 계약금 Y + 한 칸 아래 (805 + 28.8 = 833.8)

# 폰트 크기 일괄 적용을 위한 함수 (선택적)
def get_adjusted_font_size(original_size, field_key):
    # 고객명은 이미 기준 크기(19)를 가지고 있었으므로, 요청 기준인 18로 맞춤
    if field_key == "customer_name":
        return BASE_FONT_SIZE # 18
    # 품목 수량은 너무 커지면 가독성이 떨어질 수 있어 기존 15 유지 또는 약간만 증가
    if field_key.startswith("item_") and field_key not in ["item_x_col1_val", "item_x_col2_baskets_val", "item_x_col2_others_val", "item_x_col3_val"]: # 좌표 변수 제외
        return item_font_size_val # 15
    # 총액, 잔금 등 강조가 필요한 금액은 조금 더 크게 유지 (예: BASE_FONT_SIZE + 2~4)
    if field_key in ["grand_total", "remaining_balance"]:
        return BASE_FONT_SIZE + 2 # 20 (기존 잔금 21, 총액 22였으므로 조정)
    # 일반 정보 텍스트는 BASE_FONT_SIZE로 통일
    # 그 외 작은 설명 문구 등은 원래 크기 유지 또는 BASE_FONT_SIZE보다 작게 설정 가능
    if field_key in ["fee_value_next_to_ac_right"]: # 에어컨 옆 작은 금액
        return 14 # 기존 크기 유지
    return BASE_FONT_SIZE # 기본적으로 18

FIELD_MAP = {
    # 고객 정보 (폰트 크기 BASE_FONT_SIZE 또는 약간 크게)
    "customer_name":  {"x": 175, "y": 130, "size": get_adjusted_font_size(19, "customer_name"), "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"}, # size: 19->18
    "customer_phone": {"x": 412, "y": 130, "size": get_adjusted_font_size(16, "customer_phone"), "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"}, # size: 16->18
    "quote_date":     {"x": 640, "y": 130, "size": get_adjusted_font_size(16, "quote_date"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},# size: 16->18
    "moving_date":    {"x": 640, "y": 161, "size": get_adjusted_font_size(16, "moving_date"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},# size: 16->18
    "move_time_am_checkbox":   {"x": 708, "y": 188, "size": get_adjusted_font_size(15, "move_time_am_checkbox"), "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V", "text_if_false": "□"},# size: 15->18
    "move_time_pm_checkbox":   {"x": 803, "y": 188, "size": get_adjusted_font_size(15, "move_time_pm_checkbox"), "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V", "text_if_false": "□"},# size: 15->18
    "from_location":  {"x": 175, "y": 161, "size": get_adjusted_font_size(16, "from_location"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},# size: 16->18
    "to_location":    {"x": 175, "y": 192, "size": get_adjusted_font_size(16, "to_location"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},# size: 16->18
    "from_floor":     {"x": 180, "y": 226, "size": get_adjusted_font_size(16, "from_floor"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},# size: 16->18
    "to_floor":       {"x": 180, "y": 258, "size": get_adjusted_font_size(16, "to_floor"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},# size: 16->18
    "vehicle_type":   {"x": vehicle_x_val, "y": vehicle_y_val, "size": get_adjusted_font_size(16, "vehicle_type"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": (item_x_col1_val - vehicle_x_val - 10)},# size: 16->18
    "workers_male":   {"x": 758, "y": 228, "size": get_adjusted_font_size(16, "workers_male"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},# size: 16->18
    "workers_female": {"x": 758, "y": 258, "size": get_adjusted_font_size(16, "workers_female"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},# size: 16->18

    # 품목 수량 (item_font_size_val 사용 = 15 유지)
    "item_jangrong":    {"x": item_x_col1_val, "y": 334, "size": get_adjusted_font_size(item_font_size_val, "item_jangrong"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_double_bed":  {"x": item_x_col1_val, "y": 363, "size": get_adjusted_font_size(item_font_size_val, "item_double_bed"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": item_x_col1_val, "y": 392, "size": get_adjusted_font_size(item_font_size_val, "item_drawer_5dan"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_3dan": {"x": item_x_col1_val, "y": 421, "size": get_adjusted_font_size(item_font_size_val, "item_drawer_3dan"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": item_x_col1_val, "y": 455, "size": get_adjusted_font_size(item_font_size_val, "item_fridge_4door"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_normal": {"x": item_x_col1_val, "y": 488, "size": get_adjusted_font_size(item_font_size_val, "item_kimchi_fridge_normal"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": item_x_col1_val, "y": 518, "size": get_adjusted_font_size(item_font_size_val, "item_kimchi_fridge_stand"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": item_x_col1_val, "y": _y_sofa_3seater_orig, "size": get_adjusted_font_size(item_font_size_val, "item_sofa_3seater"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_1seater":{"x": item_x_col1_val, "y": 581, "size": get_adjusted_font_size(item_font_size_val, "item_sofa_1seater"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_dining_table":{"x": item_x_col1_val, "y": 612, "size": get_adjusted_font_size(item_font_size_val, "item_dining_table"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": item_x_col1_val, "y": 645, "size": get_adjusted_font_size(item_font_size_val, "item_ac_left"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": item_x_col1_val, "y": _y_living_room_cabinet_orig, "size": get_adjusted_font_size(item_font_size_val, "item_living_room_cabinet"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_digital": {"x": item_x_col1_val, "y": 708, "size": get_adjusted_font_size(item_font_size_val, "item_piano_digital"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_washing_machine": {"x": item_x_col1_val, "y": 740, "size": get_adjusted_font_size(item_font_size_val, "item_washing_machine"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_computer":    {"x": item_x_col2_others_val, "y": 334, "size": get_adjusted_font_size(item_font_size_val, "item_computer"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_executive_desk": {"x": item_x_col2_others_val, "y": 363, "size": get_adjusted_font_size(item_font_size_val, "item_executive_desk"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": item_x_col2_others_val, "y": 392, "size": get_adjusted_font_size(item_font_size_val, "item_desk"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_bookshelf":   {"x": item_x_col2_others_val, "y": 421, "size": get_adjusted_font_size(item_font_size_val, "item_bookshelf"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": item_x_col2_others_val, "y": 450, "size": get_adjusted_font_size(item_font_size_val, "item_chair"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": item_x_col2_others_val, "y": 479, "size": get_adjusted_font_size(item_font_size_val, "item_table"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": item_x_col2_others_val, "y": 507, "size": get_adjusted_font_size(item_font_size_val, "item_blanket"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_basket":      {"x": item_x_col2_baskets_val, "y": 549, "size": get_adjusted_font_size(item_font_size_val, "item_basket"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_medium_box":  {"x": item_x_col2_baskets_val, "y": 581, "size": get_adjusted_font_size(item_font_size_val, "item_medium_box"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_large_box":   {"x": item_x_col2_baskets_val, "y": 594, "size": get_adjusted_font_size(item_font_size_val, "item_large_box"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_book_box":    {"x": _x_item_book_box, "y": 623, "size": get_adjusted_font_size(item_font_size_val, "item_book_box"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_plant_box":   {"x": item_x_col2_others_val, "y": 651, "size": get_adjusted_font_size(item_font_size_val, "item_plant_box"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": item_x_col2_others_val, "y": 680, "size": get_adjusted_font_size(item_font_size_val, "item_clothes_box"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": item_x_col2_others_val, "y": 709, "size": get_adjusted_font_size(item_font_size_val, "item_duvet_box"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_styler":      {"x": item_x_col3_val, "y": 334, "size": get_adjusted_font_size(item_font_size_val, "item_styler"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": item_x_col3_val, "y": 363, "size": get_adjusted_font_size(item_font_size_val, "item_massage_chair"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": item_x_col3_val, "y": 392, "size": get_adjusted_font_size(item_font_size_val, "item_piano_acoustic"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": item_x_col3_val, "y": 421, "size": get_adjusted_font_size(item_font_size_val, "item_copier"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": item_x_col3_val, "y": 450, "size": get_adjusted_font_size(item_font_size_val, "item_tv_45"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": item_x_col3_val, "y": 479, "size": get_adjusted_font_size(item_font_size_val, "item_tv_stand"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": item_x_col3_val, "y": 507, "size": get_adjusted_font_size(item_font_size_val, "item_wall_mount_item"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": _x_item_safe, "y": 590, "size": get_adjusted_font_size(item_font_size_val, "item_safe"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_angle_shelf": {"x": item_x_col3_val, "y": 620, "size": get_adjusted_font_size(item_font_size_val, "item_angle_shelf"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": item_x_col3_val, "y": 653, "size": get_adjusted_font_size(item_font_size_val, "item_partition"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": item_x_col3_val, "y": 684, "size": get_adjusted_font_size(item_font_size_val, "item_5ton_access"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": item_x_col3_val, "y": 710, "size": get_adjusted_font_size(item_font_size_val, "item_ac_right"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    # 비용 관련 항목들 (폰트 크기 조정됨)
    "fee_value_next_to_ac_right": {"x": costs_section_x_align_right_val, "y": 680, "size": get_adjusted_font_size(14, "fee_value_next_to_ac_right"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"}, # 14 유지
    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": _y_main_fee_yellow_box_orig, "size": get_adjusted_font_size(17, "main_fee_yellow_box"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # 17 -> 18
    "grand_total":      {"x": costs_section_x_align_right_val, "y": 861, "size": get_adjusted_font_size(22, "grand_total"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # 22 -> 20 (BASE+2)

    # 사다리 요금 (폰트 크기 BASE_FONT_SIZE = 18)
    "from_ladder_fee":  {"x": costs_section_x_align_right_val, "y": int(from_ladder_fee_y_val), "size": BASE_FONT_SIZE, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right", "prefix": "출발지 사다리 요금: "},
    "to_ladder_fee":    {"x": costs_section_x_align_right_val, "y": int(to_ladder_fee_y_val),   "size": BASE_FONT_SIZE, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right", "prefix": "도착지 사다리 요금: "},
    "regional_ladder_surcharge_display": {"x": costs_section_x_align_right_val, "y": int(regional_ladder_surcharge_y_val), "size": BASE_FONT_SIZE, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right", "prefix": "지방 사다리 추가: "},

    # 계약금, 보관료, 잔금 위치 및 스타일 변경 (폰트 크기 BASE_FONT_SIZE 또는 BASE_FONT_SIZE + alpha)
    "deposit_amount":   {"x": deposit_x_val, "y": int(deposit_y_val), "size": BASE_FONT_SIZE, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "center", "prefix": "계약금: "}, # X, Y 변경, align: center
    "storage_fee":      {"x": storage_fee_x_val, "y": int(storage_fee_y_val), "size": BASE_FONT_SIZE, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "center", "prefix": "보관료: "},   # X, Y 변경, align: center
    "remaining_balance":{"x": deposit_x_val, "y": int(remaining_balance_y_val), "size": get_adjusted_font_size(20, "remaining_balance"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "center", "prefix": "잔금: "}, # X, Y 변경, align: center
}

# ITEM_KEY_MAP은 이전 답변의 수정된 내용과 동일하게 유지
ITEM_KEY_MAP = {
    "장롱": "item_jangrong", "더블침대": "item_double_bed",
    "서랍장": "item_drawer_5dan",
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door",
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand",
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater",
    "식탁(4인)": "item_dining_table",
    "에어컨": "item_ac_left",
    "거실장": "item_living_room_cabinet",
    "피아노(디지털)": "item_piano_digital",
    "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer",
    "중역책상": "item_executive_desk", "책상&의자": "item_desk", "책장": "item_bookshelf",
    "의자": "item_chair", "테이블": "item_table", "담요": "item_blanket",
    "바구니": "item_basket", "중박스": "item_medium_box",
    "중대박스": "item_large_box",
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box",
    "스타일러": "item_styler", "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic", "복합기": "item_copier", "TV(45인치)": "item_tv_45",
    "TV다이": "item_tv_stand", "벽걸이": "item_wall_mount_item", "금고": "item_safe",
    "앵글": "item_angle_shelf", "파티션": "item_partition", "5톤진입": "item_5ton_access",
}


# ... (get_text_dimensions, _get_font, _draw_text_with_alignment, _format_currency 함수는 이전과 동일) ...
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

    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError:
        try: return ImageFont.load_default(size=size)
        except TypeError: return ImageFont.load_default()
        except Exception as e_pil_font:
            print(f"Error loading default PIL font: {e_pil_font}")
            raise
    except Exception as e_font:
        print(f"Error loading font {font_path_to_use}: {e_font}")
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
            current_line_plus_word_width, _ = get_text_dimensions(current_line + word + " ", font) if current_line else get_text_dimensions(word + " ", font)

            if word_width > max_width and len(word) > 1:
                if current_line:
                    lines.append(current_line.strip())
                temp_word_line = ""
                for char_idx, char in enumerate(word):
                    temp_word_line_plus_char_width, _ = get_text_dimensions(temp_word_line + char, font)
                    if temp_word_line_plus_char_width <= max_width:
                        temp_word_line += char
                    else:
                        lines.append(temp_word_line)
                        temp_word_line = char
                if temp_word_line:
                    lines.append(temp_word_line)
                current_line = ""
                continue

            if current_line_plus_word_width <= max_width:
                current_line += word + " "
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "
        
        if current_line.strip():
            lines.append(current_line.strip())
        
        if not lines and text:
            lines.append(text)
            
    else:
        lines.extend(text.split('\n'))

    current_y = y
    first_line = True
    _, typical_char_height = get_text_dimensions("A", font)

    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1:
            current_y += int(typical_char_height * line_spacing_factor)
            continue
        
        text_width, _ = get_text_dimensions(line, font)
        actual_x = x
        if align == "right":
            actual_x = x - text_width
        elif align == "center":
            actual_x = x - text_width / 2
        
        draw.text((actual_x, current_y), line, font=font, fill=color, anchor="lt")
        current_y += int(typical_char_height * line_spacing_factor)
        first_line = False
    return current_y

def _format_currency(amount_val):
    if amount_val is None: return "" # 금액이 없을 경우 빈 문자열 반환
    try:
        num_val = float(str(amount_val).replace(",", "").strip())
        if num_val == 0: return "" # 0원일 경우에도 빈 문자열 반환 (선택적)
        
        num = int(num_val)
        return f"{num:,}"
    except ValueError:
        return str(amount_val) # 숫자 변환 실패 시 원본 문자열 (또는 "" 처리)


# create_quote_image 함수는 이전 답변의 수정된 내용과 거의 동일하게 유지됩니다.
# data_to_draw 딕셔너리에 새로운 키들(deposit_amount, storage_fee, remaining_balance)에 대한 값을
# calculated_cost_items나 state_data에서 적절히 가져와 할당하는 로직이 필요합니다.
# (이전 코드에서 deposit_amount, storage_fee, remaining_balance는 이미 data_to_draw에 포함되어 있었으므로, 해당 부분은 유지됩니다)
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
    if not os.path.exists(FONT_PATH_BOLD): print(f"Warning: Bold font missing at {FONT_PATH_BOLD} (regular will be used)")

    customer_name = state_data.get('customer_name', '')
    customer_phone = state_data.get('customer_phone', '')
    moving_date_obj = state_data.get('moving_date')
    moving_date_str = moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj)
    quote_date_str = date.today().strftime('%Y-%m-%d')
    from_location = state_data.get('from_location', '')
    to_location = state_data.get('to_location', '')
    from_floor = str(state_data.get('from_floor', ''))
    to_floor = str(state_data.get('to_floor', ''))
    vehicle_type = state_data.get('final_selected_vehicle', '')
    workers_male = str(personnel_info.get('final_men', '0'))
    workers_female = str(personnel_info.get('final_women', '0'))

    total_moving_expenses_f22 = 0
    storage_fee_val_from_calc = 0 # calculated_cost_items 에서 가져올 보관료
    option_ac_cost_val = 0
    from_ladder_fee_val = 0
    to_ladder_fee_val = 0
    regional_ladder_surcharge_val = 0

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, _ in calculated_cost_items:
            label = str(item_l)
            try: amount = int(float(item_a or 0))
            except (ValueError, TypeError): amount = 0

            if label == '기본 운임' or label == '날짜 할증' or label == '장거리 운송료' or \
               label == '폐기물 처리' or label == '폐기물 처리(톤)' or \
               label == '추가 인력' or label == '경유지 추가요금' or "조정 금액" in label:
                total_moving_expenses_f22 += amount
            elif label == '보관료':
                storage_fee_val_from_calc = amount # 보관료 값 저장
            elif label == '에어컨 설치 및 이전 비용':
                option_ac_cost_val = amount
            elif label == '출발지 사다리차' or label == '출발지 스카이 장비':
                from_ladder_fee_val += amount
            elif label == '도착지 사다리차' or label == '도착지 스카이 장비':
                to_ladder_fee_val += amount
            elif label == '지방 사다리 추가요금':
                regional_ladder_surcharge_val += amount

    deposit_amount_val = int(float(state_data.get('deposit_amount', 0) or 0)) # state_data에서 직접 가져옴
    grand_total_num = int(float(total_cost_overall or 0))
    remaining_balance_num = grand_total_num - deposit_amount_val

    data_to_draw = {
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "quote_date": quote_date_str,
        "moving_date": moving_date_str,
        "from_location": from_location,
        "to_location": to_location,
        "from_floor": from_floor,
        "to_floor": to_floor,
        "vehicle_type": vehicle_type,
        "workers_male": workers_male,
        "workers_female": workers_female,
        "fee_value_next_to_ac_right": _format_currency(option_ac_cost_val),
        "main_fee_yellow_box": _format_currency(total_moving_expenses_f22),
        "grand_total": _format_currency(grand_total_num),
        "from_ladder_fee": _format_currency(from_ladder_fee_val),
        "to_ladder_fee": _format_currency(to_ladder_fee_val),
        "regional_ladder_surcharge_display": _format_currency(regional_ladder_surcharge_val),
        "deposit_amount": _format_currency(deposit_amount_val), # state_data에서 가져온 계약금
        "storage_fee": _format_currency(storage_fee_val_from_calc), # calculated_items에서 가져온 보관료
        "remaining_balance": _format_currency(remaining_balance_num),
    }

    move_time_option_from_state = state_data.get('move_time_option_key_in_state', state_data.get('move_time_option'))
    if move_time_option_from_state == '오전':
         data_to_draw["move_time_am_checkbox"] = FIELD_MAP["move_time_am_checkbox"].get("text_if_true", "V")
         data_to_draw["move_time_pm_checkbox"] = FIELD_MAP["move_time_pm_checkbox"].get("text_if_false", "□")
    elif move_time_option_from_state == '오후':
         data_to_draw["move_time_am_checkbox"] = FIELD_MAP["move_time_am_checkbox"].get("text_if_false", "□")
         data_to_draw["move_time_pm_checkbox"] = FIELD_MAP["move_time_pm_checkbox"].get("text_if_true", "V")
    else:
         data_to_draw["move_time_am_checkbox"] = FIELD_MAP["move_time_am_checkbox"].get("text_if_false", "□")
         data_to_draw["move_time_pm_checkbox"] = FIELD_MAP["move_time_pm_checkbox"].get("text_if_false", "□")

    try:
        import data as app_data
        current_move_type = state_data.get("base_move_type")
        item_defs_for_current_type = {}
        if hasattr(app_data, 'item_definitions') and current_move_type in app_data.item_definitions:
            item_defs_for_current_type = app_data.item_definitions[current_move_type]

        for key_in_fieldmap_vals in ITEM_KEY_MAP.values():
            if key_in_fieldmap_vals.startswith("item_") and key_in_fieldmap_vals not in data_to_draw :
                 data_to_draw[key_in_fieldmap_vals] = ""

        for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
            found_section = None
            if isinstance(item_defs_for_current_type, dict):
                for section_name, item_list_in_section in item_defs_for_current_type.items():
                    if isinstance(item_list_in_section, list) and data_py_item_name in item_list_in_section:
                        found_section = section_name
                        break
            if found_section:
                widget_key = f"qty_{current_move_type}_{found_section}_{data_py_item_name}"
                qty_raw = state_data.get(widget_key, 0)
                qty_int = 0
                try:
                    if qty_raw is not None and str(qty_raw).strip() != "":
                        qty_int = int(float(str(qty_raw)))
                except ValueError:
                    qty_int = 0

                if qty_int > 0:
                    text_val = str(qty_int)
                    if data_py_item_name == "장롱":
                        try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                        except: text_val = str(qty_int)
                    data_to_draw[field_map_key_from_map] = text_val
    except ImportError:
        print("Error: data.py module could not be imported in create_quote_image.")
    except Exception as e_item:
        print(f"Error processing item quantities for image: {e_item}")
        traceback.print_exc()

    for key, M_raw in FIELD_MAP.items():
        M = {}
        for k_map, v_map in M_raw.items():
            if k_map in ["x", "y", "size", "max_width"]:
                try: M[k_map] = int(v_map)
                except (ValueError, TypeError) : M[k_map] = v_map
            else: M[k_map] = v_map

        text_content_value = data_to_draw.get(key)
        final_text_to_draw = ""

        if key.endswith("_checkbox"):
            final_text_to_draw = data_to_draw.get(key, M.get("text_if_false", "□"))
        elif text_content_value is not None and str(text_content_value).strip() != "":
            prefix_text = M.get("prefix", "")
            final_text_to_draw = f"{prefix_text}{text_content_value}"
        
        if final_text_to_draw.strip() != "":
            # size_to_use = M.get("size", BASE_FONT_SIZE) # 모든 폰트 크기를 BASE_FONT_SIZE로 통일하려면
            size_to_use = get_adjusted_font_size(M.get("size", BASE_FONT_SIZE), key) # get_adjusted_font_size 함수 사용
            font_obj = _get_font(font_type=M.get("font", "regular"), size=size_to_use)
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
    if not (os.path.exists(FONT_PATH_REGULAR) and os.path.exists(BACKGROUND_IMAGE_PATH)):
         print(f"Ensure {FONT_PATH_REGULAR} and {BACKGROUND_IMAGE_PATH} (and optionally {FONT_PATH_BOLD}) exist for test.")
    else:
        sample_state_data = {
            'customer_name': '김테스트 고객님', 'customer_phone': '010-1234-5678',
            'moving_date': date(2025, 6, 15),
            'from_location': '서울시 강남구 테헤란로 123, 출발아파트 101동 701호 (출발동)',
            'to_location': '경기도 성남시 분당구 판교역로 456, 도착빌라 202동 1001호 (도착동)',
            'from_floor': '7', 'to_floor': '10',
            'final_selected_vehicle': '5톤',
            'deposit_amount': 100000, # 계약금
            'base_move_type': "가정 이사 🏠",
            'qty_가정 이사 🏠_주요 품목_장롱': 9,
            'qty_가정 이사 🏠_주요 품목_더블침대': 1,
            'qty_가정 이사 🏠_주요 품목_서랍장': 2,
            'qty_가정 이사 🏠_기타_서랍장(3단)': 1,
            'qty_가정 이사 🏠_주요 품목_4도어 냉장고': 1,
            'qty_가정 이사 🏠_주요 품목_거실장': 1,
            'qty_가정 이사 🏠_기타_컴퓨터&모니터': 2,
            'qty_가정 이사 🏠_주요 품목_소파(3인용)': 1,
            'qty_가정 이사 🏠_기타_소파(1인용)': 0,
            'qty_가정 이사 🏠_주요 품목_에어컨': 1,
            'qty_가정 이사 🏠_기타_피아노(디지털)': 1,
            'qty_가정 이사 🏠_포장 자재 📦_바구니': 20,
            'qty_가정 이사 🏠_포장 자재 📦_중박스': 10,
            'qty_가정 이사 🏠_포장 자재 📦_책바구니': 5,
            'move_time_option_key_in_state': '오전',
        }
        sample_personnel_info = {'final_men': 3, 'final_women': 1}
        sample_calculated_cost_items = [
            ('기본 운임', 1200000, '5톤 기준'),
            ('출발지 사다리차', 170000, '8~9층, 5톤 기준'),
            ('도착지 사다리차', 180000, '10~11층, 5톤 기준'),
            ('지방 사다리 추가요금', 50000, '수동입력'),
            ('에어컨 설치 및 이전 비용', 150000, '기본 설치'),
            ('보관료', 70000, '컨테이너 10일'), # 샘플 보관료 추가
            ('조정 금액', -70000, '프로모션 할인')
        ]
        sample_total_cost_overall = sum(item[1] for item in sample_calculated_cost_items)

        try:
            img_data = create_quote_image(sample_state_data, sample_calculated_cost_items, sample_total_cost_overall, sample_personnel_info)
            if img_data:
                output_filename = "수정된_견적서_이미지_최종_폰트조정.png"
                with open(output_filename, "wb") as f:
                    f.write(img_data)
                print(f"Test image '{output_filename}' created successfully. Please check.")
                if os.name == 'nt':
                    try: os.startfile(output_filename)
                    except: print("Could not auto-open image.")
            else:
                print("Test image creation failed.")
        except Exception as e_test:
            print(f"Error during test: {e_test}")
            traceback.print_exc()
