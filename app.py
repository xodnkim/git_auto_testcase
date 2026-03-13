# app.py
import streamlit as st
from utils.parser import parse_vcs_link 
from services.vcs_service import fetch_vcs_data 
from services.ai_service import analyze_code 
from config.settings import DEFAULT_PROMPT, EXAMPLE_PROMPT

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="💊", layout="wide")

# --- 🎨 CSS 마법 ---
st.markdown("""
<style>
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label { background-color: #ffffff; border: 2px solid #f0f2f6; border-radius: 50px !important; padding: 12px 20px; margin-bottom: 12px; cursor: pointer; transition: all 0.2s ease-in-out; box-shadow: 0 2px 5px rgba(0,0,0,0.05); width: 100%; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { border-color: #4A90E2; background-color: #F0F8FF; transform: translateY(-2px); }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(div[aria-checked="true"]), section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { background-color: #4A90E2 !important; border-color: #4A90E2 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(div[aria-checked="true"]) p, section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: white !important; font-weight: 700 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] p { font-size: 16px; margin: 0; text-align: center; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 🗂️ LNB ---
with st.sidebar:
    st.title("🛠️ 딴딴의 여러가지 툴")
    st.markdown("<br>", unsafe_allow_html=True) 
    selected_menu = st.radio("메뉴 선택", ["🚀 형상관리 QA 리스크 분석기", "📝 기획서-코드 검증기", "🛅 TC 자동 생성기"], label_visibility="collapsed")

# --- 🖥️ 본문 영역 ---
if selected_menu == "🚀 형상관리 QA 리스크 분석기":
    st.title("🛡️ 형상관리 QA 리스크 분석기")
    st.caption("GitLab과 GitHub 링크를 모두 지원합니다.") 

    with st.container(border=True):
        st.subheader("⚙️ 분석 엔진 설정")
        col1, col2, col3 = st.columns([1.2, 2, 2]) 
        
        with col1:
            ai_provider = st.radio("AI 선택", ["Gemini", "ChatGPT", "Claude"], horizontal=True) 
            with st.popover("📝 맞춤 프롬프트 입력", use_container_width=False):
                st.markdown("**프로젝트에 맞는 맞춤형 QA 지시문을 작성해보세요.**")
                with st.expander("💡 딴딴 사수의 실무 예시 (클릭해서 복사)"):
                    st.info("우측 상단의 📋 복사 버튼을 누르세요.")
                    st.code(EXAMPLE_PROMPT, language="markdown")
                custom_prompt = st.text_area("AI에게 전달할 프롬프트", value=DEFAULT_PROMPT, height=250)
                
        with col2:
            api_key = st.text_input(f"{ai_provider} API Key", type="password")
        with col3:
            vcs_token = st.text_input("GitLab / GitHub Access Token", type="password", help="Public 저장소라면 비워두셔도 됩니다.")

    st.divider()

    link = st.text_input("🔗 GitLab MR 또는 GitHub PR/Commit 링크")

    if st.button("🚀 분석 시작", type="primary"):
        if not (api_key and link):
            st.error("API 키와 분석할 링크를 입력해주세요.")
            st.stop()
            
        parsed = parse_vcs_link(link)
        if not parsed:
            st.error("지원하지 않는 링크 형식이거나 잘못된 URL입니다. (GitLab 또는 GitHub만 지원)")
            st.stop()

        with st.spinner(f"{parsed['platform'].capitalize()} 데이터를 가져오는 중..."):
            commits, diffs = fetch_vcs_data(parsed, vcs_token)
        
        if commits is None:
            st.error(diffs) 
            st.stop()

        with st.spinner(f"{ai_provider}가 최적의 모델을 탐색하여 분석 중입니다..."):
            result, used_model, error = analyze_code(ai_provider, api_key, commits, diffs, custom_prompt)
            
        if result:
            st.success(f"✅ 분석 완료 (자동 선택된 모델: {used_model})")
            st.markdown("---")
            # 💡 엑셀/HTML 다운로드 버튼은 깔끔하게 제거되고 화면에만 출력됩니다.
            st.markdown(result)
        else:
            st.error(f"분석 실패: {error}")

elif selected_menu == "📝 기획서-코드 검증기":
    st.title("📝 기획서-코드 검증기")
    st.info("이 기능은 현재 개발 중입니다.")

elif selected_menu == "🛅 TC 자동 생성기":
    st.title("🛅 TC 자동 생성기")
    st.info("이 기능은 현재 개발 중입니다.")