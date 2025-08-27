import time
import requests
import pandas as pd
from binance.client import Client
from binance.exceptions import BinanceAPIException
import talib

# Telegram secrets (GitHub injects them at runtime)
import os
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Binance client (public data, no API key needed)
client = Client()

# Coins to track
COINS = ["ETHUSDT", "BTCUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"]

# Timeframes
TIMEFRAMES = ["1h", "4h"]

def send_telegram(message: str):
    """Send plain text alert to Telegram"""
    if TELEGRAM_TOKEN and CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message}
        try:
            requests.post(url, data=data, timeout=10)
        except Exception as e:
            print("Telegram error:", e)

def fetch_klines(symbol, interval, limit=100):
    """Fetch OHLCV from Binance"""
    try:
        klines = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        df = pd.DataFrame(klines, columns=[
            "timestamp","open","high","low","close","volume",
            "close_time","qav","trades","tb_base","tb_quote","ignore"
        ])
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        return df
    except BinanceAPIException as e:
        print("Binance error:", e)
        return None

def analyze(df):
    """Simple candlestick + RSI analysis"""
    if df is None or df.empty:
        return None

    close = df["close"].values
    rsi = talib.RSI(close, timeperiod=14)
    last_rsi = rsi[-1]

    signal = None
    if last_rsi > 70:
        signal = "Overbought (Sell)"
    elif last_rsi < 30:
        signal = "Oversold (Buy)"

    # Candlestick pattern: Hammer, Doji, Engulfing
    hammer = talib.CDLHAMMER(df["open"], df["high"], df["low"], df["close"])[-1]
    doji = talib.CDLDOJI(df["open"], df["high"], df["low"], df["close"])[-1]
    engulf = talib.CDLENGULFING(df["open"], df["high"], df["low"], df["close"])[-1]

    patterns = []
    if hammer != 0: patterns.append("Hammer")
    if doji != 0: patterns.append("Doji")
    if engulf != 0: patterns.append("Engulfing")

    return signal, patterns

def main():
    send_telegram("🚀 CryptoSignalPro started. Monitoring coins...")

    while True:
        for coin in COINS:
            for tf in TIMEFRAMES:
                df = fetch_klines(coin, tf, 100)
                result = analyze(df)
                if result:
                    signal, patterns = result
                    msg = f"[{coin} - {tf}] Signal: {signal}, Patterns: {', '.join(patterns) if patterns else 'None'}"
                    print(msg)
                    send_telegram(msg)
        time.sleep(300)  # every 5 minutes

if __name__ == "__main__":
    main()
