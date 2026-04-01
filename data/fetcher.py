# data/fetcher.py

from binance.client import Client
import pandas as pd
from data.cache import load_cache, save_cache

client = Client()

def get_ohlcv(symbol="BTCUSDT", interval="4h", years=3):
    # Vérifie le cache d'abord
    cached = load_cache(symbol, interval)
    if cached is not None:
        return cached

    all_klines = []
    last_id = None

    intervals_per_day = {
        "1h": 24, "4h": 6, "1d": 1, "15m": 96
    }
    days = years * 365
    nb_candles = days * intervals_per_day.get(interval, 6)
    nb_requests = (nb_candles // 1000) + 1

    print(f"  📥 Téléchargement {symbol} {interval} ({years} ans, ~{nb_candles} bougies)...")

    for i in range(nb_requests):
        params = dict(symbol=symbol, interval=interval, limit=1000)
        if last_id:
            params["endTime"] = last_id

        klines = client.get_klines(**params)
        if not klines:
            break

        all_klines = klines + all_klines
        last_id = klines[0][0] - 1

    df = pd.DataFrame(all_klines, columns=[
        "time", "open", "high", "low", "close", "volume",
        "close_time", "qav", "trades", "tbbav", "tbqav", "ignore"
    ])

    df["time"] = pd.to_datetime(df["time"], unit="ms")
    df.set_index("time", inplace=True)
    df = df[["open", "high", "low", "close", "volume"]].astype(float)
    df = df[~df.index.duplicated()].sort_index()

    print(f"  ✅ {len(df)} bougies récupérées ({df.index[0].date()} → {df.index[-1].date()})")

    # Sauvegarde en cache
    save_cache(df, symbol, interval)

    return df

if __name__ == "__main__":
    for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]:
        df = get_ohlcv(symbol=symbol)
        print()