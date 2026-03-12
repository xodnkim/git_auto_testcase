import streamlit as st
import requests
from google import genai
from urllib.parse import urlparse, quote
import time

# --- 1. 페이지 및 프롬프트 설정 ---
st.set_page_config(page_title="QA 분석기 (최종본)", page_icon="🛡️", layout="wide")

DEFAULT_PROMPT = """너는 QA 전문가야. 아래 코드 변경점을 분석하여 QA 리스크 보고서를 작성해줘.
1. 🔑 핵심 요약 / 2. 🚨 사이드 이펙트 / 3. ⭐ 테스트 포인트 / 4. 🛅 TC
{commits} / {diffs}"""

# --- 2. 데이터 최적화 (429 에러 방지) ---
def slim_filter(diff_list):
    ALLOWED_EXT = ('.py', '.js', '.ts', '.java', '.kt', '.swift', '.vue', '.html')
    filtered = []
    curr_len = 0
    for d in diff_list:
        path = d.get('new_path', 'unknown')
        if not any(path.endswith(ext) for ext in ALLOWED_EXT): continue
        content = d.get('diff', '')[:800]
        chunk = f"📄 {path}\n{content}\n"
        if curr_len + len(chunk) > 5000: break # 무료 티어 안전선
        filtered.append(chunk)
        curr_len += len(chunk)
    return "\n".join(filtered) if filtered else "소스 코드 변경 없음"

# --- 3. GitLab 데이터 수집 ---
def _parse_link(link):
    try:
        parsed = urlparse(link)
        if "/-/" not in parsed.path: return None
        path, tail = parsed.path.split("/-/", 1)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if "commit/" in tail:
            return {"path": path.strip("/"), "type": "commit", "id": tail.split("/")[-1], "base": base}
        if "merge_requests/" in tail:
            parts = tail.split("/")
            return {"path": path.strip("/"), "type": "mr", "id": parts[parts.index("merge_requests")+1], "base": base}
    except: return None

def fetch_data(parsed, token):
    headers = {"PRIVATE-TOKEN": token}
    enc_path = quote(parsed["path"], safe="")
    base = parsed["base"]
    try:
        if parsed["type"] == "mr":
            c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/commits", headers=headers, timeout=10).json()
            d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/diffs", headers=headers, timeout=10).json()
            c_t = "\n".join([c['title'] for c in c_res])
            d_t = slim_filter(d_res)
        else:
            c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}", headers=headers, timeout=10).json()
            d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}/diff", headers=headers, timeout=10).json()
            c_t = c_res['title']
            d_text = slim_filter(d_res)
        return c_t, d_text
    except: return None, None

# --- 4. 분석 실행 및 모델 폴백(Fallback) 로직 ---
with st.sidebar:
    st.title("🔐 gittest 설정")
    g_key = st.text_input("Gemini API Key", type="password").strip()
    gl_token = st.text_input("GitLab Token", type="password").strip()

st.title("🛡️ QA 리스크 헷징 자동화")
link = st.text_input("GitLab 링크 입력 (MR/Commit)")

if st.button("🚀 분석 시작"):
    if not (g_key and gl_token and link):
        st.error("모든 정보를 입력해주세요.")
    else:
        parsed = _parse_link(link)
        if not parsed:
            st.error("올바른 링크 형식이 아닙니다.")
        else:
            with st.spinner("AI가 분석을 시도하고 있습니다..."):
                c_t, d_t = fetch_data(parsed, gl_token)
                if not c_t:
                    st.error("데이터 로드 실패")
                else:
                    client = genai.Client(api_key=g_key)
                    # 시도할 모델 순서 (2026년 기준)
                    candidate_models = ['gemini-1.5-flash-latest', 'gemini-3-flash', 'gemini-1.5-flash']
                    
                    response = None
                    error_msg = ""
                    
                    for model_name in candidate_models:
                        try:
                            response = client.models.generate_content(
                                model=model_name,
                                contents=DEFAULT_PROMPT.format(commits=c_t, diffs=d_t)
                            )
                            if response: break
                        except Exception as e:
                            error_msg = str(e)
                            continue
                    
                    if response:
                        st.success(f"✅ 분석 완료! (사용 모델: {model_name})")
                        st.markdown("---")
                        st.markdown(response.text)
                    else:
                        st.error(f"모든 모델 시도 실패. 상세 에러: {error_msg}")
