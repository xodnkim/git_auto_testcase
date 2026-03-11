import streamlit as st
import requests
from google import genai
from urllib.parse import urlparse, quote
import time

# --- 1. 설정 및 프롬프트 정의 ---
DEFAULT_PROMPT = """너는 대한민국 1인 방송 플랫폼 'SOOP'의 '모바일 앱 QA팀 리스크헷징 파트' 직원이야.
모바일 앱 QA 전문가로서 아래 데이터를 분석하여 QA 리스크 보고서를 작성해줘.

### [필수 답변 양식] ###
1. 🚩 **핵심 변경 요약**: (1줄 요약)
2. ⚠️ **사이드 이펙트 분석**:
   - 영향 범위: (모듈/화면 등)
   - 리스크 내용: (발생 가능한 결함 시나리오)
3. 🔍 **QA 중점 테스트 포인트**:
   - [우선순위] [대상] - [검증 내용]

### [데이터] ###
커밋 메시지: {commits}
코드 변경점: {diffs}"""

st.set_page_config(page_title="QA 리스크 분석기 PRO", page_icon="🤖", layout="wide")

# --- 2. 데이터 필터링 및 전처리 로직 (토큰 절약용) ---

def clean_and_filter_diffs(diff_list):
    """분석에 불필요한 파일을 걸러내고 긴 텍스트를 최적화하여 토큰을 절약합니다."""
    # 분석에서 제외할 확장자
    EXCLUDED_EXTENSIONS = ('.lock', '.json', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.min.js')
    
    filtered_texts = []
    for d in diff_list:
        file_path = d.get('new_path', 'unknown_file')
        
        # 1. 특정 확장자 제외
        if any(file_path.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
            continue
            
        # 2. 파일당 너무 긴 Diff는 상단 3,000자만 추출 (가장 핵심적인 로직 포함 가능성 높음)
        diff_content = d.get('diff', '')
        if len(diff_content) > 3000:
            diff_content = diff_content[:3000] + "\n...(파일이 너무 길어 하단 중략)..."
            
        filtered_texts.append(f"📄 파일명: {file_path}\n{diff_content}")
    
    # 전체 텍스트 합산 및 최종 길이 제한 (무료 티어 쿼터 방어)
    final_text = "\n\n".join(filtered_texts)
    if len(final_text) > 25000:
        final_text = final_text[:25000] + "\n\n...(전체 분석 데이터가 너무 많아 일부 중략됨)..."
        
    return final_text if final_text else "분석할 의미 있는 코드 변경점이 없습니다."

# --- 3. GitLab API 도우미 함수 ---

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

def fetch_data(parsed, token):
    project_encoded = quote(parsed["project_path"], safe="")
    base = parsed["base_url"]
    
    if parsed["type"] == "mr":
        c_url = f"{base}/api/v4/projects/{project_encoded}/merge_requests/{parsed['id']}/commits"
        d_url = f"{base}/api/v4/projects/{project_encoded}/merge_requests/{parsed['id']}/diffs"
        commits = _gitlab_get(c_url, token)
        diffs = _gitlab_get(d_url, token)
        if not commits or not diffs: return None, None
        c_text = "\n".join([f"• {c['title']}" for c in commits])
        d_text = clean_and_filter_diffs(diffs) # 필터링 적용
    else:
        c_url = f"{base}/api/v4/projects/{project_encoded}/repository/commits/{parsed['id']}"
        d_url = f"{base}/api/v4/projects/{project_encoded}/repository/commits/{parsed['id']}/diff"
        commit = _gitlab_get(c_url, token)
        diffs = _gitlab_get(d_url, token)
        if not commit or not diffs: return None, None
        c_text = f"• {commit['title']}"
        d_text = clean_and_filter_diffs(diffs) # 필터링 적용
    
    return c_text, d_text

# --- 4. 메인 화면 및 사이드바 ---

with st.sidebar:
    st.title("🔐 개인 API 설정")
    gemini_key = st.text_input("Gemini API Key", type="password")
    gitlab_token = st.text_input("GitLab Token", type="password")
    st.divider()
    st.markdown("### 🔍 도움말\n1분당 분석 가능 횟수가 제한될 수 있습니다. 429 에러 발생 시 1분만 기다려 주세요.")

tab1, tab2 = st.tabs(["🏠 프로젝트 소개", "🔍 리스크 분석 실행"])

with tab1:
    st.title("🤖 QA 리스크 헷징 시스템")
    st.markdown("""
    본 도구는 GitLab 변경 사항을 Gemini AI가 분석하여 **QA 리스크 리포트**를 생성합니다.
    - **효율화**: 대규모 Diff 데이터 중 핵심 리스크 파일만 선별 분석
    - **커스텀**: 사용자가 직접 AI의 분석 기준(프롬프트) 수정 가능
    """)

with tab2:
    st.header("🔍 실시간 분석")
    link = st.text_input("GitLab MR 또는 Commit 링크 입력")
    
    # 프롬프트 커스텀 (도움말 포함)
    with st.expander("📝 분석 프롬프트 수정 (선택사항)"):
        user_prompt = st.text_area(
            "AI 지시문", value=DEFAULT_PROMPT, height=300,
            help=f"AI의 분석 기준을 직접 바꿀 수 있습니다.\n\n[예시]\n{DEFAULT_PROMPT}"
        )

    if st.button("분석 시작"):
        if not (gemini_key and gitlab_token and link):
            st.error("API 키, 토큰, 링크를 모두 입력해주세요.")
        else:
            parsed = _parse_gitlab_link(link)
            if not parsed:
                st.error("올바른 GitLab 링크 형식이 아닙니다.")
            else:
                with st.spinner("GitLab 데이터를 수집하여 AI가 분석 중입니다..."):
                    c_text, d_text = fetch_data(parsed, gitlab_token)
                    
                    if not c_text:
                        st.error("GitLab 데이터를 가져오지 못했습니다. 토큰이나 링크를 확인하세요.")
                    else:
                        # --- Gemini 분석 및 에러 핸들링 ---
                        try:
                            client = genai.Client(api_key=gemini_key)
                            final_prompt = user_prompt.format(commits=c_text, diffs=d_text)
                            
                            response = client.models.generate_content(
                                model='gemini-2.0-flash',
                                contents=final_prompt
                            )
                            
                            st.success("분석 완료!")
                            st.markdown("---")
                            st.markdown(response.text)
                            st.download_button("결과 리포트 다운로드", response.text, "QA_Risk_Report.txt")

                        except Exception as e:
                            # 429 RESOURCE_EXHAUSTED 에러 대응
                            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                                st.error("⚠️ AI 사용량이 일시적으로 초과되었습니다.")
                                st.warning("구글 API 무료 티어 정책으로 인해 1분에 약 1회만 대규모 분석이 가능합니다. 1분만 기다렸다가 다시 시도해 주세요.")
                                st.info("💡 팁: 더 정확한 분석을 원하시면 [Google AI Studio](https://aistudio.google.com/app/plan_and_billing)에서 유료 결제 수단을 등록하여 쿼터를 늘릴 수 있습니다.")
                            else:
                                st.error(f"분석 중 오류 발생: {e}")
