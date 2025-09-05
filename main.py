from flask import Flask, request
import threading
import os
from binance.client import Client
import pandas as pd
import datetime as dt
import time

app = Flask(__name__)

# ✅ Binance API 설정 (.env에서 읽어옴)
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

client = Client(api_key, api_secret)
client.API_URL = 'https://testnet.binance.vision/api'  # 테스트넷 URL

symbol = "XRPUSDT"
interval = Client.KLINE_INTERVAL_15MINUTE
limit = 100

# ✅ 하이브리드 전략 (MACD + RSI)
def get_technical_signals():
    klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)

    # RSI 계산
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD 계산
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()

    last = df.iloc[-1]

    signal = "HOLD"
    if last['macd'] > last['signal'] and last['rsi'] < 30:
        signal = "BUY"
    elif last['macd'] < last['signal'] and last['rsi'] > 70:
        signal = "SELL"

    print(f"[SIGNAL] RSI={last['rsi']:.2f}, MACD={last['macd']:.5f}, Signal={last['signal']:.5f} → {signal}")
    return signal

# ✅ 매수/매도 테스트 주문
def execute_trade(signal):
    if signal == "BUY":
        try:
            client.create_test_order(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=10
            )
            print("🟢 매수 시그널: 테스트 주문 완료")
        except Exception as e:
            print(f"매수 실패: {e}")
    elif signal == "SELL":
        try:
            client.create_test_order(
                symbol=symbol,
                side=Client.SIDE_SELL,
                type=Client.ORDER_TYPE_MARKET,
                quantity=10
            )
            print("🔴 매도 시그널: 테스트 주문 완료")
        except Exception as e:
            print(f"매도 실패: {e}")
    else:
        print("⚪ HOLD: 거래 없음")

# ✅ 실행 쓰레드
def run_bot():
    print(f"\n⏰ 전략 실행: {dt.datetime.now()}")
    signal = get_technical_signals()
    execute_trade(signal)

# ✅ Railway에서 호출될 엔드포인트
@app.route("/", methods=["POST"])
def trigger():
    threading.Thread(target=run_bot).start()
    return "✅ 전략 실행됨", 200

@app.route("/", methods=["GET"])
def health():
    return "🟢 OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
