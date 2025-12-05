#!/usr/bin/env python3
"""
모든 종목의 시그널 발생일에 대해 AI 분석을 일괄 조회하고 캐싱
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from perplexity_analyzer import StockAnalyzer
import time
import sys

# 기본 티커 리스트 (app.py의 기본값과 동일)
DEFAULT_TICKERS = "CRDO,INOD,SMCI,OSCR,IREN,MSTR,BMNR,XYZ,SNPS,BE,JOBY,VRT,NUKZ,SNOW,BLDP,TLS,AAPL,MSFT,GOOGL,TSLA,AMZN,NVDA,META,CRWD,INOD,BBAI,ANET,AEHR,CEVA,IBM,NICE,ADBE,STGW,AUDC,SPR,TNXP,ENPH,SMCI,KOPN,BLDP,TLS,SSYS,LQDT,ABSI,SLDP,INVZ,VVX,DEFT,BLNK,ARDX,SGML,SEZL,QUBT,RGTI,QBTS,CHGG,SOFI,SHOP,COIN,HOOD,TSM,AMD,MU,PLTR,AVGO,RKLB,ASTS,APP,QS,NEE,FLNC,EOSE,CCJ,SMR,CEG,VST,OKLO,ORCL,APLD,AIRO,CIFR,NBIS,IONQ,CRCL,BITI"

def get_cached_stock_data(ticker, period="6mo"):
    """주가 데이터 가져오기"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        print(f"  ❌ {ticker} 데이터 가져오기 실패: {e}")
        return None

def analyze_signal(df):
    """시그널 분석 (app.py의 analyze_signal 함수 간소화 버전)"""
    df['MA5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['MA20'] = df['Close'].ewm(span=20, adjust=False).mean()

    df['Signal'] = 0
    df['MA5_prev'] = df['MA5'].shift(1)
    df['MA20_prev'] = df['MA20'].shift(1)

    # 골든크로스
    golden_cross = (df['MA5_prev'] < df['MA20_prev']) & (df['MA5'] > df['MA20'])
    df.loc[golden_cross, 'Signal'] = 1

    # 데드크로스
    dead_cross = (df['MA5_prev'] > df['MA20_prev']) & (df['MA5'] < df['MA20'])
    df.loc[dead_cross, 'Signal'] = -1

    # 현재 상태
    last_ma5 = df['MA5'].iloc[-1]
    last_ma20 = df['MA20'].iloc[-1]

    # 차이 계산
    diff_pct = ((last_ma5 - last_ma20) / last_ma20) * 100
    is_close = abs(diff_pct) < 2.0

    if last_ma5 > last_ma20:
        if is_close:
            status = "WARNING"
        else:
            status = "BUY"
    else:
        if is_close:
            status = "STRONG BUY"
        else:
            status = "SELL"

    # 최근 시그널
    all_signals = df[df['Signal'] != 0]
    if not all_signals.empty:
        last_signal = all_signals.iloc[-1]
        last_signal_date = last_signal.name.strftime('%Y-%m-%d')
        last_signal_type = last_signal['Signal']
    else:
        last_signal_date = None
        last_signal_type = 0

    return {
        'status': status,
        'last_signal_date': last_signal_date,
        'last_signal_type': last_signal_type
    }

def batch_analyze_all(tickers_input=None, delay=2):
    """
    모든 종목에 대해 일괄 AI 분석 수행

    Args:
        tickers_input: 티커 문자열 (쉼표로 구분) 또는 None (기본값 사용)
        delay: API 호출 사이 대기 시간 (초)
    """
    print("="*80)
    print("📊 모든 종목 AI 분석 일괄 조회 및 캐싱")
    print("="*80)

    # 티커 리스트 파싱
    if tickers_input is None:
        tickers_input = DEFAULT_TICKERS

    tickers = list(set([t.strip().upper() for t in tickers_input.split(',') if t.strip()]))

    print(f"\n📋 총 {len(tickers)}개 종목 분석 시작")
    print(f"⏱️  API 호출 간격: {delay}초")
    print(f"🕐 예상 소요 시간: 약 {len(tickers) * delay / 60:.1f}분")

    # 분석기 초기화
    try:
        analyzer = StockAnalyzer()
    except ValueError as e:
        print(f"\n❌ API 키 오류: {e}")
        print("💡 .env 파일에 PERPLEXITY_API_KEY를 설정해주세요.")
        return

    # 통계 변수
    total = len(tickers)
    success_count = 0
    cached_count = 0
    no_signal_count = 0
    error_count = 0

    start_time = time.time()

    print("\n" + "="*80)
    print("시작 시간:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("="*80 + "\n")

    for idx, ticker in enumerate(tickers, 1):
        print(f"[{idx}/{total}] {ticker} 처리 중...")

        try:
            # 1. 주가 데이터 가져오기
            df = get_cached_stock_data(ticker)
            if df is None or df.empty:
                print(f"  ⚠️  주가 데이터 없음")
                error_count += 1
                continue

            # 2. 시그널 분석
            analysis = analyze_signal(df)

            if not analysis['last_signal_date']:
                print(f"  ℹ️  시그널 발생 내역 없음")
                no_signal_count += 1
                continue

            # 3. 시그널 타입 결정
            signal_type_map = {1: 'BUY', -1: 'SELL'}
            signal_type = signal_type_map.get(analysis['last_signal_type'], None)

            if analysis['status'] == 'STRONG BUY':
                signal_type = 'STRONG BUY'
            elif analysis['status'] == 'WARNING':
                signal_type = 'WARNING'

            print(f"  📅 시그널: {analysis['last_signal_date']} ({signal_type})")

            # 4. AI 분석 조회
            result = analyzer.analyze_stock_price_movement(
                ticker=ticker,
                date=analysis['last_signal_date'],
                signal_type=signal_type
            )

            if result['success']:
                if result.get('cached'):
                    print(f"  ✅ 캐시됨")
                    cached_count += 1
                else:
                    print(f"  ✅ 신규 조회 완료")
                    success_count += 1
                    # API 호출 간격 대기
                    if idx < total:
                        time.sleep(delay)
            else:
                print(f"  ❌ 분석 실패: {result.get('error', 'Unknown')[:50]}")
                error_count += 1

        except KeyboardInterrupt:
            print("\n\n⚠️  사용자에 의해 중단되었습니다.")
            break
        except Exception as e:
            print(f"  ❌ 오류: {str(e)[:50]}")
            error_count += 1

        print()

    # 결과 요약
    elapsed_time = time.time() - start_time

    print("="*80)
    print("📊 분석 완료!")
    print("="*80)
    print(f"\n⏱️  총 소요 시간: {elapsed_time / 60:.1f}분")
    print(f"\n📈 결과 요약:")
    print(f"  - 총 종목 수: {total}")
    print(f"  - 신규 조회: {success_count}")
    print(f"  - 캐시 사용: {cached_count}")
    print(f"  - 시그널 없음: {no_signal_count}")
    print(f"  - 오류: {error_count}")
    print(f"\n✅ 성공률: {((success_count + cached_count) / total * 100):.1f}%")
    print("="*80)

def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description='모든 종목에 대해 AI 분석 일괄 조회')
    parser.add_argument('--tickers', type=str, help='티커 리스트 (쉼표로 구분)')
    parser.add_argument('--delay', type=int, default=2, help='API 호출 간격 (초, 기본값: 2)')

    args = parser.parse_args()

    batch_analyze_all(tickers_input=args.tickers, delay=args.delay)

if __name__ == "__main__":
    main()
