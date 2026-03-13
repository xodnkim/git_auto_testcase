# app.py
import streamlit as st
from utils.parser import parse_gitlab_link
from services.gitlab_service import fetch_gitlab_data
from services.ai_service import get_ai_models, analyze_code

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="🛠️", layout="wide")

# --- LNB (사이드바 메뉴 구성) ---
with st.sidebar:
    st.title("🛠️ 딴딴의 여러가지 툴")
    st.divider()
    
    # 세련된 메뉴 선택 (클릭 시 음영/선택 효과 발생)
    selected_menu = st.radio(
        "메뉴를 선택하세요",
        ["GitLab QA 리스크 분석기", "기획서-코드 검증기 (준비중)", "TC 자동 생성기 (준비중)"],
        label_visibility="collapsed" # 라디오 버튼 타이틀 숨김
    )

# --- 본문 영역 라우팅 ---
if selected_menu == "GitLab QA 리스크 분석기":
    st.title("🛡️ GitLab QA 리스크 분석기")

    # [A] API 및 AI 모델 설정 영역
    with st.container(border=True):
        st.subheader("⚙️ 분석 엔진 설정")
        col1, col2, col3 = st.columns([1, 2, 2])
        
        with col1:
            ai_provider = st.radio("AI 선택", ["Gemini", "ChatGPT", "Claude"])
        
        with col2:
            api_key = st.text_input(f"{ai_provider} API Key", type="password")
            # 입력된 키를 바탕으로 동적으로 모델 목록 가져오기
            available_models = get_ai_models(ai_provider, api_key)
            selected_model = st.selectbox("모델 선택", available_models if available_models else ["키를 먼저 입력하세요"])
            
        with col3:
            gitlab_token = st.text_input("GitLab Token", type="password")

    st.divider()

    # [B] 분석 실행 영역
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

        with st.spinner(f"{ai_provider}({selected_model}) 모델로 분석 중..."):
            result, error = analyze_code(ai_provider, api_key, selected_model, commits, diffs)
            
        if result:
            st.success(f"✅ 분석 완료 (사용 모델: {selected_model})")
            st.markdown("---")
            st.markdown(result)
        else:
            st.error(f"분석 실패: {error}")

elif selected_menu == "기획서-코드 검증기 (준비중)":
    st.title("📝 기획서-코드 검증기")
    st.info("이 기능은 현재 개발 중입니다. 곧 업데이트될 예정입니다!")

elif selected_menu == "TC 자동 생성기 (준비중)":
    st.title("🛅 TC 자동 생성기")
    st.info("이 기능은 현재 개발 중입니다. 곧 업데이트될 예정입니다!")
