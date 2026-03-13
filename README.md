# 🚀 AI 기반 형상관리 QA 리스크 분석 & TC 자동 생성기
> **코드 변경점을 AI가 분석하여 QA 리스크를 도출하고, 실무용 엑셀 테스트케이스(TC)를 자동 생성하는 실시간 팀 협업 대시보드입니다.**

![Python](https://img-shields.io/badge/python-3.9+-blue.svg)
![Streamlit](https://img-shields.io/badge/Streamlit-FF4B4B?style=flat&logo=Streamlit&logoColor=white)
![OpenAI](https://img-shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)
![Gemini](https://img-shields.io/badge/Gemini-8E75B2?style=flat&logo=googlebard&logoColor=white)

## 📌 프로젝트 기획 배경 (Background)
* **Pain Point**: QA 과정에서 개발자의 커밋(Commit) 로그나 PR/MR 코드를 일일이 리뷰하고, 사이드 이펙트를 예측하여 테스트케이스(TC)를 작성하는 데 막대한 시간이 소모됩니다.
* **Solution**: 멀티 플랫폼(웹/모바일) 환경을 이해하는 LLM을 활용하여, VCS 링크 하나만으로 **핵심 변경 요약, 리스크 분석, 검증 포인트, 엑셀 TC까지 원클릭으로 추출**하는 자동화 파이프라인을 구축했습니다.
* **Target User**: 사내 QA 엔지니어 및 개발 팀원 (실시간 분석 결과 공유 및 협업)

## ✨ 핵심 기능 (Key Features)

### 1. 🌍 실시간 팀 협업 대시보드 (Global In-Memory State)
* Streamlit의 전역 캐시(`@st.cache_resource`)를 활용하여 가상의 DB를 구축했습니다.
* 팀원들이 각자의 자리에서 코드를 분석하면, **동일한 대시보드 화면에 분석 히스토리가 실시간으로 공유**되어 중복 QA 작업을 방지합니다.
* 사용자명 기반 실시간 검색 및 페이징 기능을 지원하여 방대한 히스토리도 쉽게 관리할 수 있습니다.

### 2. 🔒 Zero-DB 아키텍처와 개별 암호화 (Enterprise Security)
* **Zero-DB**: 회사 내부의 민감한 소스 코드 분석 결과가 외부 DB나 하드디스크에 영구 저장되지 않고 서버의 임시 메모리(RAM)에만 존재합니다. 서버 재부팅/유휴 상태 시 완전히 파기되므로 **소스코드 유출 리스크가 제로(0)**입니다.
* **개별 잠금 및 마스터 권한**: 공용 대시보드 특성상 타인이 내 결과물을 열람하지 못하도록 분석 시 입력한 **'비밀번호'**로 다운로드를 잠금 처리합니다.
* **슈퍼 관리자**: 마스터 패스워드(`admin1234`) 입력 시 모든 항목의 강제 다운로드 및 리스트 삭제 권한이 활성화됩니다.

### 3. 🤖 멀티 LLM 엔진 & 프롬프트 커스텀
* **Gemini, ChatGPT, Claude** 등 주요 AI 모델을 사용자가 상황에 맞게 직접 선택하여 분석 가능.
* 실무 QA 환경에 맞춘 **전용 프롬프트 템플릿** 기본 제공 및 팝오버(Popover)를 통한 실시간 프롬프트 튜닝 기능.

### 4. 📊 실무 밀착형 결과물 생성 (Export)
* **QA 리스크 보고서**: 핵심 변경점과 사이드 이펙트 분석 결과를 깔끔한 HTML 리포트로 즉시 렌더링.
* **엑셀 TC 자동화**: 단순 CSV 텍스트가 아닌, `openpyxl`을 활용해 **실무 9열 포맷(1Depth, 2Depth, 상세, 사전조건, 기대결과 등)**과 디자인 서식(배경색, 테두리, 너비 정렬)이 완벽하게 적용된 엑셀(`xlsx`) 파일을 생성합니다.

## 🛠️ 기술 스택 (Tech Stack)
* **Frontend/Backend**: `Streamlit`
* **Data Manipulation**: `Pandas`, `Openpyxl` (Excel Formatting)
* **API Integration**: `requests`, `google-genai`, `openai`, `anthropic`
* **Parsing/Formatting**: `Markdown`, `urllib`
