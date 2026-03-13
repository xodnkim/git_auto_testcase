# app.py
import streamlit as st
import datetime
from utils.parser import parse_vcs_link 
from services.vcs_service import fetch_vcs_data 
from services.ai_service import analyze_code 
from config.settings import DEFAULT_PROMPT
from utils.exporter import generate_html_report, generate_tc_excel

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="💊", layout="wide")

if 'history' not in st.session_state:
    st.session_state.history = []

with st.sidebar:
    st.title("🛠️ 딴딴의 여러가지 툴")
    selected_menu = st.radio("메뉴", ["🚀 형상관리 QA 리스크 분석기", "📝 기획서-코드 검증기"])

if selected_menu == "🚀 형상관리 QA 리스크 분석기":
    st.title("🛡️ 형상관리 QA 리스크 분석기")

    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([1, 1, 2, 2])
        user_name = c1.text_input("👤 사용자명")
        ai_provider = c2.selectbox("🤖 AI", ["Gemini", "ChatGPT", "Claude"])
        api_key = c3.text_input("API Key", type="password")
        vcs_token = c4.text_input("VCS Token", type="password")
        
        with st.popover("📝 프롬프트 수정", use_container_width=True):
            custom_prompt = st.text_area("프롬프트", value=DEFAULT_PROMPT, height=300)
        
        link = st.text_input("🔗 분석할 링크")
        
        if st.button("🚀 분석 실행", type="primary", use_container_width=True):
            commits, diffs = fetch_vcs_data(parse_vcs_link(link), vcs_token)
            result, model, err = analyze_code(ai_provider, api_key, commits, diffs, custom_prompt)
            
            if result:
                st.session_state.history.insert(0, {
                    'id': len(st.session_state.history),
                    'time': datetime.datetime.now().strftime("%H:%M"),
                    'user': user_name,
                    'api': f"{ai_provider}({model})",
                    'link': link,
                    'html': generate_html_report(result),
                    'excel': generate_tc_excel(result)
                })
                st.success("완료!")

    st.subheader("🗂️ 히스토리")
    for item in st.session_state.history:
        with st.expander(f"[{item['time']}] {item['user']} - {item['link'][:40]}..."):
            col1, col2 = st.columns(2)
            col1.download_button("🌐 HTML 보고서", data=item['html'], file_name="report.html")
            if item['excel']:
                col2.download_button("📊 Excel TC", data=item['excel'], file_name="tc.xlsx")
