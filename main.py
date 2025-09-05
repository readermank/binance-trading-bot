import os
import pandas as pd
from binance.client import Client
from ta.momentum import RSIIndicator
from ta.trend import MACD
import time

# API 키 불러오기 (Railway Variables 또는 .env 사용)
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

client = Client(api_key, api_secret)
client.API_URL = 'https://testnet.binance.vision/api'

symbol = "XRPUSDT"
interval = Client.KLINE_INTERVAL_1HOUR
lookback = "200"

def get_klines():
    klines = client.get_historical_klines(symbol, interval, lookback + " hour ago UTC")
    df = pd.DataFrame(klines, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
    ])
    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df.set_index("time", inplace=True)
    df = df.astype(float)
    return df

def apply_indicators(df):
    df["rsi"] = RSIIndicator(close=df["close"], window=14).rsi()
    macd = MACD(close=df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_hist"] = macd.macd_diff()
    df["volume_avg"] = df["volume"].rolling(window=20).mean()
    return df

def strategy_signal(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # 조건 판단
    macd_cross_up = prev["macd"] < prev["macd_signal"] and latest["macd"] > latest["macd_signal"]
    macd_cross_down = prev["macd"] > prev["macd_signal"] and latest["macd"] < latest["macd_signal"]

    rsi_buy = latest["rsi"] < 30
    rsi_sell = latest["rsi"] > 70

    volume_filter = latest["volume"] > latest["volume_avg"]

    # 종합 판단
    if macd_cross_up and rsi_buy and volume_filter:
        return "BUY"
    elif macd_cross_down and rsi_sell and volume_filter:
        return "SELL"
    else:
        return "HOLD"

def execute_trade(signal):
    if signal == "BUY":
        print("매수 조건 충족 → 매수 시도")
        client.create_test_order(
            symbol=symbol,
            side=Client.SIDE_BUY,
            type=Client.ORDER_TYPE_MARKET,
            quantity=10
        )
    elif signal == "SELL":
        print("매도 조건 충족 → 매도 시도")
        client.create_test_order(
            symbol=symbol,
            side=Client.SIDE_SELL,
            type=Client.ORDER_TYPE_MARKET,
            quantity=10
        )
    else:
        print("조건 불충족 → 대기 중")

def main():
    df = get_klines()
    df = apply_indicators(df)
    signal = strategy_signal(df)
    print(f"현재 전략 시그널: {signal}")
    execute_trade(signal)

if __name__ == "__main__":
    main()
