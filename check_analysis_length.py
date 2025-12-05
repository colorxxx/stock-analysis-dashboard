#!/usr/bin/env python3
"""
분석 결과 길이 및 품질 확인
"""

import sqlite3

DB_FILE = "stock_data.db"

def check_analysis_quality():
    """분석 결과 길이 및 품질 확인"""
    print("="*80)
    print("📊 분석 결과 품질 확인")
    print("="*80)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT ticker, date, analysis, LENGTH(analysis) as length, created_at
        FROM perplexity_analysis
        ORDER BY created_at DESC
        LIMIT 10
    ''')

    results = cursor.fetchall()
    conn.close()

    if not results:
        print("\n❌ 캐시된 분석 결과가 없습니다.")
        return

    print(f"\n📋 최근 10개 분석 결과:\n")

    total_length = 0
    for idx, (ticker, date, analysis, length, created_at) in enumerate(results, 1):
        total_length += length

        print(f"{idx}. {ticker} ({date})")
        print(f"   📏 길이: {length:,}자")
        print(f"   🕐 생성: {created_at[:19]}")
        print(f"   📝 미리보기:")

        # 첫 200자 표시
        preview = analysis[:200].replace('\n', ' ')
        print(f"      {preview}...")
        print()

    avg_length = total_length / len(results)

    print("="*80)
    print(f"📊 통계")
    print("="*80)
    print(f"평균 길이: {avg_length:,.0f}자")
    print(f"최소 길이: {min(r[3] for r in results):,}자")
    print(f"최대 길이: {max(r[3] for r in results):,}자")
    print(f"총 {len(results)}개 분석")

    # 품질 평가
    print(f"\n💡 평가:")
    if avg_length > 1000:
        print("  ✅ 매우 상세한 분석 (1000자 이상)")
    elif avg_length > 500:
        print("  ✅ 적절한 분석 (500-1000자)")
    elif avg_length > 300:
        print("  ⚠️  간단한 분석 (300-500자)")
    else:
        print("  ❌ 너무 짧은 분석 (300자 미만)")

if __name__ == "__main__":
    check_analysis_quality()
