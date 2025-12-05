#!/usr/bin/env python3
"""
Perplexity 분석기 테스트 스크립트
"""

from perplexity_analyzer import StockAnalyzer
from datetime import datetime, timedelta

def test_analyzer():
    """분석기 기본 테스트"""
    print("="*80)
    print("📊 Perplexity 분석기 테스트")
    print("="*80)

    try:
        # 분석기 초기화
        analyzer = StockAnalyzer()
        print("✅ StockAnalyzer 초기화 성공")

        # 테스트 케이스
        test_ticker = "AAPL"
        test_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        print(f"\n🔍 테스트 분석 시작:")
        print(f"   - 티커: {test_ticker}")
        print(f"   - 날짜: {test_date}")
        print(f"   - 시그널: BUY")

        # 첫 번째 조회 (API 호출)
        print("\n1️⃣ 첫 번째 조회 (API 호출)...")
        result1 = analyzer.analyze_stock_price_movement(
            ticker=test_ticker,
            date=test_date,
            signal_type="BUY"
        )

        if result1['success']:
            print(f"✅ 분석 성공!")
            print(f"   - 캐시 여부: {result1.get('cached', False)}")
            print(f"   - 분석 내용 길이: {len(result1['analysis'])} 자")
            print(f"   - 참고 자료 수: {len(result1.get('citations', []))}")
            print(f"\n📝 분석 미리보기:")
            print("-"*80)
            print(result1['analysis'][:300] + "..." if len(result1['analysis']) > 300 else result1['analysis'])
            print("-"*80)
        else:
            print(f"❌ 분석 실패: {result1.get('error')}")
            return

        # 두 번째 조회 (캐시 확인)
        print("\n2️⃣ 두 번째 조회 (캐시 확인)...")
        result2 = analyzer.analyze_stock_price_movement(
            ticker=test_ticker,
            date=test_date,
            signal_type="BUY"
        )

        if result2['success']:
            if result2.get('cached'):
                print("✅ 캐시에서 성공적으로 불러왔습니다!")
            else:
                print("⚠️ 캐시를 사용하지 않았습니다.")

            # 내용 일치 확인
            if result1['analysis'] == result2['analysis']:
                print("✅ 두 결과의 내용이 일치합니다.")
            else:
                print("⚠️ 두 결과의 내용이 다릅니다.")

        print("\n" + "="*80)
        print("🎉 모든 테스트 완료!")
        print("="*80)

    except ValueError as e:
        print(f"\n❌ API 키 오류: {e}")
        print("💡 .env 파일에 PERPLEXITY_API_KEY를 설정해주세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_analyzer()
