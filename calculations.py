# calculations.py
import data
import math

# --- 이사짐 부피/무게 계산 ---
def calculate_total_volume_weight(state_data, move_type):
    total_volume = 0.0
    total_weight = 0.0
    if not hasattr(data, 'item_definitions') or not data.item_definitions:
        return 0.0, 0.0
    
    item_defs = data.item_definitions.get(move_type, {})
    processed_items = set() 
    if isinstance(item_defs, dict):
        for section, item_list in item_defs.items():
            if section == data.WASTE_SECTION_NAME if hasattr(data, "WASTE_SECTION_NAME") else False: continue 
            if isinstance(item_list, list):
                for item_name in item_list:
                    if item_name in processed_items or not hasattr(data, 'items') or not data.items or item_name not in data.items:
                        continue
                    
                    item_key = f"qty_{move_type}_{section}_{item_name}"
                    quantity = int(state_data.get(item_key, 0) or 0) # None일 경우 0으로 처리
                    
                    if quantity > 0:
                        item_spec = data.items.get(item_name, {})
                        total_volume += item_spec.get("volume_m3", 0) * quantity
                        total_weight += item_spec.get("weight_kg", 0) * quantity
                        processed_items.add(item_name)
    return round(total_volume, 2), round(total_weight, 2)


# --- 차량 추천 ---
def recommend_vehicle(total_volume, total_weight, move_type):
    if not hasattr(data, 'vehicle_specs') or not data.vehicle_specs or \
       not hasattr(data, 'vehicle_prices') or not data.vehicle_prices or \
       move_type not in data.vehicle_prices:
        return "차량 정보 부족", 0.0

    available_trucks = sorted(
        [truck for truck in data.vehicle_prices.get(move_type, {}) if truck in data.vehicle_specs],
        key=lambda x: data.vehicle_specs[x].get("capacity", 0)
    )

    if not available_trucks: return "해당 이사 유형에 사용 가능한 차량 없음", 0.0

    recommended_truck = None
    base_price = 0.0

    for truck in available_trucks:
        spec = data.vehicle_specs[truck]
        if total_volume <= spec["capacity"] and total_weight <= spec["weight_capacity"]:
            recommended_truck = truck
            base_price = data.vehicle_prices[move_type][truck].get("price", 0)
            break
    
    if not recommended_truck: # 모든 차량 초과 시 가장 큰 차량으로 표시하고 초과 메시지
        largest_truck = available_trucks[-1] if available_trucks else None
        if largest_truck:
             spec = data.vehicle_specs[largest_truck]
             vol_over = total_volume > spec["capacity"]
             wt_over = total_weight > spec["weight_capacity"]
             over_msg = []
             if vol_over: over_msg.append(f"부피({total_volume:.2f}m³ > {spec['capacity']}m³)")
             if wt_over: over_msg.append(f"무게({total_weight:.0f}kg > {spec['weight_capacity']}kg)")
             return f"{largest_truck} 용량 초과 ({', '.join(over_msg)})", data.vehicle_prices[move_type][largest_truck].get("price", 0)
        return "모든 차량 용량 초과", 0.0
        
    return recommended_truck, base_price


# --- 최종 비용 계산 ---
def calculate_total_moving_cost(state_data):
    cost_items = []
    personnel_info = {}
    cost_before_add_charges = 0  # VAT 또는 카드 수수료 전 총액

    move_type = state_data.get('base_move_type', MOVE_TYPE_OPTIONS[0] if 'MOVE_TYPE_OPTIONS' in globals() and MOVE_TYPE_OPTIONS else "가정 이사 🏠")
    selected_vehicle = state_data.get('final_selected_vehicle')

    if not selected_vehicle or not hasattr(data, 'vehicle_prices') or \
       move_type not in data.vehicle_prices or \
       selected_vehicle not in data.vehicle_prices[move_type]:
        cost_items.append(("오류", 0, "선택된 차량 또는 이사 유형에 대한 가격 정보가 없습니다."))
        return 0, cost_items, {"final_men": 0, "final_women": 0}

    vehicle_data = data.vehicle_prices[move_type][selected_vehicle]
    base_price = vehicle_data.get("price", 0)
    base_men_from_vehicle = vehicle_data.get("men", 0)
    base_housewife_from_vehicle = vehicle_data.get("housewife", 0)
    
    actual_base_price = base_price
    base_price_note = f"{selected_vehicle} 기준"

    if state_data.get('is_storage_move', False):
        actual_base_price *= 2
        base_price_note += ", 보관이사 왕복 적용"
    
    cost_items.append(("기본 운임", actual_base_price, base_price_note))
    cost_before_add_charges += actual_base_price

    # 작업비 (사다리차, 스카이)
    ladder_cost_from, sky_cost_from = 0,0
    ladder_cost_to, sky_cost_to = 0,0
    
    from_method = state_data.get('from_method', '')
    to_method = state_data.get('to_method', '')

    if "사다리차" in from_method and hasattr(data, 'ladder_surcharges'):
        from_floor_str = str(state_data.get('from_floor', '1'))
        floor_num_from = int(re.sub(r'[^0-9]', '', from_floor_str.split('-')[0].split('~')[0])) if re.sub(r'[^0-9]', '', from_floor_str.split('-')[0].split('~')[0]) else 1
        
        ladder_surcharge_key_from = next((val for key_range, val in data.ladder_surcharges.items() if key_range[0] <= floor_num_from <= key_range[1]), 0)
        ladder_cost_from = ladder_surcharge_key_from
        if ladder_cost_from > 0: cost_items.append(("출발지 사다리차", ladder_cost_from, f"{from_floor_str} 작업"))

    if "사다리차" in to_method and hasattr(data, 'ladder_surcharges'):
        to_floor_str = str(state_data.get('to_floor', '1'))
        floor_num_to = int(re.sub(r'[^0-9]', '', to_floor_str.split('-')[0].split('~')[0])) if re.sub(r'[^0-9]', '', to_floor_str.split('-')[0].split('~')[0]) else 1
        
        ladder_surcharge_key_to = next((val for key_range, val in data.ladder_surcharges.items() if key_range[0] <= floor_num_to <= key_range[1]), 0)
        ladder_cost_to = ladder_surcharge_key_to
        if ladder_cost_to > 0: cost_items.append(("도착지 사다리차", ladder_cost_to, f"{to_floor_str} 작업"))
    
    cost_before_add_charges += ladder_cost_from + ladder_cost_to

    if "스카이" in from_method and hasattr(data, 'sky_work_prices'):
        hours_from = int(state_data.get('sky_hours_from', 1) or 1)
        sky_base_cost, sky_add_cost = data.sky_work_prices.get(selected_vehicle, (0,0))
        sky_cost_from = sky_base_cost + (sky_add_cost * (hours_from - 1)) if hours_from > 0 else 0
        if sky_cost_from > 0: cost_items.append(("출발지 스카이 장비", sky_cost_from, f"출발({hours_from}h): 기본 {sky_base_cost:,} + 추가 {sky_add_cost * (hours_from - 1):,}"))

    if "스카이" in to_method and hasattr(data, 'sky_work_prices'):
        hours_to = int(state_data.get('sky_hours_final', 1) or 1) # sky_hours_to -> sky_hours_final
        sky_base_cost_to, sky_add_cost_to = data.sky_work_prices.get(selected_vehicle, (0,0))
        sky_cost_to = sky_base_cost_to + (sky_add_cost_to * (hours_to - 1)) if hours_to > 0 else 0
        if sky_cost_to > 0: cost_items.append(("도착지 스카이 장비", sky_cost_to, f"도착({hours_to}h): 기본 {sky_base_cost_to:,} + 추가 {sky_add_cost_to * (hours_to - 1):,}"))
        
    cost_before_add_charges += sky_cost_from + sky_cost_to

    # 인원 비용
    additional_person_cost = getattr(data, "ADDITIONAL_PERSON_COST", 0)
    base_personnel_discount_housewife = 0
    base_personnel_discount_man = 0

    # --- 기본 인원 제외 로직 수정: 1명만 제외 ---
    if state_data.get('remove_base_housewife', False) and base_housewife_from_vehicle > 0:
        base_personnel_discount_housewife = -additional_person_cost # 1명 비용만 할인
        cost_items.append(("기본 여성 인원 중 1명 제외 할인", base_personnel_discount_housewife, f"기본 {base_housewife_from_vehicle}명 중 1명 제외"))
    
    if state_data.get('remove_base_man', False) and base_man_from_vehicle > 0:
        base_personnel_discount_man = -additional_person_cost # 1명 비용만 할인
        cost_items.append(("기본 남성 인원 중 1명 제외 할인", base_personnel_discount_man, f"기본 {base_man_from_vehicle}명 중 1명 제외"))

    cost_before_add_charges += base_personnel_discount_housewife
    cost_before_add_charges += base_personnel_discount_man
    
    # 최종 인원 계산 수정
    final_men = base_men_from_vehicle
    if state_data.get('remove_base_man', False) and base_man_from_vehicle > 0:
        final_men -= 1
    final_men += int(state_data.get('add_men', 0) or 0)
    final_men = max(0, final_men) # 음수 방지

    final_housewives = base_housewife_from_vehicle
    if state_data.get('remove_base_housewife', False) and base_housewife_from_vehicle > 0:
        final_housewives -= 1
    final_housewives += int(state_data.get('add_women', 0) or 0)
    final_housewives = max(0, final_housewives) # 음수 방지

    personnel_info['base_men'] = base_men_from_vehicle
    personnel_info['base_women'] = base_housewife_from_vehicle
    personnel_info['additional_men'] = int(state_data.get('add_men', 0) or 0)
    personnel_info['additional_women'] = int(state_data.get('add_women', 0) or 0)
    personnel_info['final_men'] = final_men
    personnel_info['final_women'] = final_housewives
    
    # 추가 인원 비용 (기본 인원에서 가감된 후 순수하게 추가된 인원만 계산)
    manual_added_men_cost = (final_men - (base_men_from_vehicle - (1 if state_data.get('remove_base_man', False) and base_man_from_vehicle > 0 else 0))) * additional_person_cost \
        if final_men > (base_men_from_vehicle - (1 if state_data.get('remove_base_man', False) and base_man_from_vehicle > 0 else 0)) else 0
    
    manual_added_women_cost = (final_housewives - (base_housewife_from_vehicle - (1 if state_data.get('remove_base_housewife', False) and base_housewife_from_vehicle > 0 else 0))) * additional_person_cost \
        if final_housewives > (base_housewife_from_vehicle - (1 if state_data.get('remove_base_housewife', False) and base_housewife_from_vehicle > 0 else 0)) else 0
    
    manual_added_total_cost = manual_added_men_cost + manual_added_women_cost

    if manual_added_total_cost > 0:
        cost_items.append(("추가 인력", manual_added_total_cost, f"남성 {int(state_data.get('add_men',0) or 0)}명, 여성 {int(state_data.get('add_women',0) or 0)}명 추가분 반영"))
        cost_before_add_charges += manual_added_total_cost
        
    # 수기 조정 금액
    adjustment = int(state_data.get('adjustment_amount', 0) or 0)
    if adjustment != 0:
        adj_label = "할증 조정 금액" if adjustment > 0 else "할인 조정 금액"
        cost_items.append((adj_label, adjustment, "수기 입력"))
        cost_before_add_charges += adjustment

    # 수동 사다리 추가금 (Tab1에서 입력, Tab3에 표시/계산)
    dep_manual_ladder_surcharge = int(state_data.get('departure_ladder_surcharge_manual',0) or 0) if state_data.get('manual_ladder_from_check', False) else 0
    arr_manual_ladder_surcharge = int(state_data.get('arrival_ladder_surcharge_manual',0) or 0) if state_data.get('manual_ladder_to_check', False) else 0

    if dep_manual_ladder_surcharge > 0:
        cost_items.append(("출발지 수동 사다리 추가", dep_manual_ladder_surcharge, "수동 작업"))
        cost_before_add_charges += dep_manual_ladder_surcharge
    if arr_manual_ladder_surcharge > 0:
        cost_items.append(("도착지 수동 사다리 추가", arr_manual_ladder_surcharge, "수동 작업"))
        cost_before_add_charges += arr_manual_ladder_surcharge

    # 보관료
    if state_data.get('is_storage_move', False):
        duration = int(state_data.get('storage_duration', 1) or 1)
        storage_type = state_data.get('storage_type', data.DEFAULT_STORAGE_TYPE if hasattr(data, "DEFAULT_STORAGE_TYPE") else "컨테이너 보관 📦") # 이모티콘 포함된 키 사용
        use_electricity = state_data.get('storage_use_electricity', False)
        
        daily_rate = 0
        if hasattr(data, "storage_prices") and storage_type in data.storage_prices:
             daily_rate = data.storage_prices[storage_type].get('rate_per_day', 0)
        
        storage_cost = daily_rate * duration
        if use_electricity and hasattr(data, "STORAGE_ELECTRICITY_SURCHARGE_PER_MONTH"): # 월 단위 추가금, 일할 계산 필요시 복잡해짐. 여기선 단순 추가.
            # 간단하게, 한달 미만도 월 요금 부과 또는 일할 계산 (여기서는 기간 관계없이 1회성 추가금으로 가정)
            # 실제로는 (duration / 30) * 월요금 등이 될 수 있음. data.py에 명확한 정책 필요.
            # 여기서는 한달 이상 보관 시 월 요금 부과로 가정.
            if duration >=30 and hasattr(data, "STORAGE_ELECTRICITY_SURCHARGE_PER_MONTH"):
                 storage_cost += data.STORAGE_ELECTRICITY_SURCHARGE_PER_MONTH * math.ceil(duration / 30) # 개월 수 올림
            elif duration < 30 and hasattr(data, "STORAGE_ELECTRICITY_SURCHARGE_FLAT_LESS_MONTH"): # 한달 미만 고정금액 (data.py 에 정의 필요)
                 storage_cost += data.STORAGE_ELECTRICITY_SURCHARGE_FLAT_LESS_MONTH

        storage_type_display = storage_type.split(" ")[0] # 이모티콘 제거
        storage_note = f"{storage_type_display} {duration}일"
        if use_electricity: storage_note += " (전기사용)"
        
        if storage_cost > 0 : cost_items.append(("보관료", storage_cost, storage_note))
        cost_before_add_charges += storage_cost

    # 장거리 운송료
    if state_data.get('apply_long_distance', False) and hasattr(data, 'long_distance_prices'):
        ld_option = state_data.get('long_distance_selector', '선택 안 함')
        ld_cost = data.long_distance_prices.get(ld_option, 0)
        if ld_cost > 0:
            cost_items.append(("장거리 운송료", ld_cost, ld_option))
            cost_before_add_charges += ld_cost
            
    # 폐기물 처리비
    if state_data.get('has_waste_check', False) and hasattr(data, 'WASTE_DISPOSAL_COST_PER_TON'):
        waste_tons = float(state_data.get('waste_tons_input', 0.5) or 0.5)
        waste_cost = data.WASTE_DISPOSAL_COST_PER_TON * waste_tons
        if waste_cost > 0:
            cost_items.append(("폐기물 처리", math.ceil(waste_cost), f"{waste_tons}톤"))
            cost_before_add_charges += math.ceil(waste_cost)

    # 날짜 할증 (중복 적용 가능)
    if hasattr(data, 'special_day_prices'):
        date_options_keys_data_py = list(data.special_day_prices.keys()) # data.py의 원본 키 (이모티콘 포함)
        # ui_tab3의 위젯 키는 date_opt_0_widget, date_opt_1_widget ...
        # 이 위젯 키와 data.py의 할증 키를 매핑하는 정보가 필요함.
        # 현재 ui_tab3.py는 matched_date_options 리스트를 만들지만, calculations.py는 이 정보를 직접 받지 않음.
        # 임시로, data.py의 special_day_prices 순서와 ui_tab3의 위젯 순서가 일치한다고 가정. (위험)
        # 더 나은 방법: state_data에 "selected_special_days": ["이사많은날 🏠", "손없는날 ✋"] 처럼 저장하는 것.
        # 현재 구현은 state_data.get(f"date_opt_{i}_widget") 를 사용.
        
        # matched_date_options_calc는 data.py의 special_day_prices 키 순서대로 가정
        # date_options_text_tab3 = ["이사많은날", "손없는날", "월말", "공휴일", "금요일"] # ui_tab3.py 참고
        
        # 가정: data.py의 special_day_prices 딕셔너리 키 순서가 위젯의 순서와 일치
        # 이는 data.py가 OrderedDict가 아니면 보장되지 않음.
        # data.py 의 키 순서를 명시적으로 가져옴
        special_day_keys_ordered = list(data.special_day_prices.keys())

        for i in range(len(special_day_keys_ordered)): # data.py 키 기준 순회
            widget_key = f"date_opt_{i}_widget" # 해당 순번의 위젯 키
            if state_data.get(widget_key, False):
                data_py_actual_key = special_day_keys_ordered[i] # 이 순번의 data.py 키
                surcharge_val = data.special_day_prices.get(data_py_actual_key, 0)
                if surcharge_val > 0:
                    surcharge_label = data_py_actual_key.split(" ")[0] # "이사많은날"
                    cost_items.append(("날짜 할증", surcharge_val, surcharge_label))
                    cost_before_add_charges += surcharge_val
    
    # 경유지 추가요금
    if state_data.get('has_via_point', False):
        via_surcharge = int(state_data.get('via_point_surcharge', 0) or 0)
        if via_surcharge > 0:
            cost_items.append(("경유지 추가요금", via_surcharge, "경유지 작업"))
            cost_before_add_charges += via_surcharge

    # 최종 비용 계산 (VAT 또는 카드수수료 적용)
    cost_after_vat_or_card_setup = cost_before_add_charges

    if state_data.get('card_payment', False) and hasattr(data, "CARD_PAYMENT_SURCHARGE_PERCENT"):
        card_total_surcharge_on_base = math.ceil(cost_before_add_charges * (data.CARD_PAYMENT_SURCHARGE_PERCENT / 100.0))
        cost_items.append(("카드결제 (VAT 및 수수료 포함)", card_total_surcharge_on_base, f"{data.CARD_PAYMENT_SURCHARGE_PERCENT}% 적용"))
        cost_after_vat_or_card_setup += card_total_surcharge_on_base
    elif state_data.get('issue_tax_invoice', False) and hasattr(data, "VAT_RATE_PERCENT"):
        vat = math.ceil(cost_before_add_charges * (data.VAT_RATE_PERCENT / 100.0))
        cost_items.append(("부가세 (10%)", vat, f"{data.VAT_RATE_PERCENT}% 세금계산서 발행 요청"))
        cost_after_vat_or_card_setup += vat
    
    current_total_cost = math.ceil(cost_after_vat_or_card_setup / 100) * 100 # 100원 단위 올림

    return current_total_cost, cost_items, personnel_info
