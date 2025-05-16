# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math

# --- 설정값 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)

FIELD_MAP = {
    "customer_name":  {"x": 175, "y": 132, "size": 20, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "customer_phone": {"x": 475, "y": 132, "size": 20, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "quote_date":     {"x": 750, "y": 132, "size": 18, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "moving_date":    {"x": 750, "y": 160, "size": 18, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "move_time_am_checkbox":   {"x": 705, "y": 188, "size": 16, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V"},
    "move_time_pm_checkbox":   {"x": 800, "y": 188, "size": 16, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V"},
    "from_location":  {"x": 175, "y": 188, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 400, "line_spacing_factor": 1.1},
    "to_location":    {"x": 175, "y": 217, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 400, "line_spacing_factor": 1.1},
    "from_floor":     {"x": 225, "y": 247, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "to_floor":       {"x": 225, "y": 275, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "vehicle_type":   {"x": 525, "y": 247, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center", "max_width": 270},
    "workers_male":   {"x": 858, "y": 247, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "workers_female": {"x": 858, "y": 275, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_jangrong":    {"x": 226, "y": 334, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_double_bed":  {"x": 226, "y": 334 + 28*1, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": 226, "y": 334 + 28*2, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_3dan": {"x": 226, "y": 334 + 28*3, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": 226, "y": 334 + 28*4, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_normal": {"x": 226, "y": 334 + 28*5, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": 226, "y": 334 + 28*6, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": 226, "y": 334 + 28*7, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_1seater":{"x": 226, "y": 334 + 28*8, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_dining_table":{"x": 226, "y": 334 + 28*9, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": 226, "y": 334 + 28*10, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": 226, "y": 334 + 28*11, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_digital": {"x": 226, "y": 334 + 28*12, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_washing_machine": {"x": 226, "y": 334 + 28*13, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    
    "item_computer":    {"x": 521, "y": 334, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_executive_desk": {"x": 521, "y": 334 + 28*1, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": 521, "y": 334 + 28*2, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_bookshelf":   {"x": 521, "y": 334 + 28*3, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": 521, "y": 334 + 28*4, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": 521, "y": 334 + 28*5, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": 521, "y": 334 + 28*6, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_basket":      {"x": 521, "y": 334 + 28*7, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_medium_box":  {"x": 521, "y": 334 + 28*8, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_book_box":    {"x": 521, "y": 334 + 28*9, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_plant_box":   {"x": 521, "y": 334 + 28*10, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": 521, "y": 334 + 28*11, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": 521, "y": 334 + 28*12, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    
    "item_styler":      {"x": 806, "y": 334, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": 806, "y": 334 + 28*1, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": 806, "y": 334 + 28*2, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": 806, "y": 334 + 28*3, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": 806, "y": 334 + 28*4, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": 806, "y": 334 + 28*5, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": 806, "y": 334 + 28*6, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": 806, "y": 334 + 28*8, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_angle_shelf": {"x": 806, "y": 334 + 28*9, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": 806, "y": 334 + 28*10, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": 806, "y": 334 + 28*11, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": 806, "y": 334 + 28*12, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "total_moving_basic_fee": {"x": 865, "y": 718, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee":      {"x": 865, "y": 746, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # Y 조정
    "deposit_amount":   {"x": 865, "y": 774, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # Y 조정
    "remaining_balance":{"x": 865, "y": 802, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},# Y 조정
    "grand_total":      {"x": 865, "y": 840, "size": 20, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # Y 조정
}

ITEM_KEY_MAP = {
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장(5단)": "item_drawer_5dan",
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door", "김치냉장고(일반형)": "item_kimchi_fridge_normal",
    "김치냉장고(스탠드형)": "item_kimchi_fridge_stand", "소파(3인용)": "item_sofa_3seater",
    "소파(1인용)": "item_sofa_1seater", "식탁(4인)": "item_dining_table",
    "에어컨": "item_ac_left", "거실장": "item_living_room_cabinet",
    "피아노(디지털)": "item_piano_digital", "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer", "중역책상": "item_executive_desk", "책상&의자": "item_desk",
    "책장": "item_bookshelf", "의자": "item_chair", "테이블": "item_table",
    "담요": "item_blanket", "바구니": "item_basket", 
    "중박스": "item_medium_box", "책바구니": "item_book_box",
    "화분": "item_plant_box", "옷행거": "item_clothes_box",
    "이불박스": "item_duvet_box", "스타일러": "item_styler", "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic", "복합기": "item_copier",
    "TV(45인치)": "item_tv_45", "TV다이": "item_tv_stand", "벽걸이": "item_wall_mount_item",
    "금고": "item_safe", "앵글": "item_angle_shelf", "파티션": "item_partition",
    "5톤진입": "item_5ton_access", # data.py에 해당 품목이 정의되어 있어야 함
    "에어컨 실외기": "item_ac_right", # data.py에 해당 품목이 정의되어 있어야 함
}

def get_text_dimensions(text_string, font):
    """Pillow 10.0.0 이전/이후 버전에 호환되는 텍스트 크기 측정 함수"""
    if hasattr(font, 'getbbox'): # Pillow 9.2.0+ (getbbox는 (left, top, right, bottom) 튜플 반환)
        bbox = font.getbbox(text_string)
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1] # 실제 텍스트 높이
        # ascent, descent = font.getmetrics() # 더 정확한 높이 계산 시 필요
        # height = ascent + descent
    elif hasattr(font, 'getmask'): # Pillow < 9.2.0
        width, height = font.getmask(text_string).size
    else: # 아주 오래된 버전 또는 예외 상황
        try:
            width, height = font.getsize(text_string) # 이 메소드는 제거됨
        except AttributeError: # getsize도 없는 매우 예외적인 경우
             ascent, descent = font.getmetrics()
             height = ascent + descent
             width = font.getlength(text_string) if hasattr(font, 'getlength') else len(text_string) * height / 2 # 매우 대략적인 추정

    return width, height

def _get_font(font_type="regular", size=12):
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD
        else:
            print(f"Warning: Bold font file not found at {FONT_PATH_BOLD}. Using regular font {FONT_PATH_REGULAR} as bold.")
    
    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError:
        print(f"Warning: Font file not found at {font_path_to_use}. Trying to load default PIL font.")
        try:
            return ImageFont.load_default(size=size) # Pillow 10.0.0 부터 size 인자 지원
        except TypeError: 
             return ImageFont.load_default()
        except Exception as e_pil_font:
            print(f"Error loading default PIL font: {e_pil_font}")
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
            current_line_width, _ = get_text_dimensions(current_line + word + " ", font) if current_line else get_text_dimensions(word + " ", font)

            if word_width > max_width: # 단어 하나가 최대 너비보다 긴 경우 (강제 분할 필요)
                if current_line: lines.append(current_line.strip())
                # 매우 긴 단어 처리 (예: 글자 단위로 잘라서 여러 줄로 만듦)
                temp_word_line = ""
                for char_idx, char in enumerate(word):
                    char_width, _ = get_text_dimensions(temp_word_line + char, font)
                    if char_width <= max_width:
                        temp_word_line += char
                    else:
                        lines.append(temp_word_line)
                        temp_word_line = char
                if temp_word_line: lines.append(temp_word_line)
                current_line = "" # 다음 단어부터 새 줄
                continue

            if current_line_width <= max_width:
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
    _, typical_height = get_text_dimensions("A", font) # 기준 높이

    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1:
            current_y += int(typical_height * line_spacing_factor)
            continue
        
        text_width, _ = get_text_dimensions(line, font)
        
        actual_x = x
        if align == "right":
            actual_x = x - text_width
        elif align == "center":
            actual_x = x - text_width / 2
        
        # y 좌표는 텍스트의 상단을 기준으로 함. Pillow 9.0.0 부터 anchor 옵션 사용 가능
        # draw.text((actual_x, current_y), line, font=font, fill=color, anchor="la") # 'la'는 left-ascent
        draw.text((actual_x, current_y), line, font=font, fill=color) 
        current_y += int(typical_height * line_spacing_factor)
        first_line = False
    return current_y

def _format_currency(amount_val):
    if amount_val is None: return "0 원"
    try:
        num_str = str(amount_val).replace(",", "").strip()
        if not num_str: return "0 원"
        num = int(float(num_str))
        return f"{num:,} 원"
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
        error_font = _get_font(size=24)
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, 480, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, 520, error_font, (255,0,0), "center")

    customer_name = state_data.get('customer_name', '')
    customer_phone = state_data.get('customer_phone', '')
    moving_date_obj = state_data.get('moving_date')
    moving_date_str = moving_date_obj.strftime('%Y-%m-%d') if isinstance(moving_date_obj, date) else str(moving_date_obj)
    quote_date_str = date.today().strftime('%Y-%m-%d')
    from_location = state_data.get('from_location', '')
    to_location = state_data.get('to_location', '')
    from_floor = str(state_data.get('from_floor', '')) + "층" if str(state_data.get('from_floor', '')).strip() else ""
    to_floor = str(state_data.get('to_floor', '')) + "층" if str(state_data.get('to_floor', '')).strip() else ""
    vehicle_type = state_data.get('final_selected_vehicle', '')
    workers_male = str(personnel_info.get('final_men', '0'))
    workers_female = str(personnel_info.get('final_women', '0'))

    total_moving_expenses_f22 = 0
    storage_fee_j22 = 0
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
        "total_moving_basic_fee": _format_currency(total_moving_expenses_f22),
        "storage_fee": _format_currency(storage_fee_j22) if storage_fee_j22 > 0 else " ",
        "deposit_amount": _format_currency(deposit_amount),
        "remaining_balance": _format_currency(remaining_balance_num),
        "grand_total": _format_currency(grand_total_num),
    }
    
    # 오전/오후 체크 (실제 state_data에 이 정보가 어떤 키로 저장되는지에 따라 수정 필요)
    # 예시: 'move_time_preference' 키가 있고 값이 '오전' 또는 '오후' 라고 가정
    # if state_data.get('move_time_preference') == '오전':
    #      data_to_draw["move_time_am_checkbox"] = FIELD_MAP["move_time_am_checkbox"].get("text_if_true", "V")
    # elif state_data.get('move_time_preference') == '오후':
    #      data_to_draw["move_time_pm_checkbox"] = FIELD_MAP["move_time_pm_checkbox"].get("text_if_true", "V")


    try:
        import utils 
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
    except Exception as e_item:
        print(f"Error processing item quantities for image: {e_item}")


    for key, M in FIELD_MAP.items():
        # 체크박스용 텍스트는 data_to_draw에 이미 'V' 또는 기본값(None)이 설정되어 있을 것으로 기대
        text_content = data_to_draw.get(key, M.get("text")) # 기본 텍스트 (예: 체크박스 기본 모양 "□")
        
        if key.endswith("_checkbox") and data_to_draw.get(key) != M.get("text_if_true"): # 체크 안된 경우
            text_content = M.get("text", "□") # 기본 모양 (예: 빈 네모)
        elif key.endswith("_checkbox"): # 체크 된 경우
             text_content = M.get("text_if_true", "V")


        if text_content is not None : 
            font_obj = _get_font(font_type=M.get("font", "regular"), size=M.get("size", 12))
            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width")
            line_spacing_factor = M.get("line_spacing_factor", 1.2)
            
            _draw_text_with_alignment(draw, str(text_content), M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

if __name__ == '__main__':
    print("image_generator.py test mode")
    if not (os.path.exists(FONT_PATH_REGULAR) and os.path.exists(FONT_PATH_BOLD)):
        print(f"Error: Test requires fonts at {FONT_PATH_REGULAR} and {FONT_PATH_BOLD}")
    if not os.path.exists(BACKGROUND_IMAGE_PATH):
        print(f"Error: Test requires background image at {BACKGROUND_IMAGE_PATH}")
    else:
        sample_state_data = {
            'customer_name': '홍길동 테스트 고객', 'customer_phone': '010-1111-2222',
            'moving_date': date(2025, 8, 20),
            'from_location': '서울시 서초구 강남대로 123, XYZ 아파트 101동 1502호 (출발지 상세주소)', 
            'to_location': '경기도 수원시 영통구 광교중앙로 456, ABC 오피스텔 203동 707호 (도착지 주소가 길어질 경우)',
            'from_floor': '15', 'to_floor': '7',
            'final_selected_vehicle': '5톤 카고 트럭',
            'deposit_amount': 200000,
            'base_move_type': "가정 이사 🏠",
            'qty_가정 이사 🏠_주요 품목_장롱': 12,
            'qty_가정 이사 🏠_주요 품목_더블침대': 1,
            'qty_가정 이사 🏠_기타_스타일러': 1,
            'qty_가정 이사 🏠_포장 자재 📦_바구니': 30,
            # 'move_time_preference': '오후', # '오전' 또는 '오후'로 설정하여 체크박스 테스트
        }
        sample_personnel_info = {'final_men': 4, 'final_women': 0}
        sample_calculated_cost_items = [
            ('기본 운임', 1500000, '5톤 기준'),
            ('출발지 사다리차', 180000, ''),
            ('도착지 계단 작업', 50000, ''), # FIELD_MAP에 없으므로 그려지지 않음
            ('보관료', 0, ''),
            ('조정 금액', -50000, '프로모션 할인')
        ]
        sample_total_cost_overall = 1500000 + 180000 + 50000 - 50000 
        
        try:
            import data
            import utils
            img_data = create_quote_image(sample_state_data, sample_calculated_cost_items, sample_total_cost_overall, sample_personnel_info)
            if img_data:
                output_filename = "generated_final_quote_image.png"
                with open(output_filename, "wb") as f:
                    f.write(img_data)
                print(f"Test image '{output_filename}' created successfully. Please check.")
                if os.name == 'nt': # Windows에서 자동으로 이미지 열기
                    try: os.startfile(output_filename)
                    except: print("Could not auto-open image.")
            else:
                print("Test image creation failed.")
        except Exception as e_test:
            print(f"Error during test: {e_test}")
            traceback.print_exc()
