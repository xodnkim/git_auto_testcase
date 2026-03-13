# services/ai_service.py
from google import genai
import openai
import anthropic
from config.settings import DEFAULT_PROMPT

def analyze_code(provider, api_key, commits, diffs):
    """UI 개입 없이 코드 내부에서 사용 가능한 최적의 모델을 자동 탐색하여 실행합니다."""
    prompt = DEFAULT_PROMPT.format(commits=commits, diffs=diffs)
    
    if provider == "Gemini":
        try:
            client = genai.Client(api_key=api_key)
            # 1. 동적 목록 조회
            available = [m.name.replace("models/", "") for m in client.models.list() if "generateContent" in m.supported_methods]
            if not available: return None, None, "Gemini: 사용 가능한 모델이 없습니다."
            
            # 2. 선호 모델 자동 선택 (없으면 리스트 첫 번째)
            preferred = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
            selected_model = next((m for m in preferred if m in available), available[0])
            
            response = client.models.generate_content(model=selected_model, contents=prompt)
            return response.text, selected_model, None
        except Exception as e:
            return None, None, f"Gemini 실행 오류: {e}"

    elif provider == "ChatGPT":
        try:
            client = openai.OpenAI(api_key=api_key)
            # 1. 동적 목록 조회
            models = client.models.list()
            available = [m.id for m in models.data]
            
            # 2. 선호 모델 자동 선택
            preferred = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
            selected_model = next((m for m in preferred if m in available), None)
            
            if not selected_model:
                gpt_models = [m for m in available if "gpt" in m]
                if not gpt_models: return None, None, "사용 가능한 GPT 모델이 없습니다."
                selected_model = gpt_models[0]
                
            response = client.chat.completions.create(
                model=selected_model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content, selected_model, None
        except Exception as e:
            return None, None, f"ChatGPT 실행 오류: {e}"

    elif provider == "Claude":
        try:
            client = anthropic.Anthropic(api_key=api_key)
            # 🚨 Claude는 API 스펙상 list()를 지원하지 않아 내부 Fallback 루프 사용
            preferred_models = ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
            
            last_error = ""
            for selected_model in preferred_models:
                try:
                    response = client.messages.create(
                        model=selected_model,
                        max_tokens=4000,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text, selected_model, None
                except Exception as e:
                    last_error = str(e)
                    continue # 에러 나면 다음 모델로 조용히 넘어감
                    
            return None, None, f"Claude 모든 모델 실패: {last_error}"
        except Exception as e:
            return None, None, f"Claude 설정 오류: {e}"
            
    return None, None, "알 수 없는 AI Provider입니다."
