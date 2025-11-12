import streamlit as st 
import yfinance as yf 
import pandas as pd 
import plotly.graph_objects as go 
from datetime import datetime, timedelta 

# 페이지 설정 

st.set_page_config( 

    page_title="주식 이동평균선 분석", 

    page_icon="📈", 

    layout="wide" 

) 

# 시그널 분석 함수 

def analyze_signal(df): 

    """이동평균선을 기반으로 시그널 분석""" 
    # 이동평균선 계산 
    df['MA5'] = df['Close'].rolling(window=5).mean() 
    df['MA10'] = df['Close'].rolling(window=10).mean() 
    df['MA20'] = df['Close'].rolling(window=20).mean() 

    # 크로스오버 시그널 감지 
    df['Signal'] = 0 
    df['MA5_prev'] = df['MA5'].shift(1) 
    df['MA20_prev'] = df['MA20'].shift(1) 

    # 골든크로스 (BUY): MA5가 MA20을 상향돌파 

    golden_cross = (df['MA5_prev'] < df['MA20_prev']) & (df['MA5'] > df['MA20']) 
    df.loc[golden_cross, 'Signal'] = 1 

    # 데드크로스 (SELL): MA5가 MA20을 하향돌파 

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

    # 5일선과 20일선이 가까운지 판단 (2% 이내) 

    is_close = abs(diff_pct) < 2.0 

    # 시그널 상태 판단 

    if last_ma5 > last_ma20: 

        # 5일선이 20일선 위에 있음 

        if is_close and current_diff < prev_diff: 

            # 차이가 좁혀지고 있음 -> 하락돌파 경고 

            status = "WARNING"

            status_emoji = "⚠️" 

            status_color = "orange" 

            status_text = "하락돌파 경고! 5일선이 20일선에 근접" 

            bg_color = "#fff3cd" 

        else: 

            # BUY 상태

            status = "BUY"

            status_emoji = "💚" 

            status_color = "green" 

            status_text = "5일선이 20일선 위 (상승 추세)" 

            bg_color = "#d4edda" 

    else: 

        # 5일선이 20일선 아래에 있음 

        if is_close and abs(current_diff) < abs(prev_diff): 

            # 차이가 좁혀지고 있음 -> 상승돌파 임박

            status = "STRONG BUY"

            status_emoji = "🚀" 

            status_color = "blue" 

            status_text = "상승돌파 임박! 5일선이 20일선에 근접" 

            bg_color = "#cce5ff" 

        else: 

            # SELL 상태

            status = "SELL"

            status_emoji = "🔻" 

            status_color = "red" 

            status_text = "5일선이 20일선 아래 (하락 추세)" 

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

    """특정 종목의 차트 생성 - 시인성 개선 버전""" 

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

    # 배경 레이어: MA10 (연하게) 

    fig.add_trace(go.Scatter( 

        x=df.index, y=df['MA10'], 

        mode='lines', name='MA10', 

        line=dict(color='rgba(100, 180, 150, 0.35)', width=1.5, dash='dash'), 

        hovertemplate='<b>MA10</b>: $%{y:.2f}<extra></extra>', 

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

    # ★ 주요 레이어: MA20 (20일선) - 진하고 선명하게 

    fig.add_trace(go.Scatter( 

        x=df.index, y=df['MA20'], 

        mode='lines', name='★ MA20', 

        line=dict(color='#9D4EDD', width=2.5, dash='dot'), 

        hovertemplate='<b>MA20</b>: $%{y:.2f}<extra></extra>', 

        legendrank=2 

    )) 

    # ★ 주요 레이어: MA5 (5일선) - 진하고 선명하게 

    fig.add_trace(go.Scatter( 

        x=df.index, y=df['MA5'], 

        mode='lines', name='★ MA5', 

        line=dict(color='#FF6B35', width=2.5), 

        hovertemplate='<b>MA5</b>: $%{y:.2f}<extra></extra>', 

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

st.title("📊 주식 이동평균선 멀티 분석 대시보드") 

st.markdown("---") 

# 사이드바 설정 

with st.sidebar: 

    st.header("⚙️ 설정") 

    # 여러 티커 입력 (쉼표로 구분) 

    default_tickers = "RKLB, ASTS, APP, SLDP, QS, NEE, FLNC, EOSE, CCJ, SMR, CEG, VST, OKLO, ORCL, APLD, AIRO, CIFR, NBIS, RGTI, QBTS, IONQ, CRCL, BITI, SOFI, SHOP, COIN, HOOD, TSM, AMD, PLTR, GOOGL, TSLA, META, AVGO, AMZN, MSFT, NVDA" 

    tickers_input = st.text_area( 

        "종목 티커 입력 (쉼표로 구분)", 

        value=default_tickers, 

        help="예: AAPL, MSFT, GOOGL, 005930.KS, 035420.KS", 

        height=120 

    ) 

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

# 메인 영역 

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

                # 데이터 가져오기 

                stock = yf.Ticker(ticker) 

                df = stock.history(period=period) 

                if df.empty: 

                    results[ticker] = {'error': '데이터를 찾을 수 없습니다'} 

                else: 

                    # 시그널 분석 

                    analysis = analyze_signal(df) 

                    # 종목 정보 추가 

                    info = stock.info 

                    analysis['name'] = info.get('longName', ticker) 

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

            return sorted(stock_list, key=lambda x: x[1].get('last_signal_date', '1900-01-01'), reverse=True) 

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
                    <div style="font-size: 11px; color: #555; margin-bottom: 3px;"> 
                        {result.get('name', ticker)[:30]} 
                    </div> 
                    <div style="display: flex; gap: 12px; font-size: 11px; color: #666;"> 
                        <span>MA5: ${result['ma5']:.1f}</span> 
                        <span>MA20: ${result['ma20']:.1f}</span> 
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

                        st.metric("MA5-MA20 차이", f"{result['diff_pct']:+.2f}%") 

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

                    recent_data.columns = ['종가', 'MA5', 'MA20'] 

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

    이 프로그램은 5일선과 20일선의 관계를 분석하여 4가지 시그널을 제공합니다:

    - **🚀 STRONG BUY (상승돌파 임박)**

        - 5일선이 20일선 **아래**에 있지만, 점점 가까워지고 있음

        - 골든크로스(상승돌파)가 곧 발생할 가능성이 높음

        - 매수 타이밍 포착에 유리

    - **💚 BUY (상승 추세)**

        - 5일선이 20일선 **위**에 있음

        - 안정적인 상승 추세 유지 중

    - **⚠️ WARNING (하락돌파 경고)**

        - 5일선이 20일선 **위**에 있지만, 점점 가까워지고 있음

        - 데드크로스(하락돌파)가 곧 발생할 가능성

        - 매도 타이밍 고려 필요

    - **🔻 SELL (하락 추세)**

        - 5일선이 20일선 **아래**에 있음

        - 하락 추세 진행 중

    **주의**: 이 시그널은 참고용이며, 실제 투자 결정은 다양한 요소를 종합적으로 고려해야 합니다.

    """) 