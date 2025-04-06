import ccxt.async_support as ccxt_rest
import ccxt.pro as ccxt_ws
import pandas as pd
import asyncio

async def fetch_ohlcv(exchange_id, symbol, timeframe, limit=500):
    try:
        exchange_class = getattr(ccxt_rest, exchange_id.lower())
        if not exchange_class:
            raise ValueError(f"Exchange {exchange_id} not found in ccxt.async_support")
        exchange = exchange_class()
        ohlcv = await exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        await exchange.close()
        return pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    except AttributeError:
        raise ValueError(f"Invalid exchange ID: {exchange_id}")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch OHLCV data: {str(e)}")

async def stream_ohlcv(exchange_id, symbol, timeframe):
    try:
        exchange_class = getattr(ccxt_ws, exchange_id.lower())
        if not exchange_class:
            raise ValueError(f"Exchange {exchange_id} not found in ccxt.pro")
        exchange = exchange_class()
        async for ohlcv in exchange.watch_ohlcv(symbol, timeframe):
            yield pd.DataFrame([ohlcv], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        await exchange.close()
    except AttributeError:
        raise ValueError(f"Invalid exchange ID: {exchange_id}")
    except Exception as e:
        raise RuntimeError(f"Failed to stream OHLCV data: {str(e)}")