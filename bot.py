import requests
from kiteconnect import KiteConnect
import time
import os
import pandas as pd
from datetime import datetime, timedelta

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
INSTRUMENT_TOKEN = int(os.environ.get("INSTRUMENT_TOKEN"))

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    requests.post(url, data=data)

def fetch_5min():
    to_dt = datetime.now()
    from_dt = to_dt - timedelta(minutes=60)
    data = kite.historical_data(INSTRUMENT_TOKEN, from_dt, to_dt, "5minute")
    df = pd.DataFrame(data)
    if df.empty:
        return None
    df["typ"] = (df["high"] + df["low"] + df["close"]) / 3
    df["tp_vol"] = df["typ"] * df["volume"]
    df["cum_tp_vol"] = df["tp_vol"].cumsum()
    df["cum_vol"] = df["volume"].cumsum()
    df["vwap"] = df["cum_tp_vol"] / df["cum_vol"]
    return df

def pivot_levels(row):
    p = (row["high"] + row["low"] + row["close"]) / 3
    r1 = (2 * p) - row["low"]
    s1 = (2 * p) - row["high"]
    return p, r1, s1

def bot_loop():
    send_telegram("🚀 Indra, your Intraday Bot is LIVE on Render!")

    last_signal = None

    while True:
        try:
            df = fetch_5min()
            if df is None:
                time.sleep(30)
                continue

            last = df.iloc[-1]
            price = last["close"]
            vwap = last["vwap"]

            pivot, r1, s1 = pivot_levels(last)

            if price > vwap and last_signal != "BUY":
                send_telegram(f"📈 BUY SIGNAL\nPrice: {price}\nVWAP: {vwap:.2f}")
                last_signal = "BUY"

            if price < vwap and last_signal != "SELL":
                send_telegram(f"📉 SELL SIGNAL\nPrice: {price}\nVWAP: {vwap:.2f}")
                last_signal = "SELL"

            if price > r1:
                send_telegram(f"🚀 R1 Breakout\nPrice: {price}\nR1: {r1:.2f}")

            if price < s1:
                send_telegram(f"⚠️ S1 Breakdown\nPrice: {price}\nS1: {s1:.2f}")

            time.sleep(60)

        except Exception as e:
            send_telegram("⚠️ ERROR: " + str(e))
            time.sleep(30)

bot_loop()
