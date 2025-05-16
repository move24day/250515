# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math # ceil 함수 사용을 위해 추가

# --- 설정값 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png") # 사용자가 final.png로 저장한다고 가정
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

# 글자색 기본값
TEXT_COLOR_DEFAULT = (20, 20, 20) # 약간 진한 회색/검정색 (양식에 따라 조정)
TEXT_COLOR_YELLOW_BG = (0,0,0) # 노란 배경 위의 글씨는 검정색이 잘 보임

# --- 필드별 위치 및 스타일 정보 (image_3b75d1.png, 900x1000px 기준 추정치) ---
# (x, y)는 텍스트 시작점. align='right' 시 x는 오른쪽 끝점, align='center' 시 x는 중앙점.
# 폰트 크기는 이미지 해상도와 실제 인쇄/표시 크기에 따라 매우 민감하게 조정 필요.
FIELD_MAP = {
    # 상단 정보 (Y 좌표는 텍스트 베이스라인 기준으로 추정)
    "customer_name":  {"x": 175, "y": 132, "size": 20, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "customer_phone": {"x": 475, "y": 132, "size": 19, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "quote_date":     {"x": 700, "y": 132, "size": 18, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "moving_date":    {"x": 700, "y": 160, "size": 18, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    
    "move_time_am_checkbox":   {"x": 705, "y": 188, "size": 16, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V"},
    "move_time_pm_checkbox":   {"x": 800, "y": 188, "size": 16, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V"},

    "from_location":  {"x": 175, "y": 175, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 400, "line_spacing": 5},
    "to_location":    {"x": 175, "y": 200, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 400, "line_spacing": 5},
    
    "from_floor":     {"x": 225, "y": 247, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "to_floor":       {"x": 225, "y": 275, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "vehicle_type":   {"x": 525, "y": 247, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center", "max_width": 270},
    "workers_male":   {"x": 858, "y": 247, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "workers_female": {"x": 858, "y": 275, "size": 17, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    # 품목 수량 칸 (X: 칸 중앙, Y: 칸 중앙보다 약간 위쪽의 텍스트 베이스라인)
    # 첫번째 열 X: 226, 두번째 열 X: 521, 세번째 열 X: 806
    # 첫번째 행 Y: 334, 각 행 간격 약 28px
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
    # 복합기(두번째) 자리는 이미지에서 비어있음
    "item_safe":        {"x": 806, "y": 334 + 28*8, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_angle_shelf": {"x": 806, "y": 334 + 28*9, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": 806, "y": 334 + 28*10, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": 806, "y": 334 + 28*11, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": 806, "y": 334 + 28*12, "size": 15, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    # 비용 관련 (노란색 영역, 우측 정렬 기준 X 좌표)
    "total_moving_basic_fee": {"x": 865, "y": 715, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee":      {"x": 865, "y": 743, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "deposit_amount":   {"x": 865, "y": 771, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance":{"x": 865, "y": 799, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": 865, "y": 837, "size": 20, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
}

ITEM_KEY_MAP = {
    # 첫번째 열
    "장롱": "item_jangrong", "더블침대": "item_double_bed", "서랍장(5단)": "item_drawer_5dan", # data.py에 "서랍장"만 있을 수 있음
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door", "김치냉장고(일반형)": "item_kimchi_fridge_normal",
    "김치냉장고(스탠드형)": "item_kimchi_fridge_stand", "소파(3인용)": "item_sofa_3seater",
    "소파(1인용)": "item_sofa_1seater", "식탁(4인)": "item_dining_table", # data.py에는 "식탁(4인)", "식탁(6인)" 구분
    "에어컨": "item_ac_left", "거실장": "item_living_room_cabinet", # data.py에는 "장식장"
    "피아노(디지털)": "item_piano_digital", "세탁기 및 건조기": "item_washing_machine",

    # 두번째 열
    "컴퓨터&모니터": "item_computer", "중역책상": "item_executive_desk", "책상&의자": "item_desk", # data.py에는 "책상&의자"
    "책장": "item_bookshelf", "의자": "item_chair", "테이블": "item_table",
    "담요": "item_blanket", "바구니": "item_basket", 
    "중박스": "item_medium_box", "책바구니": "item_book_box", # 이미지에는 "책박스"
    "화분": "item_plant_box", # 이미지에는 "화분박스", data.py에는 "화분"
    "옷행거": "item_clothes_box", # 이미지에는 "옷박스", data.py에는 "옷행거"
    "이불박스": "item_duvet_box",

    # 세번째 열
    "스타일러": "item_styler", "안마기": "item_massage_chair", "피아노(일반)": "item_piano_acoustic", # 이미지에는 "원목피아노"
    "복합기": "item_copier", # 데이터가 없다면, 오디오/스피커?
    "TV(45인치)": "item_tv_45", "TV다이": "item_tv_stand", "벽걸이": "item_wall_mount_item",
    "금고": "item_safe", "앵글": "item_angle_shelf", "파티션": "item_partition",
    # "5톤진입"은 수량 항목이 아닐 수 있음, data.py에 해당 키가 없다면 그리지 않음
    # 에어컨(우측)도 data.py에 별도 키("에어컨 실외기" 등)가 있는지 확인 필요
    "에어컨 실외기": "item_ac_right", # data.py에 이런 키가 있다고 가정, 없다면 다른 처리
}


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
            return ImageFont.load_default(size=size)
        except TypeError: # Older Pillow versions might not support size for load_default
            return ImageFont.load_default()
        except Exception as e_pil_font:
            print(f"Error loading default PIL font: {e_pil_font}")
            raise # 폰트 로드 완전 실패 시 예외 발생


def _draw_text_with_alignment(draw, text, x, y, font, color, align="left", max_width=None, line_spacing_factor=1.2):
    if text is None: text = ""
    text = str(text)
    
    lines = []
    if max_width:
        words = text.split(' ')
        current_line = ""
        for word in words:
            # 단어 자체가 최대 너비를 넘는 경우, 강제로 자르거나 특수 처리 필요 (여기서는 일단 그대로 둠)
            if font.getsize(current_line + word)[0] <= max_width:
                current_line += word + " "
            else:
                if current_line: # 이전 라인이 있으면 추가
                    lines.append(current_line.strip())
                current_line = word + " "
        if current_line.strip():
            lines.append(current_line.strip())
        if not lines and text: # 매우 짧은 텍스트
            lines.append(text)
    else:
        lines.extend(text.split('\n'))

    current_y = y
    first_line = True
    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1: # 중간의 빈 줄은 줄간격만
            current_y += int(font.getsize("A")[1] * line_spacing_factor)
            continue
        
        # Pillow 텍스트 크기 측정 방식 변경 (getsize -> getbbox or getlength)
        if hasattr(font, 'getbbox'): # Pillow 9.2.0+
            # anchor='ls' (left-baseline) 등을 사용하면 y좌표를 베이스라인으로 사용 가능
            # 여기서는 간단히 bbox로 너비만 가져오고, 높이는 getsize("A")로 통일
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
        elif hasattr(font, 'getlength'): # Pillow 10.0.0+
            text_width = font.getlength(line)
        else: # Fallback
            text_width = font.getsize(line)[0]
        
        # 높이는 일관성을 위해 특정 문자로 측정 (getsize는 이제 사용 지양됨)
        # ascent, descent를 사용하는 것이 더 정확하나, 여기서는 간편하게 'A' 사용
        # text_height = font.getsize("A")[1] # 대략적인 한 줄 높이

        # 정확한 텍스트 높이 및 베이스라인 오프셋 계산 (선택적 고급 기능)
        # y 좌표는 텍스트의 상단에 맞춰지도록 가정, 필요시 anchor 옵션 활용
        
        actual_x = x
        if align == "right":
            actual_x = x - text_width
        elif align == "center":
            actual_x = x - text_width / 2
        
        draw.text((actual_x, current_y), line, font=font, fill=color) # anchor 기본값은 'la' (left-ascent)
        current_y += int(font.getsize("A")[1] * line_spacing_factor) # 다음 줄 Y 위치 (줄간격 포함)
        first_line = False
    return current_y


def _format_currency(amount_val):
    if amount_val is None: return "0 원"
    try:
        num_str = str(amount_val).replace(",", "").strip()
        if not num_str: return "0 원" # 빈 문자열 처리
        num = int(float(num_str))
        return f"{num:,} 원"
    except ValueError:
        return str(amount_val) # 변환 실패 시 원본 반환 (오류보다는 원본 표시)

def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA") # RGBA로 열어서 투명도 처리 가능
        draw = ImageDraw.Draw(img)
    except FileNotFoundError:
        print(f"Error: Background image not found at {BACKGROUND_IMAGE_PATH}")
        img = Image.new('RGB', (900, 1000), color = 'white')
        draw = ImageDraw.Draw(img)
        error_font = _get_font(size=24)
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, 480, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, 520, error_font, (255,0,0), "center")
        # return None # 또는 오류 이미지 반환

    # 데이터 준비
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

    # 비용 항목 (excel_filler.py와 동일한 방식으로 집계)
    total_moving_expenses_f22 = 0 # F22: 총괄 이사비용 (작업비,보관료,VAT,카드 제외)
    # departure_work_cost_f23, arrival_work_cost_f24 등은 이미지 양식에 별도 칸 없음
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
            # 출발지/도착지 작업비는 total_moving_expenses_f22에 포함되거나, 양식에 별도 항목 없음

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
    
    # 오전/오후 체크박스 처리 (실제 데이터에 따라 'V' 또는 다른 표시)
    # 예시: state_data에 'move_time_preference': '오전' 이 있다면
    if state_data.get('move_time_preference') == '오전': # 이 키는 예시, 실제 사용하는 키로 변경
         data_to_draw["move_time_am_checkbox"] = "V"
    elif state_data.get('move_time_preference') == '오후':
         data_to_draw["move_time_pm_checkbox"] = "V"


    # 품목 수량 그리기
    try:
        import utils # get_item_qty를 위함 (최상단에 이미 import 되어있다면 생략 가능)
        import data  # data.item_definitions 를 위함 (최상단에 이미 import 되어있다면 생략 가능)
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
                    try: qty_int = int(qty or 0) # Ensure it's an int
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
        text_content = data_to_draw.get(key, M.get("text_if_true") if key.endswith("_checkbox") and data_to_draw.get(key) else M.get("text")) # 기본 텍스트 또는 데이터
        if text_content is not None : # 빈 문자열도 그릴 수 있도록 (예: 체크박스 미선택 시 공백)
            font_obj = _get_font(font_type=M.get("font", "regular"), size=M.get("size", 12))
            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width")
            line_spacing_factor = M.get("line_spacing_factor", 1.2) if max_w_val else 1.0 # max_width 있을때만 줄간격 적용

            _draw_text_with_alignment(draw, str(text_content), M["x"], M["y"], font_obj, color_val, align_val, max_w_val, line_spacing_factor)

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    return img_byte_arr.getvalue()

# --- 테스트용 코드 ---
if __name__ == '__main__':
    print("image_generator.py test mode")
    if not os.path.exists(FONT_PATH_REGULAR) or (not os.path.exists(FONT_PATH_BOLD) and print("Warning: Bold font not found, regular will be used.")):
        print(f"Error: Test requires font at {FONT_PATH_REGULAR} (and optionally {FONT_PATH_BOLD})")
    if not os.path.exists(BACKGROUND_IMAGE_PATH):
        print(f"Error: Test requires background image at {BACKGROUND_IMAGE_PATH}")
    else:
        sample_state_data = {
            'customer_name': '홍길동 테스트', 'customer_phone': '010-8888-9999',
            'moving_date': date(2025, 12, 25),
            'from_location': '서울시 강남구 역삼동 코리아IT아카데미 (출발지 주소 테스트)', 
            'to_location': '경기도 판교시 분당구 삼평동 네이버그린팩토리 (도착지가 아주 긴 경우 테스트 문장입니다)',
            'from_floor': '15', 'to_floor': '2',
            'final_selected_vehicle': '5톤 탑차',
            'deposit_amount': 100000,
            'base_move_type': MOVE_TYPE_OPTIONS[0] if MOVE_TYPE_OPTIONS else "가정 이사 🏠", # 첫번째 이사유형
            'qty_가정 이사 🏠_주요 품목_장롱': 10, # utils.get_item_qty가 참조할 키
            'qty_가정 이사 🏠_주요 품목_더블침대': 2,
            'qty_가정 이사 🏠_기타_컴퓨터&모니터': 1, # ITEM_KEY_MAP 과 일치하는 키로
            'qty_가정 이사 🏠_포장 자재 📦_바구니': 20,
            # 'move_time_preference': '오후', # 오전/오후 테스트용
        }
        sample_personnel_info = {'final_men': 3, 'final_women': 1}
        sample_calculated_cost_items = [
            ('기본 운임', 1200000, '5톤 기준'),
            ('출발지 스카이 장비', 250000, '3시간 기준'),
            ('보관료', 70000, '10일 기준'),
            ('추가 인력', 150000, '남1')
        ]
        sample_total_cost_overall = 1200000 + 250000 + 70000 + 150000 
        
        # 테스트를 위해 data, utils 모듈이 필요할 수 있음 (get_item_qty 내부 로직)
        try:
            import data
            import utils
            img_data = create_quote_image(sample_state_data, sample_calculated_cost_items, sample_total_cost_overall, sample_personnel_info)
            if img_data:
                with open("generated_final_quote_image.png", "wb") as f:
                    f.write(img_data)
                print("Test image 'generated_final_quote_image.png' created successfully.")
                # 생성된 이미지 직접 열기 (Windows)
                # if os.name == 'nt': os.startfile("generated_final_quote_image.png")
            else:
                print("Test image creation failed.")
        except Exception as e_test:
            print(f"Error during test: {e_test}")
            traceback.print_exc()
