import ccxt
import pandas as pd
import pandas_ta as ta
import time
import requests
from datetime import datetime

# ————————— إعدادات البوت (هنحط بياناتك هنا) —————————
TELEGRAM_TOKEN = "8224251097:AAGyBS6Ch6pK9GE0EWUbopuoC1fOg4r_fuk"
CHAT_ID = "@shekovichyaisignals"
# إعدادات الفحص
TIMEFRAME = '15m'
PAIRS_LIMIT = 50  # هنفحص أهم 50 عملة

# ————————— دوال الإرسال والبيانات —————————
def send_msg(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"})
    except:
        pass

def get_market_data():
    exchange = ccxt.binance()
    markets = exchange.load_markets()
    # فلترة وترتيب العملات حسب السيولة
    tickers = exchange.fetch_tickers()
    sorted_tickers = sorted(tickers.items(), key=lambda x: x[1]['quoteVolume'], reverse=True)
    
    pairs = []
    blacklist = ['USDC/USDT', 'FDUSD/USDT', 'TUSD/USDT']
    
    for symbol, _ in sorted_tickers:
        if '/USDT' in symbol and symbol not in blacklist:
            pairs.append(symbol)
            if len(pairs) >= PAIRS_LIMIT: break
    return exchange, pairs

# ————————— المحرك (Logic) —————————
def scan():
    print(f"🔍 Scanning at {datetime.now().strftime('%H:%M')}...")
    exchange, pairs = get_market_data()
    
    for symbol in pairs:
        try:
            bars = exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'vol'])
            
            # المؤشرات
            df['sma55'] = ta.sma(df['close'], 55)
            df['ema_h'] = ta.ema(df['high'], 34)
            df['f3'] = ta.ema(df['close'], 3)
            df['f5'] = ta.ema(df['close'], 5)
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # استراتيجية Mother Strategy (مثال)
            # شرط: السعر فوق SMA 55 + تقاطع EMA 3/5 فوق الـ Ribbon High
            is_uptrend = curr['close'] > curr['sma55']
            cross_up = (curr['f3'] > curr['ema_h']) and (curr['f5'] > curr['ema_h']) and \
                       (prev['f3'] <= prev['ema_h'] or prev['f5'] <= prev['ema_h'])
            
            if is_uptrend and cross_up:
                msg = f"🚀 **SIGNAL DETECTED**\n\nCoin: {symbol}\nPrice: {curr['close']}\nStrategy: Mother Sniper"
                send_msg(msg)
                print(f"✅ Sent alert for {symbol}")
                
            time.sleep(0.1) # راحة عشان الـ API
            
        except:
            continue

# ————————— التشغيل —————————
if __name__ == "__main__":
    send_msg("🤖 Bot Started Successfully!")
    while True:
        scan()
        time.sleep(900) # ينام 15 دقيقة
