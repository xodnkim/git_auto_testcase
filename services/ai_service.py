# services/ai_service.py
from google import genai
from config.settings import DEFAULT_PROMPT

def get_ai_models(provider, api_key):
    """선택한 AI 제공자에 따라 사용 가능한 모델 목록을 반환합니다."""
    if not api_key: return []
    try:
        if provider == "Gemini":
            client = genai.Client(api_key=api_key)
            return [m.name.replace("models/", "") for m in client.models.list() if "generateContent" in m.supported_methods]
        elif provider == "ChatGPT":
            return ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"] # 추후 openai 라이브러리 연동
        elif provider == "Claude":
            return ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"] # 추후 anthropic 라이브러리 연동
    except Exception as e:
        return []

def analyze_code(provider, api_key, model_name, commits, diffs):
    """선택한 AI로 코드를 분석합니다."""
    prompt = DEFAULT_PROMPT.format(commits=commits, diffs=diffs)
    
    try:
        if provider == "Gemini":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text, None
        elif provider == "ChatGPT":
            return None, "ChatGPT 연동은 아직 준비 중입니다. (openai 라이브러리 필요)"
        elif provider == "Claude":
            return None, "Claude 연동은 아직 준비 중입니다. (anthropic 라이브러리 필요)"
    except Exception as e:
        return None, str(e)
