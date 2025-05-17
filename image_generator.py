# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)

# 좌표 계산용 기준값
item_y_start_val = 334
item_y_spacing_val = 28.8
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491 # "책상" 등의 X 좌표로 사용됨
item_x_col3_val = 756

vehicle_x_val = 90
vehicle_y_val = int(275 + item_y_spacing_val)

costs_section_x_align_right_val = 326

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

    "item_jangrong":    {"x": item_x_col1_val, "y": 334, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 장롱 Y: 334
    "item_double_bed":  {"x": item_x_col1_val, "y": 363, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": item_x_col1_val, "y": 392, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 서랍장(5단) Y: (363+421)/2 = 392
    "item_drawer_3dan": {"x": item_x_col1_val, "y": 421, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": item_x_col1_val, "y": 455, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_normal": {"x": item_x_col1_val, "y": 488, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": item_x_col1_val, "y": 518, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": item_x_col1_val, "y": 549, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 소파3 Y: 549
    "item_sofa_1seater":{"x": item_x_col1_val, "y": 581, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 소파1 Y: 581
    "item_dining_table":{"x": item_x_col1_val, "y": 612, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": item_x_col1_val, "y": 645, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": item_x_col1_val, "y": 677, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 거실장 Y: (645+708)/2 = 677
    "item_piano_digital": {"x": item_x_col1_val, "y": 708, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_washing_machine": {"x": item_x_col1_val, "y": 740, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_computer":    {"x": item_x_col2_others_val, "y": 334, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 컴퓨터&모니터 X: 책상X (item_x_col2_others_val), Y: 장롱Y (334)
    "item_executive_desk": {"x": item_x_col2_others_val, "y": 363, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": item_x_col2_others_val, "y": 392, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 책상 X: item_x_col2_others_val
    "item_bookshelf":   {"x": item_x_col2_others_val, "y": 421, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": item_x_col2_others_val, "y": 450, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": item_x_col2_others_val, "y": 479, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": item_x_col2_others_val, "y": 507, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_basket":      {"x": item_x_col2_baskets_val, "y": 549, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 바구니 Y: 소파3 Y (549)
    "item_medium_box":  {"x": item_x_col2_baskets_val, "y": 581, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 중박스 Y: 소파1 Y (581)
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

    "fee_value_next_to_ac_right": {"x": costs_section_x_align_right_val, "y": 680, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": 775, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee":      {"x": costs_section_x_align_right_val, "y": 1305, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "deposit_amount":   {"x": costs_section_x_align_right_val, "y": 1036, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance":{"x": costs_section_x_align_right_val, "y": 998, "size": 21, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": costs_section_x_align_right_val, "y": 861, "size": 22, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # Y: 857->861 (+4), Size: 24->22 (-2)
}

ITEM_KEY_MAP = {
    # data.py의 품목명 (키) : FIELD_MAP의 키 (값)
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장(5단)": "item_drawer_5dan", # FIELD_MAP에 'item_drawer_5dan'이 있으므로, data.py의 '서랍장'을 '서랍장(5단)'으로 보거나, 이 맵을 수정
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door",
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand",
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater",
    "식탁(4인)": "item_dining_table",
    "에어컨": "item_ac_left", # data.py에는 그냥 "에어컨"
    "거실장": "item_living_room_cabinet", # data.py에서 "장식장"을 "거실장"으로 변경했으므로, 이 매핑은 유효
    "피아노(디지털)": "item_piano_digital",
    "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer", # data.py에서 "오디오 및 스피커"를 대체
    "중역책상": "item_executive_desk", "책상&의자": "item_desk", "책장": "item_bookshelf",
    "의자": "item_chair", "테이블": "item_table", "담요": "item_blanket",
    "바구니": "item_basket", "중박스": "item_medium_box",
    "중대박스": "item_large_box", # FIELD_MAP에는 item_large_box가 있으나, data.py의 포장자재에는 '중대박스'가 없음. 일관성 필요. data.py에 '중대박스'를 추가하거나 이 맵에서 제거/수정.
    "책바구니": "item_book_box",
    "화분": "item_plant_box", # FIELD_MAP에는 item_plant_box가 있으나, ITEM_KEY_MAP에는 없음. data.py의 "화분"과 연결.
    "옷행거": "item_clothes_box", # FIELD_MAP에는 item_clothes_box, ITEM_KEY_MAP에는 없음. data.py의 "옷행거"와 연결.
    "이불박스": "item_duvet_box", # FIELD_MAP에는 item_duvet_box, ITEM_KEY_MAP에는 없음. data.py에는 "이불박스" 없음. 일관성 필요.

    "스타일러": "item_styler", "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic", "복합기": "item_copier", "TV(45인치)": "item_tv_45",
    "TV다이": "item_tv_stand", "벽걸이": "item_wall_mount_item", "금고": "item_safe",
    "앵글": "item_angle_shelf", "파티션": "item_partition", "5톤진입": "item_5ton_access",
    "에어컨 실외기": "item_ac_right", # data.py에는 "에어컨 실외기" 없음. FIELD_MAP에는 item_ac_right 있음. 일관성 필요.

    # 추가/수정 필요한 부분들
    "서랍장": "item_drawer_5dan", # data.py의 "서랍장"을 FIELD_MAP의 "item_drawer_5dan"으로 매핑 (기존 "서랍장(5단)" 대신)
}
# ITEM_KEY_MAP 보강: FIELD_MAP에 있지만 ITEM_KEY_MAP에 누락된 품목들 중 data.py와 연결 가능한 것들 추가
if "화분" not in ITEM_KEY_MAP and "item_plant_box" in FIELD_MAP:
    ITEM_KEY_MAP["화분"] = "item_plant_box"
if "옷행거" not in ITEM_KEY_MAP and "item_clothes_box" in FIELD_MAP:
    ITEM_KEY_MAP["옷행거"] = "item_clothes_box"
# 만약 data.py에 '중대박스'가 있다면:
# if "중대박스" not in ITEM_KEY_MAP and "item_large_box" in FIELD_MAP:
#    ITEM_KEY_MAP["중대박스"] = "item_large_box"
# 만약 data.py에 '에어컨 실외기'가 있다면:
# if "에어컨 실외기" not in ITEM_KEY_MAP and "item_ac_right" in FIELD_MAP:
#    ITEM_KEY_MAP["에어컨 실외기"] = "item_ac_right"


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
        print(f"Error: Background image not found at {BACKGROUND_IMAGE_PATH}")
        img = Image.new('RGB', (900, 1000), color = 'white')
        draw = ImageDraw.Draw(img)
        try: error_font = _get_font(size=24)
        except: error_font = ImageFont.load_default()
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, 480, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, 520, error_font, (255,0,0), "center")

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
    storage_fee_j22 = 0
    option_ac_cost_val = 0

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, _ in calculated_cost_items:
            label = str(item_l)
            try: amount = int(item_a or 0)
            except (ValueError, TypeError): amount = 0

            if label in ['기본 운임', '날짜 할증', '장거리 운송료', '폐기물 처리', '폐기물 처리(톤)',
                         '추가 인력', '지방 사다리 추가요금', '경유지 추가요금'] or "조정 금액" in label:
                total_moving_expenses_f22 += amount
            elif label == '보관료':
                storage_fee_j22 = amount
            elif label == '에어컨 설치 및 이전 비용':
                option_ac_cost_val = amount

    deposit_amount_raw = state_data.get('deposit_amount', state_data.get('tab3_deposit_amount', 0))
    deposit_amount = int(deposit_amount_raw or 0)
    grand_total_num = int(total_cost_overall or 0)
    remaining_balance_num = grand_total_num - deposit_amount

    data_to_draw = {
        "customer_name": customer_name, "customer_phone": customer_phone,
        "quote_date": quote_date_str, "moving_date": moving_date_str,
        "from_location": from_location, "to_location": to_location,
        "from_floor": from_floor, "to_floor": to_floor,
        "vehicle_type": vehicle_type,
        "workers_male": workers_male, "workers_female": workers_female,
        "fee_value_next_to_ac_right": _format_currency(option_ac_cost_val) if option_ac_cost_val > 0 else "",
        "main_fee_yellow_box": _format_currency(total_moving_expenses_f22),
        "storage_fee": _format_currency(storage_fee_j22) if storage_fee_j22 > 0 else "0",
        "deposit_amount": _format_currency(deposit_amount),
        "remaining_balance": _format_currency(remaining_balance_num),
        "grand_total": _format_currency(grand_total_num),
    }

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
        # data.py를 직접 임포트하여 사용 (st.session_state에 의존하지 않음)
        import data as app_data
        current_move_type = state_data.get("base_move_type")
        item_defs_for_current_type = {}
        if hasattr(app_data, 'item_definitions') and current_move_type in app_data.item_definitions:
            item_defs_for_current_type = app_data.item_definitions[current_move_type]

        for key in ITEM_KEY_MAP.values(): # ITEM_KEY_MAP의 값들은 FIELD_MAP의 키
            if key.startswith("item_") and key not in data_to_draw :
                 data_to_draw[key] = "" # 해당 FIELD_MAP 키에 대한 기본값 초기화

        # ITEM_KEY_MAP을 순회하며 data.py의 품목명과 매핑된 FIELD_MAP 키에 수량 적용
        for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
            # data.py의 item_definitions에서 해당 품목이 어느 섹션에 속하는지 찾아야 함
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
                    if data_py_item_name == "장롱": # data.py의 품목명이 "장롱"일 때
                        try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                        except: text_val = str(qty_int)
                    data_to_draw[field_map_key_from_map] = text_val
            # else:
                # print(f"Debug: Item '{data_py_item_name}' not found in any section for current move type '{current_move_type}' or its FIELD_MAP key '{field_map_key_from_map}' is not processed.")


    except Exception as e_item:
        print(f"Error processing item quantities for image: {e_item}")
        import traceback
        traceback.print_exc()


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

if __name__ == '__main__':
    print("image_generator.py test mode")
    if not (os.path.exists(FONT_PATH_REGULAR) and os.path.exists(BACKGROUND_IMAGE_PATH)):
         print(f"Ensure {FONT_PATH_REGULAR} and {BACKGROUND_IMAGE_PATH} (and optionally {FONT_PATH_BOLD}) exist for test.")
    else:
        # 테스트를 위한 샘플 데이터 (실제 애플리케이션의 state_data 구조와 유사하게)
        # data.py에서 "오디오 및 스피커"가 "컴퓨터&모니터"로, "장식장"이 "거실장"으로 변경된 것을 반영
        sample_state_data = {
            'customer_name': '김테스트 고객님', 'customer_phone': '010-1234-5678',
            'moving_date': date(2025, 6, 15),
            'from_location': '서울시 강남구 출발동 123-45',
            'to_location': '경기도 성남시 도착구 678-90',
            'from_floor': '7', 'to_floor': '10',
            'final_selected_vehicle': '5톤', # data.py의 vehicle_prices 키와 일치해야 함
            'deposit_amount': 100000,
            'base_move_type': "가정 이사 🏠", # data.py의 item_definitions 키와 일치
            # data.py의 item_definitions["가정 이사 🏠"]의 섹션 및 품목명과 일치해야 함
            'qty_가정 이사 🏠_주요 품목_장롱': 9, # 3칸으로 표시됨
            'qty_가정 이사 🏠_주요 품목_더블침대': 1,
            'qty_가정 이사 🏠_주요 품목_서랍장': 2, # '서랍장'은 ITEM_KEY_MAP에서 item_drawer_5dan으로 매핑됨
            'qty_가정 이사 🏠_기타_서랍장(3단)': 1,
            'qty_가정 이사 🏠_주요 품목_4도어 냉장고': 1,
            'qty_가정 이사 🏠_기타_김치냉장고(일반형)': 1,
            'qty_가정 이사 🏠_기타_김치냉장고(스탠드형)': 0, # 수량 0
            'qty_가정 이사 🏠_주요 품목_소파(3인용)': 1,
            'qty_가정 이사 🏠_기타_소파(1인용)': 2,
            'qty_가정 이사 🏠_주요 품목_식탁(4인)': 1,
            'qty_가정 이사 🏠_주요 품목_에어컨': 1,
            'qty_가정 이사 🏠_주요 품목_거실장': 1, # data.py에서 "장식장" -> "거실장" 변경 반영
            'qty_가정 이사 🏠_기타_피아노(디지털)': 1,
            'qty_가정 이사 🏠_주요 품목_세탁기 및 건조기':1,
            'qty_가정 이사 🏠_포장 자재 📦_바구니': 20,
            'qty_가정 이사 🏠_포장 자재 📦_중박스': 10,
            # 'qty_가정 이사 🏠_포장 자재 📦_중대박스': 0, # ITEM_KEY_MAP에서 data.py와 일관성 확인 필요
            'qty_가정 이사 🏠_포장 자재 📦_책바구니': 5,
            'qty_가정 이사 🏠_기타_스타일러': 1,
            'qty_가정 이사 🏠_기타_안마기': 0,
            'qty_가정 이사 🏠_기타_피아노(일반)': 1,
            'qty_가정 이사 🏠_기타_TV(45인치)': 1, # get_tv_qty가 사용된다면 이 값도 반영되어야 함
            'qty_가정 이사 🏠_기타_금고': 1,
            'qty_가정 이사 🏠_기타_컴퓨터&모니터': 2, # "오디오 및 스피커" 대신 사용
            # 'qty_가정 이사 🏠_기타_에어컨 실외기': 1, # ITEM_KEY_MAP에서 data.py와 일관성 확인 필요
            'move_time_option_key_in_state': '오전', # 예시: '오전', '오후', 또는 None
        }
        sample_personnel_info = {'final_men': 3, 'final_women': 1}
        sample_calculated_cost_items = [
            ('기본 운임', 1200000, '5톤 기준'),
            ('출발지 사다리차', 170000, '8~9층, 5톤 기준'),
            ('도착지 사다리차', 180000, '10~11층, 5톤 기준'),
            ('에어컨 설치 및 이전 비용', 150000, '기본 설치'),
            # ('보관료', 0, ''), # 필요시 추가
            ('조정 금액', 50000, '프로모션 할인')
        ]
        # total_cost_overall은 calculated_cost_items의 합계와 유사하게 계산
        sample_total_cost_overall = sum(item[1] for item in sample_calculated_cost_items)


        try:
            # import data # create_quote_image 내부에서 import data as app_data로 변경됨
            img_data = create_quote_image(sample_state_data, sample_calculated_cost_items, sample_total_cost_overall, sample_personnel_info)
            if img_data:
                output_filename = "수정된_견적서_이미지.png"
                with open(output_filename, "wb") as f:
                    f.write(img_data)
                print(f"Test image '{output_filename}' created successfully. Please check.")
                if os.name == 'nt': # Windows에서 자동 실행
                    try: os.startfile(output_filename)
                    except: print("Could not auto-open image.")
            else:
                print("Test image creation failed.")
        except Exception as e_test:
            print(f"Error during test: {e_test}")
            import traceback
            traceback.print_exc()
