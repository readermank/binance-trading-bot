# main.py
import time
from binance.client import Client
import os

api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")

# 확인용 출력 (배포 시 제거!)
print("API_KEY:", api_key)
print("API_SECRET:", api_secret)

client = Client(api_key, api_secret)
client.API_URL = 'https://testnet.binance.vision/api'  # 반드시 설정

def simple_strategy():
    price = float(client.get_symbol_ticker(symbol="XRPUSDT")["price"])
    print("현재 XRP 가격:", price)
    if price < 0.45:
        order = client.create_test_order(
            symbol='XRPUSDT',
            side='BUY',
            type='MARKET',
            quantity=30
        )
        print("📈 매수 시뮬레이션:", order)
    elif price > 0.55:
        order = client.create_test_order(
            symbol='XRPUSDT',
            side='SELL',
            type='MARKET',
            quantity=30
        )
        print("📉 매도 시뮬레이션:", order)

if __name__ == "__main__":
    while True:
        simple_strategy()
        time.sleep(30)  # 30초 간격 실행
