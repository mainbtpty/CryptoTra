import pandas as pd
import ta

def ema_crossover(df, fast=5, slow=20):
    df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=fast)
    df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=slow)
    df['signal'] = 0
    df.loc[df['ema_fast'] > df['ema_slow'], 'signal'] = 1  # Buy
    df.loc[df['ema_fast'] < df['ema_slow'], 'signal'] = -1  # Sell
    return df

def macd_signal(df, fast=12, slow=26, signal=9):
    macd = ta.trend.MACD(df['close'], window_fast=fast, window_slow=slow, window_sign=signal)
    df['macd'] = macd.macd()
    df['signal_line'] = macd.macd_signal()
    df['signal'] = 0
    df.loc[df['macd'] > df['signal_line'], 'signal'] = 1  # Buy
    df.loc[df['macd'] < df['signal_line'], 'signal'] = -1  # Sell
    return df

def rsi_signal(df, period=14):
    rsi = ta.momentum.RSIIndicator(df['close'], window=period)
    df['rsi'] = rsi.rsi()
    df['signal'] = 0
    df.loc[df['rsi'] < 30, 'signal'] = 1  # Buy (oversold)
    df.loc[df['rsi'] > 70, 'signal'] = -1  # Sell (overbought)
    return df