from google import genai
import openai
import anthropic

def analyze_code(provider, api_key, commits, diffs, custom_prompt):
    """선택한 AI로 코드를 분석하고 결과를 반환합니다."""
    
    prompt = custom_prompt.replace("{commits}", commits).replace("{diffs}", diffs)
    
    if provider == "Gemini":
        try:
            client = genai.Client(api_key=api_key)
            
            # 1. 사용 가능한 모델 목록 가져오기
            available = [m.name.replace("models/", "") for m in client.models.list()]
            if not available: 
                return None, None, "Gemini: 사용 가능한 모델이 없습니다."
            
            # 2. 우선순위 모델 (사용자님 대시보드 기준 2.5-flash 최우선 배치)
            preferred = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash"]
            
            # 3. 우선순위 중 사용 가능한 모델만 추려냄 (없으면 전체 목록 사용)
            models_to_try = [m for m in preferred if m in available]
            if not models_to_try:
                models_to_try = available
                
            # 💡 [핵심 해결책]: 목록에 있다고 믿지 말고, 진짜로 실행해봅니다. (Fallback Loop)
            last_error = ""
            for model_name in models_to_try:
                try:
                    # 실행을 시도해보고
                    response = client.models.generate_content(model=model_name, contents=prompt)
                    # 성공하면 바로 리턴!
                    return response.text, model_name, None
                except Exception as e:
                    # 404 에러 등이 나면 화면에 띄우지 않고 조용히 다음 모델로 넘어갑니다.
                    last_error = str(e)
                    continue 
                    
            # 모든 모델이 다 실패했을 때만 에러를 뱉습니다.
            return None, None, f"Gemini 모든 모델 실행 실패 (마지막 에러: {last_error})"
            
        except Exception as e:
            return None, None, f"Gemini API 연결 오류: {e}"

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
