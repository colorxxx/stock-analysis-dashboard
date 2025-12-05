#!/usr/bin/env python3
"""
JOBY 간단 테스트
"""

from perplexity_analyzer import StockAnalyzer

analyzer = StockAnalyzer()

# 12월 4일로 테스트
result = analyzer.analyze_stock_price_movement(
    ticker="JOBY",
    date="2025-12-04",
    signal_type="BUY"
)

print("="*80)
print(f"JOBY - 2025-12-04 (BUY)")
print("="*80)

if result['success']:
    print(f"✅ 성공 (캐시: {result.get('cached', False)})")
    print("\n📊 분석 결과:")
    print("-"*80)
    print(result['analysis'])
    print("-"*80)

    if result.get('citations'):
        print(f"\n📚 참고 자료 ({len(result['citations'])}개)")
else:
    print(f"❌ 실패: {result.get('error')}")
