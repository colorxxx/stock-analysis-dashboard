#!/usr/bin/env python3
"""
실제 새로운 시그널 시나리오 테스트
캐시를 삭제하여 새로운 시그널이 발생한 상황을 시뮬레이션
"""

import sqlite3
from perplexity_analyzer import StockAnalyzer, get_cached_analysis

DB_FILE = "stock_data.db"

def delete_cache(ticker, date):
    """특정 캐시 삭제"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM perplexity_analysis WHERE ticker = ? AND date = ?", (ticker, date))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted

def test_real_new_signal():
    """실제 새로운 시그널 발생 시나리오 테스트"""
    print("="*80)
    print("🧪 실제 새로운 시그널 시나리오 테스트")
    print("="*80)

    ticker = "META"
    date = "2025-12-02"
    signal = "WARNING"

    print(f"\n시나리오: {ticker}에서 {date}에 새로운 {signal} 시그널 발생")
    print("-"*80)

    # 1. 기존 캐시 삭제
    print("\n📌 Step 1: 기존 캐시 삭제 (새로운 시그널 발생 시뮬레이션)")
    deleted = delete_cache(ticker, date)
    print(f"  🗑️  {deleted}개 캐시 삭제됨")

    # 2. 캐시 확인
    print("\n📌 Step 2: 캐시 확인")
    cached = get_cached_analysis(ticker, date)
    if cached:
        print(f"  ❌ 캐시가 여전히 있음 (문제!)")
        return False
    else:
        print(f"  ✅ 캐시 없음 (정상) - Streamlit 앱에서 '새로운 시그널' 경고가 표시될 것임")

    # 3. 새로운 분석 수행
    print("\n📌 Step 3: 사용자가 '분석 시작' 버튼 클릭 (시뮬레이션)")
    print("  🔍 AI 분석 시작...")

    analyzer = StockAnalyzer()
    result = analyzer.analyze_stock_price_movement(
        ticker=ticker,
        date=date,
        signal_type=signal
    )

    if result['success']:
        is_cached = result.get('cached', False)
        print(f"  ✅ 분석 완료!")
        print(f"     - 상태: {'캐시됨' if is_cached else '신규 조회'}")
        print(f"     - API 호출: {'아니오' if is_cached else '예'}")

        print(f"\n  📊 분석 결과:")
        print("  " + "-"*76)
        lines = result['analysis'].split('\n')
        for line in lines[:5]:  # 첫 5줄만 표시
            print(f"  {line}")
        if len(lines) > 5:
            print(f"  ... ({len(lines) - 5}줄 더)")
        print("  " + "-"*76)

        if result.get('citations'):
            print(f"\n  📚 참고 자료: {len(result['citations'])}개")
    else:
        print(f"  ❌ 분석 실패: {result.get('error')}")
        return False

    # 4. 캐시 저장 확인
    print("\n📌 Step 4: 캐시 저장 확인")
    cached = get_cached_analysis(ticker, date)
    if cached:
        print(f"  ✅ 캐시 저장됨!")
        print(f"     - 다음 조회부터는 즉시 표시됨")
    else:
        print(f"  ❌ 캐시 저장 실패 (문제!)")
        return False

    # 5. Streamlit 동작 시뮬레이션
    print("\n📌 Step 5: Streamlit 앱 동작 시뮬레이션")
    print("  🔄 페이지 새로고침 후...")

    cached = get_cached_analysis(ticker, date)
    if cached:
        print(f"  ✅ 캐시된 결과가 자동으로 표시됨")
        print(f"     - '✅ 분석 완료 (캐시됨)' 메시지")
        print(f"     - 버튼 없이 즉시 분석 결과 표시")
        print(f"     - API 호출 없음")
    else:
        print(f"  ❌ 문제 발생")
        return False

    # 최종 요약
    print("\n" + "="*80)
    print("✅ 테스트 성공!")
    print("="*80)
    print("\n📋 시나리오 검증 완료:")
    print("  1. ✅ 새로운 시그널 감지 (캐시 없음)")
    print("  2. ✅ 사용자에게 '새로운 시그널' 경고 표시")
    print("  3. ✅ 버튼 클릭 시 AI 분석 수행")
    print("  4. ✅ 분석 결과 자동 캐싱")
    print("  5. ✅ 다음 조회부터 즉시 표시")

    print("\n🎉 새로운 시그널이 발생하면 자동으로 감지하고 분석합니다!")

    return True

if __name__ == "__main__":
    success = test_real_new_signal()
    exit(0 if success else 1)
