#!/usr/bin/env python3
"""
JOBY 종목 분석 테스트
"""

from perplexity_analyzer import StockAnalyzer
from datetime import datetime, timedelta

def test_joby():
    """JOBY 종목 테스트"""
    print("="*80)
    print("📊 JOBY 분석 테스트")
    print("="*80)

    try:
        analyzer = StockAnalyzer()

        # 최근 날짜들로 테스트
        test_cases = [
            ("JOBY", "2025-12-02", "BUY"),
            ("JOBY", "2025-12-03", "BUY"),
            ("JOBY", "2025-11-29", "SELL"),
        ]

        for ticker, date, signal in test_cases:
            print(f"\n{'='*80}")
            print(f"🔍 {ticker} - {date} ({signal})")
            print('='*80)

            result = analyzer.analyze_stock_price_movement(
                ticker=ticker,
                date=date,
                signal_type=signal
            )

            if result['success']:
                cached_text = " (캐시됨 ✓)" if result.get('cached') else " (신규 조회)"
                print(f"✅ 분석 성공{cached_text}")
                print(f"\n📝 분석 결과:")
                print("-"*80)
                print(result['analysis'])
                print("-"*80)

                if result.get('citations'):
                    print(f"\n📚 참고 자료 ({len(result['citations'])}개):")
                    for i, citation in enumerate(result['citations'][:5], 1):
                        # URL만 간단히 표시
                        citation_short = citation[:80] + "..." if len(citation) > 80 else citation
                        print(f"  {i}. {citation_short}")
            else:
                print(f"❌ 분석 실패: {result.get('error')}")

            print()

    except ValueError as e:
        print(f"\n❌ API 키 오류: {e}")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_joby()
