# config/settings.py

DEFAULT_PROMPT = """너는 소프트웨어 QA 전문가다.
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
{diffs}"""

ALLOWED_EXTENSIONS = ('.py', '.js', '.ts', '.java', '.kt', '.swift', '.vue', '.html')
MAX_CHUNK_LENGTH = 800
MAX_TOTAL_LENGTH = 5000
