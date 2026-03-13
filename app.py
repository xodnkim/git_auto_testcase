import streamlit as st
import requests
from google import genai
# OpenAI와 Anthropic은 필요 시 설치(pip install openai anthropic) 후 사용 가능합니다.
# 현재는 구조를 잡아드리기 위해 placeholder 형태를 포함했습니다.
from urllib.parse import urlparse, quote

# --- 1. 페이지 설정 및 프롬프트 ---
st.set_page_config(page_title="QA 리스크 분석기 PRO", page_icon="🛡️", layout="wide")

DEFAULT_PROMPT = """너는 소프트웨어 QA 전문가야. 아래 변경사항을 분석해서 보고서를 작성해줘.
1. 핵심 요약 / 2. 사이드 이펙트 / 3. 테스트 포인트 / 4. 추천 TC
---
커밋: {commits}
코드: {diffs}"""

# --- 2. 유틸리티 함수 (GitLab/필터) ---
def slim_filter(diff_list):
    ALLOWED_EXT = ('.py', '.js', '.ts', '.java', '.kt', '.swift', '.vue', '.html')
    filtered = []
    curr_len = 0
    for d in diff_list:
        path = d.get("new_path", "unknown")
        if not any(path.endswith(ext) for ext in ALLOWED_EXT): continue
        diff_text = d.get("diff", "")[:800]
        chunk = f"\n📄 {path}\n{diff_text}\n"
        if curr_len + len(chunk) > 5000: break
        filtered.append(chunk)
        curr_len += len(chunk)
    return "\n".join(filtered) if filtered else "소스 코드 변경 없음"

def parse_gitlab_link(link):
    try:
        parsed = urlparse(link)
        if "/-/" not in parsed.path: return None
        path, tail = parsed.path.split("/-/", 1)
        base = f"{parsed.scheme}://{parsed.netloc}"
        if "commit/" in tail:
            return {"path": path.strip("/"), "type": "commit", "id": tail.split("/")[-1], "base": base}
        if "merge_requests/" in tail:
            parts = tail.split("/")
            return {"path": path.strip("/"), "type": "mr", "id": parts[parts.index("merge_requests") + 1], "base": base}
    except: return None

# --- 3. AI 모델 로드 함수 (분기 처리) ---
def get_ai_models(provider, api_key):
    if not api_key: return []
    try:
        if provider == "Gemini":
            client = genai.Client(api_key=api_key)
            return [m.name.replace("models/", "") for m in client.models.list() if "generateContent" in m.supported_methods]
        elif provider == "ChatGPT":
            # OpenAI 로직 (예시)
            return ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
        elif provider == "Claude":
            # Anthropic 로직 (예시)
            return ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"]
    except Exception as e:
        st.error(f"{provider} 모델 로드 실패: {e}")
        return []

# --- 4. 메인 UI (LNB - 프로젝트 관리) ---
with st.sidebar:
    st.title("📁 프로젝트 목록")
    st.button("➕ 새 프로젝트 추가")
    st.divider()
    st.write("1. gittest 프로젝트")
    st.write("2. 상용 서비스 분석 (준비중)")

# --- 5. 메인 UI (본문 - 설정 및 분석) ---
st.title("🛡️ GitLab QA 리스크 분석기")

# [A] AI 설정 섹션
with st.container(border=True):
    st.subheader("⚙️ AI 모델 설정")
    col1, col2 = st.columns([1, 3])
    
    with col1:
        ai_provider = st.radio("AI 엔진 선택", ["Gemini", "ChatGPT", "Claude"], horizontal=False)
    
    with col2:
        api_key = st.text_input(f"{ai_provider} API Key 입력", type="password")
        gitlab_token = st.text_input("GitLab Token 입력", type="password")
        
        # 모델 목록 동적 가져오기
        available_models = get_ai_models(ai_provider, api_key)
        selected_model = st.selectbox("🎯 상세 모델 선택", available_models if available_models else ["키를 입력해주세요"])

# [B] 분석 실행 섹션
st.divider()
link = st.text_input("🔗 GitLab MR 또는 Commit 링크")

if st.button("🚀 분석 시작"):
    if not (api_key and gitlab_token and link):
        st.error("모든 설정값을 입력해주세요.")
    else:
        parsed = parse_gitlab_link(link)
        if not parsed:
            st.error("GitLab 링크 형식이 올바르지 않습니다.")
        else:
            with st.spinner(f"{ai_provider}가 데이터를 가져와 분석 중입니다..."):
                # GitLab 데이터 패치 (기존 함수 재사용)
                headers = {"PRIVATE-TOKEN": gitlab_token}
                enc_path = quote(parsed["path"], safe="")
                base = parsed["base"]
                
                try:
                    if parsed["type"] == "mr":
                        c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/commits", headers=headers).json()
                        d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/diffs", headers=headers).json()
                        c_text = "\n".join([c["title"] for c in c_res])
                        d_text = slim_filter(d_res)
                    else:
                        c_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}", headers=headers).json()
                        d_res = requests.get(f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}/diff", headers=headers).json()
                        c_text = c_res.get("title", "")
                        d_text = slim_filter(d_res)
                    
                    # AI 분석 실행 (분기 처리)
                    prompt = DEFAULT_PROMPT.format(commits=c_text, diffs=d_text)
                    
                    if ai_provider == "Gemini":
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(model=selected_model, contents=prompt)
                        result_text = response.text
                    else:
                        result_text = f"현재 {ai_provider} 연동 로직은 라이브러리 추가 설정이 필요합니다. (구조는 완성됨)"
                    
                    st.success(f"✅ 분석 완료 (사용 모델: {selected_model})")
                    st.markdown("---")
                    st.markdown(result_text)
                    
                except Exception as e:
                    st.error(f"실행 중 오류 발생: {e}")
