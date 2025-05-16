# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math  # ceil 함수 사용을 위해 추가

# --- 설정값 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")  # 사용자가 final.png로 저장한다고 가정
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

# 글자색 기본값
TEXT_COLOR_DEFAULT = (20, 20, 20)  # 약간 진한 회색/검정색 (양식에 따라 조정)
TEXT_COLOR_YELLOW_BG = (0, 0, 0)  # 노란 배경 위의 글씨는 검정색이 잘 보임

# --- 필드별 위치 및 스타일 정보 (900x1000px 기준 수정) ---
# (x, y)는 텍스트 시작점. align='right' 시 x는 오른쪽 끝점, align='center' 시 x는 중앙점.
# 폰트 크기는 이미지 해상도와 실제 인쇄/표시 크기에 따라 매우 민감하게 조정 필요.
FIELD_MAP = {
    # 상단 정보 (Y 좌표는 텍스트 베이스라인 기준으로 추정)
    "customer_name":  {"x": 175, "y": 145, "size": 20, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "customer_phone": {"x": 475, "y": 145, "size": 20, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "quote_date":     {"x": 750, "y": 145, "size": 18, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "moving_date":    {"x": 750, "y": 175, "size": 18, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},

    "move_time_am_checkbox":   {"x": 705, "y": 203, "size": 16, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V"},
    "move_time_pm_checkbox":   {"x": 800, "y": 203, "size": 16, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V"},

    "from_location":  {"x": 165, "y": 190, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 400, "line_spacing": 5},
    "to_location":    {"x": 165, "y": 220, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 400, "line_spacing": 5},

    "from_floor":     {"x": 215, "y": 240, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "to_floor":       {"x": 215, "y": 270, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "vehicle_type":   {"x": 525, "y": 247, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center", "max_width": 270},
    "workers_male":   {"x": 858, "y": 255, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "workers_female": {"x": 858, "y": 285, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    # 품목 수량 칸 (X: 칸 중앙, Y: 칸 중앙보다 약간 위쪽의 텍스트 베이스라인)
    # 첫번째 열 X: 226, 두번째 열 X: 521, 세번째 열 X: 806
    # 첫번째 행 Y: 345, 각 행 간격 30px로 조정
    "item_jangrong":    {"x": 226, "y": 345, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_double_bed":  {"x": 226, "y": 345 + 30*1, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": 226, "y": 345 + 30*2, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_3dan": {"x": 226, "y": 345 + 30*3, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": 226, "y": 345 + 30*4, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_normal": {"x": 226, "y": 345 + 30*5, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": 226, "y": 345 + 30*6, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": 226, "y": 345 + 30*7, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_1seater":{"x": 226, "y": 345 + 30*8, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_dining_table":{"x": 226, "y": 345 + 30*9, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": 226, "y": 345 + 30*10, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": 226, "y": 345 + 30*11, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_digital": {"x": 226, "y": 345 + 30*12, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_washing_machine": {"x": 226, "y": 345 + 30*13, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_computer":    {"x": 521, "y": 345, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_executive_desk": {"x": 521, "y": 345 + 30*1, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": 521, "y": 345 + 30*2, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_bookshelf":   {"x": 521, "y": 345 + 30*3, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": 521, "y": 345 + 30*4, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": 521, "y": 345 + 30*5, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": 521, "y": 345 + 30*6, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_basket":      {"x": 521, "y": 345 + 30*7, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_medium_box":  {"x": 521, "y": 345 + 30*8, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_book_box":    {"x": 521, "y": 345 + 30*9, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_plant_box":   {"x": 521, "y": 345 + 30*10, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": 521, "y": 345 + 30*11, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": 521, "y": 345 + 30*12, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "item_styler":      {"x": 806, "y": 345, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": 806, "y": 345 + 30*1, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": 806, "y": 345 + 30*2, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": 806, "y": 345 + 30*3, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": 806, "y": 345 + 30*4, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": 806, "y": 345 + 30*5, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": 806, "y": 345 + 30*6, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    # 복합기(두번째) 자리는 이미지에서 비어있음
    "item_safe":        {"x": 806, "y": 345 + 30*8, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_angle_shelf": {"x": 806, "y": 345 + 30*9, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": 806, "y": 345 + 30*10, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": 806, "y": 345 + 30*11, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": 806, "y": 345 + 30*12, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    # 비용 관련 (노란색 영역, 우측 정렬 기준 X 좌표)
    "total_moving_basic_fee": {"x": 880, "y": 715, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee":      {"x": 880, "y": 743, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "deposit_amount":   {"x": 880, "y": 771, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance":{"x": 880, "y": 799, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": 880, "y": 837, "size": 20, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
}

ITEM_KEY_MAP = {
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장(5단)": "item_drawer_5dan",
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door", 
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand", 
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater", 
    "식탁(4인)": "item_dining_table", "에어컨": "item_ac_left", 
    "거실장": "item_living_room_cabinet", "피아노(디지털)": "item_piano_digital", 
    "세탁기 및 건조기": "item_washing_machine", "컴퓨터&모니터": "item_computer", 
    "중역책상": "item_executive_desk", "책상&의자": "item_desk", "책장": "item_bookshelf", 
    "의자": "item_chair", "테이블": "item_table", "담요": "item_blanket", 
    "바구니": "item_basket", "중박스": "item_medium_box", "중대박스": "item_large_box", 
    "책바구니": "item_book_box", "화분": "item_plant_box", "옷행거": "item_clothes_box",
    "이불박스": "item_duvet_box", "스타일러": "item_styler", "안마기": "item_massage_chair", 
    "피아노(일반)": "item_piano_acoustic", "복합기": "item_copier", "TV(45인치)": "item_tv_45", 
    "TV다이": "item_tv_stand", "벽걸이": "item_wall_mount_item", "금고": "item_safe", 
    "앵글": "item_angle_shelf", "파티션": "item_partition", "5톤진입": "item_5ton_access", 
    "에어컨 실외기": "item_ac_right", 
    # "에어컨옵션": "fee_value_next_to_ac_right", # create_quote_image에서 직접 매핑
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
        "main_fee_yellow_box": _format_currency(total_moving_expenses_f22), # "이사비용" 레이블 옆
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
        import data 
        current_move_type = state_data.get("base_move_type")
        item_defs_for_current_type = {}
        if hasattr(data, 'item_definitions') and current_move_type in data.item_definitions:
            item_defs_for_current_type = data.item_definitions[current_move_type]

        for key in ITEM_KEY_MAP.values():
            if key.startswith("item_") and key not in data_to_draw : 
                 data_to_draw[key] = ""

        for section_name, item_list_in_section in item_defs_for_current_type.items():
            if not isinstance(item_list_in_section, list): continue
            for item_name_from_data_py in item_list_in_section:
                field_map_key = ITEM_KEY_MAP.get(item_name_from_data_py) 
                if field_map_key: 
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
        sample_state_data = {
            'customer_name': '백선희 고객님', 'customer_phone': '01088405754',
            'moving_date': date(2025, 5, 30),
            'from_location': '화양동 16-56 출발지 주소입니다 길어질 경우를 테스트합니다.', 
            'to_location': '서울시 성동구 금정로5길 10 4층 도착지 주소입니다 이것도 길어지면 어떻게 나오는지 테스트',
            'from_floor': '3', 'to_floor': '42',
            'final_selected_vehicle': '5톤 탑윙바디',
            'deposit_amount': 2300000,
            'base_move_type': "가정 이사 🏠",
            'qty_가정 이사 🏠_주요 품목_장롱': 10,
            'qty_가정 이사 🏠_주요 품목_더블침대': 1,
            'qty_가정 이사 🏠_서랍장(5단)_서랍장(5단)': 1, 
            'qty_가정 이사 🏠_서랍장(3단)_서랍장(3단)': 1, 
            'qty_가정 이사 🏠_4도어 냉장고_4도어 냉장고': 1,
            'qty_가정 이사 🏠_김치냉장고(일반형)_김치냉장고(일반형)': 1,
            'qty_가정 이사 🏠_김치냉장고(스탠드형)_김치냉장고(스탠드형)': 1,
            'qty_가정 이사 🏠_소파(3인용)_소파(3인용)': 1,
            'qty_가정 이사 🏠_소파(1인용)_소파(1인용)': 1,
            'qty_가정 이사 🏠_식탁(4인)_식탁(4인)': 1,
            'qty_가정 이사 🏠_에어컨_에어컨': 1, 
            'qty_가정 이사 🏠_거실장_거실장': 1,
            'qty_가정 이사 🏠_피아노(디지털)_피아노(디지털)': 1,
            'qty_가정 이사 🏠_세탁기 및 건조기_세탁기 및 건조기':1,
            'qty_가정 이사 🏠_포장 자재 📦_바구니': 35,
            'qty_가정 이사 🏠_포장 자재 📦_중박스': 20,
            'qty_가정 이사 🏠_포장 자재 📦_중대박스': 5, 
            'qty_가정 이사 🏠_포장 자재 📦_책바구니': 7, 
            'qty_가정 이사 🏠_기타_스타일러': 1,
            'qty_가정 이사 🏠_기타_안마기': 1,
            'qty_가정 이사 🏠_기타_피아노(일반)': 1,
            'qty_가정 이사 🏠_기타_TV(45인치)': 1,
            'qty_가정 이사 🏠_기타_금고': 1,
            'qty_가정 이사 🏠_기타_에어컨 실외기': 1, 
            'move_time_option_key_in_state': '오후', 
        }
        sample_personnel_info = {'final_men': 3, 'final_women': 0}
        sample_calculated_cost_items = [
            ('기본 운임', 500000, ''), 
            ('에어컨 설치 및 이전 비용', 572000, '파손주의'), # image_6eaa25.png의 에어컨 옆 금액
            ('보관료', 0, ''), 
            ('조정 금액', -50000, '특별 할인')
        ]
        # total_cost_overall은 견적 총액
        sample_total_cost_overall = 4082000 # image_6eaa25.png의 합계 금액
        
        try:
            import data 
            img_data = create_quote_image(sample_state_data, sample_calculated_cost_items, sample_total_cost_overall, sample_personnel_info)
            if img_data:
                output_filename = "generated_final_quote_image_v5_user_feedback.png"
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
