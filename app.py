import streamlit as st
from utils.parser import parse_gitlab_link
from services.gitlab_service import fetch_gitlab_data
from services.ai_service import analyze_code 

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="💊", layout="wide")

# --- 🎨 CSS 마법: 촌스러운 라디오 버튼을 '알약'으로 변신 ---
st.markdown("""
<style>
    /* 1. 라디오 버튼의 기본 동그라미 아이콘 숨기기 */
    div[role="radiogroup"] > label > div:first-child {
        display: none;
    }
    
    /* 2. 알약 모양(Pill) 박스 디자인 적용 */
    div[role="radiogroup"] > label {
        background-color: #ffffff;
        border: 2px solid #f0f2f6;
        border-radius: 50px !important; /* 핵심: 완전한 반원 형태 */
        padding: 12px 20px;
        margin-bottom: 12px;
        cursor: pointer;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        width: 100%;
    }
    
    /* 3. 마우스 호버(Hover) 시 살짝 떠오르는 효과 */
    div[role="radiogroup"] > label:hover {
        border-color: #4A90E2;
        background-color: #F0F8FF;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* 4. 선택된(Checked) 메뉴의 강조 효과 (음영 및 색상 반전) */
    div[role="radiogroup"] > label[aria-checked="true"] {
        background-color: #4A90E2; /* 진한 파란색 배경 */
        border-color: #4A90E2;
    }
    
    /* 선택된 텍스트 색상 변경 (흰색) 및 볼드 처리 */
    div[role="radiogroup"] > label[aria-checked="true"] p {
        color: white !important;
        font-weight: 700;
    }
    
    /* 텍스트 가운데 정렬 */
    div[role="radiogroup"] p {
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
    st.markdown("<br>", unsafe_allow_html=True) # 약간의 여백
    
    # 텍스트 앞에 이모지를 넣어주면 알약 안에서 아이콘처럼 보입니다.
    selected_menu = st.radio(
        "메뉴 선택",
        ["🚀 GitLab QA 리스크 분석기", "📝 기획서-코드 검증기", "🛅 TC 자동 생성기"],
        label_visibility="collapsed"
    )

# --- 🖥️ 본문 영역 ---
if selected_menu == "🚀 GitLab QA 리스크 분석기":
    st.title("🛡️ GitLab QA 리스크 분석기")

    # [A] 모델 자동 탐색 세팅 (Zero-Click)
    with st.container(border=True):
        st.subheader("⚙️ 분석 엔진 설정")
        col1, col2, col3 = st.columns([1, 2, 2])
        
        with col1:
            # 여기 있는 라디오 버튼은 LNB CSS에 영향받지 않도록 horizontal로 배치
            ai_provider = st.radio("AI 선택", ["Gemini", "ChatGPT", "Claude"], horizontal=True) 
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

        # 모델 선택 없이 알아서 척척 실행
        with st.spinner(f"{ai_provider}가 최적의 모델을 탐색하여 분석 중입니다..."):
            result, used_model, error = analyze_code(ai_provider, api_key, commits, diffs)
            
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
