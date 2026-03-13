# app.py
import streamlit as st
from utils.parser import parse_gitlab_link
from services.gitlab_service import fetch_gitlab_data
from services.ai_service import get_ai_models, analyze_code

st.set_page_config(page_title="QA 리스크 분석기", page_icon="🛡️", layout="wide")

# --- LNB (사이드바) ---
with st.sidebar:
    st.title("📁 프로젝트 목록")
    st.button("➕ 새 프로젝트 추가", use_container_width=True)
    st.divider()
    st.radio("현재 선택된 프로젝트", ["gittest", "상용 서비스 (준비중)"], label_visibility="collapsed")

# --- 본문 영역 ---
st.title("🛡️ GitLab QA 리스크 분석기")

# [1] API 및 AI 모델 설정 영역 (요청하신 본문 배치)
with st.container(border=True):
    st.subheader("⚙️ 분석 엔진 설정")
    col1, col2, col3 = st.columns([1, 2, 2])
    
    with col1:
        ai_provider = st.radio("AI 선택", ["Gemini", "ChatGPT", "Claude"])
    
    with col2:
        api_key = st.text_input(f"{ai_provider} API Key", type="password")
        available_models = get_ai_models(ai_provider, api_key)
        selected_model = st.selectbox("모델 선택", available_models if available_models else ["키를 먼저 입력하세요"])
        
    with col3:
        gitlab_token = st.text_input("GitLab Token", type="password")

st.divider()

# [2] 분석 실행 영역
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
        st.error(diffs) # 에러 메시지 출력
        st.stop()

    with st.spinner(f"{ai_provider}({selected_model}) 모델로 분석 중..."):
        result, error = analyze_code(ai_provider, api_key, selected_model, commits, diffs)
        
    if result:
        st.success(f"✅ 분석 완료 (사용 모델: {selected_model})")
        st.markdown("---")
        st.markdown(result)
    else:
        st.error(f"분석 실패: {error}")
