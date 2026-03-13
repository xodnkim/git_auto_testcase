import streamlit as st
import datetime
import math
from utils.parser import parse_vcs_link 
from services.vcs_service import fetch_vcs_data 
from services.ai_service import analyze_code 
from config.settings import DEFAULT_PROMPT
from utils.exporter import generate_html_report, generate_tc_excel

st.set_page_config(page_title="딴딴의 여러가지 툴", page_icon="💊", layout="wide")

# 💡 세션 상태(Session State) 초기화
if 'history' not in st.session_state:
    st.session_state.history = []
if 'current_page' not in st.session_state:
    st.session_state.current_page = 1

SUPER_PASSWORD = "admin1234"  # 👑 관리자 슈퍼 비밀번호

st.markdown("""
<style>
    section[data-testid="stSidebar"] div[role="radiogroup"] > label > div:first-child { display: none; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label { background-color: #ffffff; border: 2px solid #f0f2f6; border-radius: 50px !important; padding: 12px 20px; margin-bottom: 12px; cursor: pointer; transition: all 0.2s ease-in-out; width: 100%; text-align: center; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:hover { border-color: #4A90E2; background-color: #F0F8FF; transform: translateY(-2px); }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) { background-color: #4A90E2 !important; border-color: #4A90E2 !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] > label:has(input:checked) p { color: white !important; font-weight: 700 !important; }
    
    /* 버튼 및 인풋 정렬 보정 */
    div[data-testid="column"] button { width: 100%; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🛠️ 딴딴의 여러가지 툴")
    st.markdown("<br>", unsafe_allow_html=True) 
    selected_menu = st.radio("메뉴 선택", ["🚀 QA 리스크 분석기", "📝 뭐 만들지", "🛅 생각중..."], label_visibility="collapsed")

if selected_menu == "🚀 QA 리스크 분석기":
    st.title("🚀 QA 리스크 분석기")

    with st.container(border=True):
        # 1. 사용자명 / 비밀번호
        r1_c1, r1_c2 = st.columns(2)
        user_name = r1_c1.text_input("👤 사용자명", placeholder="홍길동")
        doc_password = r1_c2.text_input("🔒 비밀번호 (결과물 보호용)", type="password", placeholder="다운로드 시 필요합니다")

        # 2. AI 선택 / API Key
        r2_c1, r2_c2 = st.columns(2)
        ai_provider = r2_c1.selectbox("🤖 AI 선택", ["Gemini", "ChatGPT", "Claude"]) 
        api_key = r2_c2.text_input(f"{ai_provider} API Key", type="password")

        # 3. Token / 링크
        r3_c1, r3_c2 = st.columns(2)
        vcs_token = r3_c1.text_input("🔑 GitLab/GitHub Token", type="password", placeholder="비공개 저장소인 경우 필수")
        link = r3_c2.text_input("🔗 분석할 링크 (GitLab MR / GitHub PR / Commit)")

        # 4. 맞춤 프롬프트 / 실행 버튼
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
            st.success("✅ 분석이 완료되어 리스트에 추가되었습니다!")
            
            html_data = generate_html_report(result)
            excel_data = generate_tc_excel(result)
            
            record = {
                'id': len(st.session_state.history) + 1,
                'time': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), # 💡 날짜 포맷 yyyy-mm-dd hh:mm 수정
                'user': user_name,
                'password': doc_password,
                'api': f"{ai_provider} ({used_model})",
                'platform': parsed['platform'].capitalize(),
                'link': link,
                'html': html_data,
                'excel': excel_data
            }
            st.session_state.history.insert(0, record)
            st.session_state.current_page = 1
        else:
            st.error(f"분석 실패: {error}")

    st.divider()

    st.subheader("🗂️ 분석 결과 히스토리")
    
    # 💡 1. 사용자명 검색 기능 추가
    search_query = st.text_input("🔍 사용자명 검색", placeholder="검색할 사용자명을 입력하세요")
    st.markdown("<br>", unsafe_allow_html=True) # 💡 한 줄 띄우기

    if not st.session_state.history:
        st.info("실행된 분석 결과가 없습니다. 첫 분석을 시작해보세요!")
    else:
        # 검색 필터링 로직
        if search_query:
            filtered_history = [item for item in st.session_state.history if search_query.lower() in item['user'].lower()]
        else:
            filtered_history = st.session_state.history

        if not filtered_history:
            st.warning("검색 결과가 없습니다.")
        else:
            # 페이징 로직 (필터링된 데이터 기준)
            ITEMS_PER_PAGE = 5
            total_items = len(filtered_history)
            total_pages = math.ceil(total_items / ITEMS_PER_PAGE)
            
            if st.session_state.current_page > total_pages:
                st.session_state.current_page = max(1, total_pages)
                
            start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
            end_idx = start_idx + ITEMS_PER_PAGE
            current_items = filtered_history[start_idx:end_idx]

            # 💡 리스트 헤더 (가운데 정렬 + 명칭 변경)
            h1, h2, h3, h4, h5, h6, h7, h8 = st.columns([1, 1.2, 1, 1, 2, 1.5, 2, 1])
            h1.markdown("<div style='text-align: center;'><b>사용자</b></div>", unsafe_allow_html=True)
            h2.markdown("<div style='text-align: center;'><b>일시</b></div>", unsafe_allow_html=True)
            h3.markdown("<div style='text-align: center;'><b>API</b></div>", unsafe_allow_html=True)
            h4.markdown("<div style='text-align: center;'><b>저장소</b></div>", unsafe_allow_html=True)
            h5.markdown("<div style='text-align: center;'><b>분석한 링크</b></div>", unsafe_allow_html=True)
            h6.markdown("<div style='text-align: center;'><b>비밀번호</b></div>", unsafe_allow_html=True)
            h7.markdown("<div style='text-align: center;'><b>다운로드</b></div>", unsafe_allow_html=True)
            h8.markdown("<div style='text-align: center;'><b>삭제</b></div>", unsafe_allow_html=True)
            
            # 항목 출력 (가운데 정렬)
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
                        # 💡 아이콘 및 명칭 변경 반영
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
                            st.session_state.history = [x for x in st.session_state.history if x['id'] != item['id']]
                            st.rerun()
                    else:
                        st.button("🗑️ 삭제", key=f"del_dis_{item['id']}", disabled=True, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # 페이징 컨트롤 (하단)
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

elif selected_menu == "📝 기획서-코드 검증기":
    st.title("📝 기획서-코드 검증기")
    st.info("이 기능은 현재 개발 중입니다.")

elif selected_menu == "🛅 TC 자동 생성기":
    st.title("🛅 TC 자동 생성기")
    st.info("이 기능은 현재 개발 중입니다.")