# Requirements

## 1. Functional Requirements

### 입력
- 사용자는 logcat 로그 텍스트를 붙여넣을 수 있어야 한다.

---

### 분석 프로파일
- 시스템은 여러 개의 Analysis Profile을 지원해야 한다.
- 사용자는 분석 목적에 따라 프로파일을 선택할 수 있어야 한다.
- 각 프로파일은 다음을 포함해야 한다:
  - 로그 필터 조건
  - 파싱 규칙
  - 시각화 정의

---

### 파싱
- 시스템은 로그를 라인 단위로 처리해야 한다.
- timestamp를 추출할 수 있어야 한다.
- keyword 기반으로 분석 대상 로그를 식별해야 한다.
- 다양한 payload 구조를 처리할 수 있어야 한다:
  - key-value 계열
  - function 계열
  - delimiter 기반 segment 구조
  - custom regex 기반 구조

---

### 데이터 처리
- timestamp 기준 정렬
- 일부 값 누락 허용
- 파싱 결과를 구조화된 형태로 저장

---

### 시각화
- 프로파일 정의 기반 그래프 생성
- 시간 기반(x-axis) 그래프
- multi-parameter plotting 지원
- 다중 그래프 레이아웃 지원

---

### 필터링
- keyword 기반 로그 필터링

---

### 에러 처리
- 파싱 실패 라인 확인 가능
- 일부 파싱 실패 시 전체 처리 지속

---

## 2. Non-functional Requirements

- OS: Windows
- 실행 형태: 단일 exe
- 오프라인 동작
- 수천 줄 로그를 수 초 내 처리
- profile 추가/수정 용이성 확보
