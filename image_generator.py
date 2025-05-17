# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math

# (BASE_DIR, 경로, 색상, 기본 좌표 변수 등 상단 부분은 이전과 동일하게 유지)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)

item_y_start_val = 334
item_y_spacing_val = 28.8
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491
item_x_col3_val = 756

vehicle_x_val = 90
vehicle_y_val = int(275 + item_y_spacing_val)

costs_section_x_align_right_val = 326


# FIELD_MAP 수정
# 먼저, 거실장과 소파3의 Y 좌표를 가져오기 위해 FIELD_MAP 정의를 임시로 사용합니다.
# 최종 FIELD_MAP은 이 계산 후에 정의됩니다.

_temp_y_living_room_cabinet = 677 # 이전 수정에서 item_living_room_cabinet의 Y값
_temp_y_sofa_3seater = 549      # item_sofa_3seater의 Y값

# 사다리 비용 Y 좌표 계산 (해석 3 기준)
# Y_거실장 + abs(Y_소파3 - Y_거실장)
ladder_fee_y_val = _temp_y_living_room_cabinet + abs(_temp_y_sofa_3seater - _temp_y_living_room_cabinet)
# ladder_fee_y_val = 677 + abs(549 - 677) = 677 + 128 = 805

FIELD_MAP = {
    "customer_name":  {"x": 175, "y": 130, "size": 19, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "customer_phone": {"x": 412, "y": 130, "size": 16, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "quote_date":     {"x": 640, "y": 130, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "moving_date":    {"x": 640, "y": 161, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "move_time_am_checkbox":   {"x": 708, "y": 188, "size": 15, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V", "text_if_false": "□"},
    "move_time_pm_checkbox":   {"x": 803, "y": 188, "size": 15, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V", "text_if_false": "□"},
    "from_location":  {"x": 175, "y": 161, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},
    "to_location":    {"x": 175, "y": 192, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},
    "from_floor":     {"x": 180, "y": 226, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "to_floor":       {"x": 180, "y": 258, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "vehicle_type":   {"x": vehicle_x_val, "y": vehicle_y_val, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": (item_x_col1_val - vehicle_x_val - 10)},
    "workers_male":   {"x": 758, "y": 228, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "workers_female": {"x": 758, "y": 258, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_jangrong":    {"x": item_x_col1_val, "y": 334, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_double_bed":  {"x": item_x_col1_val, "y": 363, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": item_x_col1_val, "y": 392, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_3dan": {"x": item_x_col1_val, "y": 421, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": item_x_col1_val, "y": 455, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_normal": {"x": item_x_col1_val, "y": 488, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": item_x_col1_val, "y": 518, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": item_x_col1_val, "y": _temp_y_sofa_3seater, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # Y: 549
    "item_sofa_1seater":{"x": item_x_col1_val, "y": 581, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_dining_table":{"x": item_x_col1_val, "y": 612, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": item_x_col1_val, "y": 645, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": item_x_col1_val, "y": _temp_y_living_room_cabinet, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # Y: 677
    "item_piano_digital": {"x": item_x_col1_val, "y": 708, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_washing_machine": {"x": item_x_col1_val, "y": 740, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_computer":    {"x": item_x_col2_others_val, "y": 334, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_executive_desk": {"x": item_x_col2_others_val, "y": 363, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": item_x_col2_others_val, "y": 392, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_bookshelf":   {"x": item_x_col2_others_val, "y": 421, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": item_x_col2_others_val, "y": 450, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": item_x_col2_others_val, "y": 479, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": item_x_col2_others_val, "y": 507, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_basket":      {"x": item_x_col2_baskets_val, "y": 549, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_medium_box":  {"x": item_x_col2_baskets_val, "y": 581, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_large_box":   {"x": item_x_col2_baskets_val, "y": 594, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_book_box":    {"x": item_x_col2_baskets_val, "y": 623, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_plant_box":   {"x": item_x_col2_others_val, "y": 651, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": item_x_col2_others_val, "y": 680, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": item_x_col2_others_val, "y": 709, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_styler":      {"x": item_x_col3_val, "y": 334, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": item_x_col3_val, "y": 363, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": item_x_col3_val, "y": 392, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": item_x_col3_val, "y": 421, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": item_x_col3_val, "y": 450, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": item_x_col3_val, "y": 479, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": item_x_col3_val, "y": 507, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": item_x_col3_val, "y": 590, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_angle_shelf": {"x": item_x_col3_val, "y": 620, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": item_x_col3_val, "y": 653, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": item_x_col3_val, "y": 684, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": item_x_col3_val, "y": 710, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    # 비용 관련 항목들
    "fee_value_next_to_ac_right": {"x": costs_section_x_align_right_val, "y": 680, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},
    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": 775, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # "이사비용" 레이블이 붙은 값 (F22)
    "storage_fee":      {"x": costs_section_x_align_right_val, "y": 1305, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "deposit_amount":   {"x": costs_section_x_align_right_val, "y": 1036, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance":{"x": costs_section_x_align_right_val, "y": 998, "size": 21, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": costs_section_x_align_right_val, "y": 861, "size": 22, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},

    # 새로운 사다리 비용 항목 (총 사다리 비용)
    "total_ladder_fee": {"x": costs_section_x_align_right_val, "y": ladder_fee_y_val, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"}, # X: grand_total과 동일, Y: 계산된 값 (805)
}

# ITEM_KEY_MAP은 이전 답변의 수정된 버전을 사용합니다.
# data.py의 품목명 변경("장식장"->"거실장", "오디오..."->"컴퓨터&모니터")을 반영해야 합니다.
ITEM_KEY_MAP = {
    "장롱": "item_jangrong", "더블침대": "item_double_bed",
    "서랍장": "item_drawer_5dan", # data.py의 "서랍장"과 매핑
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door",
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand",
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater",
    "식탁(4인)": "item_dining_table",
    "에어컨": "item_ac_left",
    "거실장": "item_living_room_cabinet", # data.py에서 "장식장"이 "거실장"으로 변경되었으므로 이 매핑 사용
    "피아노(디지털)": "item_piano_digital",
    "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer", # data.py에서 "오디오 및 스피커"를 대체
    "중역책상": "item_executive_desk", "책상&의자": "item_desk", "책장": "item_bookshelf",
    "의자": "item_chair", "테이블": "item_table", "담요": "item_blanket",
    "바구니": "item_basket", "중박스": "item_medium_box",
    "중대박스": "item_large_box", # data.py에 "중대박스" 품목이 있다면 이 매핑 유효
    "책바구니": "item_book_box",
    "화분": "item_plant_box",
    "옷행거": "item_clothes_box",
    # "이불박스": "item_duvet_box", # data.py에 "이불박스" 품목이 있다면 이 매핑 유효
    "스타일러": "item_styler", "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic", "복합기": "item_copier", "TV(45인치)": "item_tv_45",
    "TV다이": "item_tv_stand", "벽걸이": "item_wall_mount_item", "금고": "item_safe",
    "앵글": "item_angle_shelf", "파티션": "item_partition", "5톤진입": "item_5ton_access",
    # "에어컨 실외기": "item_ac_right", # data.py에 "에어컨 실외기" 품목이 있다면 이 매핑 유효
}
# ITEM_KEY_MAP의 나머지 부분과 data.py의 품목 목록 간의 일관성 확인이 중요합니다.

# (_get_font, _draw_text_with_alignment, _format_currency 함수는 이전과 동일)
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

            if word_width > max_width:
                if current_line: lines.append(current_line.strip())
                temp_word_line = ""
                for char_idx, char in enumerate(word):
                    temp_word_line_plus_char_width, _ = get_text_dimensions(temp_word_line + char, font)
                    if temp_word_line_plus_char_width <= max_width:
                        temp_word_line += char
                    else:
                        lines.append(temp_word_line)
                        temp_word_line = char
                if temp_word_line: lines.append(temp_word_line)
                current_line = ""
                continue

            if current_line_plus_word_width <= max_width:
                current_line += word + " "
            else:
                if current_line: lines.append(current_line.strip())
                current_line = word + " "
        if current_line.strip(): lines.append(current_line.strip())
        if not lines and text: lines.append(text)
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
        if align == "right": actual_x = x - text_width
        elif align == "center": actual_x = x - text_width / 2

        draw.text((actual_x, current_y), line, font=font, fill=color, anchor="lt")
        current_y += int(typical_char_height * line_spacing_factor)
        first_line = False
    return current_y

def _format_currency(amount_val):
    if amount_val is None: return "0"
    try:
        num_str = str(amount_val).replace(",", "").strip()
        if not num_str: return "0"
        num = int(float(num_str))
        return f"{num:,}"
    except ValueError:
        return str(amount_val)


def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
    except FileNotFoundError:
        # ... (에러 처리 부분 동일) ...
        print(f"Error: Background image not found at {BACKGROUND_IMAGE_PATH}")
        img = Image.new('RGB', (900, 1000), color = 'white')
        draw = ImageDraw.Draw(img)
        try: error_font = _get_font(size=24)
        except: error_font = ImageFont.load_default()
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, 480, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, 520, error_font, (255,0,0), "center")


    if not os.path.exists(FONT_PATH_REGULAR): print(f"Warning: Regular font missing at {FONT_PATH_REGULAR}")
    if not os.path.exists(FONT_PATH_BOLD): print(f"Warning: Bold font missing at {FONT_PATH_BOLD} (regular will be used)")

    # ... (기본 정보 추출 부분 동일) ...
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

    # 비용 항목에서 데이터 추출 (사다리 비용 포함)
    total_moving_expenses_f22 = 0
    storage_fee_j22 = 0
    option_ac_cost_val = 0
    current_total_ladder_fee = 0 # 총 사다리 비용을 저장할 변수

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, _ in calculated_cost_items:
            label = str(item_l)
            try: amount = int(item_a or 0)
            except (ValueError, TypeError): amount = 0

            if label in ['기본 운임', '날짜 할증', '장거리 운송료', '폐기물 처리', '폐기물 처리(톤)',
                         '추가 인력', '경유지 추가요금'] or "조정 금액" in label: # '지방 사다리 추가요금'은 아래에서 별도 처리
                total_moving_expenses_f22 += amount
            elif label == '보관료':
                storage_fee_j22 = amount
            elif label == '에어컨 설치 및 이전 비용':
                option_ac_cost_val = amount
            elif "사다리차" in label or "스카이 장비" in label or "지방 사다리 추가요금" in label: # 모든 사다리/스카이 관련 비용 합산
                current_total_ladder_fee += amount
                if label == "지방 사다리 추가요금": # F22에 이미 포함되었을 수 있으므로, 중복 방지 (calculations.py 로직에 따라 다름)
                    # calculations.py에서 '지방 사다리 추가요금'이 total_moving_expenses_f22에 이미 더해졌다면, 여기서 빼줘야 함
                    # 현재 calculations.py는 cost_before_add_charges에 더하고 있으므로,
                    # F22에 해당하는 total_moving_expenses_f22에 포함됨.
                    # 따라서, current_total_ladder_fee에는 합산하되, F22에서 이중계산 안 되도록 주의.
                    # 여기서는 current_total_ladder_fee에 모든 사다리 비용을 넣고,
                    # total_moving_expenses_f22에는 기본 운임, 날짜 할증 등만 넣도록 조정.
                    # --> "지방 사다리 추가요금"을 total_moving_expenses_f22 조건에서 제외하고 아래 current_total_ladder_fee에만 포함되도록 수정.
                    pass # 위 조건에서 제외하고 여기서 합산

    # '지방 사다리 추가요금'을 total_moving_expenses_f22 조건에서 명시적으로 제외
    # (calculations.py에서 cost_before_add_charges에 이미 더해지므로,
    #  main_fee_yellow_box에는 포함되지만, total_ladder_fee와 별도로 표시됨)
    # 이 부분은 견적서 양식의 '이사비용' 항목(main_fee_yellow_box)이
    # 순수 운임 + 부가서비스(사다리 제외)인지, 아니면 사다리까지 포함된 금액인지에 따라 조정 필요.
    # 현재 main_fee_yellow_box는 '이사비용'이라는 레이블로, 사다리 비용이 별도 표시되므로,
    # total_moving_expenses_f22에는 사다리 관련 비용이 포함되지 않도록 하는 것이 적절해 보임.
    # -> calculations.py의 total_moving_expenses_f22 집계 로직과 일관성 확인 필요.
    # -> 현재 FIELD_MAP의 main_fee_yellow_box (F22)는 "이사비용"으로, 사다리/스카이 비용은 별도 항목으로 표시되는 양식임.
    #    따라서 total_moving_expenses_f22는 사다리/스카이 비용을 제외한 금액이어야 함.
    #    위의 calculated_cost_items 순회 시 total_moving_expenses_f22에 "지방 사다리 추가요금"이 더해지지 않도록 조건 수정.

    # total_moving_expenses_f22 재계산 (사다리/스카이 제외)
    total_moving_expenses_f22_revised = 0
    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, _ in calculated_cost_items:
            label = str(item_l)
            try: amount = int(item_a or 0)
            except (ValueError, TypeError): amount = 0
            if label in ['기본 운임', '날짜 할증', '장거리 운송료', '폐기물 처리', '폐기물 처리(톤)',
                         '추가 인력', '경유지 추가요금'] or "조정 금액" in label:
                total_moving_expenses_f22_revised += amount
    total_moving_expenses_f22 = total_moving_expenses_f22_revised


    deposit_amount_raw = state_data.get('deposit_amount', state_data.get('tab3_deposit_amount', 0))
    deposit_amount = int(deposit_amount_raw or 0)
    grand_total_num = int(total_cost_overall or 0) # total_cost_overall은 모든 비용이 합산된 최종 금액
    remaining_balance_num = grand_total_num - deposit_amount

    data_to_draw = {
        "customer_name": customer_name, "customer_phone": customer_phone,
        "quote_date": quote_date_str, "moving_date": moving_date_str,
        "from_location": from_location, "to_location": to_location,
        "from_floor": from_floor, "to_floor": to_floor,
        "vehicle_type": vehicle_type,
        "workers_male": workers_male, "workers_female": workers_female,
        "fee_value_next_to_ac_right": _format_currency(option_ac_cost_val) if option_ac_cost_val > 0 else "",
        "main_fee_yellow_box": _format_currency(total_moving_expenses_f22), # 순수 이사 비용 (사다리 등 제외)
        "storage_fee": _format_currency(storage_fee_j22) if storage_fee_j22 > 0 else "0",
        "deposit_amount": _format_currency(deposit_amount),
        "remaining_balance": _format_currency(remaining_balance_num),
        "grand_total": _format_currency(grand_total_num), # 모든 비용 합산된 총액
        "total_ladder_fee": _format_currency(current_total_ladder_fee) if current_total_ladder_fee > 0 else "", # 계산된 총 사다리 비용
    }

    # (move_time_option_from_state 및 품목 수량 data_to_draw에 추가하는 로직은 이전과 동일)
    move_time_option_from_state = state_data.get('move_time_option_key_in_state', None)
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
        import data as app_data # data.py를 app_data로 임포트
        current_move_type = state_data.get("base_move_type")
        item_defs_for_current_type = {}
        if hasattr(app_data, 'item_definitions') and current_move_type in app_data.item_definitions:
            item_defs_for_current_type = app_data.item_definitions[current_move_type]

        for key in ITEM_KEY_MAP.values():
            if key.startswith("item_") and key not in data_to_draw :
                 data_to_draw[key] = ""

        for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
            found_section = None
            if isinstance(item_defs_for_current_type, dict):
                for section_name, item_list_in_section in item_defs_for_current_type.items():
                    if isinstance(item_list_in_section, list) and data_py_item_name in item_list_in_section:
                        found_section = section_name
                        break
            if found_section:
                widget_key = f"qty_{current_move_type}_{found_section}_{data_py_item_name}"
                qty = state_data.get(widget_key, 0)
                try: qty_int = int(qty or 0)
                except ValueError: qty_int = 0

                if qty_int > 0:
                    text_val = str(qty_int)
                    if data_py_item_name == "장롱":
                        try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                        except: text_val = str(qty_int)
                    data_to_draw[field_map_key_from_map] = text_val
    except Exception as e_item:
        print(f"Error processing item quantities for image: {e_item}")
        import traceback
        traceback.print_exc()


    # FIELD_MAP을 순회하며 텍스트 그리기 (이전과 동일)
    for key, M_raw in FIELD_MAP.items():
        M = {}
        for k_map, v_map in M_raw.items():
            if k_map in ["x", "y", "size", "max_width"]:
                try: M[k_map] = int(v_map)
                except (ValueError, TypeError): M[k_map] = v_map
            else: M[k_map] = v_map

        text_content = data_to_draw.get(key)
        if key.endswith("_checkbox"):
            text_content = data_to_draw.get(key, M.get("text_if_false", "□"))

        if text_content is not None and str(text_content).strip() != "":
            font_obj = _get_font(font_type=M.get("font", "regular"), size=M.get("size", 12))
            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width")
            line_spacing_factor = M.get("line_spacing_factor", 1.15)

            _draw_text_with_alignment(draw, str(text_content), M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)


    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

# (if __name__ == '__main__': 테스트 부분은 이전과 동일하게 유지)
if __name__ == '__main__':
    print("image_generator.py test mode")
    if not (os.path.exists(FONT_PATH_REGULAR) and os.path.exists(BACKGROUND_IMAGE_PATH)):
         print(f"Ensure {FONT_PATH_REGULAR} and {BACKGROUND_IMAGE_PATH} (and optionally {FONT_PATH_BOLD}) exist for test.")
    else:
        sample_state_data = {
            'customer_name': '김테스트 고객님', 'customer_phone': '010-1234-5678',
            'moving_date': date(2025, 6, 15),
            'from_location': '서울시 강남구 출발동 123-45',
            'to_location': '경기도 성남시 도착구 678-90',
            'from_floor': '7', 'to_floor': '10',
            'final_selected_vehicle': '5톤',
            'deposit_amount': 100000,
            'base_move_type': "가정 이사 🏠",
            'qty_가정 이사 🏠_주요 품목_장롱': 9,
            'qty_가정 이사 🏠_주요 품목_더블침대': 1,
            'qty_가정 이사 🏠_주요 품목_서랍장': 2,
            'qty_가정 이사 🏠_기타_서랍장(3단)': 1,
            'qty_가정 이사 🏠_주요 품목_4도어 냉장고': 1,
            'qty_가정 이사 🏠_주요 품목_거실장': 1,
            'qty_가정 이사 🏠_기타_컴퓨터&모니터': 2,
            'qty_가정 이사 🏠_주요 품목_소파(3인용)': 1,
            'qty_가정 이사 🏠_기타_소파(1인용)': 1,
            'qty_가정 이사 🏠_주요 품목_에어컨': 1,
            'qty_가정 이사 🏠_기타_피아노(디지털)': 1,
            'qty_가정 이사 🏠_포장 자재 📦_바구니': 20,
            'qty_가정 이사 🏠_포장 자재 📦_중박스': 10,
            'move_time_option_key_in_state': '오전',
        }
        sample_personnel_info = {'final_men': 3, 'final_women': 1}
        # 사다리 비용이 포함된 calculated_cost_items 예시
        sample_calculated_cost_items = [
            ('기본 운임', 1200000, '5톤 기준'),
            ('출발지 사다리차', 170000, '8~9층, 5톤 기준'), # 사다리 비용 1
            ('도착지 사다리차', 180000, '10~11층, 5톤 기준'),# 사다리 비용 2
            ('지방 사다리 추가요금', 50000, '수동입력'), # 사다리 비용 3
            ('에어컨 설치 및 이전 비용', 150000, '기본 설치'),
            ('조정 금액', 50000, '프로모션 할인')
        ]
        # total_cost_overall은 모든 비용이 합산된 금액
        sample_total_cost_overall = sum(item[1] for item in sample_calculated_cost_items)

        try:
            img_data = create_quote_image(sample_state_data, sample_calculated_cost_items, sample_total_cost_overall, sample_personnel_info)
            if img_data:
                output_filename = "수정된_견적서_이미지_사다리포함.png"
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
            import traceback
            traceback.print_exc()
