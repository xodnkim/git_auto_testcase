import streamlit as st
import time

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="QA 리스크 분석 포트폴리오", page_icon="🤖")

# --- 2. 사이드바 (설정) ---
with st.sidebar:
    st.title("⚙️ 설정")
    st.info("실제 기능을 사용하려면 아래 정보가 필요합니다.")
    user_gemini_key = st.text_input("Gemini API Key", type="password", help="Google AI Studio에서 발급받은 키를 입력하세요.")
    st.markdown("---")
    st.caption("© 2026 QA Automation Portfolio")

# --- 3. 메인 화면 구성 (탭 사용) ---
tab1, tab2 = st.tabs(["🏠 프로젝트 소개", "🔍 AI 리스크 분석기 체험"])

# [탭 1: 프로젝트 소개]
with tab1:
    st.title("🤖 AI 기반 QA 리스크 헷징 시스템")
    st.subheader("업무 효율화를 위한 GitLab MR 분석 자동화 도구")
    
    st.markdown("""
    ### 📝 프로젝트 배경
    - **문제점**: 수많은 Merge Request(MR)의 코드 변경점을 매번 수동으로 확인하여 리스크를 도출하는 데 많은 시간 소요.
    - **해결책**: Gemini 2.0 AI를 활용해 코드 Diff를 분석하고, QA 관점의 사이드 이펙트와 핵심 테스트 포인트를 자동으로 생성.
    - **기대 효과**: 분석 시간 70% 단축 및 휴먼 에러 방지.
    """)
    
    st.image("https://images.unsplash.com/photo-1551288049-bbbda536ad37?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80", caption="QA 분석 프로세스 시각화")

# [탭 2: 실제 도구 체험]
with tab2:
    st.header("🔍 분석 도구 체험하기")
    
    # 예시 데이터 (체험용)
    sample_diff = """
    @@ -15,5 +15,6 @@ def process_payment(amount):
    -    if amount > 0:
    +    if amount > 0 and user.is_verified():
             return gateway.pay(amount)
    +    else:
    +        raise ValueError("Invalid payment request")
    """
    
    mode = st.radio("모드 선택", ["데모 데이터로 확인 (즉시)", "실제 GitLab 링크 분석 (API 키 필요)"])

    if mode == "데모 데이터로 확인 (즉시)":
        target_url = st.text_input("GitLab 링크 (예시)", value="https://gitlab.com/demo/project/-/merge_requests/123", disabled=True)
        if st.button("데모 분석 시작"):
            with st.spinner("AI가 샘플 데이터를 분석 중입니다..."):
                time.sleep(2) # 분석하는 느낌 전달
                st.success("✅ 분석 완료!")
                st.markdown("""
                ### 🚩 **핵심 변경 요약**:
                결제 처리 로직에 사용자 인증(Verification) 절차 추가 및 예외 처리 강화.

                ### ⚠️ **사이드 이펙트 분석**:
                - **영향 범위**: 결제 모듈, 회원 인증 시스템.
                - **리스크 내용**: 인증되지 않은 사용자가 결제 시도 시 적절한 UI 안내가 없는 경우 무한 로딩이나 앱 크래시 발생 가능성.

                ### 🔍 **QA 중점 테스트 포인트**:
                - [P0] 결제 시도 - 인증된 사용자의 정상 결제 여부 확인
                - [P0] 결제 시도 - 미인증 사용자의 차단 및 에러 메시지 노출 확인
                - [P1] 인증 상태 변경 - 결제 도중 인증이 만료되는 엣지 케이스 확인
                """)

    else:
        gitlab_link = st.text_input("GitLab MR/Commit 링크를 입력하세요")
        if st.button("실제 분석 시작"):
            if not user_gemini_key:
                st.warning("사이드바에 Gemini API Key를 입력해주세요!")
            else:
                st.info("입력하신 키와 링크를 통해 실제 분석을 수행하는 로직이 여기에 들어갑니다.")
                # 여기에 기존의 GitLab API 및 Gemini 호출 로직을 연결하면 됩니다.
