# Architecture

## 1. 전체 흐름

Raw Log Input
→ Line Split
→ Timestamp Parsing
→ Profile Selection
→ Rule-based Parsing
→ Data Normalization
→ Visualization

---

## 2. 구조

app/
 ├── main.py
 ├── ui/
 ├── parser/
 │    ├── log_parser.py
 │    ├── rule_engine.py
 │    └── profiles/
 ├── model/
 ├── visualize/

---

## 3. 주요 컴포넌트

### Profile Manager
- 프로파일 로딩 및 선택

### Log Parser
- 라인 분리
- timestamp 추출

### Rule Engine
- 프로파일 기반 파싱
- 패턴 체인 처리

### Data Model
- 정규화 데이터 저장

### Plot Engine
- 시각화 메타 해석
- 그래프 생성

---

## 4. 설계 핵심

- Parsing + Visualization = Profile
- 코드 변경 없이 분석 변경 가능
- 패턴 체인 구조

---

## 5. 기술 스택

- Python
- PyQt / Tkinter
- matplotlib
- regex
- PyInstaller
