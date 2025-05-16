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

# FIELD_MAP: (x, y)는 텍스트 시작점. align='right' 시 x는 오른쪽 끝, align='center' 시 x는 중앙.
# 폰트 크기, 좌표는 final.png (image_6d63e9.png 와 동일한 양식으로 가정) 및
# 실제 폰트 렌더링 결과에 따라 세밀한 조정이 반드시 필요합니다.
FIELD_MAP = {
    "customer_name":  {"x": 175, "y": 130, "size": 18, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "customer_phone": {"x": 475, "y": 130, "size": 18, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "quote_date":     {"x": 750, "y": 130, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "moving_date":    {"x": 750, "y": 158, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "move_time_am_checkbox":   {"x": 708, "y": 188, "size": 15, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V", "text_if_false": "□"},
    "move_time_pm_checkbox":   {"x": 803, "y": 188, "size": 15, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V", "text_if_false": "□"},
    "from_location":  {"x": 175, "y": 188, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},
    "to_location":    {"x": 175, "y": 217, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},
    "from_floor":     {"x": 225, "y": 247, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "to_floor":       {"x": 225, "y": 275, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "vehicle_type":   {"x": 525, "y": 247, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center", "max_width": 260},
    "workers_male":   {"x": 858, "y": 247, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "workers_female": {"x": 858, "y": 275, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_jangrong":    {"x": 226, "y": 334, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_double_bed":  {"x": 226, "y": 362, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": 226, "y": 390, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_3dan": {"x": 226, "y": 418, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": 226, "y": 446, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_normal": {"x": 226, "y": 474, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": 226, "y": 502, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": 226, "y": 530, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_1seater":{"x": 226, "y": 558, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_dining_table":{"x": 226, "y": 586, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": 226, "y": 614, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": 226, "y": 642, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_digital": {"x": 226, "y": 670, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_washing_machine": {"x": 226, "y": 698, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    
    "item_computer":    {"x": 521, "y": 334, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_executive_desk": {"x": 521, "y": 362, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": 521, "y": 390, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_bookshelf":   {"x": 521, "y": 418, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": 521, "y": 446, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": 521, "y": 474, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": 521, "y": 502, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_basket":      {"x": 521, "y": 530, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_medium_box":  {"x": 521, "y": 558, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_book_box":    {"x": 521, "y": 586, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_plant_box":   {"x": 521, "y": 614, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": 521, "y": 642, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": 521, "y": 670, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    
    "item_styler":      {"x": 806, "y": 334, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": 806, "y": 362, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": 806, "y": 390, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": 806, "y": 418, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": 806, "y": 446, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": 806, "y": 474, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": 806, "y": 502, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": 806, "y": 558, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 복합기2 자리 건너뜀
    "item_angle_shelf": {"x": 806, "y": 586, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": 806, "y": 614, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": 806, "y": 642, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": 806, "y": 670, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, # 우측 에어컨 (실제론 옵션 비용)

    # 비용 부분 (노란색 배경 위의 검은색 글씨)
    "fee_value_next_to_ac_right": {"x": 865, "y": 670, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"}, # 에어컨 옆 1,600,000

    "storage_fee":      {"x": 865, "y": 716, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "deposit_amount":   {"x": 865, "y": 744, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance":{"x": 865, "y": 772, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": 865, "y": 808, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
}

ITEM_KEY_MAP = {
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장(5단)": "item_drawer_5dan",
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door", 
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand", 
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater", 
    "식탁(4인)": "item_dining_table", # 식탁(6인) 등 다른 크기는 별도 키 필요
    "에어컨": "item_ac_left", # 좌측 에어컨 품목
    "거실장": "item_living_room_cabinet", # data.py 에는 "장식장" 가능성
    "피아노(디지털)": "item_piano_digital", "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer", "중역책상": "item_executive_desk", 
    "책상&의자": "item_desk", # data.py에는 "책상&의자" 하나의 키
    "책장": "item_bookshelf", "의자": "item_chair", "테이블": "item_table",
    "담요": "item_blanket", "바구니": "item_basket", "중박스": "item_medium_box", 
    "책바구니": "item_book_box", # 이미지에는 "책박스"
    "화분": "item_plant_box", # 이미지에는 "화분박스", data.py에는 "화분"
    "옷행거": "item_clothes_box", # 이미지에는 "옷박스", data.py에는 "옷행거"
    "이불박스": "item_duvet_box", "스타일러": "item_styler", "안마기": "item_massage_chair", 
    "피아노(일반)": "item_piano_acoustic", # 이미지에는 "원목피아노"
    "복합기": "item_copier", "TV(45인치)": "item_tv_45", "TV다이": "item_tv_stand", 
    "벽걸이": "item_wall_mount_item", "금고": "item_safe", "앵글": "item_angle_shelf", 
    "파티션": "item_partition", 
    "5톤진입": "item_5ton_access", # 이 항목은 data.py에 수량성 품목으로 있어야 함
    # "에어컨 실외기" 또는 다른 이름의 우측 에어컨 품목을 data.py에서 찾아 매핑해야 함
    # 예를 들어 data.py 에 "에어컨옵션" 이라는 키가 있고 그 값이 1,600,000을 의미한다면:
    "에어컨옵션": "item_ac_right", 
    # 만약 에어컨옵션 비용이 cost_items에 별도로 계산된다면, 그 값을 "fee_value_next_to_ac_right"에 매핑
}


def get_text_dimensions(text_string, font):
    if not text_string: return 0,0 # 빈 문자열 처리
    if hasattr(font, 'getbbox'):
        try: # 특정 문자 (예: 일부 특수 기호) 에서 getbbox가 에러나는 경우 방지
            bbox = font.getbbox(str(text_string))
            width = bbox[2] - bbox[0]
            ascent, descent = font.getmetrics()
            height = ascent + descent # 글꼴의 일반적인 높이
            # height = bbox[3] - bbox[1] # 실제 그려지는 높이, line spacing에 영향
        except Exception: # 에러 발생시 대체 로직
            if hasattr(font, 'getlength'): width = font.getlength(str(text_string))
            else: width = len(str(text_string)) * font.size / 2 # 매우 대략적
            ascent, descent = font.getmetrics()
            height = ascent + descent

    elif hasattr(font, 'getmask'):
        try:
            width, height = font.getmask(str(text_string)).size
        except Exception: # 에러 발생시 대체 로직
            ascent, descent = font.getmetrics()
            height = ascent + descent
            width = font.getlength(str(text_string)) if hasattr(font, 'getlength') else len(str(text_string)) * height / 2
    else: # getsize는 제거됨
        ascent, descent = font.getmetrics()
        height = ascent + descent
        if hasattr(font, 'getlength'):
            width = font.getlength(str(text_string))
        else: # 최후의 수단
            width = len(str(text_string)) * height / 2 # 매우 부정확한 추정
    return width, height


def _get_font(font_type="regular", size=12):
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD
        # else: Bold 폰트 없으면 Regular 사용 (별도 경고는 create_quote_image 시작 시 한번만)
    
    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError: 
             return ImageFont.load_default()
        except Exception as e_pil_font:
            print(f"Error loading default PIL font: {e_pil_font}")
            raise
    except Exception as e_font: # 기타 폰트 로드 에러
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

            if word_width > max_width: # 단어 하나가 최대 너비보다 긴 경우
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
    _, typical_char_height = get_text_dimensions("A", font) # 기준 높이 (베이스라인 무관)

    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1:
            current_y += int(typical_char_height * line_spacing_factor)
            continue
        
        text_width, _ = get_text_dimensions(line, font)
        actual_x = x
        if align == "right": actual_x = x - text_width
        elif align == "center": actual_x = x - text_width / 2
        
        draw.text((actual_x, current_y), line, font=font, fill=color, anchor="lt") # lt (left-top)
        current_y += int(typical_char_height * line_spacing_factor)
        first_line = False
    return current_y

def _format_currency(amount_val):
    if amount_val is None: return "0" # "원" 제외하고 숫자만 반환 (이미지에 "원"이 있을 수 있음)
    try:
        num_str = str(amount_val).replace(",", "").strip()
        if not num_str: return "0"
        num = int(float(num_str))
        return f"{num:,}" # 콤마만 포함
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
    from_floor = str(state_data.get('from_floor', '')) # "층" 글자는 FIELD_MAP에서 제외하고 값만 전달
    to_floor = str(state_data.get('to_floor', ''))
    vehicle_type = state_data.get('final_selected_vehicle', '')
    workers_male = str(personnel_info.get('final_men', '0'))
    workers_female = str(personnel_info.get('final_women', '0'))

    total_moving_expenses_f22 = 0
    storage_fee_j22 = 0
    # '에어컨' 옆 금액은 특정 옵션비용으로, calculations.py에서 해당 항목이 있다면 가져와야함
    # 여기서는 예시로 '에어컨옵션' 이라는 키로 cost_items에서 찾아본다고 가정
    option_ac_cost = 0 

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
            elif label == '에어컨옵션': # 예시 키, 실제 calculations.py의 레이블로 변경
                option_ac_cost = amount


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
        "fee_value_next_to_ac_right": _format_currency(option_ac_cost) if option_ac_cost > 0 else "", # 에어컨 옆 금액
        "storage_fee": _format_currency(storage_fee_j22) if storage_fee_j22 > 0 else "0",
        "deposit_amount": _format_currency(deposit_amount),
        "remaining_balance": _format_currency(remaining_balance_num),
        "grand_total": _format_currency(grand_total_num),
    }
    
    # 'move_time_preference'는 state_data에 어떻게 저장되는지에 따라 키 이름과 값(오전/오후)을 맞춰야 합니다.
    # 예를 들어 st.radio 등으로 선택된 값이 state_data['move_time_option']에 저장된다고 가정합니다.
    move_time_option_from_state = state_data.get('move_time_option_key_in_state', None) # 실제 키로 변경 필요
    if move_time_option_from_state == '오전': # 실제 '오전'을 나타내는 값으로 변경
         data_to_draw["move_time_am_checkbox"] = FIELD_MAP["move_time_am_checkbox"].get("text_if_true", "V")
         data_to_draw["move_time_pm_checkbox"] = FIELD_MAP["move_time_pm_checkbox"].get("text_if_false", "□")
    elif move_time_option_from_state == '오후': # 실제 '오후'를 나타내는 값으로 변경
         data_to_draw["move_time_am_checkbox"] = FIELD_MAP["move_time_am_checkbox"].get("text_if_false", "□")
         data_to_draw["move_time_pm_checkbox"] = FIELD_MAP["move_time_pm_checkbox"].get("text_if_true", "V")
    else: # 선택 안됨 또는 다른 값
         data_to_draw["move_time_am_checkbox"] = FIELD_MAP["move_time_am_checkbox"].get("text_if_false", "□")
         data_to_draw["move_time_pm_checkbox"] = FIELD_MAP["move_time_pm_checkbox"].get("text_if_false", "□")

    try:
        import data 
        current_move_type = state_data.get("base_move_type")
        item_defs_for_current_type = {}
        if hasattr(data, 'item_definitions') and current_move_type in data.item_definitions:
            item_defs_for_current_type = data.item_definitions[current_move_type]

        for section_name, item_list_in_section in item_defs_for_current_type.items():
            if not isinstance(item_list_in_section, list): continue
            for item_name_from_data_py in item_list_in_section:
                if item_name_from_data_py in ITEM_KEY_MAP:
                    field_map_key = ITEM_KEY_MAP[item_name_from_data_py]
                    widget_key = f"qty_{current_move_type}_{section_name}_{item_name_from_data_py}"
                    qty = state_data.get(widget_key, 0)
                    try: qty_int = int(qty or 0)
                    except ValueError: qty_int = 0

                    if qty_int > 0:
                        text_val = str(qty_int)
                        if item_name_from_data_py == "장롱":
                            try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                            except: text_val = str(qty_int)
                        data_to_draw[field_map_key] = text_val
                    else: # 수량이 0이면 빈칸으로 표시 (선택적)
                        data_to_draw[field_map_key] = "" 
    except Exception as e_item:
        print(f"Error processing item quantities for image: {e_item}")


    for key, M in FIELD_MAP.items():
        text_content = data_to_draw.get(key) 
        if key.endswith("_checkbox"): # 체크박스류는 값이 없으면 기본 false 텍스트로
            text_content = data_to_draw.get(key, M.get("text_if_false"))
        
        if text_content is not None and str(text_content).strip() != "": # 빈 문자열이 아니거나, 체크박스 기본 모양일 때만 그림
            font_obj = _get_font(font_type=M.get("font", "regular"), size=M.get("size", 12))
            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width")
            line_spacing_factor = M.get("line_spacing_factor", 1.15) # 기본 줄간격 약간 조정
            
            _draw_text_with_alignment(draw, str(text_content), M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

if __name__ == '__main__':
    print("image_generator.py test mode")
    # ... (테스트 코드는 이전 답변의 것을 사용하시되, 경로 및 키 값들을 현재 코드에 맞게 조정하세요) ...
    # 예: BACKGROUND_IMAGE_PATH, FONT_PATH*, ITEM_KEY_MAP, FIELD_MAP 키 이름 등
    # 테스트 시 data, utils 모듈이 필요 없도록 sample_state_data를 최대한 상세히 구성
    if not (os.path.exists(FONT_PATH_REGULAR) and os.path.exists(BACKGROUND_IMAGE_PATH)):
         print(f"Ensure {FONT_PATH_REGULAR} and {BACKGROUND_IMAGE_PATH} exist for test.")
    else:
        # ... (테스트 실행 코드 - 이전 답변 참고하여 현재 함수/키에 맞게 수정)
        pass
