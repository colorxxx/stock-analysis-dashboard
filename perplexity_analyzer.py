#!/usr/bin/env python3
"""
Perplexity API를 사용한 주식 분석 모듈
"""

import os
import requests
import sqlite3
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 데이터베이스 파일
DB_FILE = "stock_data.db"


def init_analysis_cache_db():
    """분석 결과 캐시 테이블 초기화"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS perplexity_analysis (
            ticker TEXT,
            date TEXT,
            analysis TEXT,
            citations TEXT,
            created_at TEXT,
            PRIMARY KEY (ticker, date)
        )
    ''')

    conn.commit()
    conn.close()


def get_cached_analysis(ticker: str, date: str) -> Optional[dict]:
    """캐시된 분석 결과 가져오기"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT analysis, citations, created_at
        FROM perplexity_analysis
        WHERE ticker = ? AND date = ?
    ''', (ticker, date))

    result = cursor.fetchone()
    conn.close()

    if result:
        return {
            'success': True,
            'ticker': ticker,
            'date': date,
            'analysis': result[0],
            'citations': eval(result[1]) if result[1] else [],
            'cached': True,
            'timestamp': result[2]
        }

    return None


def save_analysis_to_cache(ticker: str, date: str, analysis: str, citations: list):
    """분석 결과를 캐시에 저장"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO perplexity_analysis
        (ticker, date, analysis, citations, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (ticker, date, analysis, str(citations), datetime.now().isoformat()))

    conn.commit()
    conn.close()


class StockAnalyzer:
    """Perplexity API를 사용한 주식 분석기"""

    def __init__(self, api_key: Optional[str] = None):
        """
        초기화

        Args:
            api_key: Perplexity API 키 (없으면 환경변수에서 가져옴)
        """
        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Perplexity API 키가 필요합니다. "
                "PERPLEXITY_API_KEY 환경변수를 설정하세요."
            )

        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def analyze_stock_price_movement(
        self,
        ticker: str,
        date: str,
        signal_type: Optional[str] = None
    ) -> dict:
        """
        주식 가격 변동 이유 분석

        Args:
            ticker: 주식 티커 심볼 (예: AAPL, TSLA)
            date: 분석 날짜 (YYYY-MM-DD)
            signal_type: 시그널 타입 (BUY, SELL, STRONG BUY, WARNING)

        Returns:
            분석 결과 딕셔너리
        """
        # 캐시 확인
        cached = get_cached_analysis(ticker, date)
        if cached:
            return cached

        # 한국 주식 여부 확인
        is_korean = ticker.endswith('.KS') or ticker.endswith('.KQ')

        # 프롬프트 구성
        prompt = self._build_prompt(ticker, is_korean, date, signal_type)

        # API 요청
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a financial news analyst. Search the web for recent news and provide specific information. Focus only on news and fundamentals, not technical analysis."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1500,
            "return_citations": True,
            "search_recency_filter": "month"
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            parsed_result = self._parse_response(result, ticker, date)

            # 성공한 경우 캐시에 저장
            if parsed_result['success']:
                save_analysis_to_cache(
                    ticker,
                    date,
                    parsed_result['analysis'],
                    parsed_result.get('citations', [])
                )

            return parsed_result

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "ticker": ticker,
                "date": date,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _build_prompt(
        self,
        ticker: str,
        is_korean: bool,
        date: str,
        signal_type: Optional[str] = None
    ) -> str:
        """분석용 프롬프트 생성"""
        if is_korean:
            return f"""
{ticker} 주식의 {date} 전후 뉴스를 검색하세요.

검색 결과를 바탕으로 **3-5문장**으로 설명:
- {date} 전후 어떤 뉴스/실적/발표가 있었나요?
- 왜 주가가 {'올랐나요' if signal_type in ['BUY', 'STRONG BUY'] else '떨어졌나요'}?
- 구체적인 숫자(실적, 계약 규모 등)가 있다면 포함하세요

**금지사항**: 차트, 이동평균선, RSI, MACD 등 기술적 용어 금지. "접근 불가" 같은 핑계 금지.

한국어로 답변.
"""
        else:
            return f"""
Search for {ticker} stock news around {date}.

Based on search results, explain in 3-5 sentences:
- What news/earnings/announcements happened around {date}?
- Why did stock price {'rise' if signal_type in ['BUY', 'STRONG BUY'] else 'fall'}?
- Include specific numbers (earnings, deal size, etc.) if available

**Prohibited**: Charts, moving averages, RSI, MACD, technical terms. No excuses like "cannot access".

Answer in Korean.
"""

    def _parse_response(self, result: dict, ticker: str, date: str) -> dict:
        """API 응답 파싱"""
        try:
            content = result['choices'][0]['message']['content']
            citations = result.get('citations', [])

            return {
                "success": True,
                "ticker": ticker,
                "date": date,
                "analysis": content,
                "citations": citations,
                "cached": False,
                "timestamp": datetime.now().isoformat()
            }
        except (KeyError, IndexError) as e:
            return {
                "success": False,
                "ticker": ticker,
                "date": date,
                "error": f"응답 파싱 실패: {str(e)}",
                "raw_response": result,
                "timestamp": datetime.now().isoformat()
            }


# DB 초기화
init_analysis_cache_db()
