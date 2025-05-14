# app.py

import streamlit as st

st.set_page_config(page_title="이삿날 포장이사 견적서", layout="wide", page_icon="🚚")

import pandas as pd
from datetime import datetime, date
import pytz
import math
import traceback
import io

try:
    import data
    import utils
    import calculations
    import google_drive_helper as gdrive
    import pdf_generator
    import excel_filler
except ImportError as ie:
    st.error(f"메인 앱: 필수 유틸리티 모듈 로딩 실패 - {ie}.")
    st.stop()
except Exception as e:
    st.error(f"메인 앱: 유틸리티 모듈 로딩 중 오류 발생 - {e}")
    traceback.print_exc()
    st.stop()

try:
    import state_manager
    import callbacks
    import ui_tab1
    import ui_tab2
    import ui_tab3
    import email_utils
except ImportError as ie:
    st.error(f"메인 앱: 필수 UI/상태 모듈 로딩 실패 - {ie}.")
    if hasattr(ie, 'name') and ie.name:
        st.error(f"실패한 모듈: {ie.name}")
    st.stop()
except Exception as e:
    st.error(f"메인 앱: UI/상태 모듈 로딩 중 예외 발생 - {e}")
    traceback.print_exc()
    st.stop()

st.markdown("<h1 style='text-align: center; color: #1E90FF;'>🚚 이삿날 스마트 견적 🚚</h1>", unsafe_allow_html=True)
st.write("")

if not st.session_state.get("_app_initialized", False):
    if hasattr(callbacks, 'update_basket_quantities') and callable(callbacks.update_basket_quantities):
        state_manager.initialize_session_state(update_basket_callback=callbacks.update_basket_quantities)
    else:
        st.error("초기화 오류: callbacks.update_basket_quantities 함수를 찾을 수 없습니다.")
        state_manager.initialize_session_state() # 콜백 없이 초기화
    st.session_state._app_initialized = True

tab1_title = "👤 고객 정보"
tab2_title = "📋 물품 선택"
tab3_title = "💰 견적 및 비용"

tab1, tab2, tab3 = st.tabs([tab1_title, tab2_title, tab3_title])

with tab1:
    if hasattr(ui_tab1, 'render_tab1') and callable(ui_tab1.render_tab1):
        ui_tab1.render_tab1()
    else:
        st.error("Tab 1 UI를 로드할 수 없습니다.")

with tab2:
    if hasattr(ui_tab2, 'render_tab2') and callable(ui_tab2.render_tab2):
        ui_tab2.render_tab2()
    else:
        st.error("Tab 2 UI를 로드할 수 없습니다.")

with tab3:
    if hasattr(ui_tab3, 'render_tab3') and callable(ui_tab3.render_tab3):
        ui_tab3.render_tab3()
    else:
        st.error("Tab 3 UI를 로드할 수 없습니다.")