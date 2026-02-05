import asyncio, time
from telethon import TelegramClient, events
import ccxt
import numpy as np
# 🔹 Wprowadź swoje dane
API_ID = 38797310              # Twój API_ID z my.telegram.org
API_HASH = "124a85bdb9cd7263d79d60c1df9cb079"        # Twój API_HASH
BOT_TOKEN = "8508629876:AAFd1q7R2PRkEF4R-ZtK5XssaAszZr1qXRM"      # Token od BotFather
DEST_CHAT = -1003759735479            # Twój chat ID w Telegramie
# 🔹 Parametry bota
TIMEFRAMES = ["15m", "1h"]
CHECK_INTERVAL = 120  # w sekundach
TP_LEVELS = [0.5, 1.0, 1.5]  # procenty TP
SL_PERCENT = 0.5  # procent SL
COOLDOWN = 3600  # czas przed ponownym wysłaniem sygnału dla tej samej pary
TOP_SIGNALS = 5   # maksymalna liczba sygnałów na rundę
# 🔹 Połączenie z Telegramem
client = TelegramClient("vipbot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)
# 🔹 Połączenie z BloFin
exchange = ccxt.blofin({"enableRateLimit": True})
last_signal = {}
# 🔹 Funkcje techniczne
def ema(prices, period):
    return np.mean(prices[-period:])
def rsi(prices, period=14):
    d = np.diff(prices)
    u = [x for x in d if x > 0]
    dn = [-x for x in d if x < 0]
    au = np.mean(u[-period:]) if u else 0.0001
    ad = np.mean(dn[-period:]) if dn else 0.0001
    rs = au / ad
    return 100 - (100 / (1 + rs))
def score_symbol(symbol):
    score = 0
    for tf in TIMEFRAMES:
        try:
            c = exchange.fetch_ohlcv(symbol, tf, limit=50)
            closes = [x[4] for x in c]
            vols = [x[5] for x in c]
            if closes[-1] > ema(closes, 20): score += 1
            if ema(closes, 5) > ema(closes, 20): score += 1
            if rsi(closes) < 40: score += 1
            if vols[-1] > np.mean(vols[-20:]): score += 1
        except:
            pass
    return score
def targets(entry_price):
    tps = [round(entry_price * (1 + t/100), 4) for t in TP_LEVELS]
    sl = round(entry_price * (1 - SL_PERCENT/100), 4)
    return tps, sl
# 🔹 Start command
@client.on(events.NewMessage(pattern="/start"))
async def start(e):
    await e.respond("✅ VIP Signal Bot is running!")
# 🔹 Główna funkcja
async def main():
    markets = [m for m in exchange.load_markets() if m.endswith("/USDT")]
    await client.send_message(DEST_CHAT, "🚀 VIP Bot Started")
    while True:
        found = []
        for s in markets:
            if s in last_signal and time.time() - last_signal[s] < COOLDOWN:
                continue
            try:
                sc = score_symbol(s)
                if sc >= 6:
                    price = exchange.fetch_ticker(s)["last"]
                    tps, sl = targets(price)
                    found.append((sc, s, price, tps, sl))
            except:
                pass
        found.sort(reverse=True)
        for sc, s, p, tps, sl in found[:TOP_SIGNALS]:
            msg = f"🔥 VIP SIGNAL\n{s}\nEntry: {p}\nTP1: {tps[0]}\nTP2: {tps[1]}\nTP3: {tps[2]}\nSL: {sl}\nScore: {sc}/8"
            await client.send_message(DEST_CHAT, msg)
            last_signal[s] = time.time()
            await asyncio.sleep(1)
        await asyncio.sleep(CHECK_INTERVAL)
with client:
    client.loop.run_until_complete(main())

