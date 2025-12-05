#!/usr/bin/env python3
"""
Daily update script to analyze new signals
Run this via cron/scheduler after market close
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
from perplexity_analyzer import StockAnalyzer, get_cached_analysis
import time
import sqlite3

DB_FILE = "stock_data.db"

# Same DEFAULT_TICKERS from app.py
DEFAULT_TICKERS = "CRDO,INOD,SMCI,OSCR,IREN,MSTR,BMNR,XYZ,SNPS,BE,JOBY,VRT,NUKZ,SNOW,BLDP,TLS,AAPL,MSFT,GOOGL,TSLA,AMZN,NVDA,META,CRWD,INOD,BBAI,ANET,AEHR,CEVA,IBM,NICE,ADBE,STGW,AUDC,SPR,TNXP,ENPH,SMCI,KOPN,BLDP,TLS,SSYS,LQDT,ABSI,SLDP,INVZ,VVX,DEFT,BLNK,ARDX,SGML,SEZL,QUBT,RGTI,QBTS,CHGG,SOFI,SHOP,COIN,HOOD,TSM,AMD,MU,PLTR,AVGO,RKLB,ASTS,APP,QS,NEE,FLNC,EOSE,CCJ,SMR,CEG,VST,OKLO,ORCL,APLD,AIRO,CIFR,NBIS,IONQ,CRCL,BITI"


def init_signal_state_table():
    """Create table to track signal history"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS signal_state (
            ticker TEXT PRIMARY KEY,
            last_signal_date TEXT,
            last_signal_type TEXT,
            last_checked TEXT
        )
    ''')
    conn.commit()
    conn.close()


def get_previous_signal_state(ticker):
    """Get last known signal date for ticker"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT last_signal_date, last_signal_type FROM signal_state WHERE ticker = ?',
        (ticker,)
    )
    result = cursor.fetchone()
    conn.close()
    return result if result else (None, None)


def update_signal_state(ticker, signal_date, signal_type):
    """Update signal state after analysis"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO signal_state (ticker, last_signal_date, last_signal_type, last_checked)
        VALUES (?, ?, ?, ?)
    ''', (ticker, signal_date, signal_type, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_cached_stock_data(ticker, period="6mo"):
    """Fetch stock data"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty:
            return None
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except:
        return None


def analyze_signal(df):
    """Detect EMA crossovers (simplified from app.py)"""
    df['MA5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['MA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['Signal'] = 0
    df['MA5_prev'] = df['MA5'].shift(1)
    df['MA20_prev'] = df['MA20'].shift(1)

    golden_cross = (df['MA5_prev'] < df['MA20_prev']) & (df['MA5'] > df['MA20'])
    df.loc[golden_cross, 'Signal'] = 1

    dead_cross = (df['MA5_prev'] > df['MA20_prev']) & (df['MA5'] < df['MA20'])
    df.loc[dead_cross, 'Signal'] = -1

    last_ma5 = df['MA5'].iloc[-1]
    last_ma20 = df['MA20'].iloc[-1]
    diff_pct = ((last_ma5 - last_ma20) / last_ma20) * 100
    is_close = abs(diff_pct) < 2.0

    if last_ma5 > last_ma20:
        status = "WARNING" if is_close else "BUY"
    else:
        status = "STRONG BUY" if is_close else "SELL"

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


def daily_update():
    """Main update function"""
    print("="*80)
    print(f"📊 Daily Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    init_signal_state_table()

    tickers = [t.strip().upper() for t in DEFAULT_TICKERS.split(',') if t.strip()]
    tickers = list(set(tickers))  # Remove duplicates

    analyzer = StockAnalyzer()
    new_count = 0
    cached_count = 0
    error_count = 0

    for idx, ticker in enumerate(tickers, 1):
        print(f"\n[{idx}/{len(tickers)}] {ticker}")

        try:
            # Get current signal
            df = get_cached_stock_data(ticker)
            if df is None:
                print(f"  ⚠️  No data")
                error_count += 1
                continue

            current_signal = analyze_signal(df)
            current_date = current_signal['last_signal_date']

            if not current_date:
                print(f"  ℹ️  No signal")
                continue

            # Get previous signal state
            prev_date, prev_type = get_previous_signal_state(ticker)

            # Check if signal changed
            if prev_date != current_date:
                print(f"  🆕 New signal: {current_date}")

                # Map signal type
                signal_type_map = {1: 'BUY', -1: 'SELL'}
                signal_type = signal_type_map.get(current_signal['last_signal_type'], None)
                if current_signal['status'] == 'STRONG BUY':
                    signal_type = 'STRONG BUY'
                elif current_signal['status'] == 'WARNING':
                    signal_type = 'WARNING'

                # Analyze
                result = analyzer.analyze_stock_price_movement(
                    ticker=ticker,
                    date=current_date,
                    signal_type=signal_type
                )

                if result['success']:
                    print(f"  ✅ Analyzed and cached")
                    new_count += 1
                    update_signal_state(ticker, current_date, str(current_signal['last_signal_type']))
                else:
                    print(f"  ❌ Analysis failed")
                    error_count += 1

                time.sleep(2)  # Rate limiting
            else:
                print(f"  💾 Already cached ({current_date})")
                cached_count += 1
                update_signal_state(ticker, current_date, str(current_signal['last_signal_type']))

        except Exception as e:
            print(f"  ❌ Error: {str(e)[:50]}")
            error_count += 1

    print("\n" + "="*80)
    print("📊 Update Complete")
    print("="*80)
    print(f"  🆕 New analyses: {new_count}")
    print(f"  💾 Cached: {cached_count}")
    print(f"  ❌ Errors: {error_count}")
    print("="*80)


if __name__ == "__main__":
    daily_update()
