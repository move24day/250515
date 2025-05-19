# calculations.py
import data
import math

# --- 이사짐 부피/무게 계산 ---
def calculate_total_volume_weight(state_data, move_type):
    total_volume = 0.0
    total_weight = 0.0
    if not hasattr(data, 'item_definitions') or not data.item_definitions:
        return 0.0, 0.0
    
    # 이사 유형 키에서 이모티콘 제거 (data.py의 키와 일치시키기 위해)
    # move_type_key = move_type.split(" ")[0] # 예: "가정 이사 🏠" -> "가정" (data.py의 키가 이렇게 되어있다면)
    # 현재 data.py의 키는 이모티콘을 포함하고 있으므로 원본 move_type 사용
    item_defs = data.item_definitions.get(move_type, {})
    processed_items = set() 
    if isinstance(item_defs, dict):
        for section, item_list in item_defs.items():
            # 폐기 처리 품목은 부피/무게 계산에서 제외 (data.py에 해당 섹션 이름이 정확해야 함)
            if section == "폐기 처리 품목 🗑️": continue 
            if isinstance(item_list, list):
                for item_name in item_list:
                    if item_name in processed_items or not hasattr(data, 'items') or not data.items or item_name not in data.items:
                        continue
                    # session_state 키 생성 시 이모티콘 포함된 move_type과 section 이름 사용
                    widget_key = f"qty_{move_type}_{section}_{item_name}"
                    qty_raw = state_data.get(widget_key)
                    qty = int(qty_raw) if qty_raw is not None and str(qty_raw).strip() != "" else 0
                    if qty > 0:
                        try:
                            volume, weight = data.items[item_name] 
                            total_volume += volume * qty
                            total_weight += weight * qty
                        except KeyError: pass # data.items에 해당 품목 없는 경우
                        except Exception: pass # 기타 예외
                    processed_items.add(item_name)
    return round(total_volume, 2), round(total_weight, 2)

# --- 차량 추천 ---
def recommend_vehicle(total_volume, total_weight, current_move_type):
    recommended_vehicle, remaining_space_percent = None, 0.0
    if not hasattr(data, 'vehicle_specs') or not data.vehicle_specs: return None, 0
    
    # current_move_type은 이모티콘 포함된 값 (예: "가정 이사 🏠")
    priced_trucks_for_move_type = list(data.vehicle_prices.get(current_move_type, {}).keys()) if hasattr(data, 'vehicle_prices') and data.vehicle_prices else []
    if not priced_trucks_for_move_type: return None, 0 # 해당 이사 유형에 가격 정보 있는 차량 없음
    
    relevant_vehicle_specs = {truck: specs for truck, specs in data.vehicle_specs.items() if truck in priced_trucks_for_move_type}
    if not relevant_vehicle_specs: return None, 0
    
    # 차량 용량(capacity) 기준으로 정렬
    sorted_trucks = sorted(relevant_vehicle_specs.items(), key=lambda item: item[1].get('capacity', 0))
    
    if total_volume <= 0 and total_weight <= 0: return None, 0 # 물품이 없으면 추천 불가
    
    loading_efficiency = getattr(data, 'LOADING_EFFICIENCY', 1.0) # 기본값 1.0 (100%)
    
    for truck_name, specs in sorted_trucks:
        usable_capacity = specs.get('capacity', 0) * loading_efficiency
        usable_weight = specs.get('weight_capacity', 0) # 무게는 효율 적용 안함 (일반적)
        
        if usable_capacity > 0 and total_volume <= usable_capacity and total_weight <= usable_weight:
            recommended_vehicle = truck_name
            remaining_space_percent = (1 - (total_volume / usable_capacity)) * 100 if usable_capacity > 0 else 0
            break 
            
    if recommended_vehicle: 
        return recommended_vehicle, round(remaining_space_percent, 1)
    elif (total_volume > 0 or total_weight > 0) and sorted_trucks: # 물품은 있는데 맞는 차량이 없는 경우 (가장 큰 차량 용량 초과)
        return f"{sorted_trucks[-1][0]} 용량 초과", 0 
    else: # 기타 경우 (예: 차량 정보는 있으나 물품이 아예 없는 경우 등 - 위에서 처리됨)
        return None, 0

# --- 층수 숫자 추출 ---
def get_floor_num(floor_str):
    try:
        if floor_str is None: return 0
        cleaned = str(floor_str).strip().upper() # 대소문자 구분 없이 B 처리
        if not cleaned: return 0 
        
        # "B1", "B2" 등을 -1, -2로 변환
        if cleaned.startswith('B') and cleaned[1:].isdigit():
            return -int(cleaned[1:])
        
        # 일반 숫자, 음수 처리
        num_part = ''.join(filter(lambda x: x.isdigit() or x == '-', cleaned)) # 숫자와 마이너스만 추출
        if num_part:
             # 마이너스 부호가 여러 개 있거나, 숫자 중간에 있는 경우 처리
            if num_part.count('-') > 1 or (num_part.count('-') == 1 and not num_part.startswith('-')):
                # 유효하지 않은 형식으로 간주, 숫자만 추출 시도
                num_part_digits_only = ''.join(filter(str.isdigit, num_part))
                return int(num_part_digits_only) if num_part_digits_only else 0

            return int(num_part)
        return 0
    except: return 0 

# --- 사다리차 비용 계산 ---
def get_ladder_cost(floor_num, vehicle_name):
    cost, note = 0, ""
    if floor_num < 2: return 0, "1층 이하" # 1층 이하는 사다리차 사용 안함
    
    # floor_num에 해당하는 가격 범위 찾기
    floor_range_key = next((rng_str for (min_f, max_f), rng_str in getattr(data, 'ladder_price_floor_ranges', {}).items() if min_f <= floor_num <= max_f), None)
    if not floor_range_key: return 0, f"{floor_num}층 해당 가격 없음"
        
    vehicle_spec = getattr(data, 'vehicle_specs', {}).get(vehicle_name)
    if not vehicle_spec or 'weight_capacity' not in vehicle_spec: return 0, "선택 차량 정보 없음"
    
    vehicle_ton_num = vehicle_spec['weight_capacity'] / 1000.0 # kg을 ton으로
    
    # 차량 톤수에 맞는 사다리차 톤수 기준 찾기
    tonnage_key = next((data.ladder_tonnage_map[ton_n] for ton_n in sorted(getattr(data, 'ladder_tonnage_map', {}).keys(), reverse=True) if vehicle_ton_num >= ton_n), getattr(data, 'default_ladder_size', None))
    if not tonnage_key: return 0, "사다리차 톤수 기준 없음"
    
    try:
        floor_prices = getattr(data, 'ladder_prices', {}).get(floor_range_key, {})
        cost = floor_prices.get(tonnage_key, 0)
        
        if cost > 0: 
            note = f"{floor_range_key}, {tonnage_key} 기준"
        else: # 해당 톤수 가격이 없을 경우, 기본 사다리차 사이즈로 재시도
            def_size = getattr(data, 'default_ladder_size', None)
            if def_size and def_size != tonnage_key: # 기본 사이즈가 있고, 현재 톤수와 다르면
                 cost = floor_prices.get(def_size, 0)
                 note = f"{floor_range_key}, 기본({def_size}) 적용" if cost > 0 else f"{floor_range_key}, {tonnage_key}(기본 {def_size}) 가격 없음"
            else: # 기본 사이즈가 없거나 같으면, 그냥 가격 정보 없음 처리
                 note = f"{floor_range_key}, {tonnage_key} 가격 정보 없음"
    except Exception as e: 
        note, cost = f"가격 조회 오류: {e}", 0
    return cost, note

# --- 총 이사 비용 계산 ---
def calculate_total_moving_cost(state_data):
    cost_before_add_charges = 0 
    cost_items = [] 
    personnel_info = {} 

    current_move_type = state_data.get('base_move_type') # 이모티콘 포함된 키
    selected_vehicle = state_data.get('final_selected_vehicle') 
    is_storage, has_via_point = state_data.get('is_storage_move', False), state_data.get('has_via_point', False)

    if not selected_vehicle:
        return 0, [("오류", 0, "차량 선택 필요")], {}

    base_price, base_men, base_women = 0, 0, 0
    vehicle_prices_options = getattr(data, 'vehicle_prices', {}).get(current_move_type, {})
    if selected_vehicle in vehicle_prices_options:
        v_info = vehicle_prices_options[selected_vehicle]
        base_price, base_men = v_info.get('price', 0), v_info.get('men', 0)
        # 가정 이사일 때만 housewife 기본 인원 고려
        base_women = v_info.get('housewife', 0) if current_move_type == "가정 이사 🏠" else 0
        
        actual_base_price = base_price * 2 if is_storage else base_price # 보관 시 기본 운임 2배
        cost_items.append(("기본 운임", actual_base_price, f"{selected_vehicle} 기준" + (" (보관 x2)" if is_storage else "")))
        cost_before_add_charges += actual_base_price
    else:
        return 0, [("오류", 0, f"차량({selected_vehicle}) 가격 정보 없음")], {}

    # 출발지, 도착지, (경유지 - 별도 처리) 작업 비용
    for loc_type_key, floor_key, method_key, sky_hours_key, loc_label_prefix in [
        ("from", 'from_floor', 'from_method', 'sky_hours_from', "출발지"),
        ("to", 'to_floor', 'to_method', 'sky_hours_final', "도착지")]:
        
        floor_num = get_floor_num(state_data.get(floor_key))
        method_with_emoji = state_data.get(method_key) # 예: "사다리차 🪜"
        method = method_with_emoji.split(" ")[0] if method_with_emoji else "" # "사다리차"

        if method == "사다리차":
            l_cost, l_note = get_ladder_cost(floor_num, selected_vehicle)
            if l_cost > 0 or (l_cost == 0 and l_note != "1층 이하"): 
                cost_items.append((f"{loc_label_prefix} 사다리차", l_cost, l_note))
                cost_before_add_charges += l_cost
        elif method == "스카이":
            sky_h = max(1, int(state_data.get(sky_hours_key, 1) or 1)) # None이나 빈 문자열일 경우 1로
            s_base = getattr(data, 'SKY_BASE_PRICE',0)
            s_extra_hour_price = getattr(data, 'SKY_EXTRA_HOUR_PRICE',0)
            s_cost = s_base + s_extra_hour_price * (sky_h - 1)
            s_note = f"{loc_label_prefix}({sky_h}h): 기본 {s_base:,.0f}" + (f" + 추가 {s_extra_hour_price*(sky_h-1):,.0f}" if sky_h > 1 else "")
            cost_items.append((f"{loc_label_prefix} 스카이 장비", s_cost, s_note))
            cost_before_add_charges += s_cost
    
    # 추가 인력 비용
    add_m = int(state_data.get('add_men',0) or 0)
    add_w = int(state_data.get('add_women',0) or 0)
    add_person_cost_unit = getattr(data, 'ADDITIONAL_PERSON_COST', 0)
    
    actual_removed_hw = False # 실제 기본 여성 인원 제외 여부 플래그
    if current_move_type == "가정 이사 🏠" and state_data.get('remove_base_housewife', False) and base_women > 0:
        discount = -add_person_cost_unit * base_women # 음수로 할인 처리
        cost_items.append(("기본 여성 인원 제외 할인", discount, f"여 {base_women}명 제외"))
        cost_before_add_charges += discount
        actual_removed_hw = True # 실제 제외됨
        
    manual_added_total_cost = (add_m + add_w) * add_person_cost_unit
    if manual_added_total_cost > 0:
        cost_items.append(("추가 인력", manual_added_total_cost, f"남{add_m}, 여{add_w}"))
        cost_before_add_charges += manual_added_total_cost

    # 수기 조정 금액
    adj_amount = int(state_data.get('adjustment_amount',0) or 0) # state_manager에서 tab3_ 값으로 매핑됨
    if adj_amount != 0: 
        cost_items.append((f"{'할증' if adj_amount > 0 else '할인'} 조정 금액", adj_amount, "수동입력"))
        cost_before_add_charges += adj_amount

    # 보관료
    if is_storage:
        s_dur = max(1, int(state_data.get('storage_duration',1) or 1))
        s_type_raw = state_data.get('storage_type', getattr(data,'DEFAULT_STORAGE_TYPE',"정보없음")) # 예: "컨테이너 보관 📦"
        s_type = s_type_raw.split(" ")[0] if s_type_raw else "정보없음" # "컨테이너"
        
        # data.py의 STORAGE_RATES_PER_DAY 키도 이모티콘 없이 "컨테이너 보관" 등으로 가정
        # 여기서는 split으로 첫 단어만 사용
        s_daily_rate = getattr(data,'STORAGE_RATES_PER_DAY',{}).get(s_type_raw,0) # data.py 키는 이모티콘 포함된 원본 사용

        if s_daily_rate > 0:
            s_base_cost = s_daily_rate * s_dur
            s_elec_surcharge = 0
            s_note = f"{s_type_raw}, {s_dur}일" # 표시용은 원본 s_type_raw 사용
            if state_data.get('storage_use_electricity', False):
                s_elec_surcharge_per_day = getattr(data,'STORAGE_ELECTRICITY_SURCHARGE_PER_DAY',3000)
                s_elec_surcharge = s_elec_surcharge_per_day * s_dur
                s_note += ", 전기사용"
            s_final_cost = s_base_cost + s_elec_surcharge
            cost_items.append(("보관료", s_final_cost, s_note))
            cost_before_add_charges += s_final_cost
        else: 
            cost_items.append(("오류", 0, f"보관유형({s_type_raw}) 요금정보 없음"))

    # 장거리 운송료
    if state_data.get('apply_long_distance', False):
        ld_sel = state_data.get('long_distance_selector') # "선택 안 함" 또는 거리 옵션
        if ld_sel and ld_sel != "선택 안 함": # "선택 안 함"이 아닐 때만
            ld_cost = getattr(data,'long_distance_prices',{}).get(ld_sel,0)
            if ld_cost > 0: 
                cost_items.append(("장거리 운송료", ld_cost, ld_sel))
                cost_before_add_charges += ld_cost
            
    # 폐기물 처리 비용
    if state_data.get('has_waste_check', False):
        w_tons = max(0.5, float(state_data.get('waste_tons_input',0.5) or 0.5))
        w_cost_ton = getattr(data,'WASTE_DISPOSAL_COST_PER_TON',0)
        w_cost = w_cost_ton * w_tons
        cost_items.append(("폐기물 처리", w_cost, f"{w_tons:.1f}톤 기준"))
        cost_before_add_charges += w_cost

    # 날짜 할증
    dt_surcharge, dt_notes = 0, []
    # data.py의 special_day_prices 키는 이모티콘 포함된 원본 사용
    dt_opts_data_keys = ["이사많은날 🏠", "손없는날 ✋", "월말 📅", "공휴일 🎉", "금요일 📅"]
    dt_prices = getattr(data,'special_day_prices',{})
    for i, opt_key_data in enumerate(dt_opts_data_keys):
        # session_state 키는 'date_opt_0_widget' 등 (state_manager에서 tab3_ 값으로 매핑됨)
        if state_data.get(f"date_opt_{i}_widget", False): 
            s = dt_prices.get(opt_key_data,0); 
            if s > 0: 
                dt_surcharge += s
                dt_notes.append(opt_key_data.split(" ")[0]) # 이모티콘 제외하고 "이사많은날" 등
    if dt_surcharge > 0: 
        cost_items.append(("날짜 할증", dt_surcharge, ", ".join(dt_notes)))
        cost_before_add_charges += dt_surcharge
    
    # 지방 사다리 추가요금
    reg_ladder_surcharge = int(state_data.get('regional_ladder_surcharge',0) or 0) # state_manager에서 tab3_ 값으로 매핑됨
    if reg_ladder_surcharge > 0: 
        cost_items.append(("지방 사다리 추가요금", reg_ladder_surcharge, "수동입력"))
        cost_before_add_charges += reg_ladder_surcharge
    
    # 경유지 추가요금 (경유지 작업비용은 여기서 합산 안함, 별도 항목으로 또는 기본운임에 포함될 수 있음 - 현재는 수기입력만)
    if has_via_point:
        via_s = int(state_data.get('via_point_surcharge',0) or 0)
        if via_s > 0: 
            cost_items.append(("경유지 추가요금", via_s, "수동입력"))
            cost_before_add_charges += via_s

    # --- VAT 및 카드 수수료 계산 (수정된 로직) ---
    cost_after_vat_or_card_setup = cost_before_add_charges

    if state_data.get('card_payment', False):
        # 카드 결제 시, 13%에 VAT가 포함된 것으로 간주 (또는 13%가 VAT 포함 금액에 대한 순수 수수료).
        # 사용자 요청: "세금계산서 발행 10%가 더 추가 될 필요가 없어 카드결제에 VAT 포함이 되어있기 때문이야"
        # 이는 카드결제 자체가 VAT를 포함하는 최종 가격 조정으로 본다는 의미.
        # 따라서, (기본 비용의 13%)를 추가하고, 이것이 VAT와 카드 수수료를 모두 포함한다고 가정.
        # 만약 13%가 (원금 + 10%VAT)에 대한 수수료라면 계산이 달라져야 함.
        # 현재는 "카드결제(VAT 및 수수료 포함)"으로 13%를 원금에 부과하는 것으로 해석.
        card_total_surcharge_on_base = math.ceil(cost_before_add_charges * 0.13)
        cost_items.append(("카드결제 (VAT 및 수수료 포함)", card_total_surcharge_on_base, "카드 결제 요청"))
        cost_after_vat_or_card_setup += card_total_surcharge_on_base
        # 이 경우, 'issue_tax_invoice'가 True여도 별도의 10% VAT는 추가하지 않음.
    elif state_data.get('issue_tax_invoice', False):
        # 카드 결제가 아니면서 세금계산서 발행이 선택된 경우에만 10% VAT 추가
        vat = math.ceil(cost_before_add_charges * 0.1)
        cost_items.append(("부가세 (10%)", vat, "세금계산서 발행 요청"))
        cost_after_vat_or_card_setup += vat
    
    current_total_cost = cost_after_vat_or_card_setup 
    # --- VAT 및 카드 수수료 계산 완료 ---

    # 최종 인원 계산
    final_men = base_men + add_m
    final_women = (base_women + add_w) if not actual_removed_hw else add_w # 기본 여성 제외 시, 추가된 여성만

    personnel_info = {
        'base_men': base_men, 'base_women': base_women, # 차량 기본 인원
        'manual_added_men': add_m, 'manual_added_women': add_w, # 수동 추가 인원
        'final_men': final_men, 'final_women': final_women, # 최종 투입 인원
        'removed_base_housewife': actual_removed_hw # 기본 여성 인원 실제 제외 여부
    }
    return max(0, round(current_total_cost)), cost_items, personnel_info
