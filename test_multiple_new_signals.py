#!/usr/bin/env python3
"""
여러 종목의 새로운 시그널 테스트
"""

import sqlite3
from perplexity_analyzer import StockAnalyzer, get_cached_analysis
import time

DB_FILE = "stock_data.db"

def test_multiple_new_signals():
    """여러 종목의 새로운 시그널 테스트"""
    print("="*80)
    print("🧪 여러 종목 새로운 시그널 테스트")
    print("="*80)

    # 테스트할 종목들 (캐시 삭제하여 새로운 시그널 시뮬레이션)
    test_cases = [
        ("NVDA", "2025-11-13", "STRONG BUY"),
        ("AAPL", "2025-10-17", "BUY"),
        ("META", "2025-12-02", "WARNING"),
    ]

    analyzer = StockAnalyzer()
    results = []

    for idx, (ticker, date, signal) in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"[{idx}/{len(test_cases)}] {ticker} - {date} ({signal})")
        print('='*80)

        # 1. 캐시 확인
        cached = get_cached_analysis(ticker, date)
        cache_status = "✅ 캐시 있음" if cached else "❌ 캐시 없음"
        print(f"캐시 상태: {cache_status}")

        # 2. 캐시가 없다면 (또는 삭제했다면) 새로운 분석
        if not cached:
            print(f"🔍 새로운 분석 시작...")

            result = analyzer.analyze_stock_price_movement(
                ticker=ticker,
                date=date,
                signal_type=signal
            )

            if result['success']:
                is_cached = result.get('cached', False)
                status = "캐시됨" if is_cached else "신규 조회"
                print(f"✅ 분석 완료 ({status})")

                # 분석 결과 미리보기
                preview = result['analysis'][:200] + "..." if len(result['analysis']) > 200 else result['analysis']
                print(f"\n📊 분석 결과:")
                print("-"*80)
                print(preview)
                print("-"*80)

                results.append({
                    'ticker': ticker,
                    'date': date,
                    'signal': signal,
                    'success': True,
                    'cached': is_cached
                })
            else:
                print(f"❌ 분석 실패: {result.get('error')}")
                results.append({
                    'ticker': ticker,
                    'date': date,
                    'signal': signal,
                    'success': False,
                    'cached': False
                })

            # API 호출 간격
            if idx < len(test_cases):
                time.sleep(2)
        else:
            print(f"✅ 이미 캐시된 결과 사용")
            preview = cached['analysis'][:200] + "..." if len(cached['analysis']) > 200 else cached['analysis']
            print(f"\n📊 분석 결과:")
            print("-"*80)
            print(preview)
            print("-"*80)

            results.append({
                'ticker': ticker,
                'date': date,
                'signal': signal,
                'success': True,
                'cached': True
            })

    # 최종 요약
    print("\n" + "="*80)
    print("📊 테스트 결과 요약")
    print("="*80)

    success_count = sum(1 for r in results if r['success'])
    cached_count = sum(1 for r in results if r['cached'])
    new_count = sum(1 for r in results if r['success'] and not r['cached'])

    print(f"\n총 {len(results)}개 종목:")
    print(f"  ✅ 성공: {success_count}")
    print(f"  💾 캐시 사용: {cached_count}")
    print(f"  🆕 신규 조회: {new_count}")

    print("\n상세:")
    for r in results:
        status_emoji = "✅" if r['success'] else "❌"
        cache_emoji = "💾" if r['cached'] else "🆕"
        print(f"  {status_emoji} {cache_emoji} {r['ticker']} ({r['date']}) - {r['signal']}")

    print("\n" + "="*80)
    print("🎉 테스트 완료!")
    print("="*80)

    return all(r['success'] for r in results)

if __name__ == "__main__":
    success = test_multiple_new_signals()
    exit(0 if success else 1)
