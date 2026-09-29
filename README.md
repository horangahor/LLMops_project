# PaperDraft AI Service : SW 연구 및 실증 데이터 기반 논문 초안 생성 서비스

비정형 **SW 연구 및 시스템 설계 노트(문서 A)**와 **실증 검증 및 아티팩트 리포트(문서 B)**를 분석하여, 가설 입증 수준을 자동 판정하고 **논문 4장(방법론)** 및 **5장(검증 및 고찰)** 초안을 생성하는 AI 서비스입니다.

본 프로젝트는 **Upstage Studio Agent API (및 Solar LLM 파이프라인)**를 이용하여 문서를 분석하고, 연구 설계와 실증 데이터를 대조하여 학술 논문 초안과 정합성 평가를 JSON 및 PDF 형태로 생성합니다.

---

# 1. Project Overview

본 프로젝트는 기획서(`[Template] 전남대 Studio 활용 프로젝트 기획서의 사본.pdf`)에 명시된 3단 에이전트 파이프라인으로 구성됩니다.

```text
SW_Design_Notes.pdf (문서 A: SW 연구/설계 노트)
      │
      ▼
Proposal Agent (Parse -> Extract)
      │
      ▼
proposal.json (연구 문제, 제안 기법, 핵심 기여점, 전제조건)

Validation_Report.pdf (문서 B: 실증 검증 리포트)
      │
      ▼
Validation Agent (Parse -> Extract)
      │
      ▼
validation.json (검증 유형, 벤치마크 실증 근거, 검증 속성, 한계점)

proposal.json + validation.json
      │
      ▼
Evaluation Builder (matching_builder.py / ReportLab)
      │
      ▼
Evaluation_Input.pdf (설계 목표 대비 실증 근거 대조표)
      │
      ▼
Paper Draft Agent (Parse -> Classify -> Extract)
      │
      ▼
matching_result.json (가설 입증 수준, 정합성 점수, 논문 4장/5장 초안, 기여점, 후속 과제)
```

---

# 2. 비정형 원천 데이터 (Raw Unstructured Data)

사용자가 제공한 비정형 PDF 데이터:
- **`data/GPU_Programming_CUDA_Parallel_Processing.pdf`** : 62페이지 분량의 딥러닝 형식 검증(LiRPA/CROWN 알고리즘) CUDA 병렬 가속화 연구/개발 노트 및 벤치마크/프로파일링 로그.
- **`data/SW_Design_Notes.pdf`** (문서 A) : CROWN 바운드 전파 GPU 가속 설계 사상 및 cuBLAS/cuSPARSE/메모리 풀 아키텍처 명세.
- **`data/Validation_Report.pdf`** (문서 B) : CPU(101ms) 대비 단계별 최적화(353ms → 201ms → 85ms → 40ms) 측정 수치 및 Nsight Systems 프로파일링 결과.

---

# 3. Project Structure

```text
hr-ai-service-workflow/
│
├── app.py                      # Main Workflow Orchestrator (CLI)
├── streamlit_app.py            # Streamlit 웹 UI MVP
├── service.py                  # 비즈니스 로직 서비스 계층
├── config.py                   # 환경설정 및 파일 경로 관리
├── upload.py                   # Upstage Files API 업로드 모듈
├── agent_client.py             # Upstage Studio Agent 및 Solar LLM 클라이언트
├── proposal_agent.py           # Proposal Agent 실행 모듈
├── validation_agent.py         # Validation Agent 실행 모듈
├── paper_draft_agent.py        # Paper Draft Agent 실행 모듈
├── matching_builder.py         # Evaluation_Input.pdf 합성 대조표 생성기
├── file_manager.py             # JSON 저장 및 파일 유틸리티
├── requirements.txt            # 의존성 패키지 목록
├── README.md                   # 프로젝트 설명서
├── .gitignore                  # Git 무시 파일 (.env, .venv 등)
├── .env                        # 환경 변수 (API Key, Agent ID)
│
├── agent_configs/              # Upstage Studio 에이전트 설정 파일 (Draft)
│     ├── Proposal Agent.json
│     ├── Validation Agent.json
│     └── Paper Draft Agent.json
│
├── fonts/
│     └── NanumGothic-Regular.ttf
│
├── data/                       # 입력 PDF 문서
│     ├── GPU_Programming_CUDA_Parallel_Processing.pdf
│     ├── SW_Design_Notes.pdf
│     └── Validation_Report.pdf
│
├── output/                     # 중간 산출물
│     ├── proposal.json
│     ├── validation.json
│     └── Evaluation_Input.pdf
│
└── result/                     # 최종 결과물
      └── matching_result.json
```

---

# 4. 실행 방법

### 1) 환경 설정
```bash
# 가상환경 활성화
.\.venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2) 전체 Workflow 파이프라인 실행 (CLI)
```bash
python app.py
```
- Step 1: Proposal Agent 실행 → `output/proposal.json` 생성
- Step 2: Validation Agent 실행 → `output/validation.json` 생성
- Step 3: Evaluation Builder 실행 → `output/Evaluation_Input.pdf` 생성
- Step 4: Paper Draft Agent 실행 → `result/matching_result.json` 생성

### 3) Streamlit 웹 UI 실행
```bash
streamlit run streamlit_app.py
```
- 브라우저(`http://localhost:8501`)에서 문서 A, 문서 B 업로드 후 [🚀 논문 초안 생성 및 정합성 분석 실행] 클릭
- 가설 입증 수준(Strongly Supported 등), 정합성 점수, 논문 4장/5장 본문 초안 서술문 확인 및 다운로드