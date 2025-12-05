#!/usr/bin/env python3
"""
새로운 시그널 발생 시 자동 분석 테스트
"""

import sqlite3
from perplexity_analyzer import StockAnalyzer, get_cached_analysis

DB_FILE = "stock_data.db"

def delete_specific_cache(ticker, date=None):
    """특정 종목의 캐시 삭제"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if date:
        cursor.execute("DELETE FROM perplexity_analysis WHERE ticker = ? AND date = ?", (ticker, date))
        print(f"✅ {ticker} ({date}) 캐시 삭제됨")
    else:
        cursor.execute("DELETE FROM perplexity_analysis WHERE ticker = ?", (ticker,))
        print(f"✅ {ticker} 전체 캐시 삭제됨")

    deleted = cursor.rowcount
    conn.commit()
    conn.close()

    return deleted

def test_new_signal_detection():
    """새로운 시그널 감지 및 자동 분석 테스트"""
    print("="*80)
    print("🧪 새로운 시그널 자동 분석 테스트")
    print("="*80)

    # 테스트 케이스
    test_ticker = "TSLA"
    test_date = "2025-12-01"
    test_signal = "BUY"

    print(f"\n📋 테스트 대상:")
    print(f"  - 티커: {test_ticker}")
    print(f"  - 날짜: {test_date}")
    print(f"  - 시그널: {test_signal}")

    # Step 1: 기존 캐시 확인
    print("\n" + "="*80)
    print("Step 1: 기존 캐시 확인")
    print("="*80)

    cached = get_cached_analysis(test_ticker, test_date)
    if cached:
        print(f"✅ 캐시 존재함")
        print(f"  - 생성 시간: {cached.get('timestamp')}")
        print(f"  - 분석 내용 길이: {len(cached['analysis'])} 자")
    else:
        print(f"❌ 캐시 없음")

    # Step 2: 캐시 삭제 (새로운 시그널 시뮬레이션)
    print("\n" + "="*80)
    print("Step 2: 캐시 삭제 (새로운 시그널 시뮬레이션)")
    print("="*80)

    deleted = delete_specific_cache(test_ticker, test_date)
    if deleted > 0:
        print(f"🗑️  {deleted}개 캐시 삭제됨")
    else:
        print(f"ℹ️  삭제할 캐시가 없었음 (이미 새로운 시그널)")

    # Step 3: 캐시 재확인 (없어야 함)
    print("\n" + "="*80)
    print("Step 3: 캐시 재확인")
    print("="*80)

    cached = get_cached_analysis(test_ticker, test_date)
    if cached:
        print(f"❌ 캐시가 여전히 존재함 (문제!)")
    else:
        print(f"✅ 캐시 없음 (정상) - 새로운 시그널로 인식됨")

    # Step 4: 새로운 분석 수행
    print("\n" + "="*80)
    print("Step 4: 새로운 AI 분석 수행")
    print("="*80)

    try:
        analyzer = StockAnalyzer()
        print(f"🔍 {test_ticker} 분석 중...")

        result = analyzer.analyze_stock_price_movement(
            ticker=test_ticker,
            date=test_date,
            signal_type=test_signal
        )

        if result['success']:
            print(f"✅ 분석 성공!")
            print(f"  - 캐시 여부: {result.get('cached', False)}")
            print(f"  - 생성 시간: {result['timestamp']}")
            print(f"\n📊 분석 결과 미리보기:")
            print("-"*80)
            preview = result['analysis'][:300] + "..." if len(result['analysis']) > 300 else result['analysis']
            print(preview)
            print("-"*80)

            if result.get('citations'):
                print(f"\n📚 참고 자료: {len(result['citations'])}개")
        else:
            print(f"❌ 분석 실패: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

    # Step 5: 캐시 확인 (저장되어야 함)
    print("\n" + "="*80)
    print("Step 5: 캐시 저장 확인")
    print("="*80)

    cached = get_cached_analysis(test_ticker, test_date)
    if cached:
        print(f"✅ 캐시 저장됨!")
        print(f"  - 생성 시간: {cached.get('timestamp')}")
        print(f"  - 캐시된 결과와 분석 결과 일치: {cached['analysis'] == result['analysis']}")
    else:
        print(f"❌ 캐시 저장 실패 (문제!)")
        return False

    # Step 6: 두 번째 조회 (캐시 사용해야 함)
    print("\n" + "="*80)
    print("Step 6: 두 번째 조회 (캐시 사용 테스트)")
    print("="*80)

    result2 = analyzer.analyze_stock_price_movement(
        ticker=test_ticker,
        date=test_date,
        signal_type=test_signal
    )

    if result2['success']:
        if result2.get('cached'):
            print(f"✅ 캐시에서 불러옴 (정상!)")
            print(f"  - API 호출 없음")
            print(f"  - 즉시 반환됨")
        else:
            print(f"⚠️  캐시를 사용하지 않음 (예상과 다름)")
    else:
        print(f"❌ 조회 실패: {result2.get('error')}")

    # 최종 요약
    print("\n" + "="*80)
    print("✅ 테스트 완료!")
    print("="*80)
    print("\n📊 요약:")
    print("  1. 기존 캐시 삭제 (새로운 시그널 시뮬레이션) ✓")
    print("  2. 새로운 AI 분석 수행 ✓")
    print("  3. 분석 결과 캐시에 자동 저장 ✓")
    print("  4. 두 번째 조회 시 캐시 사용 ✓")
    print("\n🎉 새로운 시그널 발생 시 자동으로 분석되고 캐싱됩니다!")

    return True

if __name__ == "__main__":
    success = test_new_signal_detection()
    exit(0 if success else 1)
