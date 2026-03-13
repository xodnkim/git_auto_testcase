# app.py
import streamlit as st
from utils.parser import parse_gitlab_link
from services.gitlab_service import fetch_gitlab_data
from services.ai_service import analyze_code # get_ai_models 삭제됨

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="🛠️", layout="wide")

# --- LNB (사이드바) ---
with st.sidebar:
    st.title("🛠️ 딴딴의 여러가지 툴")
    st.divider()
    selected_menu = st.radio(
        "메뉴 선택",
        ["GitLab QA 리스크 분석기", "기획서-코드 검증기 (준비중)", "TC 자동 생성기 (준비중)"],
        label_visibility="collapsed"
    )

# --- 본문 영역 ---
if selected_menu == "GitLab QA 리스크 분석기":
    st.title("🛡️ GitLab QA 리스크 분석기")

    # [A] 모델 선택 UI 삭제! 키 입력만 받음
    with st.container(border=True):
        st.subheader("⚙️ 분석 엔진 설정")
        col1, col2, col3 = st.columns([1, 2, 2])
        
        with col1:
            ai_provider = st.radio("AI 선택", ["Gemini", "ChatGPT", "Claude"])
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

        # 알아서 모델을 찾아오도록 실행
        with st.spinner(f"{ai_provider}가 최적의 모델을 탐색하여 분석 중입니다..."):
            result, used_model, error = analyze_code(ai_provider, api_key, commits, diffs)
            
        if result:
            # 알아서 찾은 모델 이름을 여기에 출력
            st.success(f"✅ 분석 완료 (자동 선택된 모델: {used_model})")
            st.markdown("---")
            st.markdown(result)
        else:
            st.error(f"분석 실패: {error}")

# (기타 준비중 메뉴 생략...)
