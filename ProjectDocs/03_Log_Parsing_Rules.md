# Log Parsing Rules & Analysis Profiles

## 1. 개념

파싱 룰은 Analysis Profile 단위로 정의된다.

각 프로파일은 다음을 포함한다:
1. 필터링 규칙
2. 파싱 규칙
3. 데이터 구조
4. 시각화 정의

---

## 2. Analysis Profile 구조

```python
AnalysisProfile = {
    "name": str,
    "filter": {...},
    "parsing": {
        "patterns": [...]
    },
    "visualization": {
        "layout": str,
        "plots": [...]
    }
}
```

---

## 3. Payload Parsing Pattern (추상 정의)

다양한 로그 형식을 지원하기 위해 패턴 기반 파싱 구조를 사용한다.

---

## 4. 패턴 유형

### 4.1 Key-Value 계열

#### 정의
- key와 value가 구분자로 연결된 구조

#### 예시
```
lens=123
lens = 123
lens: 123
```

#### 구현 결정 사항
- separator 종류 (`=`, `:` 등)
- whitespace 허용
- value 종료 조건
- dtype 변환

---

### 4.2 Function 계열

```
roi(10,20)
```

---

### 4.3 Segment 기반

```
| DoF 64 | PDresult 8.214 |
```

- delimiter 기준 split
- segment 단위 parsing

---

### 4.4 Segment 내부 Key-Value

```
DoF 64
PDresult 8.214
```

---

### 4.5 Custom Regex

```
Curr lens 1739, 43mm
```

---

## 5. 패턴 적용 전략

권장 순서:
1. custom regex
2. key-value
3. function
4. segment
5. fallback

---

## 6. 데이터 구조

```python
{
    "timestamp": datetime,
    "values": {
        "key": value
    }
}
```

---

## 7. 설계 원칙

- 유연성 우선
- 포맷 변화 대응
- 패턴 독립성 유지
- 프로파일 기반 확장
