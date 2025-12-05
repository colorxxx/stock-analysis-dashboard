# 🤖 Automatic Background AI Analysis System

## 개요
사용자가 버튼을 클릭할 필요 없이 모든 주식 분석이 자동으로 캐시되어 즉시 표시되는 시스템입니다.

## 작동 방식

### 1. 초기 캐시 (완료)
- **batch_analyze_all.py** 실행으로 81개 종목 전체 분석 완료
- 100% 성공률, 10.2분 소요
- 모든 시그널 발생일에 대한 AI 분석이 `stock_data.db`에 저장됨

### 2. 사용자 경험 (app.py)
```
📅 시그널 발생일: 2025-12-05 (STRONG BUY)
✅ AI 분석

📊 분석 결과:
[캐시된 분석 결과가 즉시 표시됨]

📚 참고 자료:
1. [출처 링크]
2. [출처 링크]
```

**변경사항:**
- ❌ 버튼 제거 ("🔍 분석 시작" 버튼 없음)
- ✅ 캐시된 결과만 표시
- ℹ️ 캐시 없을 경우: "분석이 준비되지 않았습니다. 다음 업데이트를 기다려주세요."

### 3. 자동 업데이트 (daily_update.py)

#### 매일 자동 실행
- **시간**: 매일 22:00 UTC (미국 장 마감 후)
- **방식**: GitHub Actions 또는 수동 스크립트

#### 작동 로직
1. 모든 종목의 현재 시그널 확인
2. 이전 시그널과 비교 (`signal_state` 테이블 사용)
3. **새로운 시그널만 분석** (변경 감지)
4. 분석 결과 자동 캐싱
5. 데이터베이스 커밋 및 푸시

#### 예시
```
📊 Daily Update - 2025-12-05 22:00:00

[1/81] AAPL
  💾 Already cached (2025-10-17)

[2/81] IONQ
  🆕 New signal: 2025-12-05
  ✅ Analyzed and cached

[3/81] TSLA
  💾 Already cached (2025-12-01)

📊 Update Complete
  🆕 New analyses: 3
  💾 Cached: 78
  ❌ Errors: 0
```

## 배포 방법

### Option 1: GitHub Actions (자동화)

1. **GitHub Secrets 설정**
   - Repository → Settings → Secrets → Actions
   - `PERPLEXITY_API_KEY` 추가

2. **자동 실행**
   - 매일 22:00 UTC에 자동 실행
   - Workflow file: `.github/workflows/daily-analysis.yml`
   - Manual trigger: Actions 탭에서 "Run workflow" 클릭 가능

3. **결과 확인**
   - Actions 탭에서 실행 로그 확인
   - 성공 시 stock_data.db 자동 커밋/푸시
   - Streamlit Cloud 자동 재배포

### Option 2: 수동 스크립트 (간단)

매일 장 마감 후 직접 실행:

```bash
# 방법 1: 스크립트 실행 (자동 커밋/푸시 포함)
./update_cache.sh

# 방법 2: Python만 실행 (수동 커밋)
python3 daily_update.py
git add stock_data.db
git commit -m "Update cache: $(date +'%Y-%m-%d')"
git push
```

## 데이터베이스 구조

### perplexity_analysis (AI 분석 결과)
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

### signal_state (시그널 변경 추적)
```sql
CREATE TABLE signal_state (
    ticker TEXT PRIMARY KEY,
    last_signal_date TEXT,
    last_signal_type TEXT,
    last_checked TEXT
);
```

## 파일 구조

```
stock-analysis-dashboard/
├── app.py                          # Streamlit 앱 (버튼 제거됨)
├── perplexity_analyzer.py          # AI 분석 및 캐싱
├── batch_analyze_all.py            # 초기 전체 분석
├── daily_update.py                 # 매일 자동 업데이트 스크립트 ⭐
├── update_cache.sh                 # 수동 업데이트 스크립트 ⭐
├── stock_data.db                   # 캐시 데이터베이스 (Git 추적됨)
├── .github/workflows/
│   └── daily-analysis.yml          # GitHub Actions 설정 ⭐
└── .gitignore                      # stock_data.db 포함 설정 ⭐
```

## 비용 최적화

### API 호출 빈도
- **초기**: 81개 종목 × 1회 = 81 API 호출
- **매일**: 평균 1-5개 새로운 시그널만 분석
- **예상 비용**: 하루 $0.01-0.05 (Perplexity API 기준)

### 캐싱 전략
- 시그널 발생일이 동일하면 재분석 안 함
- `signal_state` 테이블로 변경 감지
- 중복 API 호출 0%

## 테스트 방법

### 1. 로컬 테스트
```bash
# 전체 시스템 테스트
python3 test_real_new_signal.py

# daily_update.py 테스트
python3 daily_update.py
```

### 2. 새로운 시그널 시뮬레이션
```bash
# 특정 종목 캐시 삭제
sqlite3 stock_data.db "DELETE FROM perplexity_analysis WHERE ticker = 'AAPL'"
sqlite3 stock_data.db "DELETE FROM signal_state WHERE ticker = 'AAPL'"

# 업데이트 실행
python3 daily_update.py

# 결과 확인
sqlite3 stock_data.db "SELECT * FROM perplexity_analysis WHERE ticker = 'AAPL'"
```

### 3. GitHub Actions 테스트
1. Repository → Actions → "Daily Stock Analysis"
2. "Run workflow" 클릭
3. 실행 로그 확인

## 모니터링

### 캐시 상태 확인
```bash
# 전체 캐시 개수
sqlite3 stock_data.db "SELECT COUNT(*) FROM perplexity_analysis"

# 최근 분석 확인
python3 check_analysis_length.py

# 특정 종목 확인
sqlite3 stock_data.db "SELECT * FROM perplexity_analysis WHERE ticker = 'TSLA'"
```

### GitHub Actions 로그
- Actions 탭에서 실행 히스토리 확인
- 실패 시 이메일 알림 (GitHub 설정)

## 문제 해결

### Q: "분석이 준비되지 않았습니다" 메시지가 뜨는 경우
**A:**
1. 해당 종목에 새로운 시그널이 발생했지만 아직 분석되지 않음
2. `daily_update.py` 실행 또는 다음 자동 업데이트 대기
3. 수동으로 분석하려면:
   ```bash
   python3 -c "
   from perplexity_analyzer import StockAnalyzer
   analyzer = StockAnalyzer()
   result = analyzer.analyze_stock_price_movement('TICKER', '2025-12-05', 'BUY')
   print(result)
   "
   ```

### Q: GitHub Actions가 실행되지 않는 경우
**A:**
1. Repository → Settings → Actions → "Allow all actions and reusable workflows" 확인
2. `PERPLEXITY_API_KEY` Secret 설정 확인
3. Workflow 파일 문법 확인

### Q: Streamlit Cloud에서 DB가 업데이트되지 않는 경우
**A:**
1. GitHub 커밋이 제대로 푸시되었는지 확인
2. Streamlit Cloud → Settings → "Reboot app" 클릭
3. `.gitignore`에 `!stock_data.db` 있는지 확인

## 유지보수

### 주기적 작업
- **매일**: GitHub Actions 실행 확인 (자동)
- **주간**: API 비용 확인
- **월간**: 오래된 분석 정리 (선택사항)

### 캐시 정리 (선택사항)
```bash
# 6개월 이전 데이터 삭제
sqlite3 stock_data.db "DELETE FROM perplexity_analysis WHERE date < '2024-06-01'"
```

## 장점

✅ **완전 자동화**: 사용자 개입 불필요
✅ **즉시 표시**: 캐시된 결과 0초 응답
✅ **비용 효율**: 변경된 시그널만 분석
✅ **안정성**: Git 기반 데이터 지속성
✅ **확장성**: 새 종목 추가 시 자동 대응
✅ **투명성**: GitHub Actions 로그로 모든 실행 추적

## 다음 단계

1. ✅ 초기 캐시 완료 (81개 종목)
2. ✅ app.py 버튼 제거
3. ✅ daily_update.py 생성
4. ⏳ GitHub Actions 설정 (또는 수동 스크립트 사용)
5. ⏳ Git push (stock_data.db 포함)
6. ⏳ Streamlit Cloud 배포

## 참고

- 새로운 시그널 감지: `NEW_SIGNAL_DETECTION_README.md`
- API 문서: `perplexity_analyzer.py`
- 테스트 스크립트: `test_*.py`
