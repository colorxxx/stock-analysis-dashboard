#!/usr/bin/env python3
"""
최근 날짜로 간단한 분석 테스트
"""

from perplexity_analyzer import StockAnalyzer
from datetime import datetime, timedelta

def test_recent_analysis():
    """최근 날짜로 간단한 분석 테스트"""
    print("="*80)
    print("📊 Perplexity 간단 분석 테스트 (최근 날짜)")
    print("="*80)

    try:
        analyzer = StockAnalyzer()

        # 최근 날짜 테스트
        test_cases = [
            ("NVDA", "2025-12-02", "BUY"),
            ("TSLA", "2025-12-03", "SELL"),
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
                print(f"✅ 분석 성공 (캐시: {result.get('cached', False)})")
                print(f"\n📝 분석 결과:")
                print("-"*80)
                print(result['analysis'])
                print("-"*80)

                if result.get('citations'):
                    print(f"\n📚 참고 자료 ({len(result['citations'])}개):")
                    for i, citation in enumerate(result['citations'][:3], 1):
                        print(f"  {i}. {citation}")
            else:
                print(f"❌ 분석 실패: {result.get('error')}")

            print()

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_recent_analysis()
