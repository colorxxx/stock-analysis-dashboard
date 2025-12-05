# 🚨 새로운 시그널 자동 감지 및 분석

## 개요
시그널 발생일이 변경되면 자동으로 감지하고, 새로운 AI 분석을 수행하는 기능입니다.

## 작동 방식

### 1. 자동 캐시 확인
종목 차트를 열면 자동으로 해당 시그널 발생일에 대한 캐시를 확인합니다.

### 2. 두 가지 시나리오

#### ✅ 캐시가 있는 경우 (기존 시그널)
```
📅 시그널 발생일: 2025-12-01 (BUY)
✅ 분석 완료 (캐시됨)

📊 분석 결과:
[분석 내용이 즉시 표시됨]
```

- 버튼 없이 즉시 분석 결과 표시
- API 호출 없음 (0초)
- 추가 비용 없음

#### ⚠️ 캐시가 없는 경우 (새로운 시그널)
```
📅 시그널 발생일: 2025-12-05 (STRONG BUY)
⚠️ 새로운 시그널입니다. AI 분석이 필요합니다.  [🔍 분석 시작]
```

- 새로운 시그널 발생을 자동으로 감지
- "분석 시작" 버튼 표시
- 버튼 클릭 시:
  1. Perplexity API 호출 (2-3초 소요)
  2. 분석 결과 표시
  3. 자동으로 캐시에 저장
  4. 페이지 새로고침 → 다음부터는 즉시 표시

## 새로운 시그널이 발생하는 경우

### 시나리오 1: 골든크로스/데드크로스 발생
```python
# 예: AAPL에서 새로운 골든크로스 발생
2025-12-05: EMA5가 EMA20을 상향 돌파
→ last_signal_date = "2025-12-05"
→ 캐시 확인: 없음
→ "새로운 시그널" 경고 표시
→ 사용자가 "분석 시작" 클릭
→ AI 분석 수행 및 캐싱
```

### 시나리오 2: 일괄 분석 누락
```python
# batch_analyze_all.py 실행 시 누락된 종목
→ 해당 종목의 차트 열 때
→ 캐시 없음 감지
→ "새로운 시그널" 경고
→ 수동으로 분석 시작
```

### 시나리오 3: 캐시 삭제
```python
# clear_cache.py로 전체 캐시 삭제 후
→ 모든 종목이 "새로운 시그널" 상태
→ 다시 분석 필요
```

## 테스트 방법

### 1. 단일 종목 테스트
```bash
python3 test_new_signal.py
```

**테스트 내용:**
- TSLA 캐시 삭제
- 새로운 분석 수행
- 캐시 저장 확인
- 두 번째 조회 시 캐시 사용 확인

### 2. 여러 종목 테스트
```bash
python3 test_multiple_new_signals.py
```

**테스트 내용:**
- NVDA, AAPL, META 3개 종목
- 캐시 상태 확인
- 분석 결과 검증

### 3. 실제 시나리오 테스트
```bash
python3 test_real_new_signal.py
```

**테스트 내용:**
- META 캐시 삭제 (새로운 시그널 시뮬레이션)
- API 호출 확인
- 캐시 저장 확인
- Streamlit 동작 시뮬레이션

## 실제 사용 예시

### 매일 아침 시나리오

1. **전날 종가 기준으로 새로운 시그널 발생**
   ```
   JOBY: 2025-12-05 골든크로스 발생
   ```

2. **Streamlit 앱 실행**
   ```bash
   streamlit run app.py
   ```

3. **JOBY 차트 열기**
   ```
   📅 시그널 발생일: 2025-12-05 (BUY)
   ⚠️ 새로운 시그널입니다. AI 분석이 필요합니다.  [🔍 분석 시작]
   ```

4. **"분석 시작" 버튼 클릭**
   ```
   🔍 JOBY AI 분석 중...
   ✅ 분석 완료 (신규)

   📊 분석 결과:
   2025년 12월 5일 JOBY 주가가 상승한 이유는...
   ```

5. **다음 조회부터는 즉시 표시**
   ```
   ✅ 분석 완료 (캐시됨)
   [분석 결과 즉시 표시]
   ```

## 장점

### 1. 자동 감지
- 수동으로 확인할 필요 없음
- 새로운 시그널을 놓치지 않음

### 2. API 비용 절감
- 캐시된 결과 재사용
- 필요할 때만 API 호출

### 3. 빠른 응답
- 캐시된 결과: 0초 (즉시)
- 새로운 분석: 2-3초

### 4. 사용자 경험
- 명확한 상태 표시
- "새로운 시그널" vs "캐시됨"
- 필요한 경우에만 버튼 표시

## 데이터베이스 구조

### perplexity_analysis 테이블
```sql
CREATE TABLE perplexity_analysis (
    ticker TEXT,
    date TEXT,
    analysis TEXT,
    citations TEXT,
    created_at TEXT,
    PRIMARY KEY (ticker, date)
);
```

### 캐시 키
```python
# 캐시 키는 (ticker, date) 조합
# 예: ("AAPL", "2025-12-01")

# 새로운 시그널 = 해당 키가 DB에 없음
# 기존 시그널 = 해당 키가 DB에 있음
```

## 유지보수

### 캐시 관리

**특정 종목 캐시 삭제:**
```python
import sqlite3
conn = sqlite3.connect('stock_data.db')
cursor = conn.cursor()
cursor.execute("DELETE FROM perplexity_analysis WHERE ticker = 'AAPL'")
conn.commit()
conn.close()
```

**특정 날짜 이전 캐시 삭제:**
```python
cursor.execute("DELETE FROM perplexity_analysis WHERE date < '2025-11-01'")
```

**전체 캐시 삭제:**
```bash
python3 clear_cache.py
```

### 캐시 통계 확인
```bash
sqlite3 stock_data.db "SELECT COUNT(*), MIN(date), MAX(date) FROM perplexity_analysis"
```

## 문제 해결

### Q: "새로운 시그널" 경고가 계속 뜨는 경우
**A:** 분석을 수행했는데도 계속 뜨면:
1. 캐시가 제대로 저장되었는지 확인
2. `ticker`와 `date`가 정확한지 확인
3. 데이터베이스 권한 확인

### Q: 분석 결과가 즉시 표시되지 않는 경우
**A:** "분석 시작" 버튼을 클릭한 후:
1. 페이지가 자동으로 새로고침됨 (`st.rerun()`)
2. 새로고침 안 되면 수동으로 F5 키
3. 캐시 확인: `get_cached_analysis(ticker, date)`

### Q: API 호출이 너무 자주 발생하는 경우
**A:**
1. 캐시가 제대로 저장되고 있는지 확인
2. `batch_analyze_all.py`로 미리 캐싱
3. 필요없는 종목은 티커 리스트에서 제거

## 향후 개선 가능 사항

1. **자동 일괄 분석**: 매일 새벽에 cron으로 자동 실행
2. **우선순위 분석**: 중요한 종목 먼저 분석
3. **알림 기능**: 새로운 시그널 발생 시 이메일/슬랙 알림
4. **분석 갱신**: 일정 기간(예: 7일) 지난 분석은 자동 갱신

## 관련 파일

```
stock-analysis-dashboard/
├── app.py                           # 메인 앱 (자동 감지 로직 포함)
├── perplexity_analyzer.py          # 분석 및 캐싱 로직
├── test_new_signal.py               # 단일 종목 테스트
├── test_multiple_new_signals.py    # 여러 종목 테스트
├── test_real_new_signal.py         # 실제 시나리오 테스트
├── batch_analyze_all.py            # 일괄 분석
├── clear_cache.py                  # 캐시 삭제
└── stock_data.db                    # 캐시 데이터베이스
```
