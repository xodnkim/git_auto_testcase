# services/ai_service.py (일부 수정)
from google import genai
import openai
import anthropic

# 🚀 수정: custom_prompt를 파라미터로 받습니다.
def analyze_code(provider, api_key, commits, diffs, custom_prompt):
    
    # .format() 대신 .replace()를 써야 사용자가 {commits}를 실수로 지워도 에러가 안 납니다.
    prompt = custom_prompt.replace("{commits}", commits).replace("{diffs}", diffs)
    
    if provider == "Gemini":
        try:
            client = genai.Client(api_key=api_key)
            available = [m.name.replace("models/", "") for m in client.models.list() if "generateContent" in m.supported_methods]
            if not available: return None, None, "Gemini: 사용 가능한 모델이 없습니다."
            
            preferred = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
            selected_model = next((m for m in preferred if m in available), available[0])
            
            response = client.models.generate_content(model=selected_model, contents=prompt)
            return response.text, selected_model, None
        except Exception as e:
            return None, None, f"Gemini 실행 오류: {e}"

    elif provider == "ChatGPT":
        try:
            client = openai.OpenAI(api_key=api_key)
            models = client.models.list()
            available = [m.id for m in models.data]
            
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
                    continue 
                    
            return None, None, f"Claude 모든 모델 실패: {last_error}"
        except Exception as e:
            return None, None, f"Claude 설정 오류: {e}"
            
    return None, None, "알 수 없는 AI Provider입니다."
