# Vibe Coding Project - Prompt Recommendation System v0.2

이 레포지토리는 코딩 학습 및 문제 해결을 위한 프롬프트 추천 시스템의 Streamlit 애플리케이션입니다. 사용자가 입력한 내용과 유사한 코딩 프롬프트를 추천하여 아이디어를 얻거나 문제 해결에 도움을 주는 것을 목표로 합니다.

## 주요 기능

- **프롬프트 추천**:
    - **키워드 기반 추천**: 입력된 키워드가 포함된 프롬프트를 검색하여 추천합니다.
    - **벡터 기반 추천**: `jhgan/ko-sroberta-multitask` 임베딩 모델과 FAISS 벡터 스토어를 사용하여 의미론적으로 유사한 프롬프트를 추천합니다. (한국어 특화)
- **프롬프트 관리**:
    - 전체 프롬프트 목록 보기
    - 새로운 프롬프트 추가

## 기술 스택

- **언어**: Python
- **프레임워크**: Streamlit (웹 애플리케이션)
- **핵심 라이브러리**:
    - LangChain: LLM 애플리케이션 개발 프레임워크
    - HuggingFace Transformers: 자연어 처리 및 임베딩 모델 접근
    - FAISS: 효율적인 유사도 검색을 위한 벡터 스토어
- **임베딩 모델**: `jhgan/ko-sroberta-multitask` (768차원 벡터, 한국어 특화)
- **데이터 저장**: JSON 파일 (`vibe_prompt_reco_vector_v0.2/prompts_v2.json`)

## 디렉토리 구조

- `vibe_prompt_reco_vector_v0.2/`: 메인 애플리케이션 디렉토리
    - `vibe_prompt_manager_with_vector.py`: Streamlit 애플리케이션 실행 파일
    - `prompts_v2.json`: 프롬프트 데이터 저장 파일
    - `requirements.txt`: Python 패키지 의존성 목록
    - `vector_search_explanation.md`: 벡터 검색 원리 설명 문서

## 설치 및 실행 방법

1.  **레포지토리 클론:**
    ```bash
    git clone https://github.com/your-username/vibe_coding_project.git
    cd vibe_coding_project
    ```

2.  **가상 환경 생성 및 활성화 (권장):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/macOS
    # venv\Scripts\activate    # Windows
    ```

3.  **의존성 패키지 설치:**
    ```bash
    pip install -r vibe_prompt_reco_vector_v0.2/requirements.txt
    ```

4.  **애플리케이션 실행:**
    ```bash
    streamlit run vibe_prompt_reco_vector_v0.2/vibe_prompt_manager_with_vector.py
    ```

## 🗂️ Data File Management

프롬프트 데이터는 `vibe_prompt_reco_vector_v0.2/` 디렉토리 내의 `vibe_prompts_structured_upgraded.json` 파일에 저장됩니다. (현재 `v0.2` 애플리케이션은 이 파일을 우선적으로 사용하도록 설정되어 있습니다.)

이전 버전의 애플리케이션 디렉토리(예: `vibe_prompt_reco/`, `vibe_prompt_reco_vector/`)에도 유사한 JSON 데이터 파일 (`vibe_prompts_structured.json` 등)이 존재할 수 있습니다.

**데이터 일관성 유지를 위한 권장 사항:**

*   **단일 데이터 소스 유지**: 현재 활성화된 `v0.2` 애플리케이션을 위해서는 `vibe_prompt_reco_vector_v0.2/vibe_prompts_structured_upgraded.json` 파일을 기준으로 데이터를 관리하는 것이 좋습니다.
*   **구버전 데이터 관리**: 만약 이전 버전의 애플리케이션/스크립트를 별도로 유지보수하며 해당 버전의 데이터를 사용해야 한다면, 데이터 파일의 버전을 명확히 관리하거나 (예: `prompts_v0.1.json`, `prompts_v0.2.json`) 각 버전에 맞는 별도의 데이터 디렉토리를 사용하는 것을 고려하세요.
*   **v0.2 애플리케이션 일관성**: `vibe_prompt_reco_vector_v0.2` 애플리케이션은 지정된 JSON 파일을 일관되게 사용하므로, 데이터 변경 시 이 파일을 대상으로 작업해야 합니다.

여러 버전의 애플리케이션이 동일 레포지토리에 공존함에 따라 발생할 수 있는 데이터 혼동 및 불일치를 방지하기 위해 위와 같은 데이터 관리 방식을 권장합니다.

## 🧹 이전 버전 관리

이 저장소에는 `vibe_prompt_reco/` 및 `vibe_prompt_reco_vector/`와 같이 이전 버전의 애플리케이션 파일 및 디렉토리가 포함되어 있을 수 있습니다. 현재 활성 버전은 `vibe_prompt_reco_vector_v0.2/` 디렉토리에 있는 애플리케이션입니다.

코드베이스를 깔끔하게 유지하고 혼란을 방지하기 위해, 사용하지 않는 이전 버전의 디렉토리 및 파일은 다음 방법 중 하나로 처리하는 것을 권장합니다:

*   **아카이브**: 더 이상 적극적으로 사용하지 않지만 기록 보존의 가치가 있는 이전 버전들은 별도의 `archive/` 폴더로 옮기거나, 해당 디렉토리를 압축 파일(예: `.zip`, `.tar.gz`)로 만들어 보관합니다.
*   **삭제 (Git 기록 활용)**: 만약 해당 버전들이 더 이상 필요 없고 모든 변경 사항이 Git 버전 관리 시스템에 안전하게 기록되어 있다면, 로컬 작업 디렉토리에서 해당 파일 및 디렉토리를 삭제하는 것을 고려할 수 있습니다. Git은 과거 버전을 복원할 수 있는 기능을 제공합니다.

이러한 정리는 현재 프로젝트 버전에 집중하고, 저장소를 탐색하며 관리하는 데 도움이 됩니다.

## 사용 방법

애플리케이션이 실행되면 웹 브라우저에서 다음 기능을 사용할 수 있습니다:

1.  **프롬프트 추천 받기**:
    - 사이드바에서 "프롬프트 추천"을 선택합니다.
    - 검색창에 원하는 내용을 입력합니다.
    - "추천 방식"을 선택합니다:
        - **Keyword**: 입력한 단어가 포함된 프롬프트를 보여줍니다.
        - **Vector**: 입력 내용과 의미적으로 가장 유사한 프롬프트를 보여줍니다.
    - "추천 받기" 버튼을 클릭합니다.

2.  **전체 프롬프트 보기**:
    - 사이드바에서 "전체 프롬프트 보기"를 선택하여 저장된 모든 프롬프트를 확인합니다.

3.  **새로운 프롬프트 추가하기**:
    - 사이드바에서 "새 프롬프트 추가"를 선택합니다.
    - `ID`, `title`, `prompt`, `category`, `tags` (쉼표로 구분)를 입력합니다.
    - "프롬프트 추가" 버튼을 클릭하여 저장합니다.

## 기여하기

새로운 기능 제안, 버그 수정 등 모든 종류의 기여를 환영합니다. 이슈를 생성하거나 풀 리퀘스트를 보내주세요.

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
