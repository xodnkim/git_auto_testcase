import streamlit as st
from utils.parser import parse_gitlab_link
from services.gitlab_service import fetch_gitlab_data
from services.ai_service import analyze_code 
from config.settings import DEFAULT_PROMPT, EXAMPLE_PROMPT

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="💊", layout="wide")

# --- 🎨 CSS 마법: 사이드바(LNB)에만 알약 스타일 적용 ---
st.markdown("""
<style>
    /* 사이드바 영역의 라디오 버튼 동그라미만 숨기기 */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    
    /* 사이드바 라디오 버튼을 알약(Pill) 모양으로 만들기 */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label {
        background-color: #ffffff;
        border: 2px solid #f0f2f6;
        border-radius: 50px !important;
        padding: 12px 20px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        width: 100%;
    }
    
    /* 마우스 올렸을 때 효과 */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover {
        border-color: #4A90E2;
        background-color: #F0F8FF;
        transform: translateY(-2px);
    }
    
    /* 선택된 메뉴 음영 효과 */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(div[aria-checked="true"]),
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) {
        background-color: #4A90E2 !important;
        border-color: #4A90E2 !important;
    }
    
    /* 선택된 메뉴 글씨 하얗고 굵게 */
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(div[aria-checked="true"]) p,
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p {
        color: white !important;
        font-weight: 700 !important;
    }
    
    /* 글자 가운데 정렬 */
    section[data-testid="stSidebar"] div[role="radiogroup"] p {
        font-size: 16px;
        margin: 0;
        text-align: center;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# --- 🗂️ LNB (사이드바) ---
with st.sidebar:
    st.title("🛠️ 딴딴의 여러가지 툴")
    st.markdown("<br>", unsafe_allow_html=True) 
    
    selected_menu = st.radio(
        "메뉴 선택",
        ["🚀 GitLab QA 리스크 분석기", "📝 기획서-코드 검증기", "🛅 TC 자동 생성기"],
        label_visibility="collapsed"
    )

# --- 🖥️ 본문 영역 ---
if selected_menu == "🚀 GitLab QA 리스크 분석기":
    st.title("🛡️ GitLab QA 리스크 분석기")

    # [A] ⚙️ 분석 엔진 및 프롬프트 설정 (UI 개선)
    with st.container(border=True):
        st.subheader("⚙️ 분석 엔진 설정")
        col1, col2, col3 = st.columns([1.2, 2, 2]) # 팝오버 크기를 위해 col1 비율 살짝 조정
        
        with col1:
            # 1. AI 라디오 버튼
            ai_provider = st.radio("AI 선택", ["Gemini", "ChatGPT", "Claude"], horizontal=True) 
            
            # 2. 🚀 위치 이동: 프롬프트 팝오버를 AI 선택 바로 아래에, 작게 배치
            # use_container_width=False 로 설정하여 텍스트 길이에 딱 맞게 콤팩트해집니다.
            with st.popover("📝 맞춤 프롬프트 입력", use_container_width=False):
                st.markdown("**프로젝트에 맞는 맞춤형 QA 지시문을 작성해보세요.**")
                
                with st.expander("💡 딴딴 사수의 실무 예시 (클릭해서 복사)"):
                    st.info("우측 상단의 📋 복사 버튼을 누르세요.")
                    st.code(EXAMPLE_PROMPT, language="markdown")
                    
                custom_prompt = st.text_area(
                    "AI에게 전달할 프롬프트", 
                    value=DEFAULT_PROMPT, 
                    height=250,
                    help="{commits}와 {diffs} 예약어는 지우지 마세요!"
                )
                
        with col2:
            api_key = st.text_input(f"{ai_provider} API Key", type="password")
        with col3:
            gitlab_token = st.text_input("GitLab Token", type="password")

    st.divider()

    # [B] 분석 실행
    link = st.text_input("🔗 GitLab MR 또는 Commit 링크")

    if st.button("🚀 분석 시작", type="primary"):
        if not (api_key and gitlab_token and link):
            st.error("모든 설정값을 입력해주세요.")
            st.stop()
            
        parsed = parse_gitlab_link(link)
        if not parsed:
            st.error("GitLab 링크 형식이 올바르지 않습니다.")
            st.stop()

        with st.spinner("GitLab 데이터를 가져오는 중..."):
            commits, diffs = fetch_gitlab_data(parsed, gitlab_token)
        
        if commits is None:
            st.error(diffs) 
            st.stop()

        with st.spinner(f"{ai_provider}가 최적의 모델을 탐색하여 분석 중입니다..."):
            result, used_model, error = analyze_code(ai_provider, api_key, commits, diffs, custom_prompt)
            
        if result:
            st.success(f"✅ 분석 완료 (자동 선택된 모델: {used_model})")
            st.markdown("---")
            st.markdown(result)
        else:
            st.error(f"분석 실패: {error}")

elif selected_menu == "📝 기획서-코드 검증기":
    st.title("📝 기획서-코드 검증기")
    st.info("이 기능은 현재 개발 중입니다. (기획서 URL과 코드를 대조해 누락된 스펙을 찾습니다.)")

elif selected_menu == "🛅 TC 자동 생성기":
    st.title("🛅 TC 자동 생성기")
    st.info("이 기능은 현재 개발 중입니다. (기획/코드를 바탕으로 테스트 케이스 초안을 자동 생성합니다.)")
