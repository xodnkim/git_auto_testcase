import streamlit as st
import requests
from google import genai
from urllib.parse import urlparse, quote
import time

# --- 1. 프롬프트 기본값 설정 ---
DEFAULT_PROMPT = """너는 OOO 플랫폼 'xxx'의 'QA팀' 직원이야.
(웹 or 모바일) QA 전문가로서 아래 데이터를 분석하여 QA 리스크 보고서를 작성해줘.

### [필수 답변 양식] ###
1. 🔑 **핵심 변경 요약**: (수정된 기능의 핵심을 1줄로 요약)
2. 🚨 **사이드 이펙트 분석**:
   - 영향 범위: (예: 로그인, 채팅창, UI 레이아웃 등)
   - 리스크 내용: (코드 변경으로 인해 발생 가능한 구체적인 결함 시나리오)
3. ⭐ **QA 중점 테스트 포인트 (Atomic Test Cases)**:
   - [우선순위] [테스트 대상] - [검증 내용]
4. 🛅 **테스트 케이스 ;
   - [경로] [사전조건] [동작] [예상결과]

### [분석 지침] ###
- 반드시 위의 '필수 답변 양식'의 헤더와 구조를 유지할 것.
- OOO 서비스의 특성(실시간성, 멀티 플랫폼, 플레이어 제스처 등)을 고려할 것.

### [데이터] ###
커밋 메시지: {commits}
코드 변경점: {diffs}"""

# --- 2. 페이지 설정 ---
st.set_page_config(page_title="QA 리스크 분석 사이트 ", page_icon="💻", layout="wide")

# --- 3. 도우미 함수들 ---

def _parse_gitlab_link(link):
    try:
        parsed = urlparse(link)
        if "/-/" not in parsed.path: return None
        project_path, tail = parsed.path.split("/-/", 1)
        project_path = project_path.strip("/")
        tail = tail.strip("/")
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        if tail.startswith("commit/"):
            sha = tail.split("/", 1)[1].split("/")[0]
            return {"project_path": project_path, "type": "commit", "id": sha, "base_url": base_url}
        if tail.startswith("merge_requests/"):
            iid = tail.split("/", 1)[1].split("/")[0]
            return {"project_path": project_path, "type": "mr", "id": iid, "base_url": base_url}
    except: return None
    return None

def _gitlab_get(url, token):
    headers = {"PRIVATE-TOKEN": token}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        return res.json() if res.status_code == 200 else None
    except: return None

def fetch_gitlab_data(parsed, token):
    project_encoded = quote(parsed["project_path"], safe="")
    base = parsed["base_url"]
    if parsed["type"] == "mr":
        c_url = f"{base}/api/v4/projects/{project_encoded}/merge_requests/{parsed['id']}/commits"
        d_url = f"{base}/api/v4/projects/{project_encoded}/merge_requests/{parsed['id']}/diffs"
        commits = _gitlab_get(c_url, token)
        diffs = _gitlab_get(d_url, token)
        if not commits or not diffs: return None, None
        c_text = "\n".join([f"• {c['title']}" for c in commits])
        d_text = "\n".join([f"📄 {d['new_path']}\n{d['diff']}" for d in diffs])
    else:
        c_url = f"{base}/api/v4/projects/{project_encoded}/repository/commits/{parsed['id']}"
        d_url = f"{base}/api/v4/projects/{project_encoded}/repository/commits/{parsed['id']}/diff"
        commit = _gitlab_get(c_url, token)
        diffs = _gitlab_get(d_url, token)
        if not commit or not diffs: return None, None
        c_text = f"• {commit['title']}"
        d_text = "\n".join([f"📄 {d['new_path']}\n{d['diff']}" for d in diffs])
    return c_text, d_text

# --- 4. 사이드바 UI ---
with st.sidebar:
    st.title("🔐 API 키 설정")
    st.caption("외부 사용자를 위한 개인 키 입력란입니다.")
    gemini_key = st.text_input("Gemini API Key", type="password")
    gitlab_token = st.text_input("GitLab Personal Token", type="password")
    st.divider()
    st.markdown("### 🛠️ 사용 스택\n- Python / Streamlit\n- Google Gemini 2.0 Flash\n- GitLab REST API")

# --- 5. 메인 UI ---
tab1, tab2 = st.tabs(["🏠 프로젝트 소개", "🔍 리스크 분석 실행"])

# [탭 1: 소개]
with tab1:
    st.title("🚀 QA Risk Analysis System")
    st.markdown("""
    ### 💡 프로젝트 개요
    이 시스템은 개발 과정에서 발생하는 **코드 변경점을 실시간으로 분석하여 QA 리스크를 도출**합니다. 
    
    - **효율성**: 수작업으로 진행되던 Diff 분석 시간을 획기적으로 단축
    - **정확성**: AI를 통한 사이드 이펙트 교차 검증
    - **확장성**: 사용자 정의 프롬프트를 통한 다양한 분석 모드 지원
    """)
    st.info("오른쪽 '리스크 분석 실행' 탭에서 실제 기능을 체험해 볼 수 있습니다.")

# [탭 2: 분석기]
with tab2:
    st.header("🔍 실시간 데이터 분석")
    
    # 분석 모드 선택
    mode = st.radio("실행 모드 선택", ["데모 데이터 체험", "실제 GitLab 연동"], horizontal=True)
    
    # 1. 프롬프트 커스텀 영역 (도움말 아이콘 포함)
    with st.expander("📝 AI 분석 프롬프트 설정", expanded=False):
        user_prompt = st.text_area(
            "AI 지시문 작성",
            value=DEFAULT_PROMPT,
            height=350,
            help=f"이곳에서 AI의 페르소나와 답변 형식을 자유롭게 수정할 수 있습니다.\n\n[기본 프롬프트 예시]\n{DEFAULT_PROMPT}"
        )
        st.caption("💡 `{commits}`와 `{diffs}`는 실제 데이터로 자동 치환되는 예약어입니다.")

    # 2. 링크 입력 및 분석 실행
    if mode == "실제 GitLab 연동":
        link = st.text_input("GitLab MR 또는 Commit 링크 입력")
        if st.button("분석 시작"):
            if not gemini_key or not gitlab_token:
                st.error("사이드바에 API 키와 토큰을 입력해주세요.")
            elif not link:
                st.warning("분석할 링크를 입력해주세요.")
            else:
                parsed = _parse_gitlab_link(link)
                if not parsed:
                    st.error("올바른 GitLab 링크 형식이 아닙니다.")
                else:
                    with st.spinner("GitLab 데이터를 수집하고 AI가 분석 중입니다..."):
                        c_text, d_text = fetch_gitlab_data(parsed, gitlab_token)
                        if not c_text:
                            st.error("데이터를 가져오지 못했습니다. 링크나 토큰 권한을 확인하세요.")
                        else:
                            try:
                                client = genai.Client(api_key=gemini_key)
                                final_prompt = user_prompt.replace("{commits}", c_text).replace("{diffs}", d_text)
                                response = client.models.generate_content(model='Gemini 2.5 Flash', contents=final_prompt)
                                
                                st.success("분석 완료!")
                                st.markdown("---")
                                st.markdown(response.text)
                                st.download_button("리포트 다운로드", response.text, f"QA_Report_{parsed['id']}.txt")
                            except Exception as e:
                                st.error(f"AI 분석 중 오류 발생: {e}")

    else: # 데모 데이터 모드
        if st.button("데모 분석 시작"):
            with st.spinner("데모 분석 중..."):
                time.sleep(1.5)
                st.success("✅ [데모] 분석 결과입니다.")
                st.markdown("""
                ### 🚩 **핵심 변경 요약**:
                로그인 화면의 레이아웃 구조 변경 및 SNS 로그인 버튼 추가.

                ### ⚠️ **사이드 이펙트 분석**:
                - **영향 범위**: 로그인 페이지 UI, 카카오/네이버 SDK 연동부.
                - **리스크 내용**: 저사양 기기에서 버튼 겹침 현상 발생 가능성 및 SDK 초기화 실패 시 앱 종료 리스크.

                ### 🔍 **QA 중점 테스트 포인트**:
                - [P0] 로그인 - 카카오 로그인 클릭 시 인증 창 정상 호출 여부
                - [P1] UI - 다크모드 환경에서 신규 버튼 텍스트 가독성 확인
                """)




