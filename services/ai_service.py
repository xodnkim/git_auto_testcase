from google import genai
import openai
import anthropic

def analyze_code(provider, api_key, commits, diffs, custom_prompt):
    """선택한 AI로 코드를 분석하고 결과를 반환합니다."""
    
    # .replace()를 사용하여 사용자가 실수로 예약어를 지우는 것을 방지
    prompt = custom_prompt.replace("{commits}", commits).replace("{diffs}", diffs)
    
    if provider == "Gemini":
        try:
            client = genai.Client(api_key=api_key)
            
            # 💡 [ERROR FIX]: supported_methods 체크를 완전히 제거하고 이름만 깔끔하게 가져옵니다.
            available = [m.name.replace("models/", "") for m in client.models.list()]
            if not available: 
                return None, None, "Gemini: 사용 가능한 모델이 없습니다."
            
            # 우리가 쓰고 싶은 최신/안정화 모델 목록
            preferred = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-2.5-flash"]
            
            # available 목록 중에 preferred가 있으면 그걸 쓰고, 없으면 그냥 첫 번째 모델 사용
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
                if not gpt_models: 
                    return None, None, "사용 가능한 GPT 모델이 없습니다."
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
            
            # Claude는 API 스펙상 list()를 지원하지 않아 내부 Fallback(순차적 시도) 로직 사용
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
                    continue # 에러 나면 조용히 다음 모델로 넘어감
                    
            return None, None, f"Claude 모든 모델 실패: {last_error}"
        except Exception as e:
            return None, None, f"Claude 설정 오류: {e}"
            
    return None, None, "알 수 없는 AI Provider입니다."
