# image_generator.py 의 FIELD_MAP 수정 제안
# (image_6e36be.png 또는 image_6e3984.png 와 같은 900x1000px 이미지를 기준으로 한 대략적인 추정치입니다.)

FIELD_MAP = {
    # 상단 정보
    "customer_name":  {"x": 175, "y": 130, "size": 19, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "customer_phone": {"x": 415, "y": 130, "size": 18, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "quote_date":     {"x": 680, "y": 130, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    "moving_date":    {"x": 680, "y": 161, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left"},
    
    "move_time_am_checkbox":   {"x": 708, "y": 188, "size": 15, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V", "text_if_false": "□"},
    "move_time_pm_checkbox":   {"x": 803, "y": 188, "size": 15, "font": "bold", "color": TEXT_COLOR_DEFAULT, "align": "center", "text_if_true": "V", "text_if_false": "□"},

    "from_location":  {"x": 175, "y": 186, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},
    "to_location":    {"x": 175, "y": 215, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "left", "max_width": 380, "line_spacing_factor": 1.1},
    
    "from_floor":     {"x": 180, "y": 247, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "to_floor":       {"x": 180, "y": 275, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "vehicle_type":   {"x": 525, "y": 247, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center", "max_width": 260},
    "workers_male":   {"x": 858, "y": 247, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "workers_female": {"x": 858, "y": 275, "size": 16, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    # 품목 Y 간격 (기존 29px -> 28.5 또는 28로 약간 줄여볼 수도 있음, 이미지와 비교하며 조정)
    # 여기서는 28.8 정도로 가정 (정수가 아니어도 내부적으로 int 처리됨)
    "item_y_start": 334, 
    "item_y_spacing": 28.8, # 또는 28, 29 등 실제 이미지에 맞춰 조정
    "item_x_col1": 226,
    "item_x_col2_baskets": 491, # 바구니류 X 좌표 (왼쪽으로 이동된)
    "item_x_col2_others": 521,  # 두번째 열 기타 품목 X 좌표
    "item_x_col3": 806,
    "item_font_size": 14,

    # 첫번째 열 품목
    "item_jangrong":    {"x": "{item_x_col1}", "y": "{item_y_start}", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_double_bed":  {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*1", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_5dan": {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*2", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_drawer_3dan": {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*3", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_fridge_4door":{"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*4", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_normal": {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*5", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_kimchi_fridge_stand": {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*6", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_3seater":{"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*7", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_sofa_1seater":{"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*8", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_dining_table":{"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*9", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_left":     {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*10", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_living_room_cabinet": {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*11", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_digital": {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*12", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_washing_machine": {"x": "{item_x_col1}", "y": "{item_y_start} + {item_y_spacing}*13", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    
    # 두번째 열 품목
    "item_computer":    {"x": "{item_x_col2_others}", "y": "{item_y_start}", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_executive_desk": {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*1", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_desk":        {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*2", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_bookshelf":   {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*3", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_chair":       {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*4", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_table":       {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*5", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_blanket":     {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*6", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, 
    "item_basket":      {"x": "{item_x_col2_baskets}", "y": "{item_y_start} + {item_y_spacing}*7", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, 
    "item_medium_box":  {"x": "{item_x_col2_baskets}", "y": "{item_y_start} + {item_y_spacing}*8", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, 
    "item_large_box":   {"x": "{item_x_col2_baskets}", "y": "{item_y_start} + {item_y_spacing}*9", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"}, 
    "item_book_box":    {"x": "{item_x_col2_baskets}", "y": "{item_y_start} + {item_y_spacing}*10", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_plant_box":   {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*11", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_clothes_box": {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*12", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_duvet_box":   {"x": "{item_x_col2_others}", "y": "{item_y_start} + {item_y_spacing}*13", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    
    # 세번째 열 품목
    "item_styler":      {"x": "{item_x_col3}", "y": "{item_y_start}", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_massage_chair":{"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*1", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_piano_acoustic":{"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*2", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_copier":      {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*3", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_45":       {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*4", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_tv_stand":    {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*5", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_wall_mount_item": {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*6", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_safe":        {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*8", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_angle_shelf": {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*9", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_partition":   {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*10", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_5ton_access": {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*11", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},
    "item_ac_right":    {"x": "{item_x_col3}", "y": "{item_y_start} + {item_y_spacing}*12", "size": "{item_font_size}", "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "center"},

    "fee_value_next_to_ac_right": {"x": 865, "y": "{item_y_start} + {item_y_spacing}*12", "size": 14, "font": "regular", "color": TEXT_COLOR_DEFAULT, "align": "right"},

    "storage_fee":      {"x": 865, "y": 716, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "deposit_amount":   {"x": 865, "y": 744, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "remaining_balance":{"x": 865, "y": 772, "size": 17, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
    "grand_total":      {"x": 865, "y": 808, "size": 18, "font": "bold", "color": TEXT_COLOR_YELLOW_BG, "align": "right"},
}
