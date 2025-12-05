# 🤖 AI 주식 시그널 분석 기능

## 개요
Perplexity API를 활용하여 각 종목의 시그널 발생 날짜에 대한 AI 분석을 제공합니다.

## 주요 기능

### 1. 시그널 발생일 기준 분석
- **BUY 시그널**: 골든크로스 발생일 분석
- **SELL 시그널**: 데드크로스 발생일 분석
- **STRONG BUY**: 상승돌파 임박 시점 분석
- **WARNING**: 하락돌파 경고 시점 분석

### 2. 캐싱 시스템
- 동일한 티커와 날짜에 대한 중복 조회 방지
- SQLite 데이터베이스에 분석 결과 저장
- 두 번째 조회부터는 캐시된 데이터 즉시 반환

### 3. 분석 내용
각 시그널 발생일에 대해 다음 정보를 제공합니다:
- 해당일의 주가 동향 (상승/하락 폭)
- 주가 변동을 일으킨 구체적 원인
- 관련 뉴스 및 이벤트
- 단기 전망
- 참고 자료 (뉴스 링크 등)

## 설정 방법

### 1. Perplexity API 키 발급
1. [Perplexity AI 설정](https://www.perplexity.ai/settings/api) 페이지 방문
2. API 키 생성
3. 생성된 키 복사

### 2. .env 파일 설정
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가:

```bash
PERPLEXITY_API_KEY=your-api-key-here
```

## 사용 방법

### Streamlit 대시보드에서
1. 종목 분석 탭에서 종목 조회
2. 각 종목의 "📈 {TICKER} 차트" expander 클릭
3. 하단의 "🤖 AI 시그널 분석" 섹션 확인
4. "🔍 AI 분석 조회" 버튼 클릭
5. 분석 결과 및 참고 자료 확인

### 프로그래밍 방식으로
```python
from perplexity_analyzer import StockAnalyzer

# 분석기 초기화
analyzer = StockAnalyzer()

# 분석 실행
result = analyzer.analyze_stock_price_movement(
    ticker="AAPL",
    date="2025-11-28",
    signal_type="BUY"
)

# 결과 확인
if result['success']:
    print(result['analysis'])
    print(result['citations'])
```

## 파일 구조

```
stock-analysis-dashboard/
├── app.py                      # Streamlit 메인 앱
├── perplexity_analyzer.py     # Perplexity API 분석 모듈
├── test_perplexity.py         # 테스트 스크립트
├── .env                        # API 키 설정 (git에 포함 안 됨)
├── stock_data.db               # 주가 및 분석 결과 캐시 DB
└── requirements.txt            # Python 패키지 의존성
```

## 데이터베이스 스키마

### perplexity_analysis 테이블
| 컬럼 | 타입 | 설명 |
|------|------|------|
| ticker | TEXT | 종목 티커 |
| date | TEXT | 분석 날짜 (YYYY-MM-DD) |
| analysis | TEXT | AI 분석 결과 |
| citations | TEXT | 참고 자료 목록 |
| created_at | TEXT | 생성 시간 |

**Primary Key**: (ticker, date)

## 테스트

```bash
cd /home/hyeonbeom/stock-analysis-dashboard
python3 test_perplexity.py
```

테스트 스크립트는 다음을 검증합니다:
- ✅ API 키 정상 작동 여부
- ✅ 분석 결과 생성
- ✅ 캐싱 시스템 작동
- ✅ 결과 일관성

## 주의사항

1. **API 사용량**: Perplexity API는 유료 서비스입니다. 사용량을 확인하세요.
2. **캐싱**: 동일한 분석은 캐시에서 불러오므로 API 호출 횟수를 절약합니다.
3. **에러 처리**: API 키가 없거나 잘못된 경우 안내 메시지가 표시됩니다.

## 문제 해결

### "API 키 오류" 발생 시
- `.env` 파일이 프로젝트 루트에 있는지 확인
- `PERPLEXITY_API_KEY` 값이 올바른지 확인
- API 키에 공백이나 따옴표가 없는지 확인

### "분석 실패" 발생 시
- 인터넷 연결 확인
- API 사용량 한도 확인
- 날짜 형식이 YYYY-MM-DD인지 확인

## 개발자 정보

- 모듈: `perplexity_analyzer.py`
- 주요 클래스: `StockAnalyzer`
- 데이터베이스: SQLite3 (`stock_data.db`)
