import streamlit as st
import datetime
import math
from utils.parser import parse_vcs_link 
from services.vcs_service import fetch_vcs_data 
from services.ai_service import analyze_code 
from config.settings import DEFAULT_PROMPT
from utils.exporter import generate_html_report, generate_tc_excel

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="💊", layout="wide")

# 💡 [핵심 변경] DB를 대신할 '글로벌 공유 메모리' 생성
@st.cache_resource
def get_global_state():
    return {"history": []}

global_state = get_global_state()

# 페이징은 사용자마다 다르게 보여야 하므로 세션 유지
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

SUPER_PASSWORD = "admin1234"  # 👑 관리자 슈퍼 비밀번호

st.markdown("""
<style>
    /* 메인 화면 상단 여백 축소 */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label { background-color: #ffffff; border: 2px solid #f0f2f6; border-radius: 50px !important; padding: 12px 20px; margin-bottom: 12px; cursor: pointer; transition: all 0.2s ease-in-out; width: 100%; text-align: center; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { border-color: #4A90E2; background-color: #F0F8FF; transform: translateY(-2px); }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { background-color: #4A90E2 !important; border-color: #4A90E2 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: white !important; font-weight: 700 !important; }
    
    div[data-testid="column"] button { width: 100%; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🛠️ 딴딴의 여러가지 툴")
    st.markdown("<br>", unsafe_allow_html=True) 
    selected_menu = st.radio("메뉴 선택", ["🚀 QA 리스크 분석 및 TC 생성 툴", "📝 2번째 프로젝트", "🛅 3번째 프로젝트"], label_visibility="collapsed")

if selected_menu == "🚀 QA 리스크 분석 및 TC 생성 툴":
    st.title("🚀 QA 리스크 분석 및 TC 생성 툴")

    # 💡 [신규 기능] 데모 화면과 실제 툴을 탭(Tab)으로 깔끔하게 분리
    tab_main, tab_demo = st.tabs(["💻 직접 사용해보기", "👀 1분 데모 보기 (API 키가 없다면)"])

    # ---------------------------------------------------------
    # 탭 1: 실제 동작하는 기존 툴 로직
    # ---------------------------------------------------------
    with tab_main:
        with st.container(border=True):
            r1_c1, r1_c2 = st.columns(2)
            user_name = r1_c1.text_input("👤 사용자명", placeholder="홍길동")
            doc_password = r1_c2.text_input("🔒 비밀번호 (결과물 보호용)", type="password", placeholder="다운로드 시 필요합니다")

            r2_c1, r2_c2 = st.columns(2)
            ai_provider = r2_c1.selectbox("🤖 AI 선택", ["Gemini", "ChatGPT", "Claude"]) 
            api_key = r2_c2.text_input(f"{ai_provider} API Key", type="password")

            r3_c1, r3_c2 = st.columns(2)
            vcs_token = r3_c1.text_input("🔑 GitLab/GitHub Token", type="password", placeholder="비공개 저장소인 경우 필수")
            link = r3_c2.text_input("🔗 분석할 링크 (GitLab MR / GitHub PR / Commit)")

            r4_c1, r4_c2 = st.columns([3, 1])
            with r4_c1.popover("📝 맞춤 프롬프트 확인 및 수정", use_container_width=True):
                custom_prompt = st.text_area("AI 프롬프트", value=DEFAULT_PROMPT, height=300)
            
            submit_btn = r4_c2.button("🚀 분석 실행", type="primary", use_container_width=True)

        if submit_btn:
            if not (user_name and doc_password and api_key and link):
                st.error("사용자명, 비밀번호, API 키, 링크를 모두 입력해주세요.")
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
                result, used_model, error = analyze_code(ai_provider, api_key, commits, diffs, custom_prompt)
                
            if result:
                st.success("✅ 분석이 완료되어 공용 리스트에 추가되었습니다!")
                
                html_data = generate_html_report(result)
                excel_data = generate_tc_excel(result)
                
                # 고유 ID 생성 (삭제 후에도 중복 방지)
                new_id = max([item['id'] for item in global_state["history"]] + [0]) + 1
                
                record = {
                    'id': new_id,
                    'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'user': user_name,
                    'password': doc_password,
                    'api': f"{ai_provider} ({used_model})",
                    'platform': parsed['platform'].capitalize(),
                    'link': link,
                    'html': html_data,
                    'excel': excel_data
                }
                # 글로벌 상태에 저장!
                global_state["history"].insert(0, record)
                st.session_state.current_page = 1
            else:
                st.error(f"분석 실패: {error}")

        st.divider()

        st.subheader("🗂️ 실시간 공용 분석 히스토리")
        
        search_col, _ = st.columns([1, 5])
        with search_col:
            search_query = st.text_input("🔍 사용자명 검색", placeholder="검색할 사용자명")
            
        st.markdown("<br>", unsafe_allow_html=True) 

        if not global_state["history"]:
            st.info("실행된 분석 결과가 없습니다. 첫 분석을 시작해보세요!")
        else:
            # 글로벌 상태에서 데이터 가져오기
            if search_query:
                filtered_history = [item for item in global_state["history"] if search_query.lower() in item['user'].lower()]
            else:
                filtered_history = global_state["history"]

            if not filtered_history:
                st.warning("검색 결과가 없습니다.")
            else:
                ITEMS_PER_PAGE = 5
                total_items = len(filtered_history)
                total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
                
                if st.session_state.current_page > total_pages:
                    st.session_state.current_page = max(1, total_pages)
                    
                start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
                end_idx = start_idx + ITEMS_PER_PAGE
                current_items = filtered_history[start_idx:end_idx]

                h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([1, 1.2, 1, 1, 2, 1.5, 2, 1])
                h1.markdown("<div style='text-align: center;'><b>사용자</b></div>", unsafe_allow_html=True)
                h2.markdown("<div style='text-align: center;'><b>일시</b></div>", unsafe_allow_html=True)
                h3.markdown("<div style='text-align: center;'><b>API</b></div>", unsafe_allow_html=True)
                h4.markdown("<div style='text-align: center;'><b>저장소</b></div>", unsafe_allow_html=True)
                h5.markdown("<div style='text-align: center;'><b>분석한 링크</b></div>", unsafe_allow_html=True)
                h6.markdown("<div style='text-align: center;'><b>비밀번호</b></div>", unsafe_allow_html=True)
                h7.markdown("<div style='text-align: center;'><b>다운로드</b></div>", unsafe_allow_html=True)
                h8.markdown("<div style='text-align: center;'><b>삭제</b></div>", unsafe_allow_html=True)
                
                for item in current_items:
                    st.markdown("<hr style='margin: 0.5em 0;'>", unsafe_allow_html=True)
                    c1, c2, c3, c4, c5, c6, c7, c8 = st.columns([1, 1.2, 1, 1, 2, 1.5, 2, 1])
                    
                    with c1: st.markdown(f"<div style='text-align: center;'>👤 {item['user']}</div>", unsafe_allow_html=True)
                    with c2: st.markdown(f"<div style='text-align: center; color: gray; font-size: 0.9em;'>{item['time']}</div>", unsafe_allow_html=True)
                    with c3: st.markdown(f"<div style='text-align: center; color: gray; font-size: 0.9em;'>{item['api']}</div>", unsafe_allow_html=True)
                    with c4: st.markdown(f"<div style='text-align: center;'>{item['platform']}</div>", unsafe_allow_html=True)
                    with c5: 
                        short_link = item['link'][:30] + "..." if len(item['link']) > 30 else item['link']
                        st.markdown(f"<div style='text-align: center; font-size: 0.9em;'><a href='{item['link']}' target='_blank'>{short_link}</a></div>", unsafe_allow_html=True)
                    
                    with c6:
                        input_pw = st.text_input("PW", type="password", key=f"pw_{item['id']}", label_visibility="collapsed", placeholder="비밀번호")
                        
                    is_unlocked = (input_pw == item['password'] or input_pw == SUPER_PASSWORD)
                    
                    with c7:
                        if is_unlocked:
                            btn_col1, btn_col2 = st.columns(2)
                            btn_col1.download_button("📊 보고서", data=item['html'], file_name=f"Report_{item['id']}.html", mime="text/html", key=f"h_{item['id']}", use_container_width=True)
                            if item['excel']:
                                btn_col2.download_button("📗 엑셀", data=item['excel'], file_name=f"TC_{item['id']}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"e_{item['id']}", use_container_width=True)
                        else:
                            if input_pw:
                                st.markdown("<div style='text-align: center; color: red; margin-top: 8px;'>불일치</div>", unsafe_allow_html=True)
                            else:
                                st.markdown("<div style='text-align: center; color: gray; margin-top: 8px;'>🔒 잠김</div>", unsafe_allow_html=True)

                    with c8:
                        if is_unlocked:
                            if st.button("🗑️ 삭제", key=f"del_{item['id']}", type="secondary", use_container_width=True):
                                # 글로벌 상태에서 항목 삭제
                                global_state["history"] = [x for x in global_state["history"] if x['id'] != item['id']]
                                st.rerun()
                        else:
                            st.button("🗑️ 삭제", key=f"del_dis_{item['id']}", disabled=True, use_container_width=True)

                st.markdown("<br>", unsafe_allow_html=True)
                
                if total_pages > 1:
                    p1, p2, p3 = st.columns([1, 3, 1])
                    with p1:
                        if st.button("◀ 이전", use_container_width=True, disabled=(st.session_state.current_page == 1)):
                            st.session_state.current_page -= 1
                            st.rerun()
                    with p2:
                        st.markdown(f"<div style='text-align: center; padding-top: 5px;'><b>{st.session_state.current_page} / {total_pages} 페이지</b></div>", unsafe_allow_html=True)
                    with p3:
                        if st.button("다음 ▶", use_container_width=True, disabled=(st.session_state.current_page == total_pages)):
                            st.session_state.current_page += 1
                            st.rerun()

    # ---------------------------------------------------------
    # 탭 2: 1분 데모 보기 (이미지 워크스루)
    # ---------------------------------------------------------
    with tab_demo:
        st.subheader("💡 1분 데모 워크스루")
        st.info("API 키나 토큰이 없으신 분들을 위해 실제 구동 화면을 캡처하여 제공합니다. 아래 순서대로 툴이 동작합니다.")
        
        st.markdown("### 1️⃣ Step 1. 분석 대상 및 환경 설정")
        st.markdown("사용자명, AI 모델, API 키, 그리고 **분석할 코드의 깃허브(또는 깃랩) PR/MR 링크**를 입력합니다.")
        # ⚠️ 아래 캡처 이미지들의 주석을 풀고 파일명을 맞추면 화면에 바로 나옵니다!
        # st.image("step1_input.png", use_container_width=True) 
        
        st.divider()

        st.markdown("### 2️⃣ Step 2. AI 분석 완료 및 히스토리 누적")
        st.markdown("분석이 완료되면 팀원 모두가 볼 수 있는 **실시간 공용 대시보드**에 결과가 누적됩니다. 타인이 열람하지 못하도록 설정한 비밀번호로 다운로드를 제어합니다.")
        # st.image("step2_dashboard.png", use_container_width=True)

        st.divider()

        st.markdown("### 3️⃣ Step 3. QA 리스크 보고서 확인 (HTML)")
        st.markdown("AI가 코드 변경점을 분석하여 도출한 **사이드 이펙트와 QA 중점 테스트 포인트**를 깔끔한 HTML 보고서로 즉시 다운로드하여 확인할 수 있습니다.")
        # st.image("step3_html.png", use_container_width=True)

        st.divider()

        st.markdown("### 4️⃣ Step 4. 엑셀 테스트케이스(TC) 확인")
        st.markdown("보고서뿐만 아니라, **실제 QA 실무에서 사용하는 9열 포맷(Depth, 상세, 사전조건 등)**이 서식까지 완벽하게 적용된 엑셀 파일로 자동 생성됩니다.")
        # st.image("step4_excel.png", use_container_width=True)

elif selected_menu == "📝 2번째 프로젝트":
    st.title("📝 2번째 프로젝트")
    st.info("이 기능은 현재 개발 중입니다.")

elif selected_menu == "🛅 3번째 프로젝트":
    st.title("🛅 3번째 프로젝트")
    st.info("이 기능은 현재 개발 중입니다.")