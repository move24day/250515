# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math
import traceback
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)

BASE_FONT_SIZE = 18
item_y_start_val = 334
item_y_spacing_val = 28.8 # 항목 간 표준 Y 간격
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
# 작업 비용 레이블 X 좌표 (하단 출발/도착 작업 방법 레이블)
work_method_fee_label_x_val = 35 # 최대한 왼쪽 (조정 필요)

_y_from_floor_orig = 226
_y_to_floor_orig = 258
work_method_text_display_x_val = int((item_x_col1_val + item_x_col2_baskets_val) / 2)

_y_living_room_cabinet_orig = 677
_y_sofa_3seater_orig = 549
_y_main_fee_yellow_box_orig = 775
_y_grand_total_orig = 861

from_work_fee_y_val = _y_living_room_cabinet_orig + abs(_y_sofa_3seater_orig - _y_living_room_cabinet_orig) # 805
to_work_fee_y_val = from_work_fee_y_val + item_y_spacing_val # 833.8

fees_x_val_right_aligned = item_x_col3_val # 스타일러 X (756)

deposit_y_val = from_work_fee_y_val # 805
storage_fee_y_val = _y_main_fee_yellow_box_orig # 775
remaining_balance_y_val = deposit_y_val + item_y_spacing_val # 833.8

grand_total_y_new = _y_grand_total_orig + 4

def get_adjusted_font_size(original_size_ignored, field_key):
    if field_key == "customer_name": return BASE_FONT_SIZE
    if field_key == "customer_phone": return BASE_FONT_SIZE - 2
    if field_key.startswith("item_") and field_key not in ["item_x_col1_val", "item_x_col2_baskets_val", "item_x_col2_others_val", "item_x_col3_val"]:
        return item_font_size_val
    if field_key in ["grand_total", "remaining_balance_display"]: return BASE_FONT_SIZE + 2
    if field_key in ["fee_value_next_to_ac_right"]: return 14
    if field_key in ["from_work_method_text_display", "to_work_method_text_display"]: return BASE_FONT_SIZE - 2
    if field_key in ["from_method_label", "to_method_label",
                     "from_method_fee_value", "to_method_fee_value",
                     "deposit_amount_display", "storage_fee_display"]:
        return BASE_FONT_SIZE
    if field_key in ["vehicle_type_numbers_only", "actual_dispatched_vehicles_display"]: return BASE_FONT_SIZE -2
    return BASE_FONT_SIZE

FIELD_MAP = {
    "customer_name":  {"x": 175, "y": 130, "size": get_adjusted_font_size(0, "customer_name"), "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "customer_phone": {"x": 412, "y": 130, "size": get_adjusted_font_size(0, "customer_phone"), "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "quote_date":     {"x": 640, "y": 130, "size": get_adjusted_font_size(0, "quote_date"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
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

    # 품목 정보 (Col 1)
    "item_jangrong":    {"x": item_x_col1_val, "y": item_y_start_val, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_double_bed":  {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_3dan": {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 4.2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 약간의 Y 조정 반영 가능
    "item_kimchi_fridge_normal": {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 5.3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": item_x_col1_val, "y": int(item_y_start_val + item_y_spacing_val * 6.4), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": item_x_col1_val, "y": _y_sofa_3seater_orig, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 549
    "item_sofa_1seater":{"x": item_x_col1_val, "y": int(_y_sofa_3seater_orig + item_y_spacing_val * 1.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 581
    "item_dining_table":{"x": item_x_col1_val, "y": int(_y_sofa_3seater_orig + item_y_spacing_val * 2.2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 612
    "item_ac_left":     {"x": item_x_col1_val, "y": int(_y_sofa_3seater_orig + item_y_spacing_val * 3.3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 645
    "item_living_room_cabinet": {"x": item_x_col1_val, "y": _y_living_room_cabinet_orig, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 677
    "item_piano_digital": {"x": item_x_col1_val, "y": int(_y_living_room_cabinet_orig + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 708
    "item_washing_machine": {"x": item_x_col1_val, "y": int(_y_living_room_cabinet_orig + item_y_spacing_val * 2.2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 740

    # 품목 정보 (Col 2)
    "item_computer":    {"x": item_x_col2_others_val, "y": item_y_start_val, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_executive_desk": {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_bookshelf":   {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 4), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 5), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": item_x_col2_others_val, "y": int(item_y_start_val + item_y_spacing_val * 6), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_basket":      {"x": item_x_col2_baskets_val, "y": 549, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_medium_box":  {"x": item_x_col2_baskets_val, "y": 581, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_large_box":   {"x": item_x_col2_baskets_val, "y": int(581 + item_y_spacing_val * 0.45), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 594 (Y 조정됨)
    "item_book_box":    {"x": item_x_col2_baskets_val, "y": int(581 + item_y_spacing_val * 1.45), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 623 (Y 조정됨)

    # <<<--- 요청에 따라 Y 좌표 수정된 품목들 시작 --->>>
    "item_plant_box":   {"x": item_x_col2_others_val, "y": 680, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 기존 Y:651 -> 680
    "item_clothes_box": {"x": item_x_col2_others_val, "y": 709, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 기존 Y:680 -> 709
    "item_duvet_box":   {"x": item_x_col2_others_val, "y": 738, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 기존 Y:709 -> 738
    # <<<--- 요청에 따라 Y 좌표 수정된 품목들 끝 --->>>

    # 품목 정보 (Col 3)
    "item_styler":      {"x": item_x_col3_val, "y": item_y_start_val, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 2), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 3), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 4), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 5), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 6), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 8.9), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 590 (Y 조정됨)
    "item_angle_shelf": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 10), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 620 (Y 조정됨)
    "item_partition":   {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 11.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 653 (Y 조정됨)
    "item_5ton_access": {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 12.15), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},# 684 (Y 조정됨)
    "item_ac_right":    {"x": item_x_col3_val, "y": int(item_y_start_val + item_y_spacing_val * 13.1), "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 710 (Y 조정됨)


    # 비용 관련 항목들
    "fee_value_next_to_ac_right": {"x": costs_section_x_align_right_val, "y": 680, "size": get_adjusted_font_size(0, "fee_value_next_to_ac_right"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},
    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": _y_main_fee_yellow_box_orig, "size": get_adjusted_font_size(0, "main_fee_yellow_box"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": costs_section_x_align_right_val, "y": int(grand_total_y_new), "size": get_adjusted_font_size(0, "grand_total"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},

    "from_method_label":  {"x": work_method_fee_label_x_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "from_method_fee_value": {"x": costs_section_x_align_right_val, "y": int(from_work_fee_y_val), "size": get_adjusted_font_size(0, "from_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "to_method_label":    {"x": work_method_fee_label_x_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_label"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "to_method_fee_value":  {"x": costs_section_x_align_right_val, "y": int(to_work_fee_y_val),   "size": get_adjusted_font_size(0, "to_method_fee_value"), "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "deposit_amount_display":   {"x": fees_x_val_right_aligned, "y": int(deposit_y_val), "size": get_adjusted_font_size(0, "deposit_amount_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee_display":      {"x": fees_x_val_right_aligned, "y": int(storage_fee_y_val), "size": get_adjusted_font_size(0, "storage_fee_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance_display":{"x": fees_x_val_right_aligned, "y": int(remaining_balance_y_val), "size": get_adjusted_font_size(0, "remaining_balance_display"), "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
}
# ITEM_KEY_MAP (data.py 품목명 변경 사항 반영 필요)
ITEM_KEY_MAP = {
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장": "item_drawer_5dan",
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door",
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand",
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater", "식탁(4인)": "item_dining_table",
    "에어컨": "item_ac_left",  # 왼쪽 에어컨 수량에 매핑 (견적서 이미지상 왼쪽 위치)
    "거실장": "item_living_room_cabinet",
    "피아노(디지털)": "item_piano_digital",
    "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer", # data.py와 일치
    "사무실책상": "item_executive_desk", # '중역책상' 대신 '사무실책상'으로 변경되었을 수 있음 (data.py 확인)
    "책상&의자": "item_desk",
    "책장": "item_bookshelf",
    "의자": "item_chair",       # 이 품목은 data.py에 단독으로 없음. "책상&의자"의 일부로 간주되거나 별도 추가 필요.
    "테이블": "item_table",     # data.py에 명확한 '테이블'이 없음. '소파 테이블' 등을 구체적으로 지정 필요.
    "담요": "item_blanket",     # 이 품목은 data.py에 없음.
    "바구니": "item_basket",
    "중박스": "item_medium_box",
    "중대박스": "item_large_box", # 이 품목은 data.py에 없음. '중박스' 또는 '바구니' 등으로 대체될 수 있음.
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box", # 이미지에는 '옷행거'지만, ITEM_KEY_MAP에서는 'item_clothes_box'로 되어있음. 일관성 확인 필요.
                               # data.py에 '옷행거'가 있고, 이미지에서도 의도한 바가 '옷행거'라면 'item_clothes_hanger' 등으로 키 변경 및 FIELD_MAP 추가 고려.
                               # 현재는 '옷박스' 위치에 '옷행거' 수량이 들어갈 수 있음.
    "스타일러": "item_styler",
    "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic",
    "복합기": "item_copier", # 이 품목은 data.py에 없음.
    "TV(45인치)": "item_tv_45",
    "TV(75인치)": "item_tv_stand", # TV(75인치) 수량이 TV다이(item_tv_stand)에 매핑된 것으로 보임. 검토 필요.
                                   # 만약 TV(75인치)를 별도로 표시하려면 item_tv_75 등의 키와 FIELD_MAP 항목 필요.
    "벽걸이": "item_wall_mount_item", # 이 품목은 data.py에 없음.
    "금고": "item_safe",
    "앵글": "item_angle_shelf",
    "파티션": "item_partition", # 이 품목은 data.py에 없음.
    "5톤진입": "item_5ton_access" # 이 품목은 data.py에 없음.
    # "이불박스" (item_duvet_box) 는 ITEM_KEY_MAP에 누락됨. 추가 필요 시: "이불박스": "item_duvet_box"
}

def get_text_dimensions(text_string, font):
    if not text_string: return 0,0
    if hasattr(font, 'getbbox'): # 최신 Pillow 방식
        try:
            bbox = font.getbbox(str(text_string))
            width = bbox[2] - bbox[0]
            ascent, descent = font.getmetrics()
            height = ascent + descent # 실제 텍스트 높이에 더 가까움
        except Exception: # 예외 발생 시 이전 방식 사용
            if hasattr(font, 'getlength'): width = font.getlength(str(text_string))
            else: width = len(str(text_string)) * (font.size if hasattr(font, 'size') else 10) / 2 # 근사치
            ascent, descent = font.getmetrics()
            height = ascent + descent
    elif hasattr(font, 'getmask'): # 구형 Pillow 방식 (getsize 대신)
        try:
            width, height = font.getmask(str(text_string)).size
        except Exception: # getmask도 실패하면, getmetrics 기반 높이와 근사 너비
            ascent, descent = font.getmetrics()
            height = ascent + descent
            width = font.getlength(str(text_string)) if hasattr(font, 'getlength') else len(str(text_string)) * height / 2
    else: # 모든 getbbox, getmask, getsize가 없는 매우 예외적인 경우
        ascent, descent = font.getmetrics() # 최소한 글꼴 메트릭은 있어야 함
        height = ascent + descent
        if hasattr(font, 'getlength'): # getlength라도 있다면 사용
            width = font.getlength(str(text_string))
        else: # 최후의 수단: 문자 수 * 높이/2 (매우 부정확)
            width = len(str(text_string)) * height / 2
    return width, height


def _get_font(font_type="regular", size=12):
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD
        # else: bold 폰트 없으면 regular로 대체 (경고 없이)
    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError: # 파일 못 찾거나 손상 시
        try: return ImageFont.load_default(size=size) # Pillow 10+
        except TypeError: return ImageFont.load_default() # 이전 Pillow
        except Exception as e_pil_font:
            print(f"Error loading default PIL font: {e_pil_font}")
            raise # 기본 폰트 로드도 실패하면 앱 중단 유도
    except Exception as e_font:
        print(f"Error loading font {font_path_to_use}: {e_font}")
        raise # 특정 폰트 로드 실패 시 앱 중단 유도


def _draw_text_with_alignment(draw, text, x, y, font, color, align="left", max_width=None, line_spacing_factor=1.2):
    if text is None: text = ""
    text = str(text) # 모든 입력을 문자열로 변환

    lines = []
    if max_width: # 자동 줄바꿈 로직
        words = text.split(' ')
        current_line = ""
        for word in words:
            # 단어 자체가 max_width를 초과하는 경우 (예: 긴 URL) - 강제 분할
            word_width, _ = get_text_dimensions(word, font)
            if word_width > max_width and len(word) > 1: # 한 글자 이상일 때만 강제 분할 시도
                if current_line: # 이전까지의 라인 추가
                    lines.append(current_line.strip())
                # 긴 단어 분할
                temp_word_line = ""
                for char_idx, char in enumerate(word):
                    temp_word_line_plus_char_width, _ = get_text_dimensions(temp_word_line + char, font)
                    if temp_word_line_plus_char_width <= max_width:
                        temp_word_line += char
                    else: # 현재 글자 추가 시 넘치면, 이전까지의 부분 추가하고 새 부분 시작
                        lines.append(temp_word_line)
                        temp_word_line = char
                if temp_word_line: # 남은 부분 추가
                    lines.append(temp_word_line)
                current_line = "" # 새 라인 시작
                continue # 다음 단어로

            # 일반적인 단어 추가 로직
            current_line_plus_word_width, _ = get_text_dimensions(current_line + word + " ", font) if current_line else get_text_dimensions(word + " ", font)
            if current_line_plus_word_width <= max_width:
                current_line += word + " "
            else: # 현재 단어 추가 시 넘치면
                if current_line: # 이전까지의 라인 추가
                    lines.append(current_line.strip())
                current_line = word + " " # 새 라인 시작
        if current_line.strip(): # 마지막 남은 라인 추가
            lines.append(current_line.strip())
        if not lines and text: # 줄바꿈 로직 후에도 lines가 비어있지만 원본 text가 있다면 (예: max_width가 매우 작을 때)
             lines.append(text) # 원본 text를 그대로 사용 (잘릴 수 있음)
    else: # max_width가 없으면 기존 개행 문자 기준으로 분리
        lines.extend(text.split('\n'))

    current_y = y
    first_line = True
    _, typical_char_height = get_text_dimensions("A", font) # 줄 간격 계산용 대표 문자 높이

    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1: # 첫 줄이 아니고, 빈 줄이며, 여러 줄 중 하나일 때
            current_y += int(typical_char_height * line_spacing_factor) # 빈 줄에 대한 간격 적용
            continue

        text_width, _ = get_text_dimensions(line, font)
        actual_x = x
        if align == "right":
            actual_x = x - text_width
        elif align == "center":
            actual_x = x - text_width / 2

        # anchor="lt"는 텍스트의 왼쪽 상단을 기준점으로 사용 (Pillow 9.0.0+)
        draw.text((actual_x, current_y), line, font=font, fill=color, anchor="lt")
        current_y += int(typical_char_height * line_spacing_factor) # 다음 줄 위치로 이동
        first_line = False
    return current_y # 마지막으로 그려진 줄의 다음 시작 y 위치 반환


def _format_currency(amount_val):
    if amount_val is None or str(amount_val).strip() == "":
        return ""
    try:
        # 숫자 앞뒤 공백 제거 및 쉼표 제거 후 float 변환
        num_val = float(str(amount_val).replace(",", "").strip())
        num = int(num_val) # 정수부만 사용
        return f"{num:,}" # 천 단위 쉼표 포맷
    except ValueError: # float 변환 실패 시 (예: 숫자가 아닌 문자열)
        return str(amount_val) # 원본 문자열 반환


def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA") # RGBA로 열어 투명도 지원
        draw = ImageDraw.Draw(img)
    except FileNotFoundError:
        print(f"Error: Background image not found at {BACKGROUND_IMAGE_PATH}")
        # 대체 이미지 생성 (오류 메시지 포함)
        img = Image.new('RGB', (900, 1400), color = 'white') # 가로 800, 세로 1200 (예시 크기)
        draw = ImageDraw.Draw(img)
        try: error_font = _get_font(size=24)
        except: error_font = ImageFont.load_default() # 기본 폰트 사용
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, 480, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, 520, error_font, (255,0,0), "center")
        # return None # 여기서 None 반환 대신 오류 이미지라도 반환
    except Exception as e_bg:
        print(f"Error loading background image: {e_bg}")
        return None # 심각한 오류 시 None 반환

    # 폰트 파일 존재 여부 확인 (선택적, _get_font에서 처리됨)
    if not os.path.exists(FONT_PATH_REGULAR): print(f"Warning: Regular font missing at {FONT_PATH_REGULAR}")
    if not os.path.exists(FONT_PATH_BOLD): print(f"Warning: Bold font missing at {FONT_PATH_BOLD}")

    # --- 데이터 준비 ---
    customer_name = state_data.get('customer_name', '')
    customer_phone = state_data.get('customer_phone', '')
    moving_date_obj = state_data.get('moving_date') # date 객체 또는 None
    moving_date_str = moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj)
    quote_date_str = date.today().strftime('%Y-%m-%d') # 견적 생성일은 항상 오늘
    from_location = state_data.get('from_location', '')
    to_location = state_data.get('to_location', '')
    from_floor = str(state_data.get('from_floor', '')) # 문자열로 변환
    to_floor = str(state_data.get('to_floor', ''))   # 문자열로 변환
    
    # 차량 톤수 정보 추출
    selected_vehicle_for_calc = state_data.get('final_selected_vehicle', '') # 예: "5톤", "2.5톤"
    vehicle_tonnage_display = ""
    if isinstance(selected_vehicle_for_calc, str):
        match = re.search(r'(\d+(\.\d+)?)', selected_vehicle_for_calc) # 숫자 부분만 추출
        if match: vehicle_tonnage_display = match.group(1)
    elif isinstance(selected_vehicle_for_calc, (int, float)): # 혹시 숫자로 들어올 경우
        vehicle_tonnage_display = str(selected_vehicle_for_calc)

    # 실제 투입 차량 텍스트 조합
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

    # 작업 방법 텍스트 (아이콘 제외)
    from_method_raw = state_data.get('from_method', '') # 예: "사다리차 🪜"
    from_method_text_for_label = "출발" + (from_method_raw.split(" ")[0] if from_method_raw else "작업")
    from_method_text_for_display_top = from_method_raw.split(" ")[0] if from_method_raw else ""

    to_method_raw = state_data.get('to_method', '')
    to_method_text_for_label = "도착" + (to_method_raw.split(" ")[0] if to_method_raw else "작업")
    to_method_text_for_display_top = to_method_raw.split(" ")[0] if to_method_raw else ""


    # 비용 항목 분류 및 합산 (견적서 이미지 양식에 맞게)
    total_moving_expenses_val = 0 # 기본운임, 날짜할증, 장거리, 폐기물, 추가인력, 경유지, 조정금액 등 포함
    storage_fee_val = 0
    option_ac_cost_val = 0 # 에어컨 비용 (FIELD_MAP의 "fee_value_next_to_ac_right"에 해당)
    from_method_fee_val = 0 # 출발지 작업 비용 (사다리, 스카이 등)
    to_method_fee_raw_val = 0 # 도착지 작업 비용 (사다리, 스카이 등) - 지방사다리 할증 전
    regional_ladder_surcharge_val = 0 # 지방 사다리 추가요금

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, _ in calculated_cost_items: # item_l:항목, item_a:금액
            label = str(item_l)
            try: amount = int(float(item_a or 0)) # 금액은 정수로 처리
            except (ValueError, TypeError): amount = 0

            # "fee_value_next_to_ac_right" 에 해당하는 비용 항목 레이블 확인 필요
            # 예를 들어, data.py 또는 calculations.py에서 에어컨 비용 레이블이 "에어컨 옵션" 이라면:
            if label == "에어컨 설치 및 이전 비용": # 이 레이블은 calculations.py와 일치해야 함
                option_ac_cost_val += amount
            elif label == '보관료':
                storage_fee_val += amount
            elif label.startswith('출발지'): # "출발지 사다리차", "출발지 스카이 장비" 등
                from_method_fee_val += amount
            elif label.startswith('도착지'): # "도착지 사다리차", "도착지 스카이 장비" 등
                to_method_fee_raw_val += amount
            elif label == '지방 사다리 추가요금':
                 regional_ladder_surcharge_val += amount
            # 그 외 항목들은 total_moving_expenses_val에 합산 (기본운임, 할증, 장거리, 폐기물, 인력, 조정 등)
            # VAT, 카드수수료는 grand_total에 포함되므로 여기서는 제외
            elif "부가세" not in label and "카드결제 수수료" not in label:
                total_moving_expenses_val += amount
            
    final_to_method_fee_val = to_method_fee_raw_val + regional_ladder_surcharge_val

    # 계약금, 총액, 잔금
    deposit_amount_val = int(float(state_data.get('deposit_amount', 0) or 0))
    grand_total_num = int(float(total_cost_overall or 0)) # calculations.py에서 계산된 최종 금액
    remaining_balance_num = grand_total_num - deposit_amount_val

    # 그릴 데이터 준비
    data_to_draw = {
        "customer_name": customer_name, "customer_phone": customer_phone, "quote_date": quote_date_str,
        "moving_date": moving_date_str, "from_location": from_location, "to_location": to_location,
        "from_floor": from_floor, "to_floor": to_floor,
        "vehicle_type_numbers_only": vehicle_tonnage_display, # 예: "5", "2.5"
        "actual_dispatched_vehicles_display": actual_dispatched_vehicles_text, # 예: "1톤:1, 2.5톤:1"
        "workers_male": workers_male, "workers_female": workers_female,
        "from_work_method_text_display": from_method_text_for_display_top, # 예: "사다리차"
        "to_work_method_text_display": to_method_text_for_display_top,     # 예: "스카이"
        "fee_value_next_to_ac_right": _format_currency(option_ac_cost_val),
        "main_fee_yellow_box": _format_currency(total_moving_expenses_val),
        "grand_total": _format_currency(grand_total_num),

        "from_method_label": from_method_text_for_label, # 예: "출발사다리차"
        "from_method_fee_value": _format_currency(from_method_fee_val),
        "to_method_label": to_method_text_for_label,     # 예: "도착스카이"
        "to_method_fee_value": _format_currency(final_to_method_fee_val),

        "deposit_amount_display": _format_currency(deposit_amount_val),
        "storage_fee_display": _format_currency(storage_fee_val),
        "remaining_balance_display": _format_currency(remaining_balance_num),
    }

    # 품목 수량 데이터 추가
    try:
        import data as app_data # data.py 임포트 (품목 정의 접근용)
        current_move_type = state_data.get("base_move_type")
        item_defs_for_current_type = {}
        if hasattr(app_data, 'item_definitions') and current_move_type in app_data.item_definitions:
            item_defs_for_current_type = app_data.item_definitions[current_move_type]

        # ITEM_KEY_MAP에 정의된 모든 품목 키에 대해 기본값 "" 설정 (값이 없는 경우 빈칸으로 표시)
        for key_in_fieldmap_vals in ITEM_KEY_MAP.values():
            if key_in_fieldmap_vals.startswith("item_") and key_in_fieldmap_vals not in data_to_draw :
                 data_to_draw[key_in_fieldmap_vals] = "" # 기본값 ""

        # 실제 수량 채우기
        for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
            found_section = None
            # 현재 이사 유형의 품목 정의에서 해당 품목의 섹션 찾기
            if isinstance(item_defs_for_current_type, dict):
                for section_name, item_list_in_section in item_defs_for_current_type.items():
                    if isinstance(item_list_in_section, list) and data_py_item_name in item_list_in_section:
                        found_section = section_name
                        break
            
            if found_section: # 섹션을 찾았으면
                widget_key = f"qty_{current_move_type}_{found_section}_{data_py_item_name}"
                qty_raw = state_data.get(widget_key, 0) # session_state에서 수량 가져오기
                qty_int = 0
                try: # 수량을 정수로 변환
                    if qty_raw is not None and str(qty_raw).strip() != "":
                        qty_int = int(float(str(qty_raw))) # float으로 먼저 변환 후 int
                except ValueError: qty_int = 0
                
                if qty_int > 0: # 수량이 0보다 크면
                    text_val = str(qty_int)
                    if data_py_item_name == "장롱": # 장롱은 칸 수로 계산 (3개당 1.0칸 등으로 표시)
                        try: text_val = f"{(float(qty_int) / 3.0):.1f}" # 소수점 한 자리
                        except: text_val = str(qty_int) # 계산 실패 시 원본 수량
                    data_to_draw[field_map_key_from_map] = text_val
    except ImportError: print("Error: data.py module could not be imported in create_quote_image.")
    except Exception as e_item:
        print(f"Error processing item quantities for image: {e_item}")
        traceback.print_exc()


    # --- 텍스트 그리기 ---
    for key, M_raw in FIELD_MAP.items():
        M = {} # 각 필드 속성 복사 (원본 FIELD_MAP 변경 방지)
        for k_map, v_map in M_raw.items(): # 좌표, 크기 등은 정수로 변환 시도
            if k_map in ["x", "y", "size", "max_width"]:
                try: M[k_map] = int(v_map)
                except (ValueError, TypeError) : M[k_map] = v_map # 변환 실패시 원본값
            else: M[k_map] = v_map

        # FIELD_MAP에 text_override가 있으면 그것을 우선 사용하고, 없으면 data_to_draw에서 값을 가져옴
        text_content_value = M.get("text_override", data_to_draw.get(key))
        final_text_to_draw = ""

        if text_content_value is not None and str(text_content_value).strip() != "":
            final_text_to_draw = str(text_content_value)
        
        # 그릴 내용이 있을 때만 (공백 문자열은 그리지 않음)
        if final_text_to_draw.strip() != "":
            size_to_use = get_adjusted_font_size(M.get("size", BASE_FONT_SIZE), key) # 필드별 폰트 크기 조정
            font_obj = _get_font(font_type=M.get("font", "regular"), size=size_to_use)
            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left") # 기본 정렬은 왼쪽
            
            max_w_val = M.get("max_width") # 최대 너비 (자동 줄바꿈용)
            line_spacing_factor = M.get("line_spacing_factor", 1.15) # 줄 간격 계수
            
            _draw_text_with_alignment(draw, final_text_to_draw, M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    # --- 이미지 바이트로 변환 ---
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG') # PNG로 저장
    img_byte_arr.seek(0) # 버퍼 포인터 처음으로 리셋
    return img_byte_arr.getvalue()


if __name__ == '__main__':
    print("image_generator.py test mode")
    # 목업 데이터 생성
    mock_state = {
        "customer_name": "홍길동 테스트", "customer_phone": "010-9876-5432",
        "moving_date": date(2024, 7, 15),
        "from_location": "서울시 강남구 테헤란로 123, 삼성아파트 101동 202호 (역삼동)",
        "to_location": "경기도 성남시 분당구 판교역로 456, 애플빌라 303동 404호 (삼평동)",
        "from_floor": "2", "to_floor": "4",
        "final_selected_vehicle": "5톤", "dispatched_5t": 1,
        "from_method": "사다리차 🪜", "to_method": "엘리베이터 🛗",
        "deposit_amount": 100000,
        "base_move_type": "가정 이사 🏠", # 필수
        # 품목 수량 (ITEM_KEY_MAP 과 data.py 정의 기반)
        "qty_가정 이사 🏠_주요 품목_4도어 냉장고": 1,
        "qty_가정 이사 🏠_주요 품목_TV(75인치)": 1,
        "qty_가정 이사 🏠_기타_김치냉장고(스탠드형)": 1,
        "qty_가정 이사 🏠_주요 품목_옷장": 5, # 장롱 5칸 -> 5/3.0 = 1.7
        "qty_가정 이사 🏠_주요 품목_더블침대": 1,
        "qty_가정 이사 🏠_포장 자재 📦_바구니": 20,
        "qty_가정 이사 🏠_포장 자재 📦_중박스": 10, # 중박스
    }
    mock_costs = [
        ("기본 운임", 1200000, "5톤 기준"),
        ("출발지 사다리차", 150000, "2층, 5톤 기준"),
        ("도착지 엘리베이터 사용료", 50000, "관리실 납부 대행"),
        ("특별 할인", -50000, "프로모션 적용")
    ]
    mock_total_cost = 1350000 # (120만 + 15만 + 5만 - 5만)
    mock_personnel = {"final_men": 3, "final_women": 1}

    # 이미지 생성
    try:
        image_bytes = create_quote_image(mock_state, mock_costs, mock_total_cost, mock_personnel)
        if image_bytes:
            with open("test_quote_image.png", "wb") as f:
                f.write(image_bytes)
            print("Test image 'test_quote_image.png' saved successfully.")
            # 생성된 이미지 바로 열기 (Windows 기준)
            # if os.name == 'nt': os.startfile("test_quote_image.png")
        else:
            print("Test image generation failed.")
    except Exception as e_main:
        print(f"Error in test run: {e_main}")
        traceback.print_exc()
