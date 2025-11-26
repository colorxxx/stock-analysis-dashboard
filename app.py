import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import requests
from pandas_datareader import data as pdr
import sqlite3

# 페이지 설정

st.set_page_config(

    page_title="주식 지수이동평균선(EMA) 분석",

    page_icon="📈",

    layout="wide"

)

# 데이터베이스 설정
DB_FILE = "stock_data.db"

def init_db():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 주식 데이터 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_data (
            ticker TEXT,
            date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (ticker, date)
        )
    ''')

    # 거시경제 지표 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS macro_data (
            indicator TEXT,
            date TEXT,
            value REAL,
            PRIMARY KEY (indicator, date)
        )
    ''')

    # CNN 공포탐욕지수 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fear_greed (
            date TEXT PRIMARY KEY,
            score REAL,
            rating TEXT
        )
    ''')

    # 기준금리 테이블
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fed_rate (
            date TEXT PRIMARY KEY,
            rate REAL
        )
    ''')

    # 주식 정보 캐시 테이블 (종목명 등)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_info (
            ticker TEXT PRIMARY KEY,
            long_name TEXT,
            description TEXT,
            updated_at TEXT
        )
    ''')

    conn.commit()
    conn.close()

def get_last_date(table, ticker=None, indicator=None):
    """테이블의 마지막 날짜 가져오기"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if table == 'stock_data' and ticker:
        cursor.execute('SELECT MAX(date) FROM stock_data WHERE ticker = ?', (ticker,))
    elif table == 'macro_data' and indicator:
        cursor.execute('SELECT MAX(date) FROM macro_data WHERE indicator = ?', (indicator,))
    elif table == 'fear_greed':
        cursor.execute('SELECT MAX(date) FROM fear_greed')
    elif table == 'fed_rate':
        cursor.execute('SELECT MAX(date) FROM fed_rate')
    else:
        return None

    result = cursor.fetchone()[0]
    conn.close()
    return result

def get_cached_stock_data(ticker, period="1y"):
    """캐시된 주식 데이터 가져오기 및 업데이트"""
    conn = sqlite3.connect(DB_FILE)

    # 기존 데이터 가져오기
    query = 'SELECT * FROM stock_data WHERE ticker = ? ORDER BY date'
    df = pd.read_sql_query(query, conn, params=(ticker,))

    # 마지막 날짜 확인
    last_date = get_last_date('stock_data', ticker=ticker)

    # 필요한 기간 계산
    period_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    days = period_map.get(period, 365)
    start_date = datetime.now() - timedelta(days=days)

    # 업데이트 필요 여부 확인
    if last_date is None:
        # 데이터가 없으면 전체 가져오기
        stock = yf.Ticker(ticker)
        new_df = stock.history(period=period)
        # timezone 제거
        if new_df.index.tz is not None:
            new_df.index = new_df.index.tz_localize(None)
    else:
        last_datetime = pd.to_datetime(last_date)
        today = datetime.now()

        # 오늘 데이터가 이미 있으면 DB 데이터만 반환
        if last_datetime.date() >= today.date():
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df = df[df.index >= start_date]
                df.columns = ['ticker', 'Open', 'High', 'Low', 'Close', 'Volume']
                df = df.drop('ticker', axis=1)
                return df

        # 마지막 날짜 이후 데이터만 가져오기
        stock = yf.Ticker(ticker)
        days_to_fetch = (today - last_datetime).days + 5  # 여유분
        new_df = stock.history(period=f"{days_to_fetch}d")

        # timezone 제거
        if not new_df.empty and new_df.index.tz is not None:
            new_df.index = new_df.index.tz_localize(None)

        if not new_df.empty:
            new_df = new_df[new_df.index > last_datetime]

    # 새 데이터 저장
    if not new_df.empty:
        save_df = new_df.copy()
        save_df['ticker'] = ticker
        save_df['date'] = save_df.index.strftime('%Y-%m-%d')
        save_df = save_df.reset_index(drop=True)
        save_df = save_df[['ticker', 'date', 'Open', 'High', 'Low', 'Close', 'Volume']]
        save_df.columns = ['ticker', 'date', 'open', 'high', 'low', 'close', 'volume']

        save_df.to_sql('stock_data', conn, if_exists='append', index=False)

    # 전체 데이터 다시 가져오기
    df = pd.read_sql_query(query, conn, params=(ticker,))
    conn.close()

    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df[df.index >= start_date]
        df.columns = ['ticker', 'open', 'high', 'low', 'close', 'volume']
        df = df.drop('ticker', axis=1)
        df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    return df

def get_company_description(ticker, info):
    """회사 사업 설명 추출 및 요약 - 한국어"""
    # 수동으로 정리한 주요 종목 정보 (산업 분야 + 한국어 설명)
    manual_company_info = {
        'AAPL': {'industry': '전자제품', 'description': '아이폰, 맥북 등 스마트폰과 컴퓨터 제조'},
        'MSFT': {'industry': '소프트웨어', 'description': '윈도우, 오피스, Azure 클라우드 서비스'},
        'GOOGL': {'industry': '인터넷', 'description': '검색엔진, 광고, 클라우드, AI 서비스'},
        'TSLA': {'industry': '전기차', 'description': '전기 자동차 제조 및 청정 에너지'},
        'AMZN': {'industry': '전자상거래', 'description': '온라인 쇼핑몰 및 AWS 클라우드'},
        'NVDA': {'industry': '반도체', 'description': 'GPU 및 AI 칩 설계'},
        'META': {'industry': '소셜미디어', 'description': '페이스북, 인스타그램, 왓츠앱 운영'},
        'CRWD': {'industry': '보안', 'description': '클라우드 기반 사이버 보안 플랫폼'},
        'INOD': {'industry': '의료기기', 'description': '폐질환 치료 의료기기 개발'},
        'BBAI': {'industry': 'AI', 'description': 'AI 기반 의사결정 분석 플랫폼'},
        'ANET': {'industry': '네트워크', 'description': '데이터센터용 클라우드 네트워킹 솔루션'},
        'AEHR': {'industry': '반도체', 'description': '반도체 테스트 및 검증 장비 제조'},
        'CEVA': {'industry': '반도체', 'description': '무선 연결 및 센서 기술'},
        'IBM': {'industry': 'IT서비스', 'description': '기업용 IT, 클라우드, AI 솔루션'},
        'NICE': {'industry': '소프트웨어', 'description': '고객관리 및 금융범죄 방지 솔루션'},
        'ADBE': {'industry': '소프트웨어', 'description': '포토샵, PDF 등 크리에이티브 소프트웨어'},
        'STGW': {'industry': '보안', 'description': '데이터 보호 및 규정 준수 솔루션'},
        'AUDC': {'industry': '반도체', 'description': '오디오 기술 및 DSP 칩 솔루션'},
        'SPR': {'industry': '방위산업', 'description': '항공우주 및 국방 기술 제조'},
        'TNXP': {'industry': '바이오', 'description': '암 치료제 개발'},
        'ENPH': {'industry': '신재생에너지', 'description': '태양광 마이크로인버터 및 에너지 관리'},
        'SMCI': {'industry': 'IT하드웨어', 'description': '고성능 서버 및 스토리지 솔루션'},
        'KOPN': {'industry': '디스플레이', 'description': '웨어러블 디스플레이 및 광학 시스템'},
        'BLDP': {'industry': '신재생에너지', 'description': '수소연료전지 기술'},
        'TLS': {'industry': '통신', 'description': '통신 및 네트워크 인프라'},
        'SSYS': {'industry': '3D프린팅', 'description': '3D 프린팅 및 적층 제조 솔루션'},
        'LQDT': {'industry': '전자상거래', 'description': '잉여자산 온라인 경매 마켓플레이스'},
        'ABSI': {'industry': '바이오', 'description': '신약 개발'},
        'SLDP': {'industry': '배터리', 'description': '전고체 배터리 기술 개발'},
        'INVZ': {'industry': '자율주행', 'description': '자율주행용 라이다 센서'},
        'VVX': {'industry': '바이오', 'description': '암 치료제 개발'},
        'DEFT': {'industry': '방위산업', 'description': '국방 및 정보 기술 솔루션'},
        'BLNK': {'industry': '전기차', 'description': '전기차 충전 인프라'},
        'ARDX': {'industry': '바이오', 'description': '희귀질환 치료제 개발'},
        'SGML': {'industry': '바이오', 'description': '흡입형 치료제 개발'},
        'SEZL': {'industry': '소프트웨어', 'description': '클라우드 기반 협업 플랫폼'},
        'QUBT': {'industry': '양자컴퓨팅', 'description': '양자컴퓨터 하드웨어 및 소프트웨어'},
        'RGTI': {'industry': '양자컴퓨팅', 'description': '양자컴퓨팅 및 AI 기술'},
        'QBTS': {'industry': '양자컴퓨팅', 'description': '양자컴퓨팅 시스템 및 응용'},
        'CHGG': {'industry': '교육', 'description': '온라인 학습 플랫폼'},
        'SOFI': {'industry': '금융', 'description': '온라인 대출, 투자, 은행 서비스 핀테크'},
        'SHOP': {'industry': '전자상거래', 'description': '온라인 쇼핑몰 구축 플랫폼'},
        'COIN': {'industry': '암호화폐', 'description': '암호화폐 거래소'},
        'HOOD': {'industry': '금융', 'description': '수수료 무료 주식 거래 앱'},
        'TSM': {'industry': '반도체', 'description': '세계 최대 반도체 파운드리'},
        'AMD': {'industry': '반도체', 'description': 'CPU 및 GPU 설계 제조'},
        'MU': {'industry': '반도체', 'description': '메모리 반도체 제조'},
        'PLTR': {'industry': 'AI', 'description': '빅데이터 분석 및 AI 플랫폼'},
        'AVGO': {'industry': '반도체', 'description': '반도체 및 인프라 소프트웨어'},
        'RKLB': {'industry': '우주항공', 'description': '소형 위성 발사 서비스'},
        'ASTS': {'industry': '우주항공', 'description': '위성 기반 모바일 통신'},
        'APP': {'industry': '소프트웨어', 'description': '앱 개발 플랫폼'},
        'QS': {'industry': '배터리', 'description': '전고체 배터리 기술'},
        'NEE': {'industry': '전력', 'description': '신재생 에너지 전력 공급'},
        'FLNC': {'industry': '수소에너지', 'description': '수소 연료전지 솔루션'},
        'EOSE': {'industry': '태양광', 'description': '태양광 발전 설비'},
        'CCJ': {'industry': '원자력', 'description': '우라늄 채굴 및 공급'},
        'SMR': {'industry': '원자력', 'description': '소형 모듈 원자로 개발'},
        'CEG': {'industry': '전력', 'description': '원자력 발전'},
        'VST': {'industry': '전력', 'description': '전력 인프라 및 서비스'},
        'OKLO': {'industry': '원자력', 'description': '소형 원자로 기술'},
        'ORCL': {'industry': '소프트웨어', 'description': '데이터베이스 및 클라우드 솔루션'},
        'APLD': {'industry': '데이터센터', 'description': 'AI 데이터센터 인프라'},
        'AIRO': {'industry': 'AI', 'description': 'AI 솔루션 및 서비스'},
        'CIFR': {'industry': '암호화폐', 'description': '비트코인 채굴'},
        'NBIS': {'industry': 'AI', 'description': 'AI 반도체 및 솔루션'},
        'IONQ': {'industry': '양자컴퓨팅', 'description': '이온 트랩 양자컴퓨터'},
        'CRCL': {'industry': '바이오', 'description': '암 진단 및 치료 솔루션'},
        'BITI': {'industry': '암호화폐', 'description': '비트코인 인버스 ETF'},
    }

    if ticker in manual_company_info:
        info_dict = manual_company_info[ticker]
        return f"{info_dict['industry']} | {info_dict['description']}"

    # 1. yfinance에서 정보 가져오기
    sector = info.get('sector', '')
    business_summary = info.get('longBusinessSummary', '')

    # 영문 산업 분야를 한국어로 간단 변환
    industry_translation = {
        'Technology': '기술',
        'Healthcare': '헬스케어',
        'Financial Services': '금융',
        'Consumer Cyclical': '소비재',
        'Communication Services': '통신',
        'Industrials': '산업',
        'Consumer Defensive': '필수소비재',
        'Energy': '에너지',
        'Utilities': '유틸리티',
        'Real Estate': '부동산',
        'Basic Materials': '원자재',
    }

    industry_kr = industry_translation.get(sector, sector if sector else '기술')

    # manual_company_info에 없는 종목은 회사명만 표시
    long_name = info.get('longName', '')
    if long_name and long_name != ticker:
        # 회사명이 너무 길면 50자로 제한
        if len(long_name) > 50:
            long_name = long_name[:47] + '...'
        return f"{industry_kr} | {long_name}"

    return f"{industry_kr} | {ticker}"  # 기본값

def get_cached_stock_info(ticker):
    """캐시된 주식 정보 가져오기 (종목명, 설명 등)"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # 캐시된 정보 확인 (30일 이내)
    cursor.execute('''
        SELECT long_name, description, updated_at FROM stock_info
        WHERE ticker = ?
    ''', (ticker,))

    result = cursor.fetchone()

    # 캐시가 있고 30일 이내면 사용
    if result:
        long_name, description, updated_at = result
        updated_date = datetime.strptime(updated_at, '%Y-%m-%d')
        if (datetime.now() - updated_date).days < 30:
            conn.close()
            return {'name': long_name, 'description': description or '정보 없음'}

    # 캐시가 없거나 오래되면 새로 가져오기
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        long_name = info.get('longName', ticker)
        description = get_company_description(ticker, info)

        # 캐시 업데이트
        cursor.execute('''
            INSERT OR REPLACE INTO stock_info (ticker, long_name, description, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (ticker, long_name, description, datetime.now().strftime('%Y-%m-%d')))

        conn.commit()
        conn.close()
        return {'name': long_name, 'description': description}
    except Exception as e:
        conn.close()
        return {'name': ticker, 'description': '정보 없음'}

def get_cached_macro_data(indicator, ticker, period="1y"):
    """캐시된 거시경제 데이터 가져오기 및 업데이트"""
    conn = sqlite3.connect(DB_FILE)

    # 기존 데이터 가져오기
    query = 'SELECT date, value FROM macro_data WHERE indicator = ? ORDER BY date'
    df = pd.read_sql_query(query, conn, params=(indicator,))

    last_date = get_last_date('macro_data', indicator=indicator)

    # 필요한 기간 계산
    period_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    days = period_map.get(period, 365)
    start_date = datetime.now() - timedelta(days=days)

    # 업데이트 필요 여부 확인
    if last_date is None:
        # 데이터가 없으면 전체 가져오기
        stock = yf.Ticker(ticker)
        new_df = stock.history(period=period)
        # timezone 제거
        if new_df.index.tz is not None:
            new_df.index = new_df.index.tz_localize(None)
    else:
        last_datetime = pd.to_datetime(last_date)
        today = datetime.now()

        # 오늘 데이터가 이미 있으면 DB 데이터만 반환
        if last_datetime.date() >= today.date():
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df = df[df.index >= start_date]
                df.columns = ['Close']
                return df

        # 마지막 날짜 이후 데이터만 가져오기
        stock = yf.Ticker(ticker)
        days_to_fetch = (today - last_datetime).days + 5
        new_df = stock.history(period=f"{days_to_fetch}d")

        # timezone 제거
        if not new_df.empty and new_df.index.tz is not None:
            new_df.index = new_df.index.tz_localize(None)

        if not new_df.empty:
            new_df = new_df[new_df.index > last_datetime]

    # 새 데이터 저장
    if not new_df.empty:
        for idx, row in new_df.iterrows():
            try:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO macro_data (indicator, date, value) VALUES (?, ?, ?)',
                    (indicator, idx.strftime('%Y-%m-%d'), row['Close'])
                )
                conn.commit()
            except:
                pass

    # 전체 데이터 다시 가져오기
    df = pd.read_sql_query(query, conn, params=(indicator,))
    conn.close()

    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df[df.index >= start_date]
        df.columns = ['Close']

    return df

def get_cached_fed_rate(period="1y"):
    """캐시된 기준금리 데이터 가져오기 및 업데이트"""
    conn = sqlite3.connect(DB_FILE)

    # 기존 데이터 가져오기
    query = 'SELECT date, rate FROM fed_rate ORDER BY date'
    df = pd.read_sql_query(query, conn)

    last_date = get_last_date('fed_rate')

    # 필요한 기간 계산
    period_map = {"1mo": 30, "3mo": 90, "6mo": 180, "1y": 365, "2y": 730}
    days = period_map.get(period, 365)
    start_date_target = datetime.now() - timedelta(days=days)

    # 업데이트 필요 여부 확인
    if last_date is None:
        # 데이터가 없으면 전체 가져오기
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        new_df = pdr.DataReader('DFF', 'fred', start_date, end_date)
    else:
        last_datetime = pd.to_datetime(last_date)
        today = datetime.now()

        # 오늘 데이터가 이미 있으면 DB 데이터만 반환
        if last_datetime.date() >= (today - timedelta(days=3)).date():
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
                df = df[df.index >= start_date_target]
                df.columns = ['DFF']
                return df

        # 마지막 날짜 이후 데이터만 가져오기
        new_df = pdr.DataReader('DFF', 'fred', last_datetime, today)

        if not new_df.empty:
            new_df = new_df[new_df.index > last_datetime]

    # 새 데이터 저장
    if not new_df.empty:
        for idx, row in new_df.iterrows():
            try:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT OR REPLACE INTO fed_rate (date, rate) VALUES (?, ?)',
                    (idx.strftime('%Y-%m-%d'), row['DFF'])
                )
                conn.commit()
            except:
                pass

    # 전체 데이터 다시 가져오기
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')
        df = df[df.index >= start_date_target]
        df.columns = ['DFF']

    return df

# DB 초기화
init_db()

# 즐겨찾기 관리 함수들
FAVORITES_FILE = "favorites.json"

def load_favorites():
    """즐겨찾기 데이터 로드"""
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"favorites": {}}
    return {"favorites": {}}

def save_favorites(data):
    """즐겨찾기 데이터 저장"""
    with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_favorite_group(group_name):
    """새 즐겨찾기 그룹 추가"""
    data = load_favorites()
    if group_name and group_name not in data["favorites"]:
        data["favorites"][group_name] = []
        save_favorites(data)
        return True
    return False

def delete_favorite_group(group_name):
    """즐겨찾기 그룹 삭제"""
    data = load_favorites()
    if group_name in data["favorites"]:
        del data["favorites"][group_name]
        save_favorites(data)
        return True
    return False

def update_group_tickers(group_name, tickers):
    """그룹의 티커 리스트 업데이트"""
    data = load_favorites()
    if group_name in data["favorites"]:
        data["favorites"][group_name] = tickers
        save_favorites(data)
        return True
    return False

# 거시경제 지표 차트 생성 함수
def create_macro_chart(ticker, name, period="1y"):
    """거시경제 지표 차트 생성"""
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)

        if df.empty:
            return None, "데이터를 가져올 수 없습니다."

        # 현재가와 전일 대비
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        change = current_price - prev_price
        change_pct = (change / prev_price) * 100 if prev_price != 0 else 0

        # 차트 생성
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['Close'],
            mode='lines',
            name=name,
            line=dict(color='#1f77b4', width=2),
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.1)',
            hovertemplate='<b>%{x}</b><br>%{y:.2f}<extra></extra>'
        ))

        fig.update_layout(
            title=dict(
                text=f"<b>{name}</b>",
                font=dict(size=16, color='#1a1a1a')
            ),
            yaxis=dict(
                title=None,
                tickfont=dict(size=10, color='#666'),
                gridcolor='#E8E8E8',
                gridwidth=0.5,
                showgrid=True,
                zeroline=False
            ),
            xaxis=dict(
                title=None,
                tickfont=dict(size=10, color='#666'),
                gridcolor='#E8E8E8',
                gridwidth=0.5,
                showgrid=True
            ),
            hovermode='x unified',
            height=400,
            plot_bgcolor='#FAFAFA',
            paper_bgcolor='#FFFFFF',
            autosize=True,
            xaxis_rangeslider_visible=False,
            showlegend=False,
            margin=dict(l=50, r=30, t=50, b=40)
        )

        return fig, (current_price, change, change_pct)
    except Exception as e:
        return None, str(e)

def get_fear_greed_index():
    """CNN 공포탐욕지수 가져오기"""
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data
        return None
    except Exception as e:
        print(f"CNN API Error: {e}")
        return None

# 시그널 분석 함수

def analyze_signal(df):

    """지수이동평균선(EMA)을 기반으로 시그널 분석"""
    # 지수이동평균선 계산
    df['MA5'] = df['Close'].ewm(span=5, adjust=False).mean()
    df['MA10'] = df['Close'].ewm(span=10, adjust=False).mean()
    df['MA20'] = df['Close'].ewm(span=20, adjust=False).mean() 

    # 크로스오버 시그널 감지 
    df['Signal'] = 0 
    df['MA5_prev'] = df['MA5'].shift(1) 
    df['MA20_prev'] = df['MA20'].shift(1) 

    # 골든크로스 (BUY): EMA5가 EMA20을 상향돌파

    golden_cross = (df['MA5_prev'] < df['MA20_prev']) & (df['MA5'] > df['MA20'])
    df.loc[golden_cross, 'Signal'] = 1

    # 데드크로스 (SELL): EMA5가 EMA20을 하향돌파

    dead_cross = (df['MA5_prev'] > df['MA20_prev']) & (df['MA5'] < df['MA20']) 

    df.loc[dead_cross, 'Signal'] = -1 

    # 현재 상태 계산 

    last_close = df['Close'].iloc[-1] 

    last_ma5 = df['MA5'].iloc[-1] 

    last_ma20 = df['MA20'].iloc[-1] 

    # 이전 상태 

    prev_ma5 = df['MA5'].iloc[-2] if len(df) > 1 else last_ma5 

    prev_ma20 = df['MA20'].iloc[-2] if len(df) > 1 else last_ma20 

    # 차이 계산

    current_diff = last_ma5 - last_ma20

    prev_diff = prev_ma5 - prev_ma20

    diff_pct = ((last_ma5 - last_ma20) / last_ma20) * 100

    # EMA5와 EMA20이 가까운지 판단 (2% 이내)

    is_close = abs(diff_pct) < 2.0

    # 시그널 상태 판단

    if last_ma5 > last_ma20:

        # EMA5가 EMA20 위에 있음

        if is_close and current_diff < prev_diff:

            # 차이가 좁혀지고 있음 -> 하락돌파 경고

            status = "WARNING"

            status_emoji = "⚠️"

            status_color = "orange"

            status_text = "하락돌파 경고! EMA5가 EMA20에 근접"

            bg_color = "#fff3cd"

        else:

            # BUY 상태

            status = "BUY"

            status_emoji = "💚"

            status_color = "green"

            status_text = "EMA5가 EMA20 위 (상승 추세)"

            bg_color = "#d4edda"

    else:

        # EMA5가 EMA20 아래에 있음

        if is_close and abs(current_diff) < abs(prev_diff):

            # 차이가 좁혀지고 있음 -> 상승돌파 임박

            status = "STRONG BUY"

            status_emoji = "🚀"

            status_color = "blue"

            status_text = "상승돌파 임박! EMA5가 EMA20에 근접"

            bg_color = "#cce5ff"

        else:

            # SELL 상태

            status = "SELL"

            status_emoji = "🔻"

            status_color = "red"

            status_text = "EMA5가 EMA20 아래 (하락 추세)"

            bg_color = "#f8d7da" 

    # 최근 시그널 확인 

    all_signals = df[df['Signal'] != 0] 

    if not all_signals.empty: 

        last_signal = all_signals.iloc[-1] 

        last_signal_date = last_signal.name.strftime('%Y-%m-%d') 

        last_signal_price = last_signal['Close'] 

        last_signal_type = last_signal['Signal'] 

    else: 

        last_signal_date = None 

        last_signal_price = None 

        last_signal_type = 0 

    return { 

        'df': df, 

        'status': status, 

        'status_emoji': status_emoji, 

        'status_color': status_color, 

        'status_text': status_text, 

        'bg_color': bg_color, 

        'current_price': last_close, 

        'ma5': last_ma5, 

        'ma20': last_ma20, 

        'diff_pct': diff_pct, 

        'last_signal_date': last_signal_date, 

        'last_signal_price': last_signal_price, 

        'last_signal_type': last_signal_type, 

        'buy_signals': df[df['Signal'] == 1], 

        'sell_signals': df[df['Signal'] == -1] 

    } 

# 종목별 차트 생성 함수

def create_chart(ticker, analysis_result):

    """특정 종목의 차트 생성 - 지수이동평균선(EMA) 표시""" 

    df = analysis_result['df'] 

    buy_signals = analysis_result['buy_signals'] 

    sell_signals = analysis_result['sell_signals'] 

    fig = go.Figure() 

    # 배경 레이어: 종가 (연하게)

    fig.add_trace(go.Scatter(

        x=df.index,

        y=df['Close'],

        mode='lines',

        name='종가',

        line=dict(color='rgba(150, 150, 150, 0.3)', width=1.5),

        hovertemplate='<b>종가</b>: $%{y:.2f}<extra></extra>',

        legendrank=4

    ))

    # 배경 레이어: EMA10 (연하게)

    fig.add_trace(go.Scatter(

        x=df.index, y=df['MA10'],

        mode='lines', name='EMA10',

        line=dict(color='rgba(100, 180, 150, 0.35)', width=1.5, dash='dash'),

        hovertemplate='<b>EMA10</b>: $%{y:.2f}<extra></extra>',

        legendrank=3

    )) 

    # BUY 시그널 (중간 레이어) 

    if not buy_signals.empty: 

        fig.add_trace(go.Scatter( 

            x=buy_signals.index, 

            y=buy_signals['Close'], 

            mode='markers', 

            name='BUY', 

            marker=dict( 

                symbol='triangle-up', 

                size=12, 

                color='rgba(0, 200, 81, 0.75)', 

                line=dict(color='#007E33', width=2) 

            ), 

            hovertemplate='<b>BUY 시그널</b><br>%{x}<br>$%{y:.2f}<extra></extra>', 

            legendrank=5 

        )) 

    # SELL 시그널 (중간 레이어) 

    if not sell_signals.empty: 

        fig.add_trace(go.Scatter( 

            x=sell_signals.index, 

            y=sell_signals['Close'], 

            mode='markers', 

            name='SELL', 

            marker=dict( 

                symbol='triangle-down', 

                size=12, 

                color='rgba(255, 68, 68, 0.75)', 

                line=dict(color='#CC0000', width=2) 

            ), 

            hovertemplate='<b>SELL 시그널</b><br>%{x}<br>$%{y:.2f}<extra></extra>', 

            legendrank=6 

        )) 

    # ★ 주요 레이어: EMA20 (지수이동평균 20일) - 진하고 선명하게

    fig.add_trace(go.Scatter(

        x=df.index, y=df['MA20'],

        mode='lines', name='★ EMA20',

        line=dict(color='#9D4EDD', width=2.5, dash='dot'),

        hovertemplate='<b>EMA20</b>: $%{y:.2f}<extra></extra>',

        legendrank=2

    ))

    # ★ 주요 레이어: EMA5 (지수이동평균 5일) - 진하고 선명하게

    fig.add_trace(go.Scatter(

        x=df.index, y=df['MA5'],

        mode='lines', name='★ EMA5',

        line=dict(color='#FF6B35', width=2.5),

        hovertemplate='<b>EMA5</b>: $%{y:.2f}<extra></extra>',

        legendrank=1

    )) 

    # 모바일 최적화 레이아웃 

    fig.update_layout( 

        title=dict( 

            text=f"<b>{ticker}</b>", 

            font=dict(size=14, color='#1a1a1a') 

        ), 

        yaxis=dict( 

            title=None, ## Y축 제목 제거로 공간 확보 

            tickfont=dict(size=9, color='#666'), 

            gridcolor='#E8E8E8', 

            gridwidth=0.5, 

            showgrid=True, 

            zeroline=False 

        ), 

        xaxis=dict( 

            title=None, ## X축 제목 제거로 공간 확보 

            tickfont=dict(size=9, color='#666'), 

            gridcolor='#E8E8E8', 

            gridwidth=0.5, 

            showgrid=True 

        ), 

        hovermode='x unified', 

        height=400, 

        plot_bgcolor='#FAFAFA', 

        autosize=True, 

        paper_bgcolor='#FFFFFF', 

        xaxis_rangeslider_visible=False, 

        showlegend=True, 

        legend=dict( 

            orientation="h", 

            yanchor="top", 

            y=-0.15, 

            xanchor="center", 

            x=0.5, 

            bgcolor='rgba(255, 255, 255, 0.9)', 

            bordercolor='#DDD', 

            borderwidth=0.5, 

            font=dict(size=9, color='#333'), 

            traceorder='reversed+grouped' 

        ), 

        margin=dict(l=40, r=20, t=40, b=60) 

    ) 

    return fig 

# 타이틀

st.title("📊 주식 지수이동평균선(EMA) 멀티 분석 대시보드") 

st.markdown("---") 

# 사이드바 설정

with st.sidebar:

    st.header("⚙️ 설정")

    # 즐겨찾기 그룹 관리
    st.markdown("### ⭐ 즐겨찾기 그룹")

    # 즐겨찾기 데이터 로드
    favorites_data = load_favorites()
    favorites = favorites_data.get("favorites", {})

    # 그룹 선택
    group_list = ["기본"] + list(favorites.keys())
    selected_group = st.selectbox(
        "그룹 선택",
        group_list,
        key="group_selector"
    )

    # 그룹 관리
    # 새 그룹 추가
    with st.expander("➕ 새 그룹 추가"):
        new_group_name = st.text_input("그룹 이름", key="new_group_name")
        if st.button("추가", key="add_group_btn", use_container_width=True):
            if new_group_name:
                if add_favorite_group(new_group_name):
                    st.success(f"'{new_group_name}' 그룹이 추가되었습니다!")
                    st.rerun()
                else:
                    st.error("이미 존재하는 그룹 이름입니다.")

    # 그룹 삭제
    if selected_group != "기본" and selected_group in favorites:
        with st.expander("🗑️ 현재 그룹 삭제"):
            st.warning(f"'{selected_group}' 그룹을 삭제하시겠습니까?")
            if st.button("삭제 확인", key="delete_group_btn", type="primary", use_container_width=True):
                if delete_favorite_group(selected_group):
                    st.success("그룹이 삭제되었습니다!")
                    st.rerun()

    st.markdown("---")

    # 여러 티커 입력 (쉼표로 구분)

    # 선택된 그룹의 티커 불러오기
    if selected_group == "기본":
        default_tickers = "AAPL, MSFT, GOOGL, TSLA, AMZN, NVDA, META, CRWD, INOD, BBAI, ANET, AEHR, CEVA, IBM, NICE, ADBE, STGW, AUDC, SPR, TNXP, ENPH, SMCI, KOPN, BLDP, TLS, SSYS, LQDT, ABSI, SLDP, INVZ, VVX, DEFT, BLNK, ARDX, SGML, SEZL, QUBT, RGTI, QBTS, CHGG, SOFI, SHOP, COIN, HOOD, TSM, AMD, MU, PLTR, AVGO, RKLB, ASTS, APP, QS, NEE, FLNC, EOSE, CCJ, SMR, CEG, VST, OKLO, ORCL, APLD, AIRO, CIFR, NBIS, IONQ, CRCL, BITI"
    else:
        default_tickers = ", ".join(favorites.get(selected_group, []))

    tickers_input = st.text_area(

        "종목 티커 입력 (쉼표로 구분)",

        value=default_tickers,

        help="예: AAPL, MSFT, GOOGL, 005930.KS, 035420.KS",

        height=120,

        key="tickers_input"

    )

    # 현재 티커를 그룹에 저장
    if selected_group != "기본" and selected_group in favorites:
        if st.button("💾 현재 티커를 그룹에 저장", type="secondary", use_container_width=True):
            tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
            if update_group_tickers(selected_group, tickers):
                st.success(f"'{selected_group}' 그룹에 저장되었습니다!")
                st.rerun()

    # 기간 선택 

    period_options = { 

        "1개월": "1mo", 

        "3개월": "3mo", 

        "6개월": "6mo", 

        "1년": "1y", 

        "2년": "2y" 

    } 

    period_label = st.selectbox("조회 기간", list(period_options.keys()), index=2) 

    period = period_options[period_label] 

    # 조회 버튼 

    fetch_button = st.button("🔄 전체 조회", type="primary", use_container_width=True) 

    st.markdown("---") 

    st.markdown("### 📌 시그널 설명")

    st.markdown("""

    - 🚀 **STRONG BUY**: 상승돌파 임박

    - 💚 **BUY**: 상승 추세

    - ⚠️ **WARNING**: 하락돌파 경고

    - 🔻 **SELL**: 하락 추세

    """) 

# 메인 영역 - 탭 구성
tab1, tab2 = st.tabs(["📊 종목 분석", "📈 거시경제 지표"])

# 탭1: 종목 분석
with tab1:
    if fetch_button or tickers_input:
        # 티커 리스트 파싱
        tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()] 

        if not tickers:
            st.warning("⚠️ 티커를 입력해주세요.")
        else:
            # 대시보드 헤더
            st.markdown(f"### 📊 총 {len(tickers)}개 종목 분석")

            # 각 종목 분석
            results = {}

            # 진행 상황 표시
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, ticker in enumerate(tickers): 

                status_text.text(f"분석 중: {ticker} ({idx + 1}/{len(tickers)})")

                try:
                    # 데이터 가져오기 (캐시 사용)
                    df = get_cached_stock_data(ticker, period=period)

                    if df.empty:
                        results[ticker] = {'error': '데이터를 찾을 수 없습니다'}
                    else:
                        # 시그널 분석
                        analysis = analyze_signal(df)

                        # 종목 정보 추가 (캐시 사용)
                        stock_info = get_cached_stock_info(ticker)
                        analysis['name'] = stock_info['name']
                        analysis['description'] = stock_info['description']
                        analysis['ticker'] = ticker
                        results[ticker] = analysis

                except Exception as e:
                    results[ticker] = {'error': str(e)}

                # 진행률 업데이트
                progress_bar.progress((idx + 1) / len(tickers))


        # 진행 상황 제거 

        progress_bar.empty() 

        status_text.empty() 

        # 결과를 상태별로 그룹화 

        strong_buy_list = [] 

        buy_list = [] 

        warning_list = [] 

        sell_list = [] 

        error_list = [] 

        for ticker, result in results.items(): 

            if 'error' in result: 

                error_list.append((ticker, result)) 

            else: 

                if result['status'] == 'STRONG BUY': 

                    strong_buy_list.append((ticker, result)) 

                elif result['status'] == 'BUY': 

                    buy_list.append((ticker, result)) 

                elif result['status'] == 'WARNING': 

                    warning_list.append((ticker, result)) 

                else: ## SELL 

                    sell_list.append((ticker, result)) 

        # 각 카테고리 내에서 최근 시그널 날짜 순으로 정렬 

        def sort_by_signal_date(stock_list):
            """최근 시그널 날짜 기준으로 정렬 (최신순)"""
            return sorted(stock_list, key=lambda x: x[1].get('last_signal_date') or '1900-01-01', reverse=True) 

        strong_buy_list = sort_by_signal_date(strong_buy_list) 

        warning_list = sort_by_signal_date(warning_list) 

        buy_list = sort_by_signal_date(buy_list) 

        sell_list = sort_by_signal_date(sell_list) 

        # 요약 통계 (모바일 반응형: 2x2 그리드) 

        col1, col2 = st.columns(2) 

        with col1:

            st.metric("🚀 STRONG BUY", len(strong_buy_list))

            st.metric("⚠️ WARNING", len(warning_list))

        with col2:

            st.metric("💚 BUY", len(buy_list))

            st.metric("🔻 SELL", len(sell_list)) 

        st.markdown("---") 

        # 전체 종목을 하나의 테이블로 표시 

        all_stocks = strong_buy_list + warning_list + buy_list + sell_list 

        if all_stocks: 

            st.markdown("### 📊 종목 현황") 

            # 각 종목을 행으로 표시하되, expander로 차트 포함 

            for ticker, result in all_stocks: 

                # 배경색 결정 

                if result['status'] == 'STRONG BUY': 

                    bg_color = "#cce5ff" 

                elif result['status'] == 'WARNING': 

                    bg_color = "#fff3cd" 

                elif result['status'] == 'BUY': 

                    bg_color = "#d4edda" 

                else: ## SELL 

                    bg_color = "#f8d7da" 

                # 모바일 컴팩트 디자인

                st.markdown(f"""

                <div style="
                    padding: 8px 10px;
                    margin: 3px 0;
                    border-radius: 6px;
                    background-color: {bg_color};
                    border-left: 4px solid {result['status_color']};
                    color: #000000;
                    font-size: 13px;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <div style="font-weight: bold; font-size: 14px;">
                            {result['status_emoji']} <span style="font-size: 15px;">{ticker}</span>
                        </div>
                        <div style="font-weight: bold; font-size: 14px;">
                            ${result['current_price']:.2f} <span style="font-size: 12px; color: {'green' if result['diff_pct'] > 0 else 'red'};">({result['diff_pct']:+.1f}%)</span>
                        </div>
                    </div>
                    <div style="font-size: 11px; color: #1a5490; font-weight: 600; margin-bottom: 4px; line-height: 1.4;">
                        {result.get('description', '정보 없음')}
                    </div>
                    <div style="display: flex; gap: 12px; font-size: 11px; color: #666;">
                        <span>EMA5: ${result['ma5']:.1f}</span>
                        <span>EMA20: ${result['ma20']:.1f}</span>
                        <span style="font-weight: bold;">{result['status']}</span>
                    </div>
                </div>

                """, unsafe_allow_html=True) 

                # 차트를 expander 안에 넣기 

                with st.expander(f"📈 {ticker} 차트", expanded=False): 

                    # 차트 

                    fig = create_chart(ticker, result) 

                    st.plotly_chart(fig, use_container_width=True) 

                    # 추가 정보 (모바일 친화적으로 2열 배치) 

                    col1, col2 = st.columns(2) 

                    with col1:

                        st.metric("최근 시그널",
                                result['last_signal_date'] if result['last_signal_date'] else '없음')

                        st.metric("EMA5-EMA20 차이", f"{result['diff_pct']:+.2f}%") 

                    with col2: 

                        if result['last_signal_type'] == 1: 

                            st.metric("시그널 타입", "BUY (골든크로스)") 

                        elif result['last_signal_type'] == -1: 

                            st.metric("시그널 타입", "SELL (데드크로스)") 

                        else: 

                            st.metric("시그널 타입", "-") 

                    # 최근 데이터

                    df = result['df']

                    recent_data = df[['Close', 'MA5', 'MA20']].tail(7).sort_index(ascending=False)

                    recent_data.columns = ['종가', 'EMA5', 'EMA20'] 

                    recent_data.index = recent_data.index.strftime('%m/%d') 

                    st.markdown("##### 최근 데이터") 

                    st.dataframe( 

                        recent_data.style.format("{:.1f}"), 

                        use_container_width=True, 

                        height=180 

                    ) 

        # 에러 종목 

        if error_list: 

            st.markdown("### ❌ 오류 발생 종목") 

            for ticker, result in error_list:
                st.error(f"{ticker}: {result['error']}")

    else: 

            # 초기 화면 

            st.info("ℹ️ 왼쪽 사이드바에서 종목 티커를 입력하고 '전체 조회' 버튼을 클릭하세요.")

            st.markdown("### 📖 사용 방법") 

            st.markdown(""" 

            1. 왼쪽 사이드바에 여러 종목 티커를 **쉼표(,)로 구분**하여 입력하세요 

            2. 조회 기간을 선택하세요 

            3. '전체 조회' 버튼을 클릭하세요 

            4. 각 종목의 현재 시그널 상태를 확인하세요 

            5. 종목을 클릭하여 상세 차트를 확인하세요 

            #### 티커 예시: 

            ``` 

            AAPL, MSFT, GOOGL, TSLA, AMZN 

            ``` 

            또는 한국 주식: 

            ``` 

            005930.KS, 035420.KS, 000660.KS 

            ``` 

            미국 + 한국 주식 혼합: 

            ``` 

            AAPL, TSLA, 005930.KS, 035420.KS 

            ``` 

            """) 

            st.markdown("### 📌 시그널 설명")

            st.markdown("""

            이 프로그램은 지수이동평균선(EMA5, EMA20)의 관계를 분석하여 4가지 시그널을 제공합니다:

            - **🚀 STRONG BUY (상승돌파 임박)**

                - EMA5가 EMA20 **아래**에 있지만, 점점 가까워지고 있음

                - 골든크로스(상승돌파)가 곧 발생할 가능성이 높음

                - 매수 타이밍 포착에 유리

            - **💚 BUY (상승 추세)**

                - EMA5가 EMA20 **위**에 있음

                - 안정적인 상승 추세 유지 중

            - **⚠️ WARNING (하락돌파 경고)**

                - EMA5가 EMA20 **위**에 있지만, 점점 가까워지고 있음

                - 데드크로스(하락돌파)가 곧 발생할 가능성

                - 매도 타이밍 고려 필요

            - **🔻 SELL (하락 추세)**

                - EMA5가 EMA20 **아래**에 있음

                - 하락 추세 진행 중

            **주의**: 이 시그널은 참고용이며, 실제 투자 결정은 다양한 요소를 종합적으로 고려해야 합니다.

            """) 
# 탭2: 거시경제 지표

# 탭2: 거시경제 지표
with tab2:
    st.markdown("### 📈 주요 거시경제 지표")
    st.markdown("S&P 500, VIX, CNN 공포탐욕지수, 미국 기준금리를 한눈에 확인하세요.")

    # 조회 버튼
    macro_fetch_button = st.button("🔄 거시경제 지표 조회", type="primary", use_container_width=True, key="macro_fetch")

    if macro_fetch_button or st.session_state.get('macro_loaded', False):
        st.session_state['macro_loaded'] = True

        with st.spinner("거시경제 지표 데이터를 가져오는 중..."):
            # 데이터 수집 (캐시 사용)
            errors = []

            sp500_df = get_cached_macro_data("SP500", "^GSPC", period=period)
            if sp500_df.empty:
                errors.append("S&P 500 데이터를 가져올 수 없습니다.")

            vix_df = get_cached_macro_data("VIX", "^VIX", period=period)
            if vix_df.empty:
                errors.append("VIX 데이터를 가져올 수 없습니다.")

            fng_data = get_fear_greed_index()
            if not fng_data:
                errors.append("CNN 공포탐욕지수 데이터를 가져올 수 없습니다.")

            fed_rate_df = get_cached_fed_rate(period=period)
            if fed_rate_df is None or fed_rate_df.empty:
                errors.append("미국 기준금리 데이터를 가져올 수 없습니다.")

            if errors:
                for error in errors:
                    st.error(error)

            if not sp500_df.empty and not vix_df.empty and fng_data and fed_rate_df is not None and not fed_rate_df.empty:
                # 현재 값 표시
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    sp500_current = sp500_df['Close'].iloc[-1]
                    sp500_prev = sp500_df['Close'].iloc[-2] if len(sp500_df) > 1 else sp500_current
                    sp500_change = sp500_current - sp500_prev
                    sp500_change_pct = (sp500_change / sp500_prev) * 100
                    st.metric("📊 S&P 500", f"${sp500_current:.2f}", f"{sp500_change_pct:+.2f}%")

                with col2:
                    vix_current = vix_df['Close'].iloc[-1]
                    vix_prev = vix_df['Close'].iloc[-2] if len(vix_df) > 1 else vix_current
                    vix_change = vix_current - vix_prev
                    vix_change_pct = (vix_change / vix_prev) * 100
                    st.metric("📉 VIX", f"{vix_current:.2f}", f"{vix_change_pct:+.2f}%")

                with col3:
                    # CNN Fear & Greed Index 현재값
                    fng_current = fng_data['fear_and_greed']['score']
                    fng_rating = fng_data['fear_and_greed']['rating']

                    if fng_current <= 25:
                        emoji = "😨"
                    elif fng_current <= 45:
                        emoji = "😟"
                    elif fng_current <= 55:
                        emoji = "😐"
                    elif fng_current <= 75:
                        emoji = "🙂"
                    else:
                        emoji = "😍"

                    st.metric(f"{emoji} CNN 공포탐욕", f"{fng_current:.0f}/100", f"{fng_rating}")

                with col4:
                    # 미국 기준금리
                    fed_rate_current = fed_rate_df['DFF'].iloc[-1]
                    fed_rate_prev = fed_rate_df['DFF'].iloc[-2] if len(fed_rate_df) > 1 else fed_rate_current
                    fed_rate_change = fed_rate_current - fed_rate_prev
                    st.metric("💵 기준금리", f"{fed_rate_current:.2f}%", f"{fed_rate_change:+.2f}%p")
                
                st.markdown("---")
                
                # 통합 차트 생성
                st.markdown("#### 📊 통합 차트 (기간: {})".format(period_label))
                
                # CNN Fear & Greed 히스토리 데이터 처리
                fng_history = fng_data['fear_and_greed_historical']['data']
                fng_df = pd.DataFrame(fng_history)
                fng_df['x'] = pd.to_datetime(fng_df['x'], unit='ms')
                fng_df = fng_df.rename(columns={'x': 'Date', 'y': 'Score'})
                fng_df = fng_df.set_index('Date')
                fng_df = fng_df.sort_index()

                # timezone 정보 제거 (비교를 위해 모든 인덱스를 timezone-naive로 변환)
                if sp500_df.index.tz is not None:
                    sp500_df.index = sp500_df.index.tz_localize(None)
                if vix_df.index.tz is not None:
                    vix_df.index = vix_df.index.tz_localize(None)
                if fng_df.index.tz is not None:
                    fng_df.index = fng_df.index.tz_localize(None)
                if fed_rate_df.index.tz is not None:
                    fed_rate_df.index = fed_rate_df.index.tz_localize(None)

                # 날짜 범위 맞추기
                start_date = sp500_df.index.min()
                end_date = sp500_df.index.max()

                # 데이터 필터링
                sp500_filtered = sp500_df[sp500_df.index >= start_date]
                vix_filtered = vix_df[vix_df.index >= start_date]
                fng_filtered = fng_df[(fng_df.index >= start_date) & (fng_df.index <= end_date)]
                fed_rate_filtered = fed_rate_df[(fed_rate_df.index >= start_date) & (fed_rate_df.index <= end_date)]
                
                # 통합 차트 (4개 서브플롯)
                from plotly.subplots import make_subplots

                fig = make_subplots(
                    rows=4, cols=1,
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=('S&P 500', 'VIX (변동성 지수)', 'CNN 공포탐욕지수', '미국 기준금리'),
                    row_heights=[0.25, 0.25, 0.25, 0.25]
                )

                # 1. S&P 500
                fig.add_trace(
                    go.Scatter(
                        x=sp500_filtered.index,
                        y=sp500_filtered['Close'],
                        name='S&P 500',
                        line=dict(color='#2E86DE', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(46, 134, 222, 0.1)',
                        hovertemplate='<b>S&P 500</b><br>%{x}<br>$%{y:.2f}<extra></extra>'
                    ),
                    row=1, col=1
                )

                # 2. VIX
                fig.add_trace(
                    go.Scatter(
                        x=vix_filtered.index,
                        y=vix_filtered['Close'],
                        name='VIX',
                        line=dict(color='#FF6B35', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(255, 107, 53, 0.1)',
                        hovertemplate='<b>VIX</b><br>%{x}<br>%{y:.2f}<extra></extra>'
                    ),
                    row=2, col=1
                )

                # 3. CNN 공포탐욕지수
                fig.add_trace(
                    go.Scatter(
                        x=fng_filtered.index,
                        y=fng_filtered['Score'],
                        name='공포탐욕지수',
                        line=dict(color='#26C281', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(38, 194, 129, 0.1)',
                        hovertemplate='<b>공포탐욕지수</b><br>%{x}<br>%{y:.0f}/100<extra></extra>'
                    ),
                    row=3, col=1
                )

                # 4. 미국 기준금리
                fig.add_trace(
                    go.Scatter(
                        x=fed_rate_filtered.index,
                        y=fed_rate_filtered['DFF'],
                        name='기준금리',
                        line=dict(color='#8E44AD', width=3),
                        fill='tozeroy',
                        fillcolor='rgba(142, 68, 173, 0.1)',
                        hovertemplate='<b>기준금리</b><br>%{x}<br>%{y:.2f}%<extra></extra>'
                    ),
                    row=4, col=1
                )

                # Y축 설정 - 동적 범위 조정
                # S&P 500
                sp500_min = sp500_filtered['Close'].min()
                sp500_max = sp500_filtered['Close'].max()
                sp500_padding = (sp500_max - sp500_min) * 0.1  # 10% 여유
                fig.update_yaxes(
                    title_text="가격 ($)",
                    row=1, col=1,
                    tickfont=dict(size=10),
                    range=[sp500_min - sp500_padding, sp500_max + sp500_padding]
                )

                # VIX
                vix_min = vix_filtered['Close'].min()
                vix_max = vix_filtered['Close'].max()
                vix_padding = (vix_max - vix_min) * 0.1  # 10% 여유
                fig.update_yaxes(
                    title_text="지수",
                    row=2, col=1,
                    tickfont=dict(size=10),
                    range=[vix_min - vix_padding, vix_max + vix_padding]
                )

                # CNN 공포탐욕지수 (0-100 고정)
                fig.update_yaxes(
                    title_text="점수 (0-100)",
                    row=3, col=1,
                    range=[0, 100],
                    tickfont=dict(size=10)
                )

                # 미국 기준금리
                fed_min = fed_rate_filtered['DFF'].min()
                fed_max = fed_rate_filtered['DFF'].max()
                fed_padding = (fed_max - fed_min) * 0.1  # 10% 여유
                fig.update_yaxes(
                    title_text="금리 (%)",
                    row=4, col=1,
                    tickfont=dict(size=10),
                    range=[fed_min - fed_padding, fed_max + fed_padding]
                )

                # X축 설정
                fig.update_xaxes(showgrid=True, gridcolor='#E8E8E8', gridwidth=0.5)

                # 레이아웃 설정
                fig.update_layout(
                    height=900,
                    plot_bgcolor='#FAFAFA',
                    paper_bgcolor='#FFFFFF',
                    showlegend=False,
                    hovermode='x unified',
                    margin=dict(l=60, r=30, t=80, b=50),
                    font=dict(size=11)
                )

                # 서브플롯 제목 스타일
                for annotation in fig['layout']['annotations']:
                    annotation['font'] = dict(size=13, color='#2C3E50', family='Arial Black')
                
                st.plotly_chart(fig, use_container_width=True)
                
                # 추가 정보
                st.markdown("---")
                st.markdown("### 📋 현재 시장 상황 해석")
                
                # VIX 해석
                if vix_current < 15:
                    vix_status = "😌 매우 낮음 - 시장 안정"
                    vix_color = "green"
                elif vix_current < 20:
                    vix_status = "🙂 낮음 - 시장 정상"
                    vix_color = "blue"
                elif vix_current < 30:
                    vix_status = "⚠️ 높음 - 시장 불안"
                    vix_color = "orange"
                else:
                    vix_status = "🚨 매우 높음 - 극심한 변동성"
                    vix_color = "red"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"""
                    **VIX 변동성 지수**
                    - 현재 수준: **{vix_current:.2f}**
                    - 상태: :{vix_color}[**{vix_status}**]
                    - 해석: VIX가 {'낮아' if vix_current < 20 else '높아'}서 시장 {'안정적' if vix_current < 20 else '불안정'}
                    """)
                
                with col2:
                    st.markdown(f"""
                    **CNN 공포탐욕지수**
                    - 현재 점수: **{fng_current:.0f}/100**
                    - 상태: **{fng_rating}**
                    - 해석: 시장 심리가 **{fng_rating}** 상태
                    """)
                
                # 지표 설명
                st.markdown("---")
                st.markdown("### 📌 거시경제 지표 설명")
                
                with st.expander("📊 S&P 500이란?"):
                    st.markdown("""
                    **S&P 500**은 미국의 500개 대형 기업을 포함하는 주가지수입니다.
                    
                    - 미국 증시 전체의 흐름을 가장 잘 대표하는 지표
                    - S&P 500이 상승하면 일반적으로 미국 경제가 호황
                    - 기관 투자자들이 가장 많이 참고하는 지수
                    """)
                
                with st.expander("📉 VIX란?"):
                    st.markdown("""
                    **VIX (Volatility Index)**는 시장 변동성을 나타내는 지수입니다.
                    
                    - "공포 지수"라고도 불림
                    - VIX가 높을수록 시장 변동성이 크고 투자자들이 불안함
                    - VIX가 낮을수록 시장이 안정적
                    - 일반적으로 S&P 500과 반대로 움직임
                    
                    **VIX 수준 해석:**
                    - 15 미만: 매우 낮음 (시장 안정)
                    - 15~20: 낮음 (정상적인 시장)
                    - 20~30: 높음 (시장 불안)
                    - 30 초과: 매우 높음 (극심한 변동성, 공포)
                    """)
                
                with st.expander("😨😍 CNN 공포탐욕지수란?"):
                    st.markdown("""
                    **CNN Fear & Greed Index**는 미국 주식시장의 심리를 0~100 사이의 숫자로 나타낸 지표입니다.
                    
                    - 0에 가까울수록 극도의 공포 (매수 기회?)
                    - 100에 가까울수록 극도의 탐욕 (과열 경고?)
                    - 50 근처는 중립적인 시장 심리
                    
                    **지수 구간:**
                    - 0~25: Extreme Fear (극도의 공포)
                    - 25~45: Fear (공포)
                    - 45~55: Neutral (중립)
                    - 55~75: Greed (탐욕)
                    - 75~100: Extreme Greed (극도의 탐욕)
                    
                    **구성 요소:**
                    - 시장 모멘텀 (S&P 500 vs 125일 이동평균)
                    - 주가 강도 (신고가 vs 신저가 종목 수)
                    - 시장 폭 (거래량)
                    - Put/Call 옵션 비율
                    - 정크본드 수요
                    - 시장 변동성 (VIX)
                    - 안전자산 수요
                    """)

                with st.expander("💵 미국 기준금리란?"):
                    st.markdown("""
                    **미국 기준금리 (Federal Funds Rate)**는 미국 연방준비제도(Fed)가 설정하는 정책 금리입니다.

                    - 미국 경제 정책의 가장 중요한 도구
                    - 은행 간 대출 금리의 기준
                    - 경제 성장과 인플레이션 조절

                    **기준금리와 주식시장:**
                    - 금리 인상 → 자금 조달 비용 증가 → 주식 부정적
                    - 금리 인하 → 투자 환경 개선 → 주식 긍정적
                    - 높은 금리 → 채권 매력도 증가 → 주식 투자 감소
                    - 낮은 금리 → 주식 투자 매력도 증가

                    **최근 추세:**
                    - Fed는 인플레이션 조절을 위해 금리 정책 조정
                    - 기준금리 변화는 시장에 큰 영향을 미침
                    - 금리 결정 회의(FOMC) 결과 주목 필요
                    """)

    else:
        st.info("🔄 '거시경제 지표 조회' 버튼을 클릭하여 데이터를 불러오세요.")
        
        st.markdown("""
        ### 📌 이 탭에서 확인할 수 있는 지표

        - **S&P 500**: 미국 증시 대표 지수
        - **VIX**: 시장 변동성 지수 (공포 지수)
        - **CNN 공포탐욕지수**: 미국 주식시장 심리 지표
        - **미국 기준금리**: Fed 정책 금리

        네 가지 지표를 하나의 차트에서 비교하여 전체적인 시장 분위기와 리스크 수준을 파악할 수 있습니다.
        """)
