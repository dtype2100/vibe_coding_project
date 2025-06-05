# 벡터 검색(Vector Search) 원리 설명

## 1. 개요
이 프로젝트는 LangChain과 HuggingFace의 sentence-transformers를 사용하여 텍스트 기반의 의미론적 검색을 구현합니다. 벡터 검색은 텍스트를 수치화된 벡터로 변환하고, 이 벡터들 간의 유사도를 계산하여 가장 관련성 높은 결과를 찾아내는 방식입니다.

## 2. 핵심 컴포넌트

### 2.1 임베딩 모델
- **모델**: `jhgan/ko-sroberta-multitask`
- **특징**:
  - 768차원의 고정된 크기 벡터 생성
  - 한국어 특화 모델
  - 높은 이해도와 정확한 의미 분석에 중점

### 2.2 벡터 저장소
- **사용 기술**: FAISS (Facebook AI Similarity Search)
- **장점**:
  - 대규모 벡터 데이터의 효율적인 검색
  - 메모리 기반 빠른 검색
  - 유사도 기반 정렬 지원

## 3. 작동 원리

### 3.1 텍스트 벡터화 과정
1. 입력 텍스트를 임베딩 모델을 통해 벡터로 변환
2. 각 프롬프트의 텍스트도 동일한 방식으로 벡터화
3. 모든 벡터를 FAISS 벡터 저장소에 저장

### 3.2 검색 과정
1. 사용자 입력을 벡터로 변환
2. FAISS를 사용하여 가장 유사한 벡터 검색
3. 코사인 유사도 기반으로 상위 k개 결과 반환

## 4. 코드 구현

```python
# 벡터 저장소 구축
@st.cache_resource
def build_vectorstore(prompts: List[Dict]) -> FAISS:
    embeddings = HuggingFaceEmbeddings(
        model_name="jhgan/ko-sroberta-multitask"
    )
    texts = [item.get("prompt", "") for item in prompts]
    vs = FAISS.from_texts(texts, embeddings, metadatas=prompts)
    return vs

# 벡터 기반 추천
def vector_recommend(user_input: str, prompts: List[Dict], top_k: int = 3) -> List[Dict]:
    vs = build_vectorstore(prompts)
    results = vs.similarity_search_with_score(user_input, k=top_k)
    return [doc.metadata for doc, _ in results]
```

## 5. 장점

1. **의미론적 이해**
   - 단순 키워드 매칭이 아닌 문맥과 의미를 고려한 검색
   - 유사한 의미를 가진 다른 표현도 찾을 수 있음

2. **확장성**
   - 새로운 프롬프트 추가가 용이
   - 대규모 데이터셋에서도 효율적인 검색 가능

3. **정확도**
   - 의미적으로 유사한 프롬프트를 더 정확하게 찾아냄
   - 키워드 기반 검색보다 더 정교한 결과 제공

## 6. 한계점

1. **계산 비용**
   - 벡터 변환과 검색에 추가적인 계산 리소스 필요
   - 대규모 데이터셋에서는 인덱싱 시간이 필요

2. **의미적 차이**
   - 도메인 특화된 의미를 완벽하게 이해하지 못할 수 있음
   - 기술 용어의 정확한 맥락 파악이 어려울 수 있음

## 7. 개선 방향

1. **모델 최적화**
   - 도메인 특화된 임베딩 모델 사용 고려
   - 더 큰 모델로의 업그레이드 검토

2. **하이브리드 검색**
   - 키워드 기반 검색과 벡터 검색의 결합
   - 각 방식의 장점을 활용한 복합 검색 구현

3. **캐싱 전략**
   - 자주 사용되는 검색 결과 캐싱
   - 검색 성능 최적화 