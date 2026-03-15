import streamlit as st
import datetime
import math
import time  # 💡 가짜 로딩(Mock)을 위해 추가
from utils.parser import parse_vcs_link 
from services.vcs_service import fetch_vcs_data 
from services.ai_service import analyze_code 
from config.settings import DEFAULT_PROMPT
from utils.exporter import generate_html_report, generate_tc_excel

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="💊", layout="wide")

# 💡 DB를 대신할 '글로벌 공유 메모리' 생성
@st.cache_resource
def get_global_state():
    return {"history": []}

global_state = get_global_state()

# 페이징 세션 유지
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

SUPER_PASSWORD = "admin1234"  # 👑 관리자 슈퍼 비밀번호

st.markdown("""
<style>
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
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
    # 💡 메뉴 2번 이름 변경
    selected_menu = st.radio("메뉴 선택", ["🚀 QA 리스크 분석 및 TC 생성 툴", "📊 E2E 자동화 대시보드 (Demo)", "🛅 3번째 프로젝트"], label_visibility="collapsed")

# =====================================================================
# 1️⃣ 첫 번째 프로젝트: QA 리스크 분석 및 TC 생성 툴
# =====================================================================
if selected_menu == "🚀 QA 리스크 분석 및 TC 생성 툴":
    st.title("🚀 QA 리스크 분석 및 TC 생성 툴")

    tab_main, tab_demo = st.tabs(["💻 직접 사용해보기", "👀 1분 데모 보기 (API 키가 없다면)"])

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
            with r4_c1.popover("📝 맞춤 프롬프트 확인 및 수정", width="stretch"):
                custom_prompt = st.text_area("AI 프롬프트", value=DEFAULT_PROMPT, height=300)
            
            submit_btn = r4_c2.button("🚀 분석 실행", type="primary", width="stretch")

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
                new_id = max([item['id'] for item in global_state["history"]] + [0]) + 1
                
                record = {
                    'id': new_id, 'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'user': user_name, 'password': doc_password, 'api': f"{ai_provider} ({used_model})",
                    'platform': parsed['platform'].capitalize(), 'link': link,
                    'html': html_data, 'excel': excel_data
                }
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
                
                if st.session_state.current_page > total_pages: st.session_state.current_page = max(1, total_pages)
                    
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
                            btn_col1.download_button("📊 보고서", data=item['html'], file_name=f"Report_{item['id']}.html", mime="text/html", key=f"h_{item['id']}", width="stretch")
                            if item['excel']:
                                btn_col2.download_button("📗 엑셀", data=item['excel'], file_name=f"TC_{item['id']}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", key=f"e_{item['id']}", width="stretch")
                        else:
                            if input_pw: st.markdown("<div style='text-align: center; color: red; margin-top: 8px;'>불일치</div>", unsafe_allow_html=True)
                            else: st.markdown("<div style='text-align: center; color: gray; margin-top: 8px;'>🔒 잠김</div>", unsafe_allow_html=True)

                    with c8:
                        if is_unlocked:
                            if st.button("🗑️ 삭제", key=f"del_{item['id']}", type="secondary", width="stretch"):
                                global_state["history"] = [x for x in global_state["history"] if x['id'] != item['id']]
                                st.rerun()
                        else:
                            st.button("🗑️ 삭제", key=f"del_dis_{item['id']}", disabled=True, width="stretch")

                st.markdown("<br>", unsafe_allow_html=True)
                
                if total_pages > 1:
                    p1, p2, p3 = st.columns([1, 3, 1])
                    with p1:
                        if st.button("◀ 이전", width="stretch", disabled=(st.session_state.current_page == 1)):
                            st.session_state.current_page -= 1
                            st.rerun()
                    with p2:
                        st.markdown(f"<div style='text-align: center; padding-top: 5px;'><b>{st.session_state.current_page} / {total_pages} 페이지</b></div>", unsafe_allow_html=True)
                    with p3:
                        if st.button("다음 ▶", width="stretch", disabled=(st.session_state.current_page == total_pages)):
                            st.session_state.current_page += 1
                            st.rerun()

    with tab_demo:
        st.subheader("💡 1분 데모 워크스루")
        st.info("API 키나 토큰이 없으신 분들을 위해 실제 구동 화면을 캡처하여 제공합니다. 아래 순서대로 툴이 동작합니다.")
        st.markdown("### 1️⃣ Step 1. 분석 대상 및 환경 설정")
        # st.image("step1_input.png") 
        st.divider()
        st.markdown("### 2️⃣ Step 2. AI 분석 완료 및 히스토리 누적")
        # st.image("step2_dashboard.png")
        st.divider()
        st.markdown("### 3️⃣ Step 3. QA 리스크 보고서 확인 (HTML)")
        # st.image("step3_html.png")
        st.divider()
        st.markdown("### 4️⃣ Step 4. 엑셀 테스트케이스(TC) 확인")
        # st.image("step4_excel.png")


# =====================================================================
# 2️⃣ 두 번째 프로젝트: E2E 자동화 대시보드 (Demo)
# =====================================================================
elif selected_menu == "📊 E2E 자동화 대시보드 (Demo)":
    st.title("📊 E2E 테스트 자동화 대시보드")
    st.info("💡 **[포트폴리오 데모용]** 실제 Playwright 기반 자동화 테스트가 어떻게 리포팅되는지 확인하고, 직접 값을 변경하여 예외(Fail) 케이스를 유도해 볼 수 있는 인터랙티브 대시보드입니다.")

    tab_dash, tab_practice = st.tabs(["📈 종합 결과 리포트", "🧪 인터랙티브 테스트 체험"])

    # --- 탭 1: 종합 결과 리포트 (정적 대시보드) ---
    with tab_dash:
        st.subheader("최근 테스트 실행 결과 (Latest Run)")
        # 💡 시간과 환경 등은 원하시는 대로 텍스트를 수정하시면 됩니다!
        st.caption("실행 일시: 2026-03-16 09:00 KST | 소요 시간: 12m 45s | 환경: Staging")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 테스트 케이스", "142 개")
        m2.metric("✅ Passed", "138 개", "97.1%")
        m3.metric("❌ Failed", "3 개", "-2.9%")
        m4.metric("⚠️ Flaky (불안정)", "1 개")

        st.markdown("<hr style='margin: 1em 0;'>", unsafe_allow_html=True)

        st.markdown("### 🚨 주요 실패(Failed) 내역 분석")
        # 💡 expander 안의 텍스트를 회사 도메인에 맞게 수정하시면 됩니다.
        with st.expander("❌ [결제 도메인] TC-089: 포인트 전액 결제 시 PG창 호출 스킵 여부 (클릭하여 상세 보기)", expanded=True):
            st.error("**[AssertionError]** 예상결과: PG 결제창이 호출되지 않아야 함. / 실제결과: PG창 팝업이 렌더링됨.")
            st.code("""
# Playwright Traceback Log
> page.click('button#submit-order')
> expect(page.locator('#pg-iframe')).not_to_be_visible(timeout=5000)
E AssertionError: Locator expected to be hidden, but is visible.
            """, language="python")
            # 가짜 다운로드 버튼 (실제 파일 연결은 추후 필요시 추가)
            st.button("📄 상세 HTML 리포트 다운로드 (Sample)", key="download_mock_1")

        with st.expander("❌ [게시글 도메인] TC-033: 50MB 초과 이미지 첨부 시 예외 처리"):
            st.error("**[TimeoutError]** 용량 초과 경고 모달이 10초 이내에 나타나지 않고 무한 로딩 발생.")

        with st.expander("❌ [로그인 도메인] TC-012: 휴면 계정 로그인 시 안내 모달 노출 여부"):
            st.error("**[AssertionError]** 휴면 해제 안내 모달 대신 '비밀번호 5회 오류' 모달이 잘못 노출됨.")

    # --- 탭 2: 인터랙티브 테스트 체험 (동적 Mock 실행) ---
    with tab_practice:
        st.subheader("🧪 Playwright 테스트 실행기 (Interactive Mode)")
        st.markdown("사용자가 입력한 값에 따라 **미리 정의된 자동화 스크립트**가 어떻게 반응(Pass/Fail)하는지 확인해 보세요.")

        with st.container(border=True):
            # 💡 테스트할 도메인을 자유롭게 추가/수정하세요!
            test_domain = st.selectbox("📌 테스트할 시나리오 선택", ["🛒 장바구니 및 결제 로직 검증", "🔐 로그인 및 인증 로직 검증"])
            st.markdown("<br>", unsafe_allow_html=True)

            # 1. 결제 로직 시나리오
            if test_domain == "🛒 장바구니 및 결제 로직 검증":
                st.markdown("**[테스트 설명]** 상품을 장바구니에 담고 결제를 시도합니다. 결제 금액은 0원보다 커야 하며, 재고가 있어야 합니다.")
                c1, c2 = st.columns(2)
                test_amount = c1.number_input("입력할 결제 금액 (원)", value=50000, step=1000)
                test_stock = c2.selectbox("상품 재고 상태", ["재고 있음", "품절 (Out of Stock)"])

                if st.button("▶️ 테스트 스크립트 실행", type="primary", key="run_pay", width="stretch"):
                    with st.spinner("Playwright 브라우저 인스턴스 시작 중... (가상 환경)"):
                        time.sleep(1.5) # 💡 진짜 돌아가는 것 같은 로딩 효과
                        
                        # 예외 처리 로직 (미리 정의된 결과)
                        if test_stock == "품절 (Out of Stock)":
                            st.error("🚨 **[Failed]** TC-044: 품절 상품 결제 시도 방어 로직 검증")
                            st.code("AssertionError: '품절된 상품입니다' 알림창이 노출되지 않고 결제 단계로 진입함.", language="text")
                        elif test_amount <= 0:
                            st.error("🚨 **[Failed]** TC-045: 비정상 결제 금액(0원 이하) 방어 로직 검증")
                            st.code(f"Error: API 응답 코드 500 발생. (요청 금액: {test_amount}원)\n프론트엔드에서 0원 이하 입력을 차단하지 못했습니다.", language="text")
                        else:
                            st.success(f"✅ **[Passed]** TC-046: 정상 결제 시나리오 (금액: {test_amount}원, 재고 있음)")
                            st.info("실행 로그: 아이템 담기 성공 -> 결제 정보 입력 성공 -> PG사 호출 성공")

            # 2. 로그인 로직 시나리오
            elif test_domain == "🔐 로그인 및 인증 로직 검증":
                st.markdown("**[테스트 설명]** 사용자 ID와 비밀번호를 입력하여 로그인을 시도합니다. (올바른 비밀번호: `test1234`)")
                c3, c4 = st.columns(2)
                test_id = c3.text_input("아이디", value="qa_tester_01")
                test_pw = c4.text_input("비밀번호 (일부러 틀리게 적어보세요!)", value="test1234", type="password")

                if st.button("▶️ 테스트 스크립트 실행", type="primary", key="run_login", width="stretch"):
                    with st.spinner("UI 상호작용 및 API 응답 대기 중..."):
                        time.sleep(1.2)
                        
                        if test_pw == "test1234":
                            st.success("✅ **[Passed]** TC-001: 유효한 자격 증명으로 로그인 성공")
                            st.info(f"실행 로그: '{test_id}' 입력 -> '{test_pw}' 입력 -> 메인 대시보드로 라우팅 됨.")
                        else:
                            st.error("🚨 **[Failed]** TC-002: 잘못된 비밀번호 입력 시 예외 처리 검증")
                            st.code("AssertionError: '비밀번호가 일치하지 않습니다' Toast 메시지가 노출되어야 하나, 무한 로딩(Spinner) 상태에 빠짐.", language="text")

# =====================================================================
# 3️⃣ 세 번째 프로젝트 (미정)
# =====================================================================
elif selected_menu == "🛅 3번째 프로젝트":
    st.title("🛅 3번째 프로젝트")
    st.info("이 기능은 현재 기획/개발 중입니다.")