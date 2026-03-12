import streamlit as st
import requests
from google import genai
from urllib.parse import urlparse, quote

# -----------------------------
# 1. 페이지 설정
# -----------------------------
st.set_page_config(page_title="QA 리스크 분석기", page_icon="🛡️", layout="wide")

DEFAULT_PROMPT = """
너는 소프트웨어 QA 전문가다.

아래 코드 변경사항을 분석하고 QA 리스크 보고서를 작성해라.

[출력 형식]

1️⃣ 핵심 변경 요약

2️⃣ 예상 사이드 이펙트

3️⃣ 중요 테스트 포인트

4️⃣ 추천 테스트 케이스

---

커밋 메시지:
{commits}

코드 변경:
{diffs}
"""

# -----------------------------
# 2. Diff 필터 (토큰 절약)
# -----------------------------
def slim_filter(diff_list):

    ALLOWED_EXT = ('.py', '.js', '.ts', '.java', '.kt', '.swift', '.vue', '.html')

    filtered = []
    curr_len = 0

    for d in diff_list:

        path = d.get("new_path", "unknown")

        if not any(path.endswith(ext) for ext in ALLOWED_EXT):
            continue

        diff_text = d.get("diff", "")[:800]

        chunk = f"\n📄 {path}\n{diff_text}\n"

        if curr_len + len(chunk) > 5000:
            break

        filtered.append(chunk)
        curr_len += len(chunk)

    if not filtered:
        return "소스 코드 변경 없음"

    return "\n".join(filtered)


# -----------------------------
# 3. GitLab 링크 파싱
# -----------------------------
def parse_gitlab_link(link):

    try:

        parsed = urlparse(link)

        if "/-/" not in parsed.path:
            return None

        path, tail = parsed.path.split("/-/", 1)

        base = f"{parsed.scheme}://{parsed.netloc}"

        if "commit/" in tail:

            return {
                "path": path.strip("/"),
                "type": "commit",
                "id": tail.split("/")[-1],
                "base": base
            }

        if "merge_requests/" in tail:

            parts = tail.split("/")

            return {
                "path": path.strip("/"),
                "type": "mr",
                "id": parts[parts.index("merge_requests") + 1],
                "base": base
            }

    except:
        return None


# -----------------------------
# 4. GitLab 데이터 가져오기
# -----------------------------
def fetch_gitlab_data(parsed, token):

    headers = {"PRIVATE-TOKEN": token}

    enc_path = quote(parsed["path"], safe="")

    base = parsed["base"]

    try:

        if parsed["type"] == "mr":

            commit_res = requests.get(
                f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/commits",
                headers=headers
            ).json()

            diff_res = requests.get(
                f"{base}/api/v4/projects/{enc_path}/merge_requests/{parsed['id']}/diffs",
                headers=headers
            ).json()

            commit_text = "\n".join([c["title"] for c in commit_res])

            diff_text = slim_filter(diff_res)

        else:

            commit_res = requests.get(
                f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}",
                headers=headers
            ).json()

            diff_res = requests.get(
                f"{base}/api/v4/projects/{enc_path}/repository/commits/{parsed['id']}/diff",
                headers=headers
            ).json()

            commit_text = commit_res.get("title", "")

            diff_text = slim_filter(diff_res)

        return commit_text, diff_text

    except Exception as e:

        st.error(f"GitLab API 오류: {e}")

        return None, None


# -----------------------------
# 5. Gemini 모델 조회
# -----------------------------
def get_available_models(client):

    try:

        models = client.models.list()

        model_names = [m.name.replace("models/", "") for m in models]

        return model_names

    except Exception as e:

        st.error(f"모델 조회 실패: {e}")

        return []


# -----------------------------
# 6. Gemini 분석
# -----------------------------
def analyze_with_gemini(api_key, commits, diffs):

    client = genai.Client(api_key=api_key)

    available_models = get_available_models(client)

    if not available_models:
        return None, "사용 가능한 모델 없음"

    # 우선순위 모델
    preferred_models = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite"
    ]

    prompt = DEFAULT_PROMPT.format(commits=commits, diffs=diffs)

    last_error = ""

    for model in preferred_models:

        if model not in available_models:
            continue

        try:

            response = client.models.generate_content(
                model=model,
                contents=[{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }]
            )

            if response and response.text:
                return response.text, model

        except Exception as e:

            last_error = str(e)

    return None, last_error


# -----------------------------
# UI
# -----------------------------
with st.sidebar:

    st.title("🔐 API 설정")

    gemini_key = st.text_input(
        "Gemini API Key",
        type="password"
    )

    gitlab_token = st.text_input(
        "GitLab Token",
        type="password"
    )

st.title("🛡️ GitLab QA 리스크 분석기")

link = st.text_input("GitLab MR 또는 Commit 링크")

if st.button("🚀 분석 시작"):

    if not gemini_key or not gitlab_token or not link:

        st.error("모든 값을 입력해주세요")

        st.stop()

    parsed = parse_gitlab_link(link)

    if not parsed:

        st.error("GitLab 링크 형식이 올바르지 않습니다")

        st.stop()

    with st.spinner("GitLab 데이터 가져오는 중..."):

        commits, diffs = fetch_gitlab_data(parsed, gitlab_token)

    if not commits:

        st.error("GitLab 데이터 가져오기 실패")

        st.stop()

    with st.spinner("AI 분석 중..."):

        result, model = analyze_with_gemini(gemini_key, commits, diffs)

    if result:

        st.success(f"분석 완료 (모델: {model})")

        st.markdown("---")

        st.markdown(result)

    else:

        st.error(f"모든 모델 실패: {model}")
