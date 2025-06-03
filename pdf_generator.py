# pdf_generator.py (일부 비용 항목 병합 및 숨김 처리)

import pandas as pd
import io
import streamlit as st
import traceback
import utils # utils.py 필요
import data # data.py 필요
import os
from datetime import date, datetime

# --- ReportLab 관련 모듈 임포트 ---
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import Paragraph
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
    _PDF2IMAGE_AVAILABLE = True
except ImportError:
    print("Warning [PDF_GENERATOR]: pdf2image 라이브러리를 찾을 수 없습니다. PDF를 이미지로 변환하는 기능이 비활성화됩니다.")

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
FONT_DIR = os.path.dirname(os.path.abspath(__file__)) if "__file__" in locals() else "."
NANUM_GOTHIC_FONT_PATH = os.path.join(FONT_DIR, "NanumGothic.ttf")

# --- PDF 생성 함수 ---
def generate_pdf(state_data, calculated_cost_items, total_cost, personnel_info):
    if not _REPORTLAB_AVAILABLE:
        st.error("PDF 생성을 위한 ReportLab 라이브러리가 없어 PDF를 생성할 수 없습니다.")
        return None

    buffer = io.BytesIO()
    try:
        font_path = NANUM_GOTHIC_FONT_PATH
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'
        if os.path.exists(font_path):
            try:
                font_name = 'NanumGothic'
                font_name_bold = 'NanumGothicBold' 
                if font_name not in pdfmetrics.getRegisteredFontNames():
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                bold_font_path_candidate = os.path.join(FONT_DIR, "NanumGothicBold.ttf") 
                if os.path.exists(bold_font_path_candidate) and font_name_bold not in pdfmetrics.getRegisteredFontNames():
                     pdfmetrics.registerFont(TTFont(font_name_bold, bold_font_path_candidate))
                elif font_name_bold not in pdfmetrics.getRegisteredFontNames(): 
                     pdfmetrics.registerFont(TTFont(font_name_bold, font_path)) 

            except Exception as font_e:
                st.error(f"PDF 생성 오류: 폰트 로딩/등록 실패 ('{os.path.basename(font_path)}'). 상세: {font_e}")
                font_name = 'Helvetica'
                font_name_bold = 'Helvetica-Bold'
        else:
            st.warning(f"나눔고딕 폰트 파일({NANUM_GOTHIC_FONT_PATH})을 찾을 수 없습니다. 기본 폰트로 생성됩니다 (한글 깨짐 가능).")


        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        margin_x = 1.5*cm
        margin_y = 1.5*cm
        line_height = 0.6*cm
        right_margin_x = width - margin_x
        page_number = 1

        def draw_page_template(canvas_obj, page_num):
            canvas_obj.saveState()
            canvas_obj.setFont(font_name, 7)
            company_info_line_height = 0.35 * cm
            company_info_y = height - margin_y
            canvas_obj.drawRightString(right_margin_x, company_info_y, f"주소: {COMPANY_ADDRESS}")
            company_info_y -= company_info_line_height
            canvas_obj.drawRightString(right_margin_x, company_info_y, f"전화: {COMPANY_PHONE_1} | {COMPANY_PHONE_2}")
            company_info_y -= company_info_line_height
            canvas_obj.drawRightString(right_margin_x, company_info_y, f"이메일: {COMPANY_EMAIL}")
            canvas_obj.restoreState()

        current_y = height - margin_y - 1*cm
        draw_page_template(c, page_number)
        c.setFont(font_name_bold, 18)
        c.drawCentredString(width / 2.0, current_y, "이삿날 견적서(계약서)")
        current_y -= line_height * 2

        styles = getSampleStyleSheet()
        center_style = ParagraphStyle(name='CenterStyle', fontName=font_name, fontSize=10, leading=14, alignment=TA_CENTER)
        service_text = """고객님의 이사를 안전하고 신속하게 책임지는 이삿날입니다."""
        p_service = Paragraph(service_text, center_style)
        p_service_width, p_service_height = p_service.wrapOn(c, width - margin_x*2, 5*cm)
        if current_y - p_service_height < margin_y:
            c.showPage(); page_number += 1; draw_page_template(c, page_number); current_y = height - margin_y - 1*cm
        p_service.drawOn(c, margin_x, current_y - p_service_height)
        current_y -= (p_service_height + line_height)

        c.setFont(font_name, 11)
        is_storage = state_data.get('is_storage_move')
        has_via_point = state_data.get('has_via_point', False)

        kst_date_str = utils.get_current_kst_time_str("%Y-%m-%d") if utils and hasattr(utils, 'get_current_kst_time_str') else datetime.now().strftime("%Y-%m-%d")
        customer_name = state_data.get('customer_name', '-')
        customer_phone = state_data.get('customer_phone', '-')
        moving_date_val = state_data.get('moving_date', '-')
        moving_date_str = str(moving_date_val)
        if isinstance(moving_date_val, date):
             moving_date_str = moving_date_val.strftime('%Y-%m-%d')

        from_location_pdf = state_data.get('from_address_full', state_data.get('from_location', '-'))
        to_location_pdf = state_data.get('to_address_full', state_data.get('to_location', '-'))

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
            ("출 발 지:", from_location_pdf), 
            ("도 착 지:", to_location_pdf),   
        ]

        if has_via_point:
            via_location_display_pdf = state_data.get('via_point_address', state_data.get('via_point_location', '-')) 
            info_pairs.append(("경 유 지:", via_location_display_pdf))
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

        value_style = ParagraphStyle(name='InfoValueStyle', fontName=font_name, fontSize=11, leading=13)
        label_width = 3 * cm
        value_x = margin_x + label_width
        value_max_width = width - value_x - margin_x

        for label, value in info_pairs:
             value_para = Paragraph(str(value), value_style)
             value_para_width, value_para_height = value_para.wrapOn(c, value_max_width, line_height * 3)
             row_height = max(line_height, value_para_height + 0.1*cm)

             if current_y - row_height < margin_y:
                 c.showPage(); page_number += 1; draw_page_template(c, page_number); current_y = height - margin_y - 1*cm
                 c.setFont(font_name, 11)

             label_y_pos = current_y - row_height + (row_height - 11) / 2 + 2
             c.drawString(margin_x, label_y_pos, label)
             para_y_pos = current_y - row_height + (row_height - value_para_height) / 2
             value_para.drawOn(c, value_x, para_y_pos)
             current_y -= row_height
        current_y -= line_height * 0.5

        cost_start_y = current_y
        current_y -= 0.5*cm

        estimated_table_height = (2 + len(calculated_cost_items) * 1.5 + 4) * line_height * 0.5
        if current_y - estimated_table_height < margin_y:
            c.showPage(); page_number += 1; draw_page_template(c, page_number)
            current_y = height - margin_y - 1*cm
            c.setFont(font_name, 11)

        c.setFont(font_name_bold, 12)
        c.drawString(margin_x, current_y, "[ 비용 상세 내역 ]")
        current_y -= line_height * 1.2

        c.setFont(font_name_bold, 10)
        cost_col1_x = margin_x
        cost_col2_x = margin_x + 8*cm
        cost_col3_x = margin_x + 11*cm
        c.drawString(cost_col1_x, current_y, "항목")
        c.drawRightString(cost_col2_x + 2*cm, current_y, "금액")
        c.drawString(cost_col3_x, current_y, "비고")
        c.setFont(font_name, 10)
        current_y -= 0.2*cm
        c.line(cost_col1_x, current_y, right_margin_x, current_y)
        current_y -= line_height * 0.8

        # --- 비용 항목 가공 시작 (PDF 표시용) ---
        working_items = []
        if calculated_cost_items and isinstance(calculated_cost_items, list):
            working_items = [list(item) for item in calculated_cost_items if isinstance(item, (list, tuple)) and len(item) >= 2 and "오류" not in str(item[0])]

        # 1. 날짜 할증 처리
        date_surcharge_total = 0
        date_surcharge_applied = False
        date_surcharge_indices_to_remove = []
        base_fare_item_ref = None

        for i, item_list in enumerate(working_items):
            item_name = str(item_list[0])
            if item_name == "날짜 할증":
                try:
                    date_surcharge_total += int(item_list[1] or 0)
                    date_surcharge_applied = True
                    date_surcharge_indices_to_remove.append(i)
                except (ValueError, TypeError):
                    pass
            elif item_name == "기본 운임":
                base_fare_item_ref = item_list # Keep reference to modify directly

        if base_fare_item_ref and date_surcharge_applied and date_surcharge_total > 0:
            try:
                current_base_fare_cost = int(base_fare_item_ref[1] or 0)
                base_fare_item_ref[1] = current_base_fare_cost + date_surcharge_total
                
                # 비고 업데이트 (기존 비고에 추가 또는 새로 설정)
                original_note = str(base_fare_item_ref[2] if len(base_fare_item_ref) > 2 and base_fare_item_ref[2] else "")
                vehicle_remark = state_data.get('final_selected_vehicle', '')
                if not original_note or not original_note.startswith(vehicle_remark): # 비고가 없거나 차량명으로 시작 안하면
                    original_note = f"{vehicle_remark} 기준"
                
                base_fare_item_ref[2] = f"{original_note} (이사 집중일 운영 요금 적용)"
            except Exception as e_ds_merge:
                print(f"PDF Gen: Error merging date surcharge: {e_ds_merge}")

        for index in sorted(date_surcharge_indices_to_remove, reverse=True):
            del working_items[index]

        # 2. 수동 사다리 비용 처리
        departure_manual_ladder_surcharge = 0
        arrival_manual_ladder_surcharge = 0
        manual_ladder_indices_to_remove = []

        for i, item_list in enumerate(working_items):
            item_name = str(item_list[0])
            cost = 0
            try: cost = int(item_list[1] or 0)
            except: pass

            if item_name == "출발지 수동 사다리 추가" or item_name == "출발지 수동 사다리 할인":
                departure_manual_ladder_surcharge += cost
                manual_ladder_indices_to_remove.append(i)
            elif item_name == "도착지 수동 사다리 추가" or item_name == "도착지 수동 사다리 할인":
                arrival_manual_ladder_surcharge += cost
                manual_ladder_indices_to_remove.append(i)
        
        # 수동 사다리 비용 병합 함수
        def merge_manual_surcharge(items_list, surcharge_amount, primary_target_prefix, secondary_target_prefix, fallback_target_name, note_suffix):
            if surcharge_amount == 0:
                return False # 변경 없음

            merged = False
            # 1순위: "사다리차"
            for item_list in items_list:
                if str(item_list[0]).startswith(primary_target_prefix + " 사다리차"):
                    item_list[1] = int(item_list[1] or 0) + surcharge_amount
                    item_list[2] = str(item_list[2] or "") + note_suffix
                    merged = True
                    break
            if merged: return True
            
            # 2순위: "스카이 장비"
            for item_list in items_list:
                if str(item_list[0]).startswith(primary_target_prefix + " 스카이 장비"):
                    item_list[1] = int(item_list[1] or 0) + surcharge_amount
                    item_list[2] = str(item_list[2] or "") + note_suffix
                    merged = True
                    break
            if merged: return True

            # 3순위: "기본 운임"
            for item_list in items_list:
                if str(item_list[0]) == fallback_target_name: # "기본 운임"
                    item_list[1] = int(item_list[1] or 0) + surcharge_amount
                    item_list[2] = str(item_list[2] or "") + f" ({primary_target_prefix} 수동조정 포함)"
                    merged = True
                    break
            return merged

        note_add_manual = " (+수동조정)" # 비고에 추가할 문자열

        merge_manual_surcharge(working_items, departure_manual_ladder_surcharge, "출발지", "출발지", "기본 운임", note_add_manual)
        merge_manual_surcharge(working_items, arrival_manual_ladder_surcharge, "도착지", "도착지", "기본 운임", note_add_manual)

        for index in sorted(manual_ladder_indices_to_remove, reverse=True):
            del working_items[index]
        
        # 최종 PDF 표시용 비용 항목 리스트 생성
        cost_items_processed_for_pdf = []
        for item_data_list in working_items: # working_items는 모든 병합/삭제 처리 후의 리스트
            item_desc_pdf = str(item_data_list[0])
            item_cost_int_pdf = 0
            item_note_pdf = ""
            try:
                item_cost_int_pdf = int(item_data_list[1] or 0)
            except (ValueError, TypeError):
                item_cost_int_pdf = 0
            if len(item_data_list) > 2:
                item_note_pdf = str(item_data_list[2] or '')
            
            is_discount_or_negative = "할인" in item_desc_pdf or item_cost_int_pdf < 0
            if item_desc_pdf != "보관료" and item_cost_int_pdf == 0 and not is_discount_or_negative:
                continue
            cost_items_processed_for_pdf.append((item_desc_pdf, item_cost_int_pdf, item_note_pdf))
        # --- 비용 항목 가공 끝 ---


        if cost_items_processed_for_pdf: 
            styleDesc = ParagraphStyle(name='CostDesc', fontName=font_name, fontSize=9, leading=11, alignment=TA_LEFT)
            styleCost = ParagraphStyle(name='CostAmount', fontName=font_name, fontSize=9, leading=11, alignment=TA_RIGHT)
            styleNote = ParagraphStyle(name='CostNote', fontName=font_name, fontSize=9, leading=11, alignment=TA_LEFT)

            for item_desc, item_cost, item_note in cost_items_processed_for_pdf: 
                cost_str = f"{item_cost:,.0f} 원" if item_cost is not None else "0 원"
                note_str = item_note if item_note else ""
                p_desc = Paragraph(item_desc, styleDesc)
                p_cost = Paragraph(cost_str, styleCost)
                p_note = Paragraph(note_str, styleNote)
                desc_width = cost_col2_x - cost_col1_x - 0.5*cm
                cost_width = (cost_col3_x - cost_col2_x) + 1.5*cm
                note_width = right_margin_x - cost_col3_x
                desc_height = p_desc.wrap(desc_width, 1000)[1]
                cost_height = p_cost.wrap(cost_width, 1000)[1]
                note_height = p_note.wrap(note_width, 1000)[1]
                max_row_height = max(desc_height, cost_height, note_height, line_height * 0.8)

                if current_y - max_row_height < margin_y:
                    c.showPage(); page_number += 1; draw_page_template(c, page_number)
                    current_y = height - margin_y - 1*cm
                    c.setFont(font_name_bold, 10)
                    c.drawString(cost_col1_x, current_y, "항목")
                    c.drawRightString(cost_col2_x + 2*cm, current_y, "금액")
                    c.drawString(cost_col3_x, current_y, "비고")
                    current_y -= 0.2*cm; c.line(cost_col1_x, current_y, right_margin_x, current_y); current_y -= line_height * 0.8
                    c.setFont(font_name, 10)

                y_draw_base = current_y - max_row_height
                p_desc.drawOn(c, cost_col1_x, y_draw_base + (max_row_height - desc_height))
                p_cost.drawOn(c, cost_col2_x + 2*cm - cost_width, y_draw_base + (max_row_height - cost_height))
                p_note.drawOn(c, cost_col3_x, y_draw_base + (max_row_height - note_height))
                current_y -= (max_row_height + 0.2*cm)
        else:
             if current_y < margin_y + 3*cm :
                 c.showPage(); page_number += 1; draw_page_template(c, page_number)
                 current_y = height - margin_y - 1*cm
             c.drawString(cost_col1_x, current_y, "계산된 비용 내역이 없습니다.")
             current_y -= line_height

        summary_start_y = current_y
        if summary_start_y < margin_y + line_height * 5 :
            c.showPage(); page_number += 1; draw_page_template(c, page_number)
            summary_start_y = height - margin_y - 1*cm
            c.setFont(font_name, 11)

        current_y = summary_start_y
        c.line(cost_col1_x, current_y, right_margin_x, current_y)
        current_y -= line_height

        total_cost_num = 0
        if isinstance(total_cost, (int, float)): # total_cost는 이미 모든 계산이 반영된 최종 금액
            total_cost_num = int(total_cost)

        deposit_amount_raw = state_data.get('deposit_amount', state_data.get('tab3_deposit_amount', 0))
        deposit_amount = 0
        try: deposit_amount = int(deposit_amount_raw or 0)
        except (ValueError, TypeError): deposit_amount = 0
        remaining_balance = total_cost_num - deposit_amount

        is_tax_invoice_selected_pdf = state_data.get('issue_tax_invoice', False)
        is_card_payment_selected_pdf = state_data.get('card_payment', False)
        
        final_total_label_suffix = ""
        if is_card_payment_selected_pdf:
            final_total_label_suffix = "(카드수수료 포함)" 
        elif is_tax_invoice_selected_pdf:
            final_total_label_suffix = "(VAT 포함)"
        else:
            final_total_label_suffix = "(VAT 별도)"

        c.setFont(font_name_bold, 12)
        total_cost_label_pdf = f"총 견적 비용 {final_total_label_suffix}" 
        c.drawString(cost_col1_x, current_y, total_cost_label_pdf)
        total_cost_str = f"{total_cost_num:,.0f} 원"
        c.setFont(font_name_bold, 14)
        c.drawRightString(right_margin_x, current_y, total_cost_str)
        current_y -= line_height

        c.setFont(font_name, 11)
        c.drawString(cost_col1_x, current_y, "계약금 (현금)") 
        deposit_str = f"{deposit_amount:,.0f} 원"
        c.setFont(font_name, 12)
        c.drawRightString(right_margin_x, current_y, deposit_str)
        current_y -= line_height

        c.setFont(font_name_bold, 12)
        remaining_label_pdf = f"잔금 {final_total_label_suffix}" 
        c.drawString(cost_col1_x, current_y, remaining_label_pdf)
        remaining_str = f"{remaining_balance:,.0f} 원"
        c.setFont(font_name_bold, 14)
        c.drawRightString(right_margin_x, current_y, remaining_str)
        current_y -= line_height

        special_notes = state_data.get('special_notes', '').strip()
        if special_notes:
            notes_section_start_y = current_y
            if notes_section_start_y < margin_y + line_height * 3 :
                c.showPage(); page_number += 1; draw_page_template(c, page_number)
                current_y = height - margin_y - 1*cm; notes_section_start_y = current_y
                c.setFont(font_name, 11)
            else:
                current_y -= line_height

            c.setFont(font_name_bold, 11)
            c.drawString(margin_x, current_y, "[ 고객요구사항 ]")
            current_y -= line_height * 1.2

            styleNotes = ParagraphStyle(name='NotesParagraph', fontName=font_name, fontSize=10, leading=12, alignment=TA_LEFT)
            available_width = width - margin_x * 2
            notes_parts = [part.strip().replace('\n', '<br/>') for part in special_notes.split('\n') if part.strip()]

            for note_part in notes_parts:
                if not note_part: continue
                p_part = Paragraph(note_part, styleNotes)
                part_width, part_height = p_part.wrapOn(c, available_width, 1000)

                if current_y - part_height < margin_y:
                    c.showPage(); page_number += 1; draw_page_template(c, page_number)
                    current_y = height - margin_y - 1*cm
                    c.setFont(font_name, 11)

                p_part.drawOn(c, margin_x, current_y - part_height)
                current_y -= (part_height + line_height * 0.2)

        c.save()
        buffer.seek(0)
        return buffer.getvalue()

    except Exception as e:
        st.error(f"PDF 생성 중 예외 발생: {e}")
        print(f"Error during PDF generation: {e}")
        traceback.print_exc()
        return None

# --- PDF를 이미지로 변환하는 함수 ---
def generate_quote_image_from_pdf(pdf_bytes, image_format='JPEG', poppler_path=None):
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
        poppler_actual_path = poppler_path
        images = convert_from_bytes(pdf_bytes, fmt=image_format.lower(), first_page=1, last_page=1, poppler_path=poppler_actual_path, thread_count=4)

        if images:
            img_byte_arr = io.BytesIO()
            img_to_save = images[0]
            if img_to_save.mode == 'RGBA' and image_format.upper() == 'JPEG':
                img_to_save = img_to_save.convert('RGB')
            save_options = {'quality': 90} if image_format.upper() == 'JPEG' else {}
            img_to_save.save(img_byte_arr, format=image_format, **save_options)
            img_byte_arr = img_byte_arr.getvalue()
            return img_byte_arr
        else:
            st.error("PDF에서 이미지를 추출하지 못했습니다.")
            return None
    except Exception as e:
        st.error(f"PDF를 이미지로 변환하는 중 오류 발생: {e}")
        print(f"Error converting PDF to image: {e}")
        traceback.print_exc()
        if "poppler" in str(e).lower():
             st.info("Poppler가 시스템에 설치되어 있고 PATH에 등록되었는지 확인해주세요. Windows의 경우 Poppler 바이너리 경로를 직접 지정해야 할 수 있습니다.")
        return None

# --- 엑셀 생성 함수 (generate_excel) ---
def generate_excel(state_data, calculated_cost_items, total_cost, personnel_info):
    output = io.BytesIO()
    try:
        is_storage = state_data.get('is_storage_move', False)
        is_long_distance = state_data.get('apply_long_distance', False)
        is_waste = state_data.get('has_waste_check', False)
        has_via = state_data.get('has_via_point', False)

        from_method = state_data.get('from_method', '-')
        to_method = state_data.get('to_method', '-')
        to_floor = state_data.get('to_floor', '-')
        use_sky_from = (from_method == "스카이 🏗️")
        use_sky_to = (to_method == "스카이 🏗️")

        p_info = personnel_info if isinstance(personnel_info, dict) else {}
        final_men = p_info.get('final_men', 0)
        final_women = p_info.get('final_women', 0)
        personnel_text = f"남성 {final_men}명" + (f", 여성 {final_women}명" if final_women > 0 else "")
        dest_address = state_data.get('to_address_full', state_data.get('to_location', '-')) 

        kst_excel_date = ''
        if utils and hasattr(utils, 'get_current_kst_time_str'):
            try: kst_excel_date = utils.get_current_kst_time_str("%Y-%m-%d")
            except Exception as e_time: print(f"Warning: Error calling utils.get_current_kst_time_str: {e_time}"); kst_excel_date = datetime.now().strftime("%Y-%m-%d")
        else: print("Warning: utils module or get_current_kst_time_str not available."); kst_excel_date = datetime.now().strftime("%Y-%m-%d")

        ALL_INFO_LABELS = [
            "회사명", "주소", "연락처", "이메일", "",
            "고객명", "고객 연락처", "견적일", "이사 종류", "",
            "이사일", "출발지", "도착지", "출발층", "도착층", "출발 작업", "도착 작업", "",
            "경유지 이사", "경유지 주소", "경유지 작업방법", "",
            "보관 이사", "보관 기간", "보관 유형", "보관 중 전기사용", "",
            "장거리 적용", "장거리 구간", "",
            "스카이 사용 시간", "", "폐기물 처리(톤)", "", "날짜 할증 선택", "",
            "총 작업 인원", "", "선택 차량", "자동 추천 차량",
            "이사짐 총 부피", "이사짐 총 무게", "", "고객요구사항"
        ]
        info_data_list = []
        for label in ALL_INFO_LABELS:
            value = '-'
            if not label: info_data_list.append(("", "")); continue
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
            elif label == "출발지": value = state_data.get('from_address_full', state_data.get('from_location', '-')) 
            elif label == "도착지": value = dest_address
            elif label == "출발층": value = state_data.get('from_floor', '-')
            elif label == "도착층": value = to_floor
            elif label == "출발 작업": value = from_method
            elif label == "도착 작업": value = to_method
            elif label == "경유지 이사": value = '예' if has_via else '아니오'
            elif label == "경유지 주소": value = state_data.get('via_point_address', state_data.get('via_point_location', '-')) if has_via else '-' 
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
            elif label == "날짜 할증 선택": # 이 부분은 PDF와 달리 원본 '날짜 할증' 항목을 그대로 표시하도록 유지할 수 있음
                 date_options_list = list(getattr(data, "special_day_prices", {}).keys()) 
                 date_keys = [f"date_opt_{i}_widget" for i in range(len(date_options_list))]
                 selected_dates_excel = [date_options_list[i].split(" ")[0] for i, key in enumerate(date_keys) if state_data.get(key, False) or state_data.get(f"tab3_{key}", False)]
                 value = ", ".join(selected_dates_excel) if selected_dates_excel else '없음'
            elif label == "총 작업 인원": value = personnel_text
            elif label == "선택 차량": value = state_data.get('final_selected_vehicle', '미선택')
            elif label == "자동 추천 차량": value = state_data.get('recommended_vehicle_auto', '-')
            elif label == "이사짐 총 부피": value = f"{state_data.get('total_volume', 0.0):.2f} m³"
            elif label == "이사짐 총 무게": value = f"{state_data.get('total_weight', 0.0):.2f} kg"
            elif label == "고객요구사항": value = state_data.get('special_notes', '').strip() or '-'
            info_data_list.append((label, value))
        df_info = pd.DataFrame(info_data_list, columns=["항목", "내용"])

        all_items_data = []
        current_move_type = state_data.get('base_move_type', '')
        item_defs = data.item_definitions.get(current_move_type, {}) if data and hasattr(data, 'item_definitions') else {}
        processed_all_items = set()
        if isinstance(item_defs, dict):
            for section, item_list in item_defs.items():
                if section == getattr(data, "WASTE_SECTION_NAME", "폐기 처리 품목 🗑️"): continue
                if isinstance(item_list, list):
                    for item_name in item_list:
                         if item_name in processed_all_items: continue
                         if data and hasattr(data, 'items') and data.items is not None and item_name in data.items:
                              qty = 0
                              if utils and hasattr(utils, 'get_item_qty'):
                                   try: qty = utils.get_item_qty(state_data, item_name)
                                   except Exception as e_get_qty: print(f"Error calling utils.get_item_qty for {item_name}: {e_get_qty}")
                              else: print(f"Warning: utils module or get_item_qty not available.")
                              all_items_data.append({"품목명": item_name, "수량": qty})
                              processed_all_items.add(item_name)
        if all_items_data: df_all_items = pd.DataFrame(all_items_data, columns=["품목명", "수량"])
        else: df_all_items = pd.DataFrame({"정보": ["정의된 품목 없음 또는 수량 없음"]})

        # 엑셀에서는 모든 비용 항목을 가공 없이 그대로 표시 (PDF와 달리)
        cost_details_excel = []
        if calculated_cost_items and isinstance(calculated_cost_items, list):
            for item in calculated_cost_items: # 원본 calculated_cost_items 사용
                 if isinstance(item, (list, tuple)) and len(item) >= 2:
                    item_desc = str(item[0]); item_cost = 0; item_note = ""
                    try: item_cost = int(item[1] or 0)
                    except (ValueError, TypeError): item_cost = 0
                    if len(item) > 2:
                         try: item_note = str(item[2] or '')
                         except Exception: item_note = ''
                    if "오류" not in item_desc: cost_details_excel.append({"항목": item_desc, "금액": item_cost, "비고": item_note})
        
        if cost_details_excel: df_costs = pd.DataFrame(cost_details_excel, columns=["항목", "금액", "비고"])
        else: df_costs = pd.DataFrame([{"항목": "계산된 비용 없음", "금액": 0, "비고": ""}])

        num_total = total_cost if isinstance(total_cost,(int,float)) else 0
        deposit_raw = state_data.get('deposit_amount', state_data.get('tab3_deposit_amount',0))
        try: deposit_amount_excel = int(deposit_raw or 0)
        except (ValueError, TypeError): deposit_amount_excel = 0
        remaining_balance_excel = num_total - deposit_amount_excel

        is_tax_invoice_excel = state_data.get('issue_tax_invoice', False)
        is_card_payment_excel = state_data.get('card_payment', False)
        final_total_label_suffix_excel = ""
        if is_card_payment_excel: final_total_label_suffix_excel = "(카드수수료 포함)"
        elif is_tax_invoice_excel: final_total_label_suffix_excel = "(VAT 포함)"
        else: final_total_label_suffix_excel = "(VAT 별도)"


        summary_data = [
            {"항목": "--- 비용 요약 ---", "금액": "", "비고": ""},
            {"항목": f"총 견적 비용 {final_total_label_suffix_excel}", "금액": num_total, "비고": "모든 항목 합계"}, 
            {"항목": "계약금 (현금)", "금액": deposit_amount_excel, "비고": ""}, 
            {"항목": f"잔금 {final_total_label_suffix_excel}", "금액": remaining_balance_excel, "비고": "총 견적 비용 - 계약금"} 
        ]
        df_summary = pd.DataFrame(summary_data, columns=["항목", "금액", "비고"])
        df_costs_final = pd.concat([df_costs, df_summary], ignore_index=True)

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_info.to_excel(writer, sheet_name='견적 정보', index=False)
            df_all_items.to_excel(writer, sheet_name='전체 품목 수량', index=False)
            df_costs_final.to_excel(writer, sheet_name='비용 내역 및 요약', index=False)
            workbook = writer.book
            ws_info = writer.sheets['견적 정보']
            ws_items = writer.sheets['전체 품목 수량']
            ws_costs = writer.sheets['비용 내역 및 요약']
            num_format = '#,##0'
            cost_cols_to_format = ['B']
            item_cols_to_format = ['B']
            for ws in [ws_info, ws_items, ws_costs]:
                 cols_to_format = []
                 if ws.title == '비용 내역 및 요약': cols_to_format = cost_cols_to_format
                 elif ws.title == '전체 품목 수량': cols_to_format = item_cols_to_format
                 for col_letter in cols_to_format:
                     for row in range(2, ws.max_row + 1):
                         cell = ws[f'{col_letter}{row}']
                         if isinstance(cell.value, (int, float)): cell.number_format = num_format
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for col in worksheet.columns:
                    max_length = 0; column = col[0].column_letter
                    try:
                        header_value = worksheet[f"{column}1"].value
                        header_len = sum(2 if '\uac00' <= char <= '\ud7a3' else 1 for char in str(header_value)) if header_value else 0
                        max_length = header_len
                    except Exception: header_len = 0; max_length = 0
                    for cell in col[1:]:
                        try:
                            if cell.value is not None:
                                if isinstance(cell.value, (int, float)) and cell.number_format == num_format: cell_text = f"{cell.value:,}"
                                else: cell_text = str(cell.value)
                                lines = cell_text.split('\n'); current_max_line_len = 0
                                if lines:
                                     line_lengths = [sum(2 if '\uac00' <= char <= '\ud7a3' else 1 for char in str(line or '')) for line in lines]
                                     if line_lengths: current_max_line_len = max(line_lengths)
                                if current_max_line_len > max_length: max_length = current_max_line_len
                        except Exception as cell_proc_err: print(f"Warning: Error processing cell {cell.coordinate} for width calc: {cell_proc_err}")
                    adjusted_width = max_length + 2; adjusted_width = max(adjusted_width, 8); adjusted_width = min(adjusted_width, 50)
                    worksheet.column_dimensions[column].width = adjusted_width
        excel_data = output.getvalue()
        return excel_data
    except Exception as e:
        st.error(f"엑셀 파일 생성 중 오류: {e}")
        print(f"Error during Excel generation: {e}")
        traceback.print_exc()
        return None
