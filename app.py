import streamlit as st
import requests
from google import genai
from urllib.parse import urlparse, quote
import time

# --- 1. 페이지 및 프롬프트 설정 ---
st.set_page_config(page_title="QA 리스크 분석기 (안정화)", page_icon="🛡️", layout="wide")

DEFAULT_PROMPT = """너는 QA 전문가야. 아래 코드 변경점을 분석하여 QA 리스크 보고서를 작성해줘.
1. 🔑 핵심 요약 / 2. 🚨 사이드 이펙트 / 3. ⭐ 테스트 포인트 / 4. 🛅 TC
{commits} / {diffs}"""

# --- 2. 데이터 슬림화 (무료 등급 429 에러 방어) ---
def slim_filter(diff_list):
    ALLOWED_EXT = ('.py', '.js', '.ts', '.java', '.kt', '.swift', '.vue', '.html')
    filtered = []
    curr_len = 0
    for d in diff_list:
        path = d.get('new_path', 'unknown')
        if not any(path.endswith(ext) for ext in ALLOWED_EXT): continue
        # 파일당 800자 제한 (매우 타이트하게)
        content = d.get('diff', '')[:800]
        chunk = f"📄 {path}\n{content}\n"
        if curr_len + len(chunk) > 6000: break 
        filtered.append(chunk)
        curr_len += len(chunk)
    return "\n".join(filtered) if filtered else "핵심 로직 변경 없음"

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

# --- 4. 사이드바 API 설정 ---
with st.sidebar:
    st.title("🔐 gittest API 설정")
    # 공백 포함 실수를 방지하기 위해 .strip() 사용
    g_key = st.text_input("Gemini API Key", type="password").strip()
    gl_token = st.text_input("GitLab Token", type="password").strip()
    st.divider()
    
    # 모델 선택 로직 (목록 로드 실패 시에도 수동 선택 가능하게)
    safe_models = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-lite"]
    selected_model = safe_models[0]

    if g_key:
        try:
            client = genai.Client(api_key=g_key)
            api_models = [m.name.replace("models/", "") for m in client.models.list() if "generateContent" in m.supported_methods]
            if api_models:
                selected_model = st.selectbox("사용 가능한 모델 선택", api_models)
                st.success("✅ gittest 프로젝트 모델 로드 완료")
            else:
                selected_model = st.selectbox("모델 수동 선택 (목록 비어있음)", safe_models)
        except Exception as e:
            st.warning("⚠️ 모델 목록 로드 실패 (수동 선택 모드)")
            selected_model = st.selectbox("호환 모델 수동 선택", safe_models)
            with st.expander("디버깅 정보"):
                st.code(str(e))

# --- 5. 분석 실행 ---
tab1, tab2 = st.tabs(["🏠 소개", "🔍 분석 실행"])

with tab2:
    link = st.text_input("GitLab 링크 입력")
    if st.button("🚀 리스크 분석 시작"):
        if not (g_key and gl_token and link):
            st.error("모든 정보를 입력해주세요.")
        else:
            parsed = _parse_link(link)
            if not parsed:
                st.error("GitLab 링크 형식이 올바르지 않습니다.")
            else:
                with st.spinner(f"AI({selected_model})가 코드를 읽고 있습니다..."):
                    c_t, d_t = fetch_data(parsed, gl_token)
                    if not c_t:
                        st.error("GitLab 데이터를 불러오지 못했습니다. 토큰을 확인하세요.")
                    else:
                        try:
                            client = genai.Client(api_key=g_key)
                            final_p = DEFAULT_PROMPT.format(commits=c_t, diffs=d_t)
                            response = client.models.generate_content(
                                model=selected_model,
                                contents=final_p
                            )
                            st.success("✅ 분석 완료!")
                            st.markdown("---")
                            st.markdown(response.text)
                        except Exception as e:
                            if "429" in str(e):
                                st.error("⚠️ 쿼터 초과! 1분만 기다려주세요.")
                            else:
                                st.error(f"분석 중 오류 발생: {e}")
