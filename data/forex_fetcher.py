# data/forex_fetcher.py

import pandas as pd
import requests
from datetime import datetime, timedelta
from data.cache import load_cache, save_cache

# Paires Forex à trader
FOREX_PAIRS = ["EUR_USD", "GBP_USD", "USD_JPY", "XAU_USD"]  # XAU = Or

def get_forex_ohlcv(pair="EUR_USD", granularity="H4", count=5000, force_refresh=False):
    """
    Récupère les données Forex via OANDA API publique
    granularity: M15, H1, H4, D
    """
    cache_key = f"forex_{pair}"
    cached = load_cache(cache_key, granularity, force_refresh=force_refresh)
    if cached is not None:
        return cached

    print(f"  📥 Téléchargement Forex {pair} {granularity}...")

    url = f"https://api-fxtrade.oanda.com/v3/instruments/{pair}/candles"
    headers = {"Content-Type": "application/json"}
    params = {
        "granularity": granularity,
        "count": count,
        "price": "M"  # Mid price
    }

    # OANDA nécessite un token pour l'API v3
    # On utilise une alternative gratuite : Alpha Vantage ou Yahoo Finance
    # Fallback vers yfinance
    return get_forex_yfinance(pair, granularity)

def get_forex_yfinance(pair="EUR_USD", granularity="H4", force_refresh=False):
    """
    Récupère les données Forex via yfinance (gratuit, sans clé API)
    """
    import yfinance as yf

    # Conversion format OANDA → yfinance
    yf_symbols = {
        "EUR_USD": "EURUSD=X",
        "GBP_USD": "GBPUSD=X",
        "USD_JPY": "USDJPY=X",
        "XAU_USD": "GC=F",     # Or futures
        "USD_XOF": "USDXOF=X", # CFA Franc (si disponible)
    }

    intervals = {
        "H1": "1h",
        "H4": "1h",  # yfinance n'a pas H4 → on resample
        "D":  "1d"
    }

    cache_key = f"forex_{pair}"
    cached = load_cache(cache_key, granularity, force_refresh=force_refresh)
    if cached is not None:
        return cached

    symbol = yf_symbols.get(pair, pair)
    interval = intervals.get(granularity, "1h")

    print(f"  📥 Téléchargement {pair} ({symbol}) via yfinance...")

    ticker = yf.Ticker(symbol)
    df = ticker.history(period="2y", interval=interval)

    if df.empty:
        print(f"  ❌ Pas de données pour {pair}")
        return None

    # Renomme les colonnes
    df = df[["Open", "High", "Low", "Close", "Volume"]]
    df.columns = ["open", "high", "low", "close", "volume"]
    df.index.name = "time"

    # Resample en H4 si nécessaire
    if granularity == "H4":
        df = df.resample("4h").agg({
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum"
        }).dropna()

    print(f"  ✅ {len(df)} bougies ({df.index[0].date()} → {df.index[-1].date()})")

    save_cache(df, cache_key, granularity)
    return df

if __name__ == "__main__":
    import sys
    sys.path.append(".")

    for pair in ["EUR_USD", "GBP_USD", "XAU_USD"]:
        df = get_forex_yfinance(pair)
        if df is not None:
            print(df.tail(3))
            print()