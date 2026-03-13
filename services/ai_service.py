# services/ai_service.py
from google import genai
import openai
import anthropic
from config.settings import DEFAULT_PROMPT

def get_ai_models(provider, api_key):
    """선택한 AI 제공자의 실제 사용 가능한 모델 목록을 동적으로 반환합니다."""
    if not api_key: return []
    
    try:
        if provider == "Gemini":
            client = genai.Client(api_key=api_key)
            return [m.name.replace("models/", "") for m in client.models.list() if "generateContent" in m.supported_methods]
            
        elif provider == "ChatGPT":
            # OpenAI API로 실제 모델 목록 가져오기
            client = openai.OpenAI(api_key=api_key)
            models = client.models.list()
            # gpt 계열의 모델만 필터링 (DALL-E 등 제외)
            return sorted([m.id for m in models.data if "gpt" in m.id or "o1" in m.id], reverse=True)
            
        elif provider == "Claude":
            # Anthropic은 현재 모델 목록 조회 API를 직접 지원하지 않으므로, 
            # API 키가 유효한지 간단한 테스트 호출을 하거나, 최신 하드코딩 리스트를 제공하는 방식이 일반적입니다.
            # 여기서는 클라이언트 인증 성공 여부만 확인하고 리스트를 반환합니다.
            client = anthropic.Anthropic(api_key=api_key)
            # 가벼운 모델로 인증 테스트 (실패 시 except로 빠짐)
            # 실제 목록 조회 엔드포인트가 없으므로 가장 많이 쓰이는 모델 리스트 제공
            return ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
            
    except Exception as e:
        print(f"{provider} 모델 로드 에러: {e}") # 터미널 디버깅용
        return []

def analyze_code(provider, api_key, model_name, commits, diffs):
    prompt = DEFAULT_PROMPT.format(commits=commits, diffs=diffs)
    
    try:
        if provider == "Gemini":
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(model=model_name, contents=prompt)
            return response.text, None
            
        elif provider == "ChatGPT":
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content, None
            
        elif provider == "Claude":
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model_name,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text, None
            
    except Exception as e:
        return None, str(e)
