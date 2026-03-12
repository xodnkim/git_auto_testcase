import streamlit as st
import requests
from google import genai
from urllib.parse import urlparse, quote
import time

# --- 1. 프롬프트 및 설정 ---
DEFAULT_PROMPT = """너는 QA 전문가야. 아래 코드 변경점을 분석하여 QA 리스크 보고서를 작성해줘.

### [필수 답변 양식] ###
1. 🔑 **핵심 변경 요약**: (1줄 요약)
2. 🚨 **사이드 이펙트 분석**:
   - 영향 범위: (모듈/화면 등)
   - 리스크 내용: (발생 가능한 결함 시나리오)
3. ⭐ **QA 중점 테스트 포인트**:
   - [우선순위] [대상] - [검증 내용]
4. 🛅 **테스트 케이스**:
   - [경로] [사전조건] [동작] [예상결과]

### [데이터] ###
커밋 메시지: {commits}
코드 변경점: {diffs}"""

st.set_page_config(page_title="QA 리스크 분석기 PRO", page_icon="💻", layout="wide")

# --- 2. 초강력 데이터 필터링 (429 에러 방어의 핵심) ---

def slim_filter_diffs(diff_list):
    """분석에 불필요한 파일을 제거하고 텍스트를 최적화하여 토큰을 절약합니다."""
    # 분석 가치가 높은 소스 코드 확장자만 허용
    ALLOWED_EXTENSIONS = ('.py', '.js', '.ts', '.java', '.kt', '.swift', '.cpp', '.c', '.go', '.html', '.vue')
    
    filtered_texts = []
    current_total_len = 0
    MAX_TOTAL_CHARS = 15000  # 무료 티어 안전선을 위해 전체 1.5만자로 제한

    for d in diff_list:
        file_path = d.get('new_path', 'unknown')
        
        # 1. 소스 코드 파일이 아니면 무시 (이미지, 설정, 락파일 등 제거)
        if not any(file_path.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            continue
            
        # 2. 파일당 최대 1,500자만 추출 (핵심 로직 위주)
        diff_content = d.get('diff', '')[:1500]
        chunk = f"📄 파일: {file_path}\n{diff_content}\n"
        
        # 3. 전체 합계가 제한치를 넘으면 중단
        if current_total_len + len(chunk) > MAX_TOTAL_CHARS:
            filtered_texts.append("\n...(데이터가 너무 많아 하단 생략)...")
            break
            
        filtered_texts.append(chunk)
        current_total_len += len(chunk)
        
    return "\n".join(filtered_texts) if filtered_texts else "분석할 핵심 코드 변경점이 없습니다."

# --- 3. 도우미 함수들 ---

def _parse_gitlab_link(link):
    try:
        parsed = urlparse(link)
        if "/-/" not in parsed.path: return None
        project_path, tail = parsed.path.split("/-/", 1)
        project_path = project_path.strip("/")
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
        d_text = slim_filter_diffs(diffs) # 필터링 적용
    else:
        c_url = f"{base}/api/v4/projects/{project_encoded}/repository/commits/{parsed['id']}"
        d_url = f"{base}/api/v4/projects/{project_encoded}/repository/commits/{parsed['id']}/diff"
        commit = _gitlab_get(c_url, token)
        diffs = _gitlab_get(d_url, token)
        if not commit or not diffs: return None, None
        c_text = f"• {commit['title']}"
        d_text = slim_filter_diffs(diffs) # 필터링 적용
    
    return c_text, d_text

# --- 4. 메인 UI 및 사이드바 ---
with st.sidebar:
    st.title("🔐 API 키 설정")
    gemini_key = st.text_input("Gemini API Key", type="password")
    gitlab_token = st.text_input("GitLab Personal Token", type="password")
    st.divider()
    st.info("💡 429 에러 발생 시 약 1분간 대기 후 다시 시도해 주세요.")

tab1, tab2 = st.tabs(["🏠 프로젝트 소개", "🔍 리스크 분석 실행"])

with tab1:
    st.title("🚀 QA Risk Analysis System")
    st.markdown("""
    ### 💡 프로젝트 개요
    이 시스템은 코드 변경점을 AI가 분석하여 QA 리스크를 도출합니다.
    - **효율성**: 수작업 Diff 분석 시간 단축
    - **최적화**: 토큰 필터링을 통한 안정적 분석 지원
    """)

with tab2:
    st.header("🔍 실시간 데이터 분석")
    mode = st.radio("실행 모드 선택", ["데모 데이터 체험", "실제 GitLab 연동"], horizontal=True)
    
    with st.expander("📝 AI 분석 프롬프트 설정"):
        user_prompt = st.text_area("AI 지시문 작성", value=DEFAULT_PROMPT, height=350)

    if mode == "실제 GitLab 연동":
        link = st.text_input("GitLab MR 또는 Commit 링크 입력")
        if st.button("분석 시작"):
            if not (gemini_key and gitlab_token and link):
                st.error("모든 정보를 입력해 주세요.")
            else:
                parsed = _parse_gitlab_link(link)
                if not parsed:
                    st.error("올바른 GitLab 링크 형식이 아닙니다.")
                else:
                    with st.spinner("AI가 코드를 꼼꼼히 읽고 리스크를 분석 중입니다..."):
                        c_text, d_text = fetch_gitlab_data(parsed, gitlab_token)
                        if not c_text:
                            st.error("데이터를 가져오지 못했습니다.")
                        else:
                            try:
                                client = genai.Client(api_key=gemini_key)
                                # 2026년 기준 가장 안정적인 모델명 사용
                                 response = client.models.generate_content(
                                     model='gemini-1.5-flash', 
                                     contents=user_prompt.format(commits=c_text, diffs=d_text)
                                 )
                                st.success("분석 완료!")
                                st.markdown("---")
                                st.markdown(response.text)
                                st.download_button("리포트 다운로드", response.text, "QA_Report.txt")
                            except Exception as e:
                                if "429" in str(e):
                                    st.error("⚠️ AI 사용량이 초과되었습니다 (Free Tier).")
                                    st.warning("약 1분 후에 다시 시도해 주세요. 무료 API는 한 번에 처리할 수 있는 양에 제한이 있습니다.")
                                else:
                                    st.error(f"분석 중 오류 발생: {e}")
    else:
        if st.button("데모 분석 시작"):
            st.success("✅ 데모 모드입니다. (실제 요청 시 429 에러 방어 로직이 작동합니다.)")
            st.markdown("예시 결과: 로그인 UI 변경 시 사이드 이펙트 분석...")

