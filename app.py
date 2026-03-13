import streamlit as st
import datetime
from utils.parser import parse_vcs_link 
from services.vcs_service import fetch_vcs_data 
from services.ai_service import analyze_code 
from config.settings import DEFAULT_PROMPT
from utils.exporter import generate_html_report, generate_tc_excel

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="💊", layout="wide")

# 💡 세션 상태(Session State)를 이용한 데이터 저장소 초기화
if 'history' not in st.session_state:
    st.session_state.history = []

st.markdown("""
<style>
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label { background-color: #ffffff; border: 2px solid #f0f2f6; border-radius: 50px !important; padding: 12px 20px; margin-bottom: 12px; cursor: pointer; transition: all 0.2s ease-in-out; width: 100%; text-align: center; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { background-color: #4A90E2 !important; border-color: #4A90E2 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: white !important; font-weight: 700 !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🛠️ 딴딴의 여러가지 툴")
    st.markdown("<br>", unsafe_allow_html=True) 
    selected_menu = st.radio("메뉴 선택", ["🚀 형상관리 QA 리스크 분석기", "📝 기획서-코드 검증기", "🛅 TC 자동 생성기"], label_visibility="collapsed")

if selected_menu == "🚀 형상관리 QA 리스크 분석기":
    st.title("🛡️ 형상관리 QA 리스크 분석기")

    # 💡 분석 엔진 및 사용자 입력 영역
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([1, 1, 1.5, 1.5]) 
        
        with col1:
            user_name = st.text_input("👤 사용자명", placeholder="홍길동")
        with col2:
            ai_provider = st.selectbox("🤖 AI 선택", ["Gemini", "ChatGPT", "Claude"]) 
        with col3:
            api_key = st.text_input(f"{ai_provider} API Key", type="password")
        with col4:
            vcs_token = st.text_input("GitLab/GitHub Token", type="password")
            
        # 💡 [복구완료] 사라졌던 맞춤 프롬프트 팝오버 부활!
        with st.popover("📝 맞춤 프롬프트 확인 및 수정", use_container_width=True):
            st.markdown("**기본 적용된 9칸 엑셀 포맷 프롬프트입니다. 필요시 수정하세요.**")
            custom_prompt = st.text_area("AI 프롬프트", value=DEFAULT_PROMPT, height=300)

        link = st.text_input("🔗 분석할 링크 (GitLab MR / GitHub PR / Commit)")
        
        # 버튼을 꽉 차게 배치
        if st.button("🚀 분석 실행", type="primary", use_container_width=True):
            if not (user_name and api_key and link):
                st.error("사용자명, API 키, 링크를 모두 입력해주세요.")
                st.stop()
                
            parsed = parse_vcs_link(link)
            if not parsed:
                st.error("지원하지 않는 링크 형식입니다.")
                st.stop()

            with st.spinner(f"{parsed['platform'].capitalize()}에서 코드 변경점을 가져오는 중..."):
                commits, diffs = fetch_vcs_data(parsed, vcs_token)
            
            if commits is None:
                st.error(diffs)
                st.stop()

            with st.spinner("AI가 코드를 분석하고 TC를 생성하는 중..."):
                # 수정된 custom_prompt를 다시 전달
                result, used_model, error = analyze_code(ai_provider, api_key, commits, diffs, custom_prompt)
                
            if result:
                st.success("✅ 분석이 완료되어 리스트에 추가되었습니다!")
                
                # 결과물 분리 생성
                html_data = generate_html_report(result)
                excel_data = generate_tc_excel(result)
                
                # 히스토리 리스트 맨 위에 데이터 삽입
                record = {
                    'id': len(st.session_state.history) + 1,
                    'time': datetime.datetime.now().strftime("%y-%m-%d %H:%M"),
                    'user': user_name,
                    'api': f"{ai_provider} ({used_model})",
                    'platform': parsed['platform'].capitalize(),
                    'link': link,
                    'html': html_data,
                    'excel': excel_data
                }
                st.session_state.history.insert(0, record)
            else:
                st.error(f"분석 실패: {error}")

    st.divider()

    # 💡 분석 결과 대시보드 (리스트 노출)
    st.subheader("🗂️ 분석 결과 히스토리")
    
    if not st.session_state.history:
        st.info("실행된 분석 결과가 없습니다. 첫 분석을 시작해보세요!")
    else:
        # 리스트 헤더
        h1, h2, h3, h4, h5, h6 = st.columns([1, 1.5, 1.5, 1, 4, 2])
        h1.markdown("**사용자**")
        h2.markdown("**일시**")
        h3.markdown("**API**")
        h4.markdown("**저장소**")
        h5.markdown("**대상 링크**")
        h6.markdown("**다운로드**")
        
        # 누적된 히스토리 반복 출력
        for item in st.session_state.history:
            st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)
            c1, c2, c3, c4, c5, c6 = st.columns([1, 1.5, 1.5, 1, 4, 2])
            
            with c1: st.write(f"👤 {item['user']}")
            with c2: st.caption(item['time'])
            with c3: st.caption(item['api'])
            with c4: st.write(item['platform'])
            with c5: 
                short_link = item['link'][:50] + "..." if len(item['link']) > 50 else item['link']
                st.caption(f"[{short_link}]({item['link']})")
            
            with c6:
                btn_col1, btn_col2 = st.columns(2)
                btn_col1.download_button("🌐 HTML", data=item['html'], file_name=f"Report_{item['id']}.html", mime="text/html", key=f"h_{item['id']}", use_container_width=True)
                if item['excel']:
                    btn_col2.download_button("📊 Excel", data=item['excel'], file_name=f"TC_{item['id']}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"e_{item['id']}", use_container_width=True)
                else:
                    btn_col2.button("⚠️ 실패", disabled=True, key=f"err_{item['id']}", use_container_width=True)

elif selected_menu == "📝 기획서-코드 검증기":
    st.title("📝 기획서-코드 검증기")
    st.info("이 기능은 현재 개발 중입니다.")

elif selected_menu == "🛅 TC 자동 생성기":
    st.title("🛅 TC 자동 생성기")
    st.info("이 기능은 현재 개발 중입니다.")