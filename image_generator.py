# image_generator.py
from PIL import Image, ImageDraw, ImageFont
import os
import io
from datetime import date
import math
import traceback # 에러 로깅을 위해 추가

# 애플리케이션의 루트 디렉토리를 기준으로 경로 설정 (streamlit 앱 실행 위치 기준)
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # 앱의 루트 폴더로 가정
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # image_generator.py와 같은 폴더로 가정

BACKGROUND_IMAGE_PATH = os.path.join(BASE_DIR, "final.png")
FONT_PATH_REGULAR = os.path.join(BASE_DIR, "NanumGothic.ttf")
FONT_PATH_BOLD = os.path.join(BASE_DIR, "NanumGothicBold.ttf")

TEXT_COLOR_DEFAULT = (20, 20, 20)
TEXT_COLOR_YELLOW_BG = (0,0,0)

# 좌표 계산용 기준값
item_y_start_val = 334
item_y_spacing_val = 28.8 # 항목 간 기본 Y 간격
item_font_size_val = 15
item_x_col1_val = 226
item_x_col2_baskets_val = 491
item_x_col2_others_val = 491 # "책상" 등의 X 좌표로 사용됨
item_x_col3_val = 756

vehicle_x_val = 90
vehicle_y_val = int(275 + item_y_spacing_val) # 대략 304

costs_section_x_align_right_val = 326

# --- FIELD_MAP 정의 시 사다리 비용 위치 계산 ---
_y_living_room_cabinet_for_calc = 677  # 거실장 Y (이전 수정값)
_y_sofa_3seater_for_calc = 549         # 소파3 Y (이전 수정값)

# 출발지 사다리 요금 Y 좌표
from_ladder_fee_y_val_calc = _y_living_room_cabinet_for_calc + abs(_y_sofa_3seater_for_calc - _y_living_room_cabinet_for_calc) # 677 + 128 = 805

# 도착지 사다리 요금 Y 좌표
to_ladder_fee_y_val_calc = from_ladder_fee_y_val_calc + item_y_spacing_val # 805 + 28.8 = 833.8

# 지방 사다리 추가요금 Y 좌표 (도착지 사다리 요금 아래)
regional_ladder_surcharge_y_val_calc = to_ladder_fee_y_val_calc + item_y_spacing_val # 833.8 + 28.8 = 862.6

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
    "item_sofa_3seater":{"x": item_x_col1_val, "y": _y_sofa_3seater_for_calc, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_1seater":{"x": item_x_col1_val, "y": 581, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_dining_table":{"x": item_x_col1_val, "y": 612, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": item_x_col1_val, "y": 645, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": item_x_col1_val, "y": _y_living_room_cabinet_for_calc, "size": item_font_size_val, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
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

    "fee_value_next_to_ac_right": {"x": costs_section_x_align_right_val, "y": 680, "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},
    "main_fee_yellow_box": {"x": costs_section_x_align_right_val, "y": 775, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "storage_fee":      {"x": costs_section_x_align_right_val, "y": 1305, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # 이 Y값은 양식에 따라 크게 달라질 수 있음
    "deposit_amount":   {"x": costs_section_x_align_right_val, "y": 1036, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # 이 Y값은 양식에 따라 크게 달라질 수 있음
    "remaining_balance":{"x": costs_section_x_align_right_val, "y": 998, "size": 21, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"}, # 이 Y값은 양식에 따라 크게 달라질 수 있음
    "grand_total":      {"x": costs_section_x_align_right_val, "y": 861, "size": 22, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},

    "from_ladder_fee":  {"x": costs_section_x_align_right_val, "y": int(from_ladder_fee_y_val_calc), "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right", "prefix": "출발지 사다리 요금: "},
    "to_ladder_fee":    {"x": costs_section_x_align_right_val, "y": int(to_ladder_fee_y_val_calc),   "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right", "prefix": "도착지 사다리 요금: "},
    "regional_ladder_surcharge_display": {"x": costs_section_x_align_right_val, "y": int(regional_ladder_surcharge_y_val_calc), "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right", "prefix": "지방 사다리 추가: "},
}

ITEM_KEY_MAP = {
    # data.py의 품목명 (키) : FIELD_MAP의 키 (값)
    # 이 매핑은 data.py의 최종 품목 목록과 FIELD_MAP의 키를 기준으로 정확하게 일치시켜야 합니다.
    "장롱": "item_jangrong", "더블침대": "item_double_bed",
    "서랍장": "item_drawer_5dan", # data.py에 '서랍장'이 있고, FIELD_MAP에 'item_drawer_5dan'이 해당 위치를 나타낸다고 가정
    "서랍장(3단)": "item_drawer_3dan", "4도어 냉장고": "item_fridge_4door",
    "김치냉장고(일반형)": "item_kimchi_fridge_normal", "김치냉장고(스탠드형)": "item_kimchi_fridge_stand",
    "소파(3인용)": "item_sofa_3seater", "소파(1인용)": "item_sofa_1seater",
    "식탁(4인)": "item_dining_table", # data.py에 '식탁(4인)'이 있다고 가정
    "에어컨": "item_ac_left", # data.py에 '에어컨'이 있고, FIELD_MAP의 'item_ac_left'가 해당 위치
    "거실장": "item_living_room_cabinet", # data.py에서 "장식장"이 "거실장"으로 변경되었음을 반영
    "피아노(디지털)": "item_piano_digital",
    "세탁기 및 건조기": "item_washing_machine",
    "컴퓨터&모니터": "item_computer", # data.py에서 "오디오 및 스피커"를 대체했음을 반영
    "중역책상": "item_executive_desk", "책상&의자": "item_desk", "책장": "item_bookshelf",
    "의자": "item_chair", "테이블": "item_table", "담요": "item_blanket",
    "바구니": "item_basket", "중박스": "item_medium_box",
    "중대박스": "item_large_box", # data.py에 '중대박스' 품목이 존재하고, FIELD_MAP에 item_large_box가 해당 위치일 경우
    "책바구니": "item_book_box",
    "화분": "item_plant_box", # data.py에 '화분'이 있고, FIELD_MAP에 item_plant_box가 해당 위치일 경우
    "옷행거": "item_clothes_box",# data.py에 '옷행거'가 있고, FIELD_MAP에 item_clothes_box가 해당 위치일 경우
    # "이불박스": "item_duvet_box", # data.py에 '이불박스'가 있고, FIELD_MAP에 item_duvet_box가 해당 위치일 경우
    "스타일러": "item_styler", "안마기": "item_massage_chair",
    "피아노(일반)": "item_piano_acoustic", "복합기": "item_copier", "TV(45인치)": "item_tv_45",
    "TV다이": "item_tv_stand", "벽걸이": "item_wall_mount_item", "금고": "item_safe",
    "앵글": "item_angle_shelf", "파티션": "item_partition", "5톤진입": "item_5ton_access",
    # "에어컨 실외기": "item_ac_right", # data.py에 '에어컨 실외기'가 있고, FIELD_MAP에 item_ac_right가 해당 위치일 경우
}
# ITEM_KEY_MAP 보강 (data.py와 FIELD_MAP을 비교하여 누락된 항목이 있다면 추가)
# 예: data.py에 "품목A"가 있고 FIELD_MAP에 "item_A_field"가 있다면 ITEM_KEY_MAP["품목A"] = "item_A_field" 추가


def get_text_dimensions(text_string, font):
    if not text_string: return 0,0
    if hasattr(font, 'getbbox'): # Pillow 9.2.0+
        try:
            bbox = font.getbbox(str(text_string))
            width = bbox[2] - bbox[0]
            ascent, descent = font.getmetrics() # 높이 계산 개선
            height = ascent + descent # 실제 폰트 높이
        except Exception: # Fallback for older Pillow or other issues
            if hasattr(font, 'getlength'): width = font.getlength(str(text_string)) # Pillow 10.0.0+
            else: width = len(str(text_string)) * (font.size if hasattr(font, 'size') else 10) / 2 # 근사치
            ascent, descent = font.getmetrics()
            height = ascent + descent
    elif hasattr(font, 'getmask'): # Older Pillow
        try:
            width, height = font.getmask(str(text_string)).size
        except Exception: # Fallback
            ascent, descent = font.getmetrics()
            height = ascent + descent
            width = font.getlength(str(text_string)) if hasattr(font, 'getlength') else len(str(text_string)) * height / 2
    else: # Very basic fallback
        ascent, descent = font.getmetrics()
        height = ascent + descent
        if hasattr(font, 'getlength'): # Pillow 10.0.0+ getlength
            width = font.getlength(str(text_string))
        else: # 더 기본적인 근사치
            width = len(str(text_string)) * height / 2 # height가 글자 높이와 유사하다고 가정
    return width, height


def _get_font(font_type="regular", size=12):
    font_path_to_use = FONT_PATH_REGULAR
    if font_type == "bold":
        if os.path.exists(FONT_PATH_BOLD):
            font_path_to_use = FONT_PATH_BOLD
        # else: # Bold 폰트가 없으면 Regular 폰트를 그대로 사용 (경고는 create_quote_image에서 한 번만)
            # pass

    try:
        return ImageFont.truetype(font_path_to_use, size)
    except IOError: # 폰트 파일 못 찾는 경우 등
        # print(f"Warning: Font file '{font_path_to_use}' not found or cannot be opened. Using default PIL font.")
        try:
            return ImageFont.load_default(size=size) # Pillow 10.0.0부터 size 인자 지원
        except TypeError: # 이전 버전 호환
            return ImageFont.load_default()
        except Exception as e_pil_font: # 기타 PIL 폰트 로드 오류
            print(f"Error loading default PIL font: {e_pil_font}")
            raise # 더 이상 진행 불가 시 에러 발생
    except Exception as e_font: # 기타 폰트 관련 예외
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
            word_width, _ = get_text_dimensions(word, font) # Pillow 9.2.0 부터 getbbox 사용 권장
            # 현재 줄에 단어를 추가했을 때의 예상 너비
            current_line_plus_word_width, _ = get_text_dimensions(current_line + word + " ", font) if current_line else get_text_dimensions(word + " ", font)

            # 단어 자체가 최대 너비를 초과하는 경우 (한 글자씩 나눠서 줄바꿈 시도 - 매우 긴 중국어 등)
            if word_width > max_width and len(word) > 1: # 단어가 한 글자 이상일 때만 분할 시도
                if current_line: # 이전까지의 줄 추가
                    lines.append(current_line.strip())
                # 긴 단어 분할
                temp_word_line = ""
                for char_idx, char in enumerate(word):
                    temp_word_line_plus_char_width, _ = get_text_dimensions(temp_word_line + char, font)
                    if temp_word_line_plus_char_width <= max_width:
                        temp_word_line += char
                    else:
                        lines.append(temp_word_line) # 채워진 부분 추가
                        temp_word_line = char # 새 줄은 현재 문자로 시작
                if temp_word_line: # 남은 부분 추가
                    lines.append(temp_word_line)
                current_line = "" # 현재 줄 리셋
                continue # 다음 단어로

            # 현재 줄에 단어를 추가할 수 있는지 확인
            if current_line_plus_word_width <= max_width:
                current_line += word + " "
            else: # 추가할 수 없으면, 현재 줄을 확정하고 새 줄 시작
                if current_line: # 빈 줄이 아닐 경우에만 추가
                    lines.append(current_line.strip())
                current_line = word + " " # 새 줄은 현재 단어로 시작
        
        if current_line.strip(): # 마지막 남은 줄 추가
            lines.append(current_line.strip())
        
        if not lines and text: # max_width가 있지만 줄바꿈이 필요 없었거나, 단일 단어가 너무 길어서 분할 못한 경우
            lines.append(text)
            
    else: # max_width가 없으면 '\n' 기준으로만 줄바꿈
        lines.extend(text.split('\n'))

    current_y = y
    first_line = True
    # Pillow 9.1.0 부터 getmetrics(), 9.2.0 부터 getbbox()
    # font.getsize("A")[1] 대신 getmetrics 사용 권장
    _, typical_char_height = get_text_dimensions("A", font) # 정확한 높이 계산

    for line in lines:
        if not line.strip() and not first_line and len(lines) > 1: # 빈 줄이고 첫 줄이 아니며 여러 줄일 때만 간격 적용
            current_y += int(typical_char_height * line_spacing_factor)
            continue
        
        text_width, _ = get_text_dimensions(line, font)
        actual_x = x
        if align == "right":
            actual_x = x - text_width
        elif align == "center":
            actual_x = x - text_width / 2
        
        # anchor="lt" 사용 (텍스트의 왼쪽 상단 기준)
        draw.text((actual_x, current_y), line, font=font, fill=color, anchor="lt")
        current_y += int(typical_char_height * line_spacing_factor)
        first_line = False
    return current_y


def _format_currency(amount_val):
    if amount_val is None: return "0" # 또는 "" 빈 문자열 반환도 고려
    try:
        # 먼저 숫자로 변환 시도 (문자열 입력 대비)
        num_val = float(str(amount_val).replace(",", "").strip())
        if not num_val and num_val != 0: return "0" # 빈 문자열이나 None 등으로 변환된 경우
        
        # 정수로 변환하여 천단위 쉼표 포맷
        num = int(num_val)
        return f"{num:,}"
    except ValueError: # 숫자 변환 실패 시
        return str(amount_val) # 원본 값 문자열로 반환 (또는 "0" 이나 에러 표시)


def create_quote_image(state_data, calculated_cost_items, total_cost_overall, personnel_info):
    try:
        img = Image.open(BACKGROUND_IMAGE_PATH).convert("RGBA")
        draw = ImageDraw.Draw(img)
    except FileNotFoundError:
        print(f"Error: Background image not found at {BACKGROUND_IMAGE_PATH}")
        img = Image.new('RGB', (900, 1400), color = 'white') # 높이 약간 늘림 (사다리 요금 등 추가 공간 고려)
        draw = ImageDraw.Draw(img)
        try: error_font = _get_font(size=24)
        except: error_font = ImageFont.load_default() # size 인자 없이 호출
        _draw_text_with_alignment(draw, "배경 이미지 파일을 찾을 수 없습니다!", 450, 480, error_font, (255,0,0), "center")
        _draw_text_with_alignment(draw, BACKGROUND_IMAGE_PATH, 450, 520, error_font, (255,0,0), "center")
    except Exception as e_bg:
        print(f"Error loading background image: {e_bg}")
        # 여기서도 대체 이미지 생성 또는 에러 반환
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

    # 비용 항목에서 데이터 추출
    total_moving_expenses_f22 = 0 # 순수 이사 비용 (사다리 등 주요 작업비 제외)
    storage_fee_j22 = 0
    option_ac_cost_val = 0
    from_ladder_fee_val = 0
    to_ladder_fee_val = 0
    regional_ladder_surcharge_val = 0

    if calculated_cost_items and isinstance(calculated_cost_items, list):
        for item_l, item_a, _ in calculated_cost_items:
            label = str(item_l)
            try: amount = int(float(item_a or 0)) # float으로 먼저 변환 후 int
            except (ValueError, TypeError): amount = 0

            if label == '기본 운임' or label == '날짜 할증' or label == '장거리 운송료' or \
               label == '폐기물 처리' or label == '폐기물 처리(톤)' or \
               label == '추가 인력' or label == '경유지 추가요금' or "조정 금액" in label:
                total_moving_expenses_f22 += amount
            elif label == '보관료':
                storage_fee_j22 = amount
            elif label == '에어컨 설치 및 이전 비용':
                option_ac_cost_val = amount
            elif label == '출발지 사다리차' or label == '출발지 스카이 장비':
                from_ladder_fee_val += amount
            elif label == '도착지 사다리차' or label == '도착지 스카이 장비':
                to_ladder_fee_val += amount
            elif label == '지방 사다리 추가요금':
                regional_ladder_surcharge_val += amount

    deposit_amount_raw = state_data.get('deposit_amount', state_data.get('tab3_deposit_amount', 0)) # tab3_접두어는 state_manager에서 저장용으로 사용
    deposit_amount = int(float(deposit_amount_raw or 0))
    grand_total_num = int(float(total_cost_overall or 0))
    remaining_balance_num = grand_total_num - deposit_amount

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
        "fee_value_next_to_ac_right": _format_currency(option_ac_cost_val) if option_ac_cost_val > 0 else "",
        "main_fee_yellow_box": _format_currency(total_moving_expenses_f22),
        "storage_fee": _format_currency(storage_fee_j22) if storage_fee_j22 != 0 else "", # 0일때 빈칸
        "deposit_amount": _format_currency(deposit_amount),
        "remaining_balance": _format_currency(remaining_balance_num),
        "grand_total": _format_currency(grand_total_num),
        "from_ladder_fee": _format_currency(from_ladder_fee_val) if from_ladder_fee_val != 0 else "", # 0일때 빈칸
        "to_ladder_fee": _format_currency(to_ladder_fee_val) if to_ladder_fee_val != 0 else "", # 0일때 빈칸
        "regional_ladder_surcharge_display": _format_currency(regional_ladder_surcharge_val) if regional_ladder_surcharge_val != 0 else "", # 0일때 빈칸
    }

    move_time_option_from_state = state_data.get('move_time_option_key_in_state', state_data.get('move_time_option')) # 호환성
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

        for key_in_fieldmap_vals in ITEM_KEY_MAP.values(): # FIELD_MAP의 모든 item_ 키에 대해
            if key_in_fieldmap_vals.startswith("item_") and key_in_fieldmap_vals not in data_to_draw :
                 data_to_draw[key_in_fieldmap_vals] = "" # 기본값으로 빈 문자열 설정 (수량 0일 때 표시 안 함)

        for data_py_item_name, field_map_key_from_map in ITEM_KEY_MAP.items():
            found_section = None
            if isinstance(item_defs_for_current_type, dict):
                for section_name, item_list_in_section in item_defs_for_current_type.items():
                    if isinstance(item_list_in_section, list) and data_py_item_name in item_list_in_section:
                        found_section = section_name
                        break
            if found_section: # data.py의 item_definitions에 해당 품목이 정의된 경우
                # state_data에서 수량 가져오기
                widget_key = f"qty_{current_move_type}_{found_section}_{data_py_item_name}"
                qty_raw = state_data.get(widget_key, 0) # qty_raw가 None일 수 있음
                qty_int = 0
                try:
                    if qty_raw is not None and str(qty_raw).strip() != "":
                        qty_int = int(float(str(qty_raw))) # 문자열이면 float으로 먼저 변환
                except ValueError:
                    qty_int = 0 # 변환 실패시 0

                if qty_int > 0:
                    text_val = str(qty_int)
                    if data_py_item_name == "장롱":
                        try: text_val = f"{(float(qty_int) / 3.0):.1f}"
                        except: text_val = str(qty_int) # 오류 시 원래 수량 표시
                    data_to_draw[field_map_key_from_map] = text_val
                # else: 수량이 0이면 data_to_draw에 해당 키 추가 안 함 (위에서 ""로 초기화됨)
            # else:
                # print(f"Debug: Item '{data_py_item_name}' (mapped to '{field_map_key_from_map}') not found in current item definitions or section for type '{current_move_type}'. It will not be displayed.")
    except ImportError:
        print("Error: data.py module could not be imported in create_quote_image.")
    except Exception as e_item:
        print(f"Error processing item quantities for image: {e_item}")
        traceback.print_exc()


    for key, M_raw in FIELD_MAP.items():
        M = {} # 각 필드맵 항목에 대한 파싱된 설정을 저장
        for k_map, v_map in M_raw.items():
            if k_map in ["x", "y", "size", "max_width"]:
                try: M[k_map] = int(v_map)
                except (ValueError, TypeError) : M[k_map] = v_map
            else: M[k_map] = v_map

        text_content_value = data_to_draw.get(key) # data_to_draw에서 현재 키에 해당하는 값을 가져옴
        final_text_to_draw = "" # 실제로 그려질 최종 텍스트

        if key.endswith("_checkbox"):
            final_text_to_draw = data_to_draw.get(key, M.get("text_if_false", "□"))
        # 값이 존재하고 (None이 아니고, 공백 문자열이 아님)
        elif text_content_value is not None and str(text_content_value).strip() != "":
            prefix_text = M.get("prefix", "") # FIELD_MAP에 정의된 접두사 가져오기
            final_text_to_draw = f"{prefix_text}{text_content_value}" # 접두사와 값 결합
        # 값이 없거나(None 또는 빈 문자열)라도, prefix가 있고 특정 키 (예: 사다리 요금)인 경우 prefix만 표시하고 싶다면 추가 조건 필요
        # 현재 로직: 값이 있을 때만 prefix와 함께 그림. 값이 없으면 아무것도 그리지 않음.

        if final_text_to_draw.strip() != "": # 최종적으로 그릴 내용이 있을 때만
            font_obj = _get_font(font_type=M.get("font", "regular"), size=M.get("size", 12))
            color_val = M.get("color", TEXT_COLOR_DEFAULT)
            align_val = M.get("align", "left")
            max_w_val = M.get("max_width") # FIELD_MAP에서 max_width 가져오기
            line_spacing_factor = M.get("line_spacing_factor", 1.15) # 줄 간격

            # _draw_text_with_alignment 함수에 key 전달 (선택적, 디버깅용)
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
        # 테스트를 위한 샘플 데이터 (실제 애플리케이션의 state_data 구조와 유사하게)
        sample_state_data = {
            'customer_name': '김테스트 고객님', 'customer_phone': '010-1234-5678',
            'moving_date': date(2025, 6, 15),
            'from_location': '서울시 강남구 테헤란로 123, 출발아파트 101동 701호 (출발동)',
            'to_location': '경기도 성남시 분당구 판교역로 456, 도착빌라 202동 1001호 (도착동)',
            'from_floor': '7', 'to_floor': '10',
            'final_selected_vehicle': '5톤',
            'deposit_amount': 100000, # 또는 'tab3_deposit_amount': 100000
            'base_move_type': "가정 이사 🏠",
            'qty_가정 이사 🏠_주요 품목_장롱': 9,
            'qty_가정 이사 🏠_주요 품목_더블침대': 1,
            'qty_가정 이사 🏠_주요 품목_서랍장': 2, # data.py의 '서랍장'
            'qty_가정 이사 🏠_기타_서랍장(3단)': 1,
            'qty_가정 이사 🏠_주요 품목_4도어 냉장고': 1,
            'qty_가정 이사 🏠_주요 품목_거실장': 1, # data.py의 '거실장'
            'qty_가정 이사 🏠_기타_컴퓨터&모니터': 2, # data.py의 '컴퓨터&모니터'
            'qty_가정 이사 🏠_주요 품목_소파(3인용)': 1,
            'qty_가정 이사 🏠_기타_소파(1인용)': 0, # 수량 0인 경우 표시 안됨
            'qty_가정 이사 🏠_주요 품목_에어컨': 1,
            'qty_가정 이사 🏠_기타_피아노(디지털)': 1,
            'qty_가정 이사 🏠_포장 자재 📦_바구니': 20,
            'qty_가정 이사 🏠_포장 자재 📦_중박스': 10,
            'move_time_option_key_in_state': '오전',
        }
        sample_personnel_info = {'final_men': 3, 'final_women': 1}
        sample_calculated_cost_items = [
            ('기본 운임', 1200000, '5톤 기준'),
            ('출발지 사다리차', 170000, '8~9층, 5톤 기준'),
            ('도착지 사다리차', 180000, '10~11층, 5톤 기준'),
            ('지방 사다리 추가요금', 50000, '수동입력'),
            ('에어컨 설치 및 이전 비용', 150000, '기본 설치'),
            ('조정 금액', -70000, '프로모션 할인') # 음수 조정
        ]
        sample_total_cost_overall = sum(item[1] for item in sample_calculated_cost_items) # 모든 비용 합산

        try:
            # import data # create_quote_image 내부에서 import data as app_data로 변경됨
            img_data = create_quote_image(sample_state_data, sample_calculated_cost_items, sample_total_cost_overall, sample_personnel_info)
            if img_data:
                output_filename = "수정된_견적서_이미지_최종.png"
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
            traceback.print_exc()
