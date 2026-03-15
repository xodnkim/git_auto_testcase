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
        st.image("step1_1.png", use_container_width=True) 
        st.image("step1.png", use_container_width=True) 
        
        st.divider()

        st.markdown("### 2️⃣ Step 2. AI 분석 완료 및 히스토리 누적")
        st.markdown("분석이 완료되면 팀원 모두가 볼 수 있는 **실시간 공용 대시보드**에 결과가 누적됩니다. 타인이 열람하지 못하도록 설정한 비밀번호로 다운로드를 제어합니다.")
        st.image("step2.png", use_container_width=True)

        st.divider()

        st.markdown("### 3️⃣ Step 3. QA 리스크 보고서 확인 (HTML)")
        st.markdown("AI가 코드 변경점을 분석하여 도출한 **사이드 이펙트와 QA 중점 테스트 포인트**를 깔끔한 HTML 보고서로 즉시 다운로드하여 확인할 수 있습니다.")
        st.image("step3.png", use_container_width=True)

        st.divider()

        st.markdown("### 4️⃣ Step 4. 엑셀 테스트케이스(TC) 확인")
        st.markdown("보고서뿐만 아니라, **실제 QA 실무에서 사용하는 9열 포맷(Depth, 상세, 사전조건 등)**이 서식까지 완벽하게 적용된 엑셀 파일로 자동 생성됩니다.")
        st.image("step4.png", use_container_width=True)

# 사이드바 메뉴 이름부터 이렇게 바꿔주세요!
# selected_menu = st.radio("메뉴 선택", ["🚀 QA 리스크 분석 및 TC 생성 툴", "📋 Jira 테스트 계획서 생성기", "🛅 3번째 프로젝트"], label_visibility="collapsed")

elif selected_menu == "📋 Jira 테스트 계획서 생성기":
    st.title("📋 Jira 테스트 계획서 (Test Plan) 자동 생성기")
    st.info("💡 실무 표준 템플릿을 제공합니다. 빈칸을 채우고 항목을 추가하여 지라(Jira) 티켓에 복사/붙여넣기 하세요!")

    # 사용자 정의 항목 개수를 관리하기 위한 세션 상태
    if 'custom_sec_count' not in st.session_state:
        st.session_state.custom_sec_count = 0

    with st.container(border=True):
        st.subheader("1️⃣ 기본 템플릿 작성")
        
        c1, c2 = st.columns(2)
        project_name = c1.text_input("🚀 프로젝트/기능명", placeholder="예: 장바구니 UI 개편 및 결제 수단 추가")
        qa_manager = c2.text_input("👤 담당 QA", placeholder="예: 홍길동")
        
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        overview = st.text_area("📝 기능 개요 (Overview)", placeholder="이번 업데이트의 주요 목적과 기획 의도를 간략히 적어주세요.")
        
        c3, c4 = st.columns(2)
        in_scope = c3.text_area("🎯 테스트 포함 범위 (In-Scope)", placeholder="- 장바구니 상품 담기/삭제\n- 신용카드 결제 연동\n- 비회원 주문 로직")
        out_scope = c4.text_area("🚫 테스트 제외 범위 (Out-of-Scope)", placeholder="- 카카오페이 결제 (다음 스프린트)\n- 마이페이지 UI (변경 없음)")
        
        c5, c6 = st.columns(2)
        environment = c5.text_area("💻 테스트 환경 (Environment)", placeholder="- Web: Chrome, Safari (Latest)\n- Mobile: iOS 16+, Android 12+\n- Server: Staging (QA DB)")
        risks = c6.text_area("⚠️ 리스크 및 주의사항 (Risks)", placeholder="- 결제 PG사 연동 테스트 시 반드시 테스트 카드로만 진행할 것\n- 자정(00시) 데이터 배치 작업 시간대 테스트 피할 것")

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        st.subheader("2️⃣ 추가 항목 (Custom Sections)")
        st.caption("회사마다 필요한 특별한 항목(예: 테스트 일정, 산출물 링크 등)이 있다면 추가하세요.")
        
        # 💡 [핵심 UX] '+' 버튼으로 입력 폼 동적 추가
        if st.button("➕ 항목 추가하기", use_container_width=True):
            st.session_state.custom_sec_count += 1
            
        custom_sections = []
        for i in range(st.session_state.custom_sec_count):
            with st.container(border=True):
                cc1, cc2 = st.columns([1, 3])
                c_title = cc1.text_input(f"항목 제목 #{i+1}", key=f"c_title_{i}", placeholder="예: 테스트 일정")
                c_content = cc2.text_area(f"항목 내용 #{i+1}", key=f"c_content_{i}", placeholder="예: 2026-03-20 ~ 2026-03-25")
                custom_sections.append((c_title, c_content))

        submit_plan = st.button("✨ Jira 테스트 계획서 생성", type="primary", use_container_width=True)

    # 결과 출력부
    if submit_plan:
        if not project_name:
            st.warning("프로젝트/기능명을 입력해주세요!")
            st.stop()
            
        st.success("✅ 테스트 계획서가 생성되었습니다! 우측 상단의 복사 아이콘을 눌러 Jira에 붙여넣으세요.")
        
        # 💡 Jira/Confluence에 찰떡같이 붙는 Markdown 포맷 생성
        jira_markdown = f"""# 📋 [QA 테스트 계획서] {project_name}

**담당 QA:** {qa_manager if qa_manager else '미지정'}
**작성일자:** {datetime.datetime.now().strftime("%Y-%m-%d")}

---

### 🚀 1. 기능 개요 (Overview)
{overview if overview else '내용 없음'}

### 🎯 2. 테스트 대상 및 범위 (In-Scope)
{in_scope if in_scope else '내용 없음'}

### 🚫 3. 테스트 제외 대상 (Out-of-Scope)
{out_scope if out_scope else '내용 없음'}

### 💻 4. 테스트 환경 (Test Environment)
{environment if environment else '내용 없음'}

### ⚠️ 5. 리스크 및 주의사항 (Risks)
{risks if risks else '내용 없음'}
"""
        # 사용자 추가 항목 이어붙이기
        if custom_sections:
            for idx, (t, c) in enumerate(custom_sections):
                if t or c:
                    jira_markdown += f"\n### 📌 {idx+6}. {t if t else '추가 항목'}\n{c if c else '내용 없음'}\n"

        # 코드 블록으로 출력하여 쉽게 복사(Copy)할 수 있게 UX 구성
        st.code(jira_markdown, language="markdown")

elif selected_menu == "🛅 3번째 프로젝트":
    st.title("🛅 3번째 프로젝트")
    st.info("이 기능은 현재 개발 중입니다.")