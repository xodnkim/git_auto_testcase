import streamlit as st
import requests
from google import genai
from urllib.parse import urlparse, quote
import time

# --- 1. 프롬프트 및 페이지 설정 ---
DEFAULT_PROMPT = """너는 QA 전문가야. 아래 코드 변경점을 분석하여 QA 리스크 보고서를 작성해줘.
1. 🔑 핵심 요약 / 2. 🚨 사이드 이펙트 / 3. ⭐ 테스트 포인트 / 4. 🛅 TC
{commits} / {diffs}"""

st.set_page_config(page_title="QA 분석기: 모델 자동감지", page_icon="🛡️", layout="wide")

# --- 2. 데이터 슬림화 필터 (429 에러 방어) ---
def slim_filter(diff_list):
    ALLOWED_EXT = ('.py', '.js', '.ts', '.java', '.kt', '.swift', '.vue')
    filtered = []
    curr_len = 0
    for d in diff_list:
        path = d.get('new_path', 'unknown')
        if not any(path.endswith(ext) for ext in ALLOWED_EXT): continue
        content = d.get('diff', '')[:1000]
        chunk = f"📄 {path}\n{content}\n"
        if curr_len + len(chunk) > 8000: break # 무료 티어 안전선
        filtered.append(chunk)
        curr_len += len(chunk)
    return "\n".join(filtered) if filtered else "핵심 로직 변경 없음"

# --- 3. GitLab 데이터 수집 함수 ---
def _parse_link(link):
    try:
        parsed = urlparse(link)
        if "/-/" not in parsed.path: return None
        path, tail = parsed.path.split("/-/", 1)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if "commit/" in tail:
            return {"path": path.strip("/"), "type": "commit", "id": tail.split("/")[-1], "base": base}
        if "merge_requests/" in tail:
            return {"path": path.strip("/"), "type": "mr", "id": tail.split("/")[-2], "base": base}
    except: return None

def fetch_data(parsed, token):
    headers = {"PRIVATE-TOKEN": token}
    enc_path = quote(parsed["path"], safe="")
    base = parsed["base"]
    try:
        if parsed["type"] == "mr":
            c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/commits", headers=headers).json()
            d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/diffs", headers=headers).json()
            c_text = "\n".join([c['title'] for c in c_res])
            d_text = slim_filter(d_res)
        else:
            c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}", headers=headers).json()
            d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}/diff", headers=headers).json()
            c_text = c_res['title']
            d_text = slim_filter(d_res)
        return c_text, d_text
    except: return None, None

# --- 4. 메인 UI 및 모델 감지 로직 ---
with st.sidebar:
    st.title("🔐 API 설정")
    g_key = st.text_input("Gemini API Key", type="password")
    gl_token = st.text_input("GitLab Token", type="password")
    st.divider()
    
    # [핵심] 내 키가 쓸 수 있는 모델 목록 가져오기
    selected_model = "gemini-1.5-flash" # 기본값
    if g_key:
        try:
            client = genai.Client(api_key=g_key)
            models = [m.name.replace("models/", "") for m in client.models.list() if "generateContent" in m.supported_methods]
            selected_model = st.selectbox("사용 가능한 모델 선택", models, index=0)
            st.success("✅ 모델 목록 로드 완료")
        except:
            st.error("❌ 모델 목록을 불러오지 못했습니다. 키를 확인하세요.")

# --- 5. 분석 실행 레이아웃 ---
tab1, tab2 = st.tabs(["🏠 소개", "🔍 분석"])

with tab2:
    link = st.text_input("GitLab 링크 (MR/Commit)")
    if st.button("🚀 리스크 분석 시작"):
        if not (g_key and gl_token and link):
            st.error("모든 정보를 입력해주세요.")
        else:
            parsed = _parse_link(link)
            if not parsed:
                st.error("링크 형식이 잘못되었습니다.")
            else:
                with st.spinner(f"AI({selected_model})가 분석 중..."):
                    c_t, d_t = fetch_data(parsed, gl_token)
                    if not c_t:
                        st.error("GitLab 데이터 로드 실패")
                    else:
                        try:
                            client = genai.Client(api_key=g_key)
                            response = client.models.generate_content(
                                model=selected_model,
                                contents=DEFAULT_PROMPT.format(commits=c_t, diffs=d_t)
                            )
                            st.success("분석 완료!")
                            st.markdown(response.text)
                        except Exception as e:
                            st.error(f"분석 오류: {e}")
