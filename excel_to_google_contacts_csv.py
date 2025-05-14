# flexible_contacts_csv_generator_v2.py
import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import pytz
import csv
import re

# --- 시간대 및 날짜 유틸리티 ---
try:
    KST = pytz.timezone("Asia/Seoul")
except pytz.UnknownTimeZoneError:
    KST = pytz.utc # Fallback
    st.warning("Asia/Seoul 시간대를 찾을 수 없어 UTC를 사용합니다.")

def get_processing_date_str(format_str="%m%d", days_offset=1):
    try:
        base_time = datetime.now(KST)
        target_date = base_time + timedelta(days=days_offset)
        return target_date.strftime(format_str)
    except Exception:
        target_date = datetime.now() + timedelta(days=days_offset)
        return target_date.strftime(format_str)

def extract_phone_digits(phone_str, length=4, default_val="XXXX"):
    if pd.isna(phone_str) or not isinstance(phone_str, str):
        return default_val
    digits = re.sub(r'\D', '', phone_str)
    if len(digits) >= length:
        return digits[-length:]
    elif digits:
        return digits.zfill(length)
    return default_val

# --- 유사어 매핑 (엑셀용) ---
COLUMN_ALIASES_CONTACTS = {
    'name_source': ['이름', '성명', '고객명', '상호명', '원래이름'],
    'phone': ['전화번호', '연락처', '휴대폰번호', '전화', '핸드폰', 'H.P', 'HP'],
    'address': ['주소', '출발지주소', '출발지', '기본주소', '배송지'],
    'date': ['날짜', '이사날짜', '예약일', '작업일'],
    'category': ['구분', '종류', '유형', '이사종류'],
    'destination': ['도착지주소', '도착지', '배송도착지', '목적지'],
    'notes': ['비고', '메모', '특이사항', '요청사항', '참고사항', '건의사항', '희망사항'],
}

# --- 텍스트 파싱용 ---
PHONE_REGEX_TEXT = re.compile(r'(01[016789]-?\d{3,4}-?\d{4}|0\d{1,2}-?\d{3,4}-?\d{4})')
# '가', '사' 및 전체 단어 키워드
MOVE_CATEGORY_KEYWORDS_TEXT = {
    "가정": ["가정", "가"],
    "사무실": ["사무실", "사"]
}

def parse_date_flexible_contacts(date_str_input, current_year):
    if not date_str_input or str(date_str_input).strip().lower() == "미정":
        return None
    date_str = str(date_str_input).strip()
    patterns = [
        (r'(\d{4})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*일?', lambda m: (int(m.group(1)), int(m.group(2)), int(m.group(3)))),
        (r'(\d{1,2})\s*[-/월\.]\s*(\d{1,2})\s*(일?)', lambda m: (current_year, int(m.group(1)), int(m.group(2)))),
        (r'(\d{2})\s*[-/년\.]?\s*(\d{1,2})\s*[-/월\.]?\s*(\d{1,2})\s*일?', lambda m: (2000 + int(m.group(1)), int(m.group(2)), int(m.group(3))))
    ]
    for pattern, extractor in patterns:
        match = re.match(pattern, date_str)
        if match:
            try:
                matched_date_str = match.group(0)
                if len(matched_date_str) != len(date_str) and not date_str[len(matched_date_str):].strip().isspace() and date_str[len(matched_date_str):].strip() != "":
                    continue
                year, month, day = extractor(match)
                return datetime(year, month, day).date().isoformat()
            except ValueError:
                continue
    return None

# --- 데이터 추출 및 변환 함수 ---
def get_column_value_excel(row, standard_field_name, default=""):
    aliases = COLUMN_ALIASES_CONTACTS.get(standard_field_name, [])
    for alias in aliases:
        if alias in row.index and pd.notna(row[alias]):
            return str(row[alias]).strip()
    return default

def process_row_to_contact_dict(row_data, is_excel_row, current_year, line_display_prefix=""):
    contact_info = {
        'name_source': '', 'phone': '', 'address': '',
        'date': '', 'category': '', 'destination': '', 'notes': ''
    }
    error_msg = None

    if is_excel_row:
        contact_info['phone'] = get_column_value_excel(row_data, 'phone')
        contact_info['address'] = get_column_value_excel(row_data, 'address')
        contact_info['name_source'] = get_column_value_excel(row_data, 'name_source')
        contact_info['date'] = get_column_value_excel(row_data, 'date')
        contact_info['category'] = get_column_value_excel(row_data, 'category')
        contact_info['destination'] = get_column_value_excel(row_data, 'destination')
        contact_info['notes'] = get_column_value_excel(row_data, 'notes')
    else: # 텍스트 파싱 결과 (이미 딕셔너리)
        contact_info.update(row_data)

    if not contact_info['phone']: error_msg = f"{line_display_prefix}전화번호 없음 (필수)"
    elif not contact_info['address']: error_msg = f"{line_display_prefix}주소 없음 (필수)"
    
    if contact_info['date'] and not re.match(r'^\d{4}-\d{2}-\d{2}$', contact_info['date']):
        parsed_date_for_memo = parse_date_flexible_contacts(contact_info['date'], current_year)
        if parsed_date_for_memo: contact_info['date'] = parsed_date_for_memo

    if error_msg: return None, error_msg
    return contact_info, None


def parse_text_line_to_contact_dict(text_line, current_year, line_display_prefix=""):
    raw_line = text_line.strip()
    if not raw_line:
        return None, f"{line_display_prefix}빈 줄"

    contact_data = {'name_source': '', 'phone': '', 'address': '', 'date': '', 'category': '', 'destination': '', 'notes': ''}

    phone_match = PHONE_REGEX_TEXT.search(raw_line)
    if not phone_match:
        return None, f"{line_display_prefix}전화번호 없음 (필수)"
    contact_data['phone'] = phone_match.group(0)

    before_phone_text = raw_line[:phone_match.start()].strip()
    after_phone_text = raw_line[phone_match.end():].strip()

    # 전화번호 이전: 이름, 날짜
    potential_b_parts = [p.strip() for p in re.split(r'\t|\s{2,}', before_phone_text) if p.strip()]
    if not potential_b_parts and before_phone_text: potential_b_parts = [before_phone_text]
    
    temp_name_parts = []
    for part in potential_b_parts:
        parsed_date = parse_date_flexible_contacts(part, current_year)
        if parsed_date and not contact_data['date']: contact_data['date'] = parsed_date
        else: temp_name_parts.append(part)
    if temp_name_parts: contact_data['name_source'] = " ".join(temp_name_parts)

    # 전화번호 이후: [구분], 주소(필수), [도착지], [메모]
    # 탭 또는 여러 공백으로 분리. 단, 주소 내의 일반 공백은 유지해야 함.
    # 우선 탭으로 분리, 그 다음 각 덩어리를 공백 기준으로 추가 분석
    
    # 초기 분리 (탭 우선, 없으면 여러 공백)
    if '\t' in after_phone_text:
        after_phone_initial_parts = [p.strip() for p in after_phone_text.split('\t') if p.strip()]
    else: # 탭이 없으면, 여러 공백으로 시도 (하지만 주소 내 공백 유지 어려움)
          # 여기서는 주소를 하나의 긴 덩어리로 보고, '가'/'사'만 분리하는 전략
        after_phone_initial_parts = [p.strip() for p in re.split(r'\s{2,}', after_phone_text) if p.strip()]
        if not after_phone_initial_parts and after_phone_text: # 분리 안되면 전체를 한 덩어리로
            after_phone_initial_parts = [after_phone_text]

    remaining_parts = list(after_phone_initial_parts) # 복사해서 사용

    # 1. 구분 (category) 추출 시도
    if remaining_parts:
        first_part_lower = remaining_parts[0].lower()
        found_category = False
        for cat_name, keywords in MOVE_CATEGORY_KEYWORDS_TEXT.items():
            # 키워드가 정확히 일치하거나, 키워드로 시작하고 바로 뒤에 공백이 오는 경우
            for kw in keywords:
                if first_part_lower == kw or first_part_lower.startswith(kw + " "):
                    contact_data['category'] = cat_name # "가정" 또는 "사무실"로 저장
                    # 해당 부분을 remaining_parts[0]에서 제거
                    if first_part_lower == kw: # 정확히 일치
                        remaining_parts.pop(0)
                    else: # 키워드로 시작 (예: "가 서울...")
                        remaining_parts[0] = remaining_parts[0][len(kw):].strip()
                        if not remaining_parts[0]: # 제거 후 비었으면 pop
                            remaining_parts.pop(0)
                    found_category = True
                    break
            if found_category:
                break
    
    # 2. 주소 (address) 추출 (필수)
    if remaining_parts:
        # 남은 첫 번째 덩어리를 주소로 간주. 주소는 길 수 있으므로,
        # 다음 요소가 도착지나 메모의 시작처럼 보이지 않으면 현재 주소에 합침.
        # 여기서는 간단히 첫 번째 남은 요소를 주소로.
        contact_data['address'] = remaining_parts.pop(0)
    else: # 구분을 제외하고 남은 것이 없거나, 원래 아무것도 없었으면 주소 누락
        if not contact_data['address']: # category만 있고 주소가 없는 경우 방지
             return None, f"{line_display_prefix}주소 없음 (필수)"


    # 3. 도착지 (destination) 및 메모 (notes)
    # 남은 파트들을 순서대로 도착지, 그 다음 메모로 할당 (간단한 방식)
    if remaining_parts:
        # 도착지로 볼만한 패턴이 있는지? (예: "->", "도착:", 또는 단순히 두번째 주소 형태)
        # 여기서는 남은 첫번째를 도착지로 가정.
        contact_data['destination'] = remaining_parts.pop(0)
    
    if remaining_parts: # 그 이후 남은 모든 것은 notes
        contact_data['notes'] = " ".join(remaining_parts)
        
    # 주소 필드에서 혹시 '가' 또는 '사'가 단독으로 남아있으면 제거 (예: "가 서울" -> "서울")
    # 이 로직은 category 추출 후 주소 할당 전에 더 적합할 수 있음.
    # 현재는 category로 먼저 분리했으므로, address에 '가'/'사'가 남아있을 가능성은 낮음.

    return contact_data, None

# --- Streamlit UI (이전과 동일) ---
st.title("주소록 CSV 생성")
input_method = st.radio("입력 방식:", ('텍스트', '엑셀 파일'))
text_input = ""
uploaded_file = None

if input_method == '텍스트':
    text_input = st.text_area("텍스트 입력:", height=150, placeholder="여기에 주소록 정보를 한 줄씩 입력하세요...")
else: # 엑셀 파일
    uploaded_file = st.file_uploader("엑셀 파일 업로드", type=["xlsx", "xls"], label_visibility="collapsed")

if st.button("CSV 생성 및 다운로드"):
    current_year = datetime.now(KST).year
    contacts_for_csv = []
    processed_count = 0; skipped_count = 0
    all_log_messages = []; items_to_process = []; is_excel = False
    
    st.sidebar.empty()
    results_container = st.empty(); progress_bar = st.progress(0)

    if input_method == '텍스트':
        if not text_input.strip(): st.warning("입력 내용 없음")
        else: items_to_process = text_input.strip().split('\n')
    elif input_method == '엑셀 파일':
        if uploaded_file is None: st.warning("파일 선택 안됨")
        else:
            try:
                df = pd.read_excel(uploaded_file, engine='openpyxl'); df.columns = [str(col) for col in df.columns]
                items_to_process = [row for _, row in df.iterrows()]; is_excel = True
            except Exception:
                try:
                    uploaded_file.seek(0); df = pd.read_excel(uploaded_file, engine='xlrd'); df.columns = [str(col) for col in df.columns]
                    items_to_process = [row for _, row in df.iterrows()]; is_excel = True
                except Exception as e_read: st.error(f"파일 읽기 오류: {e_read}"); items_to_process = []
    
    total_items = len(items_to_process)

    if not items_to_process and (text_input.strip() or uploaded_file):
        st.info("처리할 데이터가 없습니다.")
    elif items_to_process:
        st.subheader("처리 결과")
        date_prefix_for_name = get_processing_date_str()

        for i, item_data in enumerate(items_to_process):
            line_display_prefix = f"엑셀 {i+2}행" if is_excel else f"텍스트 {i+1}줄"
            contact_dict_raw, error_msg_parse = (None, "초기화 오류")

            if is_excel:
                contact_dict_raw, error_msg_parse = process_row_to_contact_dict(item_data, True, current_year, line_display_prefix+": ")
            else: # 텍스트
                parsed_text_data, error_msg_text_parse = parse_text_line_to_contact_dict(item_data, current_year, line_display_prefix+": ")
                if parsed_text_data:
                    contact_dict_raw, error_msg_parse = process_row_to_contact_dict(parsed_text_data, False, current_year, line_display_prefix+": ")
                else:
                    error_msg_parse = error_msg_text_parse
            
            processed_count +=1
            progress_bar.progress(processed_count / total_items if total_items > 0 else 0)

            identifier_for_log = contact_dict_raw.get('phone', '') if contact_dict_raw else (item_data if not is_excel else '')
            if isinstance(identifier_for_log, pd.Series): identifier_for_log = identifier_for_log.get(COLUMN_ALIASES_CONTACTS['phone'][0], '') # 엑셀의 경우 대표 전화번호 컬럼

            log_identifier = f"({str(identifier_for_log)[:20]})"


            if contact_dict_raw and not error_msg_parse:
                phone_str = contact_dict_raw['phone']; phone_last_4 = extract_phone_digits(phone_str)
                csv_name = f"{date_prefix_for_name}-{phone_last_4}"
                csv_phone = phone_str; csv_address = contact_dict_raw['address']
                
                memo_parts = []
                if contact_dict_raw.get('name_source'): memo_parts.append(f"이름: {contact_dict_raw['name_source']}")
                if contact_dict_raw.get('date'): memo_parts.append(f"날짜: {contact_dict_raw['date']}")
                if contact_dict_raw.get('category'): memo_parts.append(f"구분: {contact_dict_raw['category']}") # '가정' 또는 '사무실'로 저장됨
                if contact_dict_raw.get('destination'): memo_parts.append(f"도착: {contact_dict_raw['destination']}")
                if contact_dict_raw.get('notes'): memo_parts.append(f"메모: {contact_dict_raw['notes']}")
                csv_memo = "\n".join(memo_parts)
                
                contacts_for_csv.append([csv_name, csv_phone, csv_address, csv_memo])
                all_log_messages.append(f"✅ 성공: {csv_name} {log_identifier}")
            else:
                skipped_count += 1
                all_log_messages.append(f"⚠️ 건너뜀: {error_msg_parse or '오류'} {log_identifier}")
        
        results_container.empty()
        st.info(f"총: {total_items} (시도: {processed_count})")
        st.info(f"성공 (CSV 포함): {len(contacts_for_csv)}")
        st.info(f"실패/건너뜀: {skipped_count}")

        if contacts_for_csv:
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["이름", "전화번호", "주소", "메모"])
            writer.writerows(contacts_for_csv)
            csv_bytes = csv_buffer.getvalue().encode('utf-8-sig')
            output_filename = f"주소록_{get_processing_date_str('%Y%m%d')}.csv"
            st.download_button(label=f"📥 '{output_filename}' 다운로드",data=csv_bytes,file_name=output_filename,mime='text/csv')
        
        if all_log_messages:
            with st.expander("상세 로그", expanded=(skipped_count > 0)):
                for log_entry in all_log_messages:
                    color = "grey"; text = log_entry
                    if log_entry.startswith("✅"): color = "green"; text = log_entry.replace("✅ ","")
                    elif log_entry.startswith("⚠️"): color = "orange"; text = log_entry.replace("⚠️ ","")
                    st.markdown(f"<p style='color:{color}; margin-bottom:0; font-size:small;'>{text}</p>", unsafe_allow_html=True)