# calculations.py
import data
import math
import re 

# --- MOVE_TYPE_OPTIONS 정의 (state_manager와 동일하게) ---
try:
    MOVE_TYPE_OPTIONS = list(data.item_definitions.keys()) if hasattr(data, 'item_definitions') and data.item_definitions else ["가정 이사 🏠", "사무실 이사 🏢"]
except Exception:
    MOVE_TYPE_OPTIONS = ["가정 이사 🏠", "사무실 이사 🏢"]

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
            waste_section_name = getattr(data, "WASTE_SECTION_NAME", "폐기 처리 품목 🗑️")
            if section == waste_section_name : continue 
            if isinstance(item_list, list):
                for item_name in item_list:
                    if item_name in processed_items or not hasattr(data, 'items') or not data.items or item_name not in data.items:
                        continue
                    
                    item_key = f"qty_{move_type}_{section}_{item_name}"
                    quantity = int(state_data.get(item_key, 0) or 0) 
                    
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
        return "차량 정보 부족", 0.0, 0, 0 # 차량명, 가격, 기본 남, 기본 여 반환

    available_trucks = sorted(
        [truck for truck in data.vehicle_prices.get(move_type, {}) if truck in data.vehicle_specs],
        key=lambda x: data.vehicle_specs[x].get("capacity", 0)
    )

    if not available_trucks: return "해당 이사 유형에 사용 가능한 차량 없음", 0.0, 0, 0

    recommended_truck = None
    base_price = 0.0
    base_men_rec = 0
    base_women_rec = 0

    if total_volume <= 0 and total_weight <= 0:
        return None, 0.0, 0, 0
    
    loading_efficiency = getattr(data, 'LOADING_EFFICIENCY', 1.0) 
    
    for truck_name in available_trucks: # 정렬된 순서대로 순회
        specs = data.vehicle_specs[truck_name]
        usable_capacity = specs.get('capacity', 0) * loading_efficiency
        usable_weight = specs.get('weight_capacity', 0) 
        
        if usable_capacity > 0 and total_volume <= usable_capacity and total_weight <= usable_weight:
            recommended_truck = truck_name
            price_info = data.vehicle_prices[move_type].get(truck_name, {})
            base_price = price_info.get("price", 0)
            base_men_rec = price_info.get("men", 0)
            base_women_rec = price_info.get("housewife", 0) if move_type == "가정 이사 🏠" else 0
            break 
            
    if recommended_truck: 
        return recommended_truck, base_price, base_men_rec, base_women_rec
    elif (total_volume > 0 or total_weight > 0) and available_trucks: 
        largest_truck = available_trucks[-1]
        spec = data.vehicle_specs[largest_truck]
        vol_over = total_volume > spec["capacity"] * loading_efficiency
        wt_over = total_weight > spec["weight_capacity"]
        over_msg = []
        if vol_over: over_msg.append(f"부피({total_volume:.2f}m³ > {spec['capacity']*loading_efficiency:.2f}m³)")
        if wt_over: over_msg.append(f"무게({total_weight:.0f}kg > {spec['weight_capacity']}kg)")
        
        price_info_largest = data.vehicle_prices[move_type].get(largest_truck, {})
        base_price_largest = price_info_largest.get("price",0)
        base_men_largest = price_info_largest.get("men",0)
        base_women_largest = price_info_largest.get("housewife",0) if move_type == "가정 이사 🏠" else 0
        
        return f"{largest_truck} 용량 초과 ({', '.join(over_msg)})", base_price_largest, base_men_largest, base_women_largest
    else: 
        return None, 0.0, 0, 0


# --- 층수 숫자 추출 ---
def get_floor_num(floor_str):
    try:
        if floor_str is None: return 0
        cleaned = str(floor_str).strip().upper() 
        if not cleaned: return 0 
        
        if cleaned.startswith('B') and cleaned[1:].isdigit():
            return -int(cleaned[1:])
        
        num_part = ''.join(filter(lambda x: x.isdigit() or x == '-', cleaned)) 
        if num_part:
            if num_part.count('-') > 1 or (num_part.count('-') == 1 and not num_part.startswith('-')):
                num_part_digits_only = ''.join(filter(str.isdigit, num_part))
                return int(num_part_digits_only) if num_part_digits_only else 0
            return int(num_part)
        return 0
    except: return 0 

# --- 사다리차 비용 계산 ---
def get_ladder_cost(floor_num, vehicle_name):
    cost, note = 0, ""
    if floor_num < 2: return 0, "1층 이하" 
    
    ladder_price_floor_ranges = getattr(data, 'ladder_price_floor_ranges', {})
    ladder_tonnage_map = getattr(data, 'ladder_tonnage_map', {})
    default_ladder_size_val = getattr(data, 'default_ladder_size', None)
    ladder_prices_val = getattr(data, 'ladder_prices', {})

    floor_range_key = next((rng_str for (min_f, max_f), rng_str in ladder_price_floor_ranges.items() if min_f <= floor_num <= max_f), None)
    if not floor_range_key: return 0, f"{floor_num}층 해당 가격 없음"
        
    vehicle_spec = getattr(data, 'vehicle_specs', {}).get(vehicle_name)
    if not vehicle_spec or 'weight_capacity' not in vehicle_spec: return 0, "선택 차량 정보 없음"
    
    vehicle_ton_num = vehicle_spec['weight_capacity'] / 1000.0 
    
    tonnage_key = next((ladder_tonnage_map[ton_n] for ton_n in sorted(ladder_tonnage_map.keys(), reverse=True) if vehicle_ton_num >= ton_n), default_ladder_size_val)
    if not tonnage_key: return 0, "사다리차 톤수 기준 없음"
    
    try:
        floor_prices_for_range = ladder_prices_val.get(floor_range_key, {})
        cost = floor_prices_for_range.get(tonnage_key, 0)
        
        if cost > 0: 
            note = f"{floor_range_key}, {tonnage_key} 기준"
        else: 
            if default_ladder_size_val and default_ladder_size_val != tonnage_key: 
                 cost = floor_prices_for_range.get(default_ladder_size_val, 0)
                 note = f"{floor_range_key}, 기본({default_ladder_size_val}) 적용" if cost > 0 else f"{floor_range_key}, {tonnage_key}(기본 {default_ladder_size_val}) 가격 없음"
            else: 
                 note = f"{floor_range_key}, {tonnage_key} 가격 정보 없음"
    except Exception as e: 
        note, cost = f"가격 조회 오류: {e}", 0
    return cost, note

# --- 총 이사 비용 계산 ---
def calculate_total_moving_cost(state_data):
    cost_before_add_charges = 0 
    cost_items = [] 
    personnel_info = {} 

    move_type = state_data.get('base_move_type', MOVE_TYPE_OPTIONS[0])
    selected_vehicle = state_data.get('final_selected_vehicle') 
    is_storage, has_via_point = state_data.get('is_storage_move', False), state_data.get('has_via_point', False)

    if not selected_vehicle:
        return 0, [("오류", 0, "차량 선택 필요")], {"final_men": 0, "final_women": 0}

    vehicle_data = {}
    if hasattr(data, 'vehicle_prices') and move_type in data.vehicle_prices and \
       selected_vehicle in data.vehicle_prices[move_type]:
        vehicle_data = data.vehicle_prices[move_type][selected_vehicle]
    else:
        cost_items.append(("오류", 0, f"차량({selected_vehicle}) 또는 이사유형({move_type}) 가격 정보 없음"))
        return 0, cost_items, {"final_men": 0, "final_women": 0}

    base_price = vehicle_data.get("price", 0)
    base_men_from_vehicle = vehicle_data.get("men", 0)
    base_housewife_from_vehicle = vehicle_data.get("housewife", 0) if move_type == "가정 이사 🏠" else 0
    
    actual_base_price = base_price
    base_price_note = f"{selected_vehicle} 기준"

    if is_storage: 
        actual_base_price *= 2
        base_price_note += ", 보관이사 왕복 적용"
    
    cost_items.append(("기본 운임", actual_base_price, base_price_note))
    cost_before_add_charges += actual_base_price

    for loc_prefix, floor_key, method_key, sky_hours_key in [
        ("출발지", 'from_floor', 'from_method', 'sky_hours_from'),
        ("도착지", 'to_floor', 'to_method', 'sky_hours_final')
    ]:
        method_val = state_data.get(method_key, '')
        floor_val_str = str(state_data.get(floor_key, '1'))
        floor_num_val = get_floor_num(floor_val_str)

        if "사다리차" in method_val:
            ladder_cost, ladder_note = get_ladder_cost(floor_num_val, selected_vehicle)
            if ladder_cost > 0:
                cost_items.append((f"{loc_prefix} 사다리차", ladder_cost, ladder_note))
                cost_before_add_charges += ladder_cost
        elif "스카이" in method_val:
            hours = int(state_data.get(sky_hours_key, 1) or 1)
            sky_base, sky_add_hr = getattr(data, 'SKY_BASE_PRICE',0), getattr(data, 'SKY_EXTRA_HOUR_PRICE',0) 
            sky_total_cost = sky_base + (sky_add_hr * (hours - 1)) if hours > 0 else 0
            if sky_total_cost > 0:
                sky_note = f"{loc_prefix}({hours}h): 기본 {sky_base:,} + 추가 {sky_add_hr * (hours - 1):,}" if hours > 1 else f"{loc_prefix}({hours}h): 기본 {sky_base:,}"
                cost_items.append((f"{loc_prefix} 스카이 장비", sky_total_cost, sky_note))
                cost_before_add_charges += sky_total_cost
    
    additional_person_cost = getattr(data, "ADDITIONAL_PERSON_COST", 0)
    
    num_housewives_removed = 0
    if state_data.get('remove_base_housewife', False) and base_housewife_from_vehicle > 0:
        cost_items.append(("기본 여성 인원 중 1명 제외 할인", -additional_person_cost, f"기본 {base_housewife_from_vehicle}명 중 1명 제외"))
        cost_before_add_charges -= additional_person_cost
        num_housewives_removed = 1 # 1명만 제외
    
    num_men_removed = 0
    if state_data.get('remove_base_man', False) and base_men_from_vehicle > 0:
        cost_items.append(("기본 남성 인원 중 1명 제외 할인", -additional_person_cost, f"기본 {base_men_from_vehicle}명 중 1명 제외"))
        cost_before_add_charges -= additional_person_cost
        num_men_removed = 1 # 1명만 제외

    final_men = base_men_from_vehicle - num_men_removed + int(state_data.get('add_men', 0) or 0)
    final_housewives = base_housewife_from_vehicle - num_housewives_removed + int(state_data.get('add_women', 0) or 0)
    final_men = max(0, final_men)
    final_housewives = max(0, final_housewives)

    personnel_info['base_men'] = base_men_from_vehicle
    personnel_info['base_women'] = base_housewife_from_vehicle
    personnel_info['additional_men'] = int(state_data.get('add_men', 0) or 0) 
    personnel_info['additional_women'] = int(state_data.get('add_women', 0) or 0) 
    personnel_info['removed_base_housewife_count'] = num_housewives_removed
    personnel_info['removed_base_men_count'] = num_men_removed
    personnel_info['final_men'] = final_men
    personnel_info['final_women'] = final_housewives
    
    added_men_for_cost = int(state_data.get('add_men', 0) or 0)
    added_women_for_cost = int(state_data.get('add_women', 0) or 0)
    manual_added_total_cost = (added_men_for_cost + added_women_for_cost) * additional_person_cost

    if manual_added_total_cost > 0:
        cost_items.append(("추가 인력", manual_added_total_cost, f"남성 {added_men_for_cost}명, 여성 {added_women_for_cost}명 추가분"))
        cost_before_add_charges += manual_added_total_cost
        
    adjustment = int(state_data.get('adjustment_amount', 0) or 0)
    if adjustment != 0:
        adj_label = "할증 조정 금액" if adjustment > 0 else "할인 조정 금액"
        cost_items.append((adj_label, adjustment, "수기 입력"))
        cost_before_add_charges += adjustment

    dep_manual_ladder_surcharge = int(state_data.get('departure_ladder_surcharge_manual',0) or 0) if state_data.get('manual_ladder_from_check', False) else 0
    arr_manual_ladder_surcharge = int(state_data.get('arrival_ladder_surcharge_manual',0) or 0) if state_data.get('manual_ladder_to_check', False) else 0

    if dep_manual_ladder_surcharge > 0:
        cost_items.append(("출발지 수동 사다리 추가", dep_manual_ladder_surcharge, "수동 작업"))
        cost_before_add_charges += dep_manual_ladder_surcharge
    if arr_manual_ladder_surcharge > 0:
        cost_items.append(("도착지 수동 사다리 추가", arr_manual_ladder_surcharge, "수동 작업"))
        cost_before_add_charges += arr_manual_ladder_surcharge

    if state_data.get('is_storage_move', False):
        duration = int(state_data.get('storage_duration', 1) or 1)
        storage_type_key = state_data.get('storage_type', getattr(data,"DEFAULT_STORAGE_TYPE","")) 
        use_electricity = state_data.get('storage_use_electricity', False)
        
        daily_rate = 0
        if hasattr(data, "storage_prices") and storage_type_key in data.storage_prices:
             daily_rate = data.storage_prices[storage_type_key].get('rate_per_day', 0)
        
        storage_cost = daily_rate * duration
        storage_type_display = storage_type_key.split(" ")[0] 
        storage_note = f"{storage_type_display} {duration}일"
        
        if use_electricity:
            elec_surcharge = 0
            # 전기료 계산 로직 (data.py 의 변수명 일치 확인 필요)
            if duration >=30 and hasattr(data, "STORAGE_ELECTRICITY_SURCHARGE_PER_MONTH"):
                 elec_surcharge = data.STORAGE_ELECTRICITY_SURCHARGE_PER_MONTH * math.ceil(duration / 30)
            elif duration < 30 and hasattr(data, "STORAGE_ELECTRICITY_SURCHARGE_FLAT_LESS_MONTH"):
                 elec_surcharge = data.STORAGE_ELECTRICITY_SURCHARGE_FLAT_LESS_MONTH
            elif hasattr(data, "STORAGE_ELECTRICITY_SURCHARGE_PER_DAY"): 
                 elec_surcharge = data.STORAGE_ELECTRICITY_SURCHARGE_PER_DAY * duration
            
            if elec_surcharge > 0:
                storage_cost += elec_surcharge
                storage_note += " (전기사용)"
        
        if storage_cost > 0 or duration > 0 : 
            cost_items.append(("보관료", storage_cost, storage_note))
        cost_before_add_charges += storage_cost

    if state_data.get('apply_long_distance', False) and hasattr(data, 'long_distance_prices'):
        ld_option = state_data.get('long_distance_selector', '선택 안 함')
        ld_cost = data.long_distance_prices.get(ld_option, 0)
        if ld_cost > 0:
            cost_items.append(("장거리 운송료", ld_cost, ld_option))
            cost_before_add_charges += ld_cost
            
    if state_data.get('has_waste_check', False) and hasattr(data, 'WASTE_DISPOSAL_COST_PER_TON'):
        waste_tons = float(state_data.get('waste_tons_input', 0.5) or 0.5)
        waste_cost = data.WASTE_DISPOSAL_COST_PER_TON * waste_tons
        if waste_cost > 0:
            cost_items.append(("폐기물 처리", math.ceil(waste_cost), f"{waste_tons}톤"))
            cost_before_add_charges += math.ceil(waste_cost)

    if hasattr(data, 'special_day_prices'):
        special_day_keys_ordered = list(data.special_day_prices.keys())
        for i, data_py_actual_key in enumerate(special_day_keys_ordered):
            widget_key = f"date_opt_{i}_widget"
            if state_data.get(widget_key, False):
                surcharge_val = data.special_day_prices.get(data_py_actual_key, 0)
                if surcharge_val > 0:
                    surcharge_label = data_py_actual_key.split(" ")[0]
                    cost_items.append(("날짜 할증", surcharge_val, surcharge_label))
                    cost_before_add_charges += surcharge_val
    
    if state_data.get('has_via_point', False):
        via_surcharge = int(state_data.get('via_point_surcharge', 0) or 0)
        if via_surcharge > 0:
            cost_items.append(("경유지 추가요금", via_surcharge, "경유지 작업"))
            cost_before_add_charges += via_surcharge

    cost_after_vat_or_card_setup = cost_before_add_charges

    if state_data.get('card_payment', False) and hasattr(data, "CARD_PAYMENT_SURCHARGE_PERCENT"):
        card_total_surcharge_on_base = math.ceil(cost_before_add_charges * (data.CARD_PAYMENT_SURCHARGE_PERCENT / 100.0))
        cost_items.append(("카드결제 (VAT 및 수수료 포함)", card_total_surcharge_on_base, f"{data.CARD_PAYMENT_SURCHARGE_PERCENT}% 적용"))
        cost_after_vat_or_card_setup += card_total_surcharge_on_base
    elif state_data.get('issue_tax_invoice', False) and hasattr(data, "VAT_RATE_PERCENT"):
        vat = math.ceil(cost_before_add_charges * (data.VAT_RATE_PERCENT / 100.0))
        cost_items.append(("부가세 (10%)", vat, f"{data.VAT_RATE_PERCENT}% 계산서 발행 요청"))
        cost_after_vat_or_card_setup += vat
    
    current_total_cost = math.ceil(cost_after_vat_or_card_setup / 100) * 100 

    return current_total_cost, cost_items, personnel_info
