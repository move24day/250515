# ui_tab3.py 의 render_tab3 함수 내 "이사 정보 요약 (텍스트)" 생성 로직 수정

            # --- 이사 정보 요약 (텍스트) ---
            st.subheader("이사 정보 요약 (텍스트)") # 이모티콘 제거
            summary_display_possible = bool(final_selected_vehicle_for_calc) and not has_cost_error

            if summary_display_possible:
                try:
                    # 필요한 변수들 (기존 로직에서 가져옴)
                    customer_name_summary = st.session_state.get('customer_name', '')
                    phone_summary = st.session_state.get('customer_phone', '')
                    email_summary = st.session_state.get('customer_email', '')
                    from_addr_summary = st.session_state.get('from_location', '정보 없음')
                    to_addr_summary = st.session_state.get('to_location', '정보 없음')
                    is_storage_move_summary = st.session_state.get('is_storage_move', False)
                    storage_details_text = ""
                    if is_storage_move_summary:
                        storage_type_raw = st.session_state.get('storage_type', '정보 없음') # 예: "컨테이너 보관 📦"
                        storage_type = storage_type_raw.split(" ")[0] if storage_type_raw else "정보 없음" # "컨테이너"
                        storage_electric_text = "(전기사용)" if st.session_state.get('storage_use_electricity', False) else ""
                        storage_details_text = f"{storage_type} {storage_electric_text}".strip()

                    vehicle_type_summary = final_selected_vehicle_for_calc
                    vehicle_tonnage_summary = ""
                    if isinstance(vehicle_type_summary, str):
                        match_summary = re.search(r'(\d+(\.\d+)?)', vehicle_type_summary)
                        vehicle_tonnage_summary = match_summary.group(1).strip() if match_summary else vehicle_type_summary.replace("톤","").strip()

                    p_info_summary = personnel_info_display
                    men_summary = p_info_summary.get('final_men', 0)
                    women_summary = p_info_summary.get('final_women', 0)
                    ppl_summary = f"{men_summary}명" + (f"+{women_summary}명" if women_summary > 0 else "")

                    from_method_full = get_method_full_name('from_method') # 이모티콘 제거된 메소드명
                    to_method_full = get_method_full_name('to_method')     # 이모티콘 제거된 메소드명
                    via_method_full = get_method_full_name('via_point_method') # 이모티콘 제거된 메소드명

                    deposit_for_summary = int(st.session_state.get("deposit_amount", 0))
                    calculated_total_for_summary = int(total_cost_display) if isinstance(total_cost_display,(int,float)) else 0
                    remaining_for_summary = calculated_total_for_summary - deposit_for_summary

                    payment_option_texts = []
                    if st.session_state.get("issue_tax_invoice", False): payment_option_texts.append("세금계산서 발행 요청")
                    if st.session_state.get("card_payment", False): payment_option_texts.append("카드 결제 예정")
                    payment_options_summary = " / ".join(payment_option_texts) if payment_option_texts else ""
                    
                    # 포장자재 정보 (이모티콘 없는 키로 접근 시도 또는 data.py 키 구조에 맞춰야 함)
                    q_b_s, q_mb_s, q_book_s = 0, 0, 0
                    original_move_type_key_sum = st.session_state.get('base_move_type') # 이모티콘 포함된 원본 키
                    original_basket_section_key_sum = "포장 자재 📦" # data.py 에 정의된 실제 키 (이모티콘 포함)

                    if original_move_type_key_sum and hasattr(data, 'items') and hasattr(data, 'item_definitions'):
                        if original_basket_section_key_sum in data.item_definitions.get(original_move_type_key_sum, {}):
                             try:
                                q_b_s = int(st.session_state.get(f"qty_{original_move_type_key_sum}_{original_basket_section_key_sum}_바구니", 0) or 0)
                                q_mb_s_key1 = f"qty_{original_move_type_key_sum}_{original_basket_section_key_sum}_중박스"
                                q_mb_s_key2 = f"qty_{original_move_type_key_sum}_{original_basket_section_key_sum}_중자바구니"
                                q_mb_s = int(st.session_state.get(q_mb_s_key1, st.session_state.get(q_mb_s_key2, 0)) or 0)
                                q_book_s = int(st.session_state.get(f"qty_{original_move_type_key_sum}_{original_basket_section_key_sum}_책바구니", 0) or 0)
                             except Exception as e_basket_sum_detail:
                                print(f"요약 바구니 상세 오류: {e_basket_sum_detail}")

                    bask_display_parts = []
                    if q_b_s > 0: bask_display_parts.append(f"바구니 {q_b_s}개")
                    if q_mb_s > 0: bask_display_parts.append(f"중박스 {q_mb_s}개")
                    if q_book_s > 0: bask_display_parts.append(f"책바구니 {q_book_s}개")
                    bask_summary_str = ", ".join(bask_display_parts) if bask_display_parts else ""

                    note_summary = st.session_state.get('special_notes', '')
                    
                    # --- 요약 정보 라인 구성 시작 ---
                    summary_lines = []

                    moving_date_val_for_summary = st.session_state.get('moving_date')
                    formatted_moving_date_summary = ""
                    if isinstance(moving_date_val_for_summary, date):
                        formatted_moving_date_summary = moving_date_val_for_summary.strftime('%m-%d')
                    elif isinstance(moving_date_val_for_summary, str):
                        try:
                            dt_obj = datetime.strptime(moving_date_val_for_summary, '%Y-%m-%d')
                            formatted_moving_date_summary = dt_obj.strftime('%m-%d')
                        except ValueError:
                            formatted_moving_date_summary = moving_date_val_for_summary
                    else:
                        formatted_moving_date_summary = "정보 없음"
                    summary_lines.append(formatted_moving_date_summary)

                    address_flow_parts_summary = []
                    address_flow_parts_summary.append(from_addr_summary if from_addr_summary else "출발지 정보 없음")
                    address_flow_parts_summary.append(to_addr_summary if to_addr_summary else "도착지 정보 없음")
                    vehicle_display_text_summary = f"/ {vehicle_tonnage_summary if vehicle_tonnage_summary else vehicle_type_summary}"
                    summary_lines.append(" - ".join(address_flow_parts_summary) + vehicle_display_text_summary)
                    summary_lines.append("")

                    if customer_name_summary: summary_lines.append(customer_name_summary)
                    if phone_summary and phone_summary != '-': summary_lines.append(phone_summary)
                    if email_summary and email_summary != '-': summary_lines.append(email_summary)
                    summary_lines.append("")

                    summary_lines.append("출발지 주소:")
                    summary_lines.append(f"{from_addr_summary if from_addr_summary else '정보 없음'}")
                    
                    if st.session_state.get('has_via_point', False):
                        via_location_detail_summary = st.session_state.get('via_point_location', '정보 없음')
                        via_floor_summary = st.session_state.get('via_point_floor', '') # --- 경유지 층수 가져오기 ---
                        summary_lines.append("경유지 주소:")
                        summary_lines.append(f"{via_location_detail_summary}" + (f" ({via_floor_summary}층)" if via_floor_summary else "")) # --- 경유지 층수 표시 ---
                    
                    if is_storage_move_summary and storage_details_text:
                        summary_lines.append("보관 정보:")
                        summary_lines.append(f"{storage_details_text}")
                    
                    summary_lines.append("도착지 주소:")
                    summary_lines.append(f"{to_addr_summary if to_addr_summary else '정보 없음'}")
                    summary_lines.append("")

                    summary_lines.append(f"{vehicle_tonnage_summary if vehicle_tonnage_summary else vehicle_type_summary} / {ppl_summary}")
                    summary_lines.append("")
                    summary_lines.append(f"출발지 작업: {from_method_full}")
                    if st.session_state.get('has_via_point', False):
                        summary_lines.append(f"경유지 작업: {via_method_full}") # --- 경유지 작업 방법 표시 ---
                    summary_lines.append(f"도착지 작업: {to_method_full}")
                    summary_lines.append("")
                    summary_lines.append(f"계약금 {deposit_for_summary:,.0f}원 / 잔금 {remaining_for_summary:,.0f}원")
                    if payment_options_summary:
                        summary_lines.append(f"  ({payment_options_summary})")
                    summary_lines.append("")

                    cost_summary_line = f"총 {calculated_total_for_summary:,.0f}원"
                    cost_breakdown_details = []
                    vat_info_str = ""
                    card_info_str = "" # 카드 수수료는 이미 총액에 포함되어 별도 표시 안함 (위 calculations.py 수정에 따름)

                    if isinstance(cost_items_display, list):
                        temp_other_costs = []
                        for item_name_disp, item_cost_disp, _ in cost_items_display:
                            item_name_str = str(item_name_disp)
                            cost_val = int(item_cost_disp or 0)

                            if "부가세" in item_name_str:
                                vat_info_str = f"부가세 ({item_name_str.split('(')[-1].split(')')[0]}): {cost_val:,}"
                            elif "카드결제 (VAT 및 수수료 포함)" in item_name_str : # 카드결제 항목은 별도로 추가하지 않음 (총액에 이미 반영)
                                pass
                            elif cost_val != 0:
                                if item_name_str == "기본 운임":
                                    temp_other_costs.append(f"이사비: {cost_val:,}")
                                elif item_name_str == "추가 인력":
                                     temp_other_costs.append(f"추가 인력: {cost_val:,}")
                                # 다른 주요 비용 항목들도 필요시 조건 추가 가능
                                # else:
                                #    temp_other_costs.append(f"{item_name_str}: {cost_val:,}")
                        
                        if temp_other_costs:
                            cost_summary_line += f" ( {', '.join(temp_other_costs)}" # 쉼표로 구분
                            # 만약 표시된 것 외 다른 비용이 있다면 '기타'로 합산
                            # displayed_sum = sum(int(re.sub(r'[^\d]', '', part.split(':')[-1])) for part in temp_other_costs)
                            # total_other_sum_from_items = sum(c for n,c,_ in cost_items_display if "부가세" not in n and "카드결제" not in n)
                            # if total_other_sum_from_items != displayed_sum:
                            #    cost_summary_line += f", 기타: {total_other_sum_from_items - displayed_sum:,}"
                            cost_summary_line += ")"

                    if vat_info_str: # VAT 정보가 있으면 추가 (카드결제시에는 이 항목이 없을 것임)
                        cost_summary_line += f" + {vat_info_str}"
                    
                    summary_lines.append(cost_summary_line)
                    summary_lines.append("")
                    
                    if bask_summary_str:
                         summary_lines.append(f"포장자재: {bask_summary_str}")
                         summary_lines.append("")
                    
                    if note_summary and note_summary.strip() and note_summary != '-':
                        summary_lines.append("고객요구사항:")
                        summary_lines.extend([f"  - {note_line.strip()}" for note_line in note_summary.strip().replace('\r\n', '\n').split('\n') if note_line.strip()])

                    st.text_area("요약 정보", "\n".join(summary_lines), height=400, key="summary_text_area_readonly_tab3", disabled=True)

                except Exception as e_summary_direct:
                    st.error(f"요약 정보 생성 중 오류: {e_summary_direct}"); traceback.print_exc()
            # ... (이하 요약 정보 생성 실패 처리 및 나머지 파일 생성/다운로드/이메일 로직은 동일하게 유지) ...
            elif not final_selected_vehicle_for_calc:
                if not validation_messages or not any("차량 종류가 선택되지 않았습니다" in msg for msg in validation_messages):
                    st.info("견적 계산용 차량 미선택으로 요약 정보 표시 불가.")
            st.divider()
        except Exception as calc_err_outer_display:
            st.error(f"최종 견적 표시 중 외부 오류 발생: {calc_err_outer_display}")
            traceback.print_exc()

    # --- 견적서 생성, 발송 및 다운로드 섹션 ---
    st.subheader("견적서 생성, 발송 및 다운로드") # 이모티콘 제거

    can_generate_anything = bool(final_selected_vehicle_for_calc) and \
                          not has_cost_error and \
                          st.session_state.get("calculated_cost_items_for_pdf") and \
                          st.session_state.get("total_cost_for_pdf", 0) > 0
    actions_disabled = not can_generate_anything

    with st.container(border=True):
        st.markdown("**고객 전달용 파일**")
        col_pdf_btn, col_pdf_img_btn = st.columns(2)

        pdf_args_common = {
            "state_data": st.session_state.to_dict(),
            "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
            "total_cost": st.session_state.get("total_cost_for_pdf", 0),
            "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
        }
        pdf_generation_possible = hasattr(pdf_generator, "generate_pdf") and can_generate_anything
        pdf_to_image_possible = hasattr(pdf_generator, "generate_quote_image_from_pdf") and pdf_generation_possible

        with col_pdf_btn:
            if st.button("고객용 PDF 생성", key="generate_customer_pdf_btn", disabled=actions_disabled or not pdf_generation_possible):
                with st.spinner("고객용 PDF 생성 중..."):
                    pdf_data = pdf_generator.generate_pdf(**pdf_args_common)
                if pdf_data:
                    st.session_state['customer_final_pdf_data'] = pdf_data
                    st.success("고객용 PDF 생성 완료!")
                    if pdf_to_image_possible:
                        with st.spinner("PDF 기반 고객용 이미지 생성 중..."):
                            poppler_bin_path = None
                            img_data_from_pdf = pdf_generator.generate_quote_image_from_pdf(pdf_data, poppler_path=poppler_bin_path)
                        if img_data_from_pdf:
                            st.session_state['customer_pdf_image_data'] = img_data_from_pdf
                            st.success("PDF 기반 고객용 이미지 생성 완료!")
                        else:
                            st.warning("PDF 기반 고객용 이미지 생성 실패. (PDF는 생성됨)")
                            if 'customer_pdf_image_data' in st.session_state: del st.session_state['customer_pdf_image_data']
                else:
                    st.error("고객용 PDF 생성 실패.")
                    if 'customer_final_pdf_data' in st.session_state: del st.session_state['customer_final_pdf_data']
                    if 'customer_pdf_image_data' in st.session_state: del st.session_state['customer_pdf_image_data']


            if st.session_state.get('customer_final_pdf_data'):
                fname_pdf_cust = f"견적서_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.pdf"
                st.download_button(
                    label="고객용 PDF 다운로드",
                    data=st.session_state['customer_final_pdf_data'],
                    file_name=fname_pdf_cust, mime="application/pdf",
                    key='dl_btn_customer_final_pdf', disabled=actions_disabled
                )
            elif pdf_generation_possible and not actions_disabled:
                st.caption("PDF 생성 버튼을 눌러 준비하세요.")

        with col_pdf_img_btn:
            if st.session_state.get('customer_pdf_image_data'):
                fname_pdf_img_cust = f"견적서_PDF이미지_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.png"
                st.download_button(
                    label="고객용 견적서 이미지 다운로드 (PDF 기반)",
                    data=st.session_state['customer_pdf_image_data'],
                    file_name=fname_pdf_img_cust, mime="image/png",
                    key='dl_btn_customer_pdf_image', disabled=actions_disabled
                )
            elif pdf_to_image_possible and st.session_state.get('customer_final_pdf_data') and not actions_disabled :
                st.caption("PDF 생성 시 함께 생성됩니다.")
            elif pdf_to_image_possible and not actions_disabled :
                 st.caption("고객용 PDF를 먼저 생성하세요.")

        if not pdf_generation_possible and not actions_disabled:
             st.caption("고객용 파일 생성 불가 (견적 내용 또는 PDF 모듈 확인)")
        elif actions_disabled:
             st.caption("견적 내용을 먼저 완성해주세요.")
    st.divider()

    with st.container(border=True):
        st.markdown("**내부 검토용 파일**")
        col_internal_img_btn, col_internal_excel_btn = st.columns(2)

        company_form_image_args = {
            "state_data": st.session_state.to_dict(),
            "calculated_cost_items": st.session_state.get("calculated_cost_items_for_pdf", []),
            "total_cost_overall": st.session_state.get("total_cost_for_pdf", 0),
            "personnel_info": st.session_state.get("personnel_info_for_pdf", {})
        }
        company_image_possible = hasattr(image_generator, "create_quote_image") and can_generate_anything

        with col_internal_img_btn:
            if st.button("내부 검토용 양식 이미지 생성", key="generate_internal_form_image_btn", disabled=actions_disabled or not company_image_possible):
                with st.spinner("내부 검토용 양식 이미지 생성 중..."):
                    internal_image_data = image_generator.create_quote_image(**company_form_image_args)
                if internal_image_data:
                    st.session_state['internal_form_image_data'] = internal_image_data
                    st.success("내부 검토용 양식 이미지 생성 완료!")
                else:
                    st.error("내부 검토용 양식 이미지 생성 실패.")
                    if 'internal_form_image_data' in st.session_state: del st.session_state['internal_form_image_data']

            if st.session_state.get('internal_form_image_data'):
                fname_internal_img = f"내부양식_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.png"
                st.download_button(
                    label="내부 검토용 양식 이미지 다운로드",
                    data=st.session_state['internal_form_image_data'],
                    file_name=fname_internal_img, mime="image/png",
                    key='dl_btn_internal_form_image', disabled=actions_disabled
                )
            elif company_image_possible and not actions_disabled:
                st.caption("생성 버튼을 눌러 내부 검토용 이미지를 준비하세요.")

        with col_internal_excel_btn:
            excel_possible = hasattr(excel_filler, "fill_final_excel_template") and can_generate_anything
            if st.button("내부용 Excel 생성", key="generate_internal_excel_tab3", disabled=actions_disabled or not excel_possible):
                if excel_possible:
                    _current_state = st.session_state.to_dict()
                    _total_cost_excel, _cost_items_excel, _personnel_info_excel = calculations.calculate_total_moving_cost(_current_state)
                    with st.spinner("내부용 Excel 파일 생성 중..."):
                        filled_excel_data_dl = excel_filler.fill_final_excel_template(
                            _current_state, _cost_items_excel, _total_cost_excel, _personnel_info_excel
                        )
                    if filled_excel_data_dl:
                        st.session_state['internal_excel_data_for_download'] = filled_excel_data_dl
                        st.success("내부용 Excel 생성 완료!")
                    else:
                        st.error("내부용 Excel 파일 생성 실패.")
                        if 'internal_excel_data_for_download' in st.session_state: del st.session_state['internal_excel_data_for_download']

            if st.session_state.get('internal_excel_data_for_download') and excel_possible:
                fname_excel_dl = f"내부견적_{st.session_state.get('customer_name', '고객')}_{utils.get_current_kst_time_str('%y%m%d')}.xlsx"
                st.download_button(label="Excel 다운로드 (내부용)", data=st.session_state['internal_excel_data_for_download'], file_name=fname_excel_dl, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key='dl_btn_excel_internal_section_tab3', disabled=actions_disabled)
            elif excel_possible and not actions_disabled: st.caption("생성 버튼을 눌러 내부용 Excel 파일을 준비하세요.")

        if not company_image_possible and not excel_possible and not actions_disabled:
             st.caption("내부 검토용 파일 생성 불가 (견적 내용 또는 관련 모듈 확인)")
        elif actions_disabled:
             st.caption("견적 내용을 먼저 완성해주세요.")
    st.divider()

    with st.container(border=True):
        st.markdown("**이메일 발송 (고객용 PDF 첨부)**")
        email_recipient_exists = bool(st.session_state.get("customer_email", "").strip())
        email_modules_ok = hasattr(email_utils, "send_quote_email") and hasattr(pdf_generator, "generate_pdf")
        email_possible = email_modules_ok and can_generate_anything and email_recipient_exists

        if st.button("이메일 발송", key="email_send_button_main_tab3", disabled=actions_disabled or not email_possible):
            recipient_email_send = st.session_state.get("customer_email")
            customer_name_send = st.session_state.get("customer_name", "고객")

            pdf_email_bytes_send = st.session_state.get('customer_final_pdf_data')
            if not pdf_email_bytes_send and pdf_generation_possible:
                with st.spinner("이메일 첨부용 PDF 생성 중..."):
                    pdf_email_bytes_send = pdf_generator.generate_pdf(**pdf_args_common)
                if pdf_email_bytes_send:
                     st.session_state['customer_final_pdf_data'] = pdf_email_bytes_send

            if pdf_email_bytes_send:
                subject_send = f"[{customer_name_send}님] 이삿날 이사 견적서입니다."
                body_send = f"{customer_name_send}님,\n\n요청하신 이사 견적서를 첨부 파일로 보내드립니다.\n\n감사합니다.\n이삿날 드림"
                pdf_filename_send = f"견적서_{customer_name_send}_{utils.get_current_kst_time_str('%Y%m%d')}.pdf"

                with st.spinner(f"{recipient_email_send}(으)로 이메일 발송 중..."):
                    email_sent_status = email_utils.send_quote_email(recipient_email_send, subject_send, body_send, pdf_email_bytes_send, pdf_filename_send)

                if email_sent_status: st.success(f"이메일 발송 성공!")
                else: st.error("이메일 발송 실패.")
            else:
                st.error("첨부할 PDF 생성에 실패하여 이메일을 발송할 수 없습니다.")
        elif actions_disabled:
            st.caption("견적 내용을 먼저 완성해주세요.")
        elif not email_recipient_exists:
            st.caption("고객 이메일 주소가 입력되지 않았습니다.")
        elif not email_modules_ok:
            st.caption("이메일 또는 PDF 생성 모듈에 문제가 있습니다.")
        elif not can_generate_anything :
            st.caption("견적 내용이 충분하지 않아 이메일을 발송할 수 없습니다.")
