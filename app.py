import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from data import fetch_ohlcv, stream_ohlcv
from strategy import ema_crossover, macd_signal, rsi_signal
import asyncio
import time
import os
import ccxt.async_support as ccxt  # Use the async version of CCXT

# Synchronous wrapper for running async coroutines
def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# Helper async function to get next item from async generator
async def get_next(generator):
    try:
        return await anext(generator)
    except StopAsyncIteration:
        return None

# Function to manage visitor count
def update_visitor_count():
    if 'visit_count' not in st.session_state:
        count_file = "visit_count.txt"
        if os.path.exists(count_file):
            with open(count_file, "r") as f:
                try:
                    st.session_state.visit_count = int(f.read().strip())
                except ValueError:
                    st.session_state.visit_count = 0
        else:
            st.session_state.visit_count = 0
        st.session_state.visit_count += 1
        with open(count_file, "w") as f:
            f.write(str(st.session_state.visit_count))
    return st.session_state.visit_count

# Asynchronous function to fetch symbols for the selected exchange
async def fetch_symbols(exchange_id):
    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class()
    try:
        markets = await exchange.load_markets()
        return list(markets.keys())
    except Exception as e:
        st.error(f"Failed to fetch symbols for {exchange_id}: {str(e)}")
        return []
    finally:
        # Only call close() if the exchange supports it
        if hasattr(exchange, 'close'):
            await exchange.close()

# List of exchanges
exchanges = [
    'ascendex', 'bequant', 'bigone', 'binancecoinm', 'binanceus', 'binanceusdm', 
    'bingx', 'bit2c', 'bitbank', 'bitbns', 'bitfinex', 'bitfinex1', 'bitmex', 'bybit', 'cex', 
    'coinbase', 'coincheck', 'deribit', 'gemini', 'hitbtc', 'kraken', 'krakenfutures', 
    'kucoin', 'kucoinfutures', 'kuna', 'luno', 'okx', 'poloniex'
]
exchanges.sort()  # Sort alphabetically for user-friendly dropdown

# Streamlit app
st.title("Crypto Trading App")

# Update and display visitor count
visitor_count = update_visitor_count()
st.markdown(f"**Number of Visitors:** {visitor_count}")

# Sidebar settings
st.sidebar.header("Settings")
exchange = st.sidebar.selectbox("Exchange", exchanges)

# Fetch symbols for the selected exchange
if 'symbols' not in st.session_state or st.session_state.selected_exchange != exchange:
    st.session_state.selected_exchange = exchange
    st.session_state.symbols = run_async(fetch_symbols(exchange))

symbol = st.sidebar.selectbox("Symbol", st.session_state.symbols if 'symbols' in st.session_state else [])

timeframe = st.sidebar.selectbox("Timeframe", ["1m", "1h", "1d"])
st.sidebar.header("Strategy Parameters")
if timeframe == "1m":
    fast_ema = st.sidebar.number_input("Fast EMA Period", min_value=1, value=5)
    slow_ema = st.sidebar.number_input("Slow EMA Period", min_value=1, value=20)
elif timeframe == "1h":
    fast_macd = st.sidebar.number_input("Fast MACD", min_value=1, value=12)
    slow_macd = st.sidebar.number_input("Slow MACD", min_value=1, value=26)
    signal_macd = st.sidebar.number_input("Signal MACD", min_value=1, value=9)
else:
    rsi_period = st.sidebar.number_input("RSI Period", min_value=1, value=14)

if st.sidebar.button("Start"):
    with st.spinner("Fetching data..."):
        try:
            df = run_async(fetch_ohlcv(exchange, symbol, timeframe))
            if timeframe == "1m":
                df = ema_crossover(df, fast=fast_ema, slow=slow_ema)
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close']))
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema_fast'], name='EMA Fast'))
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema_slow'], name='EMA Slow'))
                chart = st.plotly_chart(fig, use_container_width=True)
                if st.checkbox("Stream Updates"):
                    stream_gen = stream_ohlcv(exchange, symbol, timeframe)
                    for _ in range(10):
                        new_data = run_async(get_next(stream_gen))
                        if new_data is not None:
                            df = pd.concat([df, new_data])
                            df = ema_crossover(df.tail(100), fast=fast_ema, slow=slow_ema)
                            fig = go.Figure()
                            fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close']))
                            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema_fast'], name='EMA Fast'))
                            fig.add_trace(go.Scatter(x=df['timestamp'], y=df['ema_slow'], name='EMA Slow'))
                            chart.plotly_chart(fig, use_container_width=True)
                        time.sleep(1)
            elif timeframe == "1h":
                df = macd_signal(df, fast=fast_macd, slow=slow_macd, signal=signal_macd)
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close']))
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['macd'], name='MACD'))
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['signal_line'], name='Signal Line'))
                st.plotly_chart(fig, use_container_width=True)
            else:
                df = rsi_signal(df, period=rsi_period)
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=df['timestamp'], open=df['open'], high=df['high'], low=df['low'], close=df['close']))
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['rsi'], name='RSI'))
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Help section
st.expander("Help").write("""
- Select an exchange from the dropdown to fetch data from your chosen platform.
- Choose a trading pair symbol from the dropdown, which lists available symbols for the selected exchange.
- Select a timeframe: 1m (1 minute), 1h (1 hour), or 1d (1 day).
- Adjust strategy parameters based on the selected timeframe.
- Click 'Start' to fetch data and view charts with trading signals.
- For 1-minute timeframe, enable 'Stream Updates' to see real-time data if supported by the exchange.
- Note: Some exchanges may have geographic restrictions depending on your location.
""")

# INFO section with exact text as requested
st.markdown("---")
st.subheader("INFO")
st.markdown("""
This is an open-source project, and you are very welcome to **donate** and **contribute** your awesome comments, questions, or resources!
""")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**Contact Me:**")
    st.markdown("- Email: [onitechs@gmail.com](mailto:onitechs@gmail.com)")
with col2:
    st.markdown("**Connect Online:**")
    st.markdown("- LinkedIn: [Charles Oni](https://www.linkedin.com/in/charles-oni-b45a91253/)")
    st.markdown("- GitHub: [mainbtpty](https://github.com/mainbtpty)")