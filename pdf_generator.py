# pdf_generator.py (VAT 레이블 동적 수정 적용됨)

import pandas as pd
import io
import streamlit as st
import traceback
import utils # utils.py 필요
import data # data.py 필요
import os
from datetime import date, datetime # datetime 추가

# --- ReportLab 관련 모듈 임포트 ---
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph # Spacer는 사용 안 함
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    _REPORTLAB_AVAILABLE = True
except ImportError as reportlab_error:
    st.error(f"ReportLab 라이브러리를 찾을 수 없습니다: {reportlab_error}")
    print(f"ERROR [PDF]: ReportLab not found. PDF generation disabled. {reportlab_error}")
    _REPORTLAB_AVAILABLE = False

# --- 이미지 변환 관련 모듈 임포트 ---
_PDF2IMAGE_AVAILABLE = False
_PILLOW_AVAILABLE = False
try:
    from pdf2image import convert_from_bytes
    # Poppler 경로 설정 (필요한 경우)
    # import platform
    # if platform.system() == "Windows":
    #     # 예: poppler_path = r"C:\path\to\poppler-xx.xx.x\bin"
    #     # os.environ["PATH"] += os.pathsep + poppler_path
    #     pass # 사용자가 환경에 맞게 설정하도록 안내
    _PDF2IMAGE_AVAILABLE = True
except ImportError:
    print("Warning [PDF_GENERATOR]: pdf2image 라이브러리를 찾을 수 없습니다. PDF를 이미지로 변환하는 기능이 비활성화됩니다.")
    # 주석 처리: st.warning("pdf2image 라이브러리가 설치되지 않았거나 Poppler 유틸리티 경로가 설정되지 않았습니다. PDF의 이미지 변환 기능이 제한됩니다.")
    # 사용자에게 반복적인 경고 대신 로그만 남기는 것이 좋을 수 있음

try:
    from PIL import Image
    _PILLOW_AVAILABLE = True
except ImportError:
    print("Warning [PDF_GENERATOR]: Pillow 라이브러리를 찾을 수 없습니다. 이미지 처리에 문제가 발생할 수 있습니다.")


# --- 회사 정보 상수 정의 ---
COMPANY_ADDRESS = "서울 은평구 가좌로10길 33-1"
COMPANY_PHONE_1 = "010-5047-1111"
COMPANY_PHONE_2 = "1577-3101"
COMPANY_EMAIL = "move24day@gmail.com"

# --- 폰트 경로 설정 ---
# 폰트 파일이 실행 스크립트와 같은 위치에 있다고 가정
# 필요시 절대 경로 또는 다른 상대 경로로 수정
FONT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
NANUM_GOTHIC_FONT_PATH = os.path.join(FONT_DIR, "NanumGothic.ttf")

# --- PDF 생성 함수 ---
def generate_pdf(state_data, calculated_cost_items, total_cost, personnel_info):
    """주어진 데이터를 기반으로 견적서 PDF를 생성합니다."""
    print("--- DEBUG [PDF]: Starting generate_pdf function ---")
    if not _REPORTLAB_AVAILABLE:
        st.error("PDF 생성을 위한 ReportLab 라이브러리가 없어 PDF를 생성할 수 없습니다.")
        return None

    buffer = io.BytesIO()
    try:
        # --- 폰트 파일 확인 및 등록 ---
        font_path = NANUM_GOTHIC_FONT_PATH
        if not os.path.exists(font_path):
            st.error(f"PDF 생성 오류: 폰트 파일 '{os.path.basename(font_path)}'을(를) 찾을 수 없습니다. (경로: {font_path})")
            print(f"ERROR [PDF]: Font file not found at '{font_path}'")
            # 대체 폰트 시도 또는 오류 반환
            # 예: font_name = 'Helvetica' # ReportLab 기본 폰트 사용 시도
            # return None # 또는 여기서 중단
            # 여기서는 일단 기본 폰트로 진행 시도 (한글 깨짐 발생 가능)
            font_name = 'Helvetica'
            font_name_bold = 'Helvetica-Bold'
            st.warning(f"나눔고딕 폰트 로드 실패. 기본 폰트({font_name})로 생성 시도 중 (한글이 깨질 수 있습니다).")
        else:
            try:
                font_name = 'NanumGothic'
                font_name_bold = 'NanumGothicBold' # Bold 폰트 파일이 별도로 없다면 일반 폰트로 대체될 수 있음
                if font_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    # Bold 폰트 파일이 동일 파일인지, 별도 파일인지 확인 필요
                    # 만약 NanumGothicBold.ttf 파일이 있다면 아래처럼 등록
                    # bold_font_path = os.path.join(FONT_DIR, "NanumGothicBold.ttf")
                    # if os.path.exists(bold_font_path):
                    #     pdfmetrics.registerFont(TTFont(font_name_bold, bold_font_path))
                    # else: # Bold 파일 없으면 일반으로 대체 등록 (두께 차이 없음)
                    pdfmetrics.registerFont(TTFont(font_name_bold, font_path))
                    print(f"DEBUG [PDF]: Font '{font_name}' registered.")
                else:
                    print(f"DEBUG [PDF]: Font '{font_name}' already registered.")
            except Exception as font_e:
                st.error(f"PDF 생성 오류: 폰트 로딩/등록 실패 ('{os.path.basename(font_path)}'). 상세: {font_e}")
                print(f"ERROR [PDF]: Failed to load/register font '{font_path}': {font_e}")
                traceback.print_exc()
                font_name = 'Helvetica' # 오류 시 기본 폰트로 대체
                font_name_bold = 'Helvetica-Bold'
                st.warning(f"폰트 처리 오류. 기본 폰트({font_name})로 생성 시도 중 (한글이 깨질 수 있습니다).")


        # --- Canvas 및 기본 설정 ---
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin_x = 1.5*cm
        margin_y = 1.5*cm
        line_height = 0.6*cm # 기본 줄 간격
        right_margin_x = width - margin_x # 오른쪽 정렬 기준
        page_number = 1

        # --- 페이지 템플릿 (상단 회사 정보) ---
        def draw_page_template(canvas_obj, page_num):
            canvas_obj.saveState()
            canvas_obj.setFont(font_name, 7) # 등록된 폰트 이름 사용
            company_info_line_height = 0.35 * cm
            company_info_y = height - margin_y
            canvas_obj.drawRightString(right_margin_x, company_info_y, f"주소: {COMPANY_ADDRESS}")
            company_info_y -= company_info_line_height
            canvas_obj.drawRightString(right_margin_x, company_info_y, f"전화: {COMPANY_PHONE_1} | {COMPANY_PHONE_2}")
            company_info_y -= company_info_line_height
            canvas_obj.drawRightString(right_margin_x, company_info_y, f"이메일: {COMPANY_EMAIL}")
            # 페이지 번호 추가 (선택 사항)
            # canvas_obj.drawCentredString(width / 2.0, margin_y / 2, f"- {page_num} -")
            canvas_obj.restoreState()

        # --- 초기 페이지 그리기 및 제목 ---
        current_y = height - margin_y - 1*cm
        draw_page_template(c, page_number)
        c.setFont(font_name_bold, 18) # 등록된 폰트 이름 사용
        c.drawCentredString(width / 2.0, current_y, "이삿날 견적서(계약서)")
        current_y -= line_height * 2

        # --- 안내 문구 ---
        styles = getSampleStyleSheet()
        # ParagraphStyle에 fontName 지정 필수
        center_style = ParagraphStyle(name='CenterStyle', fontName=font_name, fontSize=10, leading=14, alignment=TA_CENTER)
        service_text = """고객님의 이사를 안전하고 신속하게 책임지는 이삿날입니다."""
        p_service = Paragraph(service_text, center_style)
        p_service_width, p_service_height = p_service.wrapOn(c, width - margin_x*2, 5*cm)
        if current_y - p_service_height < margin_y:
            c.showPage(); page_number += 1; draw_page_template(c, page_number); current_y = height - margin_y - 1*cm
        p_service.drawOn(c, margin_x, current_y - p_service_height)
        current_y -= (p_service_height + line_height)


        # --- 기본 정보 그리기 ---
        c.setFont(font_name, 11) # 등록된 폰트 이름 사용
        is_storage = state_data.get('is_storage_move')
        has_via_point = state_data.get('has_via_point', False)

        kst_date_str = utils.get_current_kst_time_str("%Y-%m-%d") if utils and hasattr(utils, 'get_current_kst_time_str') else datetime.now().strftime("%Y-%m-%d")
        customer_name = state_data.get('customer_name', '-')
        customer_phone = state_data.get('customer_phone', '-')
        moving_date_val = state_data.get('moving_date', '-')
        moving_date_str = str(moving_date_val)
        if isinstance(moving_date_val, date):
             moving_date_str = moving_date_val.strftime('%Y-%m-%d')

        from_location = state_data.get('from_location', '-')
        to_location = state_data.get('to_location', '-')

        p_info = personnel_info if isinstance(personnel_info, dict) else {}
        final_men = p_info.get('final_men', 0)
        final_women = p_info.get('final_women', 0)
        personnel_text = f"남성 {final_men}명" + (f", 여성 {final_women}명" if final_women > 0 else "")
        selected_vehicle = state_data.get('final_selected_vehicle', '미선택')

        info_pairs = [
            ("고 객 명:", customer_name),
            ("연 락 처:", customer_phone),
            ("이 사 일:", moving_date_str),
            ("견 적 일:", kst_date_str),
            ("출 발 지:", from_location),
            ("도 착 지:", to_location),
        ]

        if has_via_point:
            info_pairs.append(("경 유 지:", state_data.get('via_point_location', '-')))
            info_pairs.append(("경유 작업:", state_data.get('via_point_method', '-')))

        if is_storage:
            storage_duration_str = f"{state_data.get('storage_duration', 1)} 일"
            storage_type = state_data.get('storage_type', data.DEFAULT_STORAGE_TYPE if data and hasattr(data, 'DEFAULT_STORAGE_TYPE') else "-")
            info_pairs.append(("보관 기간:", storage_duration_str))
            info_pairs.append(("보관 유형:", storage_type))
            if state_data.get('storage_use_electricity', False):
                 info_pairs.append(("보관 중 전기사용:", "예"))


        info_pairs.append(("작업 인원:", personnel_text))
        info_pairs.append(("선택 차량:", selected_vehicle))

        # ParagraphStyle에 fontName 지정 필수
        value_style = ParagraphStyle(name='InfoValueStyle', fontName=font_name, fontSize=11, leading=13)
        label_width = 3 * cm
        value_x = margin_x + label_width
        value_max_width = width - value_x - margin_x

        for label, value in info_pairs:
             value_para = Paragraph(str(value), value_style)
             value_para_width, value_para_height = value_para.wrapOn(c, value_max_width, line_height * 3) # 높이 여유
             row_height = max(line_height, value_para_height + 0.1*cm)

             if current_y - row_height < margin_y:
                 c.showPage(); page_number += 1; draw_page_template(c, page_number); current_y = height - margin_y - 1*cm
                 c.setFont(font_name, 11) # 페이지 넘김 후 폰트 재설정

             # 라벨 위치 조정 (폰트 크기 기준)
             # ReportLab에서 정확한 수직 정렬은 까다로움. 근사치 사용.
             label_y_pos = current_y - row_height + (row_height - 11) / 2 + 2 # 11은 fontSize 추정치
             c.drawString(margin_x, label_y_pos, label)

             # Paragraph 위치 조정
             para_y_pos = current_y - row_height + (row_height - value_para_height) / 2
             value_para.drawOn(c, value_x, para_y_pos)
             current_y -= row_height
        current_y -= line_height * 0.5

        # --- 비용 상세 내역 ---
        cost_start_y = current_y
        current_y -= 0.5*cm # 제목 전 간격

        # 페이지 하단 여백 확인 (비용 테이블 그리기 전)
        # 대략적인 테이블 높이 예상 (헤더 + 아이템 수 * 평균 높이 + 합계)
        estimated_table_height = (2 + len(calculated_cost_items) * 1.5 + 4) * line_height * 0.5
        if current_y - estimated_table_height < margin_y:
            c.showPage(); page_number += 1; draw_page_template(c, page_number)
            current_y = height - margin_y - 1*cm
            c.setFont(font_name, 11) # 페이지 넘김 후 폰트 재설정

        c.setFont(font_name_bold, 12) # 제목 폰트
        c.drawString(margin_x, current_y, "[ 비용 상세 내역 ]")
        current_y -= line_height * 1.2

        # 테이블 헤더
        c.setFont(font_name_bold, 10) # 헤더 폰트
        cost_col1_x = margin_x
        cost_col2_x = margin_x + 8*cm # 금액 시작 위치 (오른쪽 정렬 감안)
        cost_col3_x = margin_x + 11*cm # 비고 시작 위치
        c.drawString(cost_col1_x, current_y, "항목")
        # 금액 헤더 오른쪽 정렬
        c.drawRightString(cost_col2_x + 2*cm, current_y, "금액") # col2_x + 폭/2 정도 위치에서 오른쪽 정렬
        c.drawString(cost_col3_x, current_y, "비고")
        c.setFont(font_name, 10) # 본문 폰트 복귀
        current_y -= 0.2*cm # 선 위 간격
        c.line(cost_col1_x, current_y, right_margin_x, current_y) # 헤더 밑줄
        current_y -= line_height * 0.8

        # 비용 항목 처리 (날짜 할증 병합 로직 포함)
        cost_items_processed = []
        date_surcharge_amount = 0
        date_surcharge_index = -1
        temp_items = []
        if calculated_cost_items and isinstance(calculated_cost_items, list):
            temp_items = [list(item) for item in calculated_cost_items if isinstance(item, (list, tuple)) and len(item) >= 2 and "오류" not in str(item[0])]

        # 날짜 할증 찾기
        for i, item in enumerate(temp_items):
             if str(item[0]) == "날짜 할증":
                 try: date_surcharge_amount = int(item[1] or 0)
                 except (ValueError, TypeError): date_surcharge_amount = 0
                 date_surcharge_index = i
                 break

        # 기본 운임 찾아서 날짜 할증 병합 (존재할 경우)
        base_fare_index = -1
        for i, item in enumerate(temp_items):
              if str(item[0]) == "기본 운임":
                 base_fare_index = i
                 if date_surcharge_index != -1 and date_surcharge_amount > 0 :
                     try:
                         current_base_fare = int(item[1] or 0)
                         item[1] = current_base_fare + date_surcharge_amount # 기본 운임에 할증 합산
                         selected_vehicle_remark = state_data.get('final_selected_vehicle', '')
                         # 비고 업데이트
                         item[2] = f"{selected_vehicle_remark} (이사 집중일 운영 요금 적용)"
                     except Exception as e:
                         print(f"Error merging date surcharge into base fare: {e}")
                 break # 기본 운임 찾으면 종료

        # 날짜 할증 항목 제거 (병합된 경우)
        if date_surcharge_index != -1 and base_fare_index != -1 and date_surcharge_amount > 0:
              # 인덱스 유효성 검사 후 삭제
              if 0 <= date_surcharge_index < len(temp_items):
                  try:
                      del temp_items[date_surcharge_index]
                  except IndexError:
                      print(f"Warning: Could not remove date surcharge item at index {date_surcharge_index}")
              else:
                   print(f"Warning: date_surcharge_index {date_surcharge_index} out of range for temp_items")


        # 최종 처리된 비용 항목 리스트 생성
        for item_data in temp_items:
             item_desc = str(item_data[0])
             item_cost_int = 0
             item_note = ""
             try: item_cost_int = int(item_data[1] or 0)
             except (ValueError, TypeError): item_cost_int = 0
             if len(item_data) > 2:
                 item_note = str(item_data[2] or '')
             # 금액이 0인 항목은 제외할 수 있음 (선택적)
             # if item_cost_int == 0: continue
             cost_items_processed.append((item_desc, item_cost_int, item_note))

        # 비용 항목 그리기
        if cost_items_processed:
            # Paragraph 스타일 정의 (fontName 지정 필수)
            styleDesc = ParagraphStyle(name='CostDesc', fontName=font_name, fontSize=9, leading=11, alignment=TA_LEFT)
            styleCost = ParagraphStyle(name='CostAmount', fontName=font_name, fontSize=9, leading=11, alignment=TA_RIGHT)
            styleNote = ParagraphStyle(name='CostNote', fontName=font_name, fontSize=9, leading=11, alignment=TA_LEFT)

            for item_desc, item_cost, item_note in cost_items_processed:
                cost_str = f"{item_cost:,.0f} 원" if item_cost is not None else "0 원"
                note_str = item_note if item_note else ""

                p_desc = Paragraph(item_desc, styleDesc)
                p_cost = Paragraph(cost_str, styleCost)
                p_note = Paragraph(note_str, styleNote)

                # 컬럼 폭 계산 (고정 값 사용 또는 동적 계산)
                desc_width = cost_col2_x - cost_col1_x - 0.5*cm # 항목 컬럼 폭
                cost_width = (cost_col3_x - cost_col2_x) + 1.5*cm # 금액 컬럼 폭 (오른쪽 정렬 여유 포함)
                note_width = right_margin_x - cost_col3_x     # 비고 컬럼 폭

                # 각 Paragraph의 높이 계산
                desc_height = p_desc.wrap(desc_width, 1000)[1] # width, height 제한
                cost_height = p_cost.wrap(cost_width, 1000)[1]
                note_height = p_note.wrap(note_width, 1000)[1]
                # 해당 행의 최대 높이 결정
                max_row_height = max(desc_height, cost_height, note_height, line_height * 0.8) # 최소 높이 보장

                # 페이지 넘김 확인
                if current_y - max_row_height < margin_y:
                    c.showPage(); page_number += 1; draw_page_template(c, page_number)
                    current_y = height - margin_y - 1*cm
                    # 페이지 넘김 후 테이블 헤더 다시 그리기
                    c.setFont(font_name_bold, 10)
                    c.drawString(cost_col1_x, current_y, "항목")
                    c.drawRightString(cost_col2_x + 2*cm, current_y, "금액")
                    c.drawString(cost_col3_x, current_y, "비고")
                    current_y -= 0.2*cm; c.line(cost_col1_x, current_y, right_margin_x, current_y); current_y -= line_height * 0.8
                    c.setFont(font_name, 10) # 본문 폰트 복귀

                # Paragraph 그리기 (수직 정렬 시도)
                y_draw_base = current_y - max_row_height # 행의 시작 Y 좌표
                # 각 셀의 내용을 해당 행의 상단에 가깝게 그림 (수직 중앙 정렬 어려움)
                p_desc.drawOn(c, cost_col1_x, y_draw_base + (max_row_height - desc_height)) # 상단 정렬 비슷하게
                # 금액은 오른쪽 정렬 위치 계산: 컬럼 시작 X + 컬럼 폭 - Paragraph 폭
                p_cost.drawOn(c, cost_col2_x + 2*cm - cost_width, y_draw_base + (max_row_height - cost_height)) # 상단 정렬 비슷하게
                p_note.drawOn(c, cost_col3_x, y_draw_base + (max_row_height - note_height)) # 상단 정렬 비슷하게
                current_y -= (max_row_height + 0.2*cm) # 행 간격
        else:
             # 비용 항목 없을 때 메시지
             if current_y < margin_y + 3*cm : # 페이지 여백 확인
                 c.showPage(); page_number += 1; draw_page_template(c, page_number)
                 current_y = height - margin_y - 1*cm
             c.drawString(cost_col1_x, current_y, "계산된 비용 내역이 없습니다.")
             current_y -= line_height

        # --- 비용 요약 ---
        summary_start_y = current_y
        # 페이지 여백 확인 (요약 정보 그리기 전)
        if summary_start_y < margin_y + line_height * 5 : # 요약 4줄 정도 필요
            c.showPage(); page_number += 1; draw_page_template(c, page_number)
            summary_start_y = height - margin_y - 1*cm
            c.setFont(font_name, 11) # 페이지 넘김 후 폰트 재설정

        current_y = summary_start_y
        c.line(cost_col1_x, current_y, right_margin_x, current_y) # 비용 항목과 요약 구분선
        current_y -= line_height

        total_cost_num = 0
        if isinstance(total_cost, (int, float)):
            total_cost_num = int(total_cost)

        deposit_amount_raw = state_data.get('deposit_amount', state_data.get('tab3_deposit_amount', 0))
        deposit_amount = 0
        try: deposit_amount = int(deposit_amount_raw or 0)
        except (ValueError, TypeError): deposit_amount = 0
        remaining_balance = total_cost_num - deposit_amount

        # --- VAT 포함 여부 결정 (수정된 부분) ---
        vat_included = state_data.get('issue_tax_invoice', False)
        vat_label_suffix = "(VAT 포함)" if vat_included else "(VAT 별도)"
        # -------------------------------------

        c.setFont(font_name_bold, 12) # 요약 항목 폰트
        # 동적 레이블 사용
        total_cost_label = f"총 견적 비용 {vat_label_suffix}"
        c.drawString(cost_col1_x, current_y, total_cost_label)
        total_cost_str = f"{total_cost_num:,.0f} 원"
        c.setFont(font_name_bold, 14) # 총 금액 폰트 강조
        c.drawRightString(right_margin_x, current_y, total_cost_str)
        current_y -= line_height

        c.setFont(font_name, 11) # 계약금 폰트
        c.drawString(cost_col1_x, current_y, "계약금 (-)")
        deposit_str = f"{deposit_amount:,.0f} 원"
        c.setFont(font_name, 12) # 계약금 금액 폰트
        c.drawRightString(right_margin_x, current_y, deposit_str)
        current_y -= line_height

        c.setFont(font_name_bold, 12) # 잔금 폰트
        # 동적 레이블 사용
        remaining_label = f"잔금 {vat_label_suffix}"
        c.drawString(cost_col1_x, current_y, remaining_label)
        remaining_str = f"{remaining_balance:,.0f} 원"
        c.setFont(font_name_bold, 14) # 잔금 금액 폰트 강조
        c.drawRightString(right_margin_x, current_y, remaining_str)
        current_y -= line_height

        # --- 고객요구사항 그리기 ---
        special_notes = state_data.get('special_notes', '').strip()
        if special_notes:
            notes_section_start_y = current_y
            # 페이지 여백 확인 (요구사항 그리기 전)
            # 요구사항 높이 예측 어려우므로 대략적으로 확인
            if notes_section_start_y < margin_y + line_height * 3 :
                c.showPage(); page_number += 1; draw_page_template(c, page_number)
                current_y = height - margin_y - 1*cm; notes_section_start_y = current_y
                c.setFont(font_name, 11) # 페이지 넘김 후 폰트 재설정
            else:
                # 요구사항 제목 전 간격
                current_y -= line_height

            c.setFont(font_name_bold, 11) # 제목 폰트
            c.drawString(margin_x, current_y, "[ 고객요구사항 ]")
            current_y -= line_height * 1.2

            # Paragraph 스타일 (fontName 지정)
            styleNotes = ParagraphStyle(name='NotesParagraph', fontName=font_name, fontSize=10, leading=12, alignment=TA_LEFT)
            available_width = width - margin_x * 2 # 사용 가능한 폭

            # '.' 대신 개행 문자로 분리하도록 수정 (text_area는 보통 개행으로 구분)
            notes_parts = [part.strip().replace('\n', '<br/>') for part in special_notes.split('\n') if part.strip()]

            for note_part in notes_parts:
                if not note_part: continue # 빈 줄 건너뛰기
                p_part = Paragraph(note_part, styleNotes)
                part_width, part_height = p_part.wrapOn(c, available_width, 1000) # 높이 계산

                # 페이지 넘김 확인
                if current_y - part_height < margin_y:
                    c.showPage(); page_number += 1; draw_page_template(c, page_number)
                    current_y = height - margin_y - 1*cm
                    # 페이지 넘김 후 요구사항 제목 다시 그릴 필요는 없음 (선택적)
                    c.setFont(font_name, 11) # 폰트 재설정

                # Paragraph 그리기
                p_part.drawOn(c, margin_x, current_y - part_height)
                current_y -= (part_height + line_height * 0.2) # 줄 간격

        # --- PDF 저장 ---
        c.save()
        buffer.seek(0)
        print("--- DEBUG [PDF]: PDF generation successful ---")
        return buffer.getvalue()

    except Exception as e:
        st.error(f"PDF 생성 중 예외 발생: {e}")
        print(f"Error during PDF generation: {e}")
        traceback.print_exc()
        return None
    finally:
        # 메모리 버퍼는 닫지 않거나, 닫으려면 예외 처리 추가
        pass


# --- PDF를 이미지로 변환하는 함수 ---
def generate_quote_image_from_pdf(pdf_bytes, image_format='JPEG', poppler_path=None):
    """
    PDF 바이트를 이미지 바이트로 변환합니다.
    첫 번째 페이지만 이미지로 변환합니다.
    poppler_path: Windows에서 Poppler 바이너리 경로 (선택 사항)
    """
    if not _PDF2IMAGE_AVAILABLE:
        st.error("pdf2image 라이브러리가 없어 PDF를 이미지로 변환할 수 없습니다. Poppler 설치 및 경로 설정을 확인하세요.")
        return None
    if not _PILLOW_AVAILABLE:
        st.error("Pillow 라이브러리가 없어 이미지를 처리할 수 없습니다.")
        return None
    if not pdf_bytes:
        st.error("이미지로 변환할 PDF 데이터가 없습니다.")
        return None

    try:
        # convert_from_bytes에 poppler_path 인자 전달 (필요한 경우)
        # 환경 변수나 secrets 등으로 poppler 경로 관리 권장
        poppler_actual_path = poppler_path # 또는 st.secrets.get("poppler_path") 등
        images = convert_from_bytes(pdf_bytes, fmt=image_format.lower(), first_page=1, last_page=1, poppler_path=poppler_actual_path, thread_count=4) # thread_count 추가

        if images:
            img_byte_arr = io.BytesIO()
            img_to_save = images[0]
            # JPEG 저장 시 RGB 변환 (알파 채널 제거)
            if img_to_save.mode == 'RGBA' and image_format.upper() == 'JPEG':
                img_to_save = img_to_save.convert('RGB')

            # 이미지 품질 및 최적화 옵션 추가 (선택적)
            save_options = {'quality': 90} if image_format.upper() == 'JPEG' else {} # JPEG 품질 설정
            # save_options['optimize'] = True # PNG/JPEG 최적화

            img_to_save.save(img_byte_arr, format=image_format, **save_options)
            img_byte_arr = img_byte_arr.getvalue()
            print(f"--- DEBUG [PDF_TO_IMAGE]: PDF converted to {image_format} successfully ---")
            return img_byte_arr
        else:
            st.error("PDF에서 이미지를 추출하지 못했습니다.")
            return None
    except Exception as e:
        # pdf2image 예외는 상세 정보를 포함하는 경우가 많음
        st.error(f"PDF를 이미지로 변환하는 중 오류 발생: {e}")
        print(f"Error converting PDF to image: {e}")
        traceback.print_exc()
        # Poppler 관련 오류 메시지 추가
        if "poppler" in str(e).lower():
             st.info("Poppler가 시스템에 설치되어 있고 PATH에 등록되었는지 확인해주세요. Windows의 경우 Poppler 바이너리 경로를 직접 지정해야 할 수 있습니다.")
        return None


# --- 엑셀 생성 함수 (generate_excel) ---
# 이 함수는 변경되지 않았으므로 기존 코드 유지
def generate_excel(state_data, calculated_cost_items, total_cost, personnel_info):
    """
    주어진 데이터를 기반으로 요약 정보를 Excel 형식으로 생성합니다.
    (ui_tab3.py의 요약 표시에 사용됨, utils.get_item_qty 호출)
    경유지 정보 추가
    """
    print("--- DEBUG [Excel Summary]: Starting generate_excel function ---")
    output = io.BytesIO()
    try:
        # --- 기본 정보 준비 ---
        is_storage = state_data.get('is_storage_move', False)
        is_long_distance = state_data.get('apply_long_distance', False)
        is_waste = state_data.get('has_waste_check', False)
        has_via = state_data.get('has_via_point', False) # 경유지 유무

        from_method = state_data.get('from_method', '-')
        to_method = state_data.get('to_method', '-')
        to_floor = state_data.get('to_floor', '-')
        use_sky_from = (from_method == "스카이 🏗️")
        use_sky_to = (to_method == "스카이 🏗️")

        p_info = personnel_info if isinstance(personnel_info, dict) else {}
        final_men = p_info.get('final_men', 0)
        final_women = p_info.get('final_women', 0)
        personnel_text = f"남성 {final_men}명" + (f", 여성 {final_women}명" if final_women > 0 else "")
        dest_address = state_data.get('to_location', '-')

        kst_excel_date = ''
        if utils and hasattr(utils, 'get_current_kst_time_str'):
            try: kst_excel_date = utils.get_current_kst_time_str("%Y-%m-%d")
            except Exception as e_time: print(f"Warning: Error calling utils.get_current_kst_time_str: {e_time}"); kst_excel_date = datetime.now().strftime("%Y-%m-%d")
        else: print("Warning: utils module or get_current_kst_time_str not available."); kst_excel_date = datetime.now().strftime("%Y-%m-%d")

        # 1. '견적 정보' 시트 데이터 생성 (경유지 정보 추가)
        ALL_INFO_LABELS = [
            "회사명", "주소", "연락처", "이메일", "",
            "고객명", "고객 연락처", "견적일", "이사 종류", "",
            "이사일", "출발지", "도착지", "출발층", "도착층", "출발 작업", "도착 작업", "",
            "경유지 이사", "경유지 주소", "경유지 작업방법", "",
            "보관 이사", "보관 기간", "보관 유형", "보관 중 전기사용", "", # 전기사용 추가
            "장거리 적용", "장거리 구간", "",
            "스카이 사용 시간", "", "폐기물 처리(톤)", "", "날짜 할증 선택", "",
            "총 작업 인원", "", "선택 차량", "자동 추천 차량",
            "이사짐 총 부피", "이사짐 총 무게", "", "고객요구사항"
        ]
        info_data_list = []
        for label in ALL_INFO_LABELS:
            value = '-'
            if not label:
                info_data_list.append(("", ""))
                continue

            if label == "회사명": value = "(주)이사데이"
            elif label == "주소": value = COMPANY_ADDRESS
            elif label == "연락처": value = f"{COMPANY_PHONE_1} | {COMPANY_PHONE_2}"
            elif label == "이메일": value = COMPANY_EMAIL
            elif label == "고객명": value = state_data.get('customer_name', '-')
            elif label == "고객 연락처": value = state_data.get('customer_phone', '-')
            elif label == "견적일": value = kst_excel_date
            elif label == "이사 종류": value = state_data.get('base_move_type', '-')
            elif label == "이사일":
                move_date_val_excel = state_data.get('moving_date', '-')
                value = move_date_val_excel.strftime('%Y-%m-%d') if isinstance(move_date_val_excel, date) else str(move_date_val_excel)
            elif label == "출발지": value = state_data.get('from_location', '-')
            elif label == "도착지": value = dest_address
            elif label == "출발층": value = state_data.get('from_floor', '-')
            elif label == "도착층": value = to_floor
            elif label == "출발 작업": value = from_method
            elif label == "도착 작업": value = to_method
            elif label == "경유지 이사": value = '예' if has_via else '아니오'
            elif label == "경유지 주소": value = state_data.get('via_point_location', '-') if has_via else '-'
            elif label == "경유지 작업방법": value = state_data.get('via_point_method', '-') if has_via else '-'
            elif label == "보관 이사": value = '예' if is_storage else '아니오'
            elif label == "보관 기간":
                duration = state_data.get('storage_duration', '-')
                value = f"{duration} 일" if is_storage and duration != '-' else '-'
            elif label == "보관 유형": value = state_data.get('storage_type', '-') if is_storage else '-'
            elif label == "보관 중 전기사용": value = '예' if is_storage and state_data.get('storage_use_electricity', False) else ('아니오' if is_storage else '-')
            elif label == "장거리 적용": value = '예' if is_long_distance else '아니오'
            elif label == "장거리 구간": value = state_data.get('long_distance_selector', '-') if is_long_distance else '-'
            elif label == "스카이 사용 시간":
                 sky_details = []
                 if use_sky_from: sky_details.append(f"출발지 {state_data.get('sky_hours_from', 1)}시간")
                 if use_sky_to: sky_details.append(f"도착지 {state_data.get('sky_hours_final', 1)}시간")
                 value = ", ".join(sky_details) if sky_details else '-'
            elif label == "폐기물 처리(톤)": value = f"예 ({state_data.get('waste_tons_input', 0.5):.1f} 톤)" if is_waste else '아니오'
            elif label == "날짜 할증 선택":
                 date_options_list = ["이사많은날 🏠", "손없는날 ✋", "월말 📅", "공휴일 🎉", "금요일 📅"]
                 date_keys = [f"date_opt_{i}_widget" for i in range(len(date_options_list))]
                 # state_manager에서 동기화된 tab3_ 키 사용 고려
                 # selected_dates_excel = [date_options_list[i] for i, key in enumerate(date_keys) if state_data.get(f"tab3_{key}", False)]
                 selected_dates_excel = [date_options_list[i] for i, key in enumerate(date_keys) if state_data.get(key, False)] # 원본 유지
                 value = ", ".join(selected_dates_excel) if selected_dates_excel else '없음'
            elif label == "총 작업 인원": value = personnel_text
            elif label == "선택 차량": value = state_data.get('final_selected_vehicle', '미선택')
            elif label == "자동 추천 차량": value = state_data.get('recommended_vehicle_auto', '-')
            elif label == "이사짐 총 부피": value = f"{state_data.get('total_volume', 0.0):.2f} m³"
            elif label == "이사짐 총 무게": value = f"{state_data.get('total_weight', 0.0):.2f} kg"
            elif label == "고객요구사항": value = state_data.get('special_notes', '').strip() or '-'
            info_data_list.append((label, value))
        df_info = pd.DataFrame(info_data_list, columns=["항목", "내용"])

        # 2. '전체 품목 수량' 시트 데이터 생성 (utils.get_item_qty 사용)
        all_items_data = []
        current_move_type = state_data.get('base_move_type', '')
        item_defs = data.item_definitions.get(current_move_type, {}) if data and hasattr(data, 'item_definitions') else {}
        processed_all_items = set()
        if isinstance(item_defs, dict):
            for section, item_list in item_defs.items():
                if section == "폐기 처리 품목 🗑️": continue
                if isinstance(item_list, list):
                    for item_name in item_list:
                         if item_name in processed_all_items: continue
                         # data.items 유효성 검사 추가
                         if data and hasattr(data, 'items') and data.items is not None and item_name in data.items:
                              qty = 0
                              if utils and hasattr(utils, 'get_item_qty'):
                                   try: qty = utils.get_item_qty(state_data, item_name)
                                   except Exception as e_get_qty: print(f"Error calling utils.get_item_qty for {item_name}: {e_get_qty}")
                              else: print(f"Warning: utils module or get_item_qty not available.")
                              # 수량이 0보다 클 때만 추가 (선택적)
                              # if qty > 0:
                              all_items_data.append({"품목명": item_name, "수량": qty})
                              processed_all_items.add(item_name)
                         # else: print(f"Info: Item '{item_name}' not found in data.items") # 디버깅용

        if all_items_data:
            df_all_items = pd.DataFrame(all_items_data, columns=["품목명", "수량"])
        else:
            df_all_items = pd.DataFrame({"정보": ["정의된 품목 없음 또는 수량 없음"]})


        # 3. '비용 내역 및 요약' 시트 데이터 생성 (경유지 추가요금 포함)
        cost_details_excel = []
        if calculated_cost_items and isinstance(calculated_cost_items, list):
            for item in calculated_cost_items:
                 if isinstance(item, (list, tuple)) and len(item) >= 2:
                    item_desc = str(item[0])
                    item_cost = 0
                    item_note = ""
                    try: item_cost = int(item[1] or 0)
                    except (ValueError, TypeError): item_cost = 0
                    if len(item) > 2:
                         try: item_note = str(item[2] or '')
                         except Exception: item_note = ''

                    # 오류 항목 제외하고 추가
                    if "오류" not in item_desc:
                        # 금액 0인 항목 포함 또는 제외 결정
                        # if item_cost != 0:
                        cost_details_excel.append({"항목": item_desc, "금액": item_cost, "비고": item_note})

        if cost_details_excel:
            df_costs = pd.DataFrame(cost_details_excel, columns=["항목", "금액", "비고"])
        else:
            df_costs = pd.DataFrame([{"항목": "계산된 비용 없음", "금액": 0, "비고": ""}])

        num_total = total_cost if isinstance(total_cost,(int,float)) else 0
        # state_manager와 일관성 있게 tab3_ 키 사용 고려
        # deposit_raw = state_data.get('tab3_deposit_amount', 0)
        deposit_raw = state_data.get('deposit_amount', 0) # 원본 유지
        try: deposit_amount = int(deposit_raw or 0)
        except (ValueError, TypeError): deposit_amount = 0

        remaining_balance = num_total - deposit_amount

        # VAT 포함 여부에 따른 레이블 동적 생성
        vat_included_excel = state_data.get('issue_tax_invoice', False)
        vat_label_suffix_excel = "(VAT 포함)" if vat_included_excel else "(VAT 별도)"

        summary_data = [
            {"항목": "--- 비용 요약 ---", "금액": "", "비고": ""},
            {"항목": f"총 견적 비용 {vat_label_suffix_excel}", "금액": num_total, "비고": "모든 항목 합계"},
            {"항목": "계약금 (-)", "금액": deposit_amount, "비고": ""},
            {"항목": f"잔금 {vat_label_suffix_excel}", "금액": remaining_balance, "비고": "총 견적 비용 - 계약금"}
        ]
        df_summary = pd.DataFrame(summary_data, columns=["항목", "금액", "비고"])
        df_costs_final = pd.concat([df_costs, df_summary], ignore_index=True)


        # 4. 엑셀 파일 쓰기 및 서식 지정 (컬럼 너비 계산 수정됨)
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_info.to_excel(writer, sheet_name='견적 정보', index=False)
            df_all_items.to_excel(writer, sheet_name='전체 품목 수량', index=False)
            df_costs_final.to_excel(writer, sheet_name='비용 내역 및 요약', index=False)

            # openpyxl 워크북/시트 객체 가져오기
            workbook = writer.book
            ws_info = writer.sheets['견적 정보']
            ws_items = writer.sheets['전체 품목 수량']
            ws_costs = writer.sheets['비용 내역 및 요약']

            # 숫자 서식 지정 (천단위 쉼표)
            num_format = '#,##0'
            # 서식 적용할 컬럼 지정 (예시)
            cost_cols_to_format = ['B'] # 비용 시트의 금액 컬럼
            item_cols_to_format = ['B'] # 품목 시트의 수량 컬럼 (필요시)

            for ws in [ws_info, ws_items, ws_costs]:
                 cols_to_format = []
                 if ws.title == '비용 내역 및 요약': cols_to_format = cost_cols_to_format
                 elif ws.title == '전체 품목 수량': cols_to_format = item_cols_to_format
                 # 다른 시트에도 숫자 서식 필요시 추가

                 for col_letter in cols_to_format:
                     # 헤더 제외하고 서식 적용 (2행부터)
                     for row in range(2, ws.max_row + 1):
                         cell = ws[f'{col_letter}{row}']
                         # 숫자형 데이터에만 서식 적용 시도
                         if isinstance(cell.value, (int, float)):
                              cell.number_format = num_format

            # 컬럼 너비 자동 조절 (개선된 로직)
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for col in worksheet.columns:
                    max_length = 0
                    column = col[0].column_letter # 열 문자 얻기 (A, B, C...)

                    try: # 헤더 길이 계산
                        header_value = worksheet[f"{column}1"].value
                        # 한글/영문 고려한 대략적인 길이 계산 (글꼴 따라 달라질 수 있음)
                        header_len = sum(2 if '\uac00' <= char <= '\ud7a3' else 1 for char in str(header_value)) if header_value else 0
                        max_length = header_len
                    except Exception:
                        header_len = 0
                        max_length = 0

                    # 각 셀 내용 길이 계산 (헤더 제외)
                    for cell in col[1:]: # col[0]은 헤더 셀
                        try:
                            if cell.value is not None:
                                # 숫자이고 서식이 지정된 경우, 서식 적용된 길이 추정
                                if isinstance(cell.value, (int, float)) and cell.number_format == num_format:
                                     cell_text = f"{cell.value:,}" # 천단위 쉼표 포함 문자열
                                else:
                                     cell_text = str(cell.value)

                                # 여러 줄 텍스트 처리 (가장 긴 줄 기준)
                                lines = cell_text.split('\n')
                                current_max_line_len = 0
                                if lines:
                                     line_lengths = [sum(2 if '\uac00' <= char <= '\ud7a3' else 1 for char in str(line or '')) for line in lines]
                                     if line_lengths: current_max_line_len = max(line_lengths)

                                if current_max_line_len > max_length:
                                    max_length = current_max_line_len
                        except Exception as cell_proc_err:
                             print(f"Warning: Error processing cell {cell.coordinate} for width calc: {cell_proc_err}")

                    # 최종 너비 조정 (약간의 여유 추가)
                    adjusted_width = max_length + 2 # 기본 여유 2
                    # 최소/최대 너비 제한 (선택적)
                    adjusted_width = max(adjusted_width, 8) # 최소 8
                    adjusted_width = min(adjusted_width, 50) # 최대 50
                    worksheet.column_dimensions[column].width = adjusted_width

        excel_data = output.getvalue()
        print("--- DEBUG [Excel Summary]: generate_excel function finished successfully ---")
        return excel_data
    except Exception as e:
        st.error(f"엑셀 파일 생성 중 오류: {e}")
        print(f"Error during Excel generation: {e}")
        traceback.print_exc()
        return None
    finally:
        # BytesIO 객체는 with 구문 밖에서 자동으로 닫히므로 명시적 close 불필요
        pass

# pdf_generator.py 파일 끝