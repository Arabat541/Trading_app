# data/external.py

import requests
import pandas as pd
from pycoingecko import CoinGeckoAPI
from datetime import datetime, timedelta

cg = CoinGeckoAPI()

# ─────────────────────────────────────────
# 1. FEAR & GREED INDEX
# ─────────────────────────────────────────

def get_fear_greed(limit=7000):
    """Récupère l'historique Fear & Greed (1 valeur par jour)"""
    url = f"https://api.alternative.me/fng/?limit={limit}&format=json"
    res = requests.get(url, timeout=10)
    data = res.json()["data"]

    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="s")
    df.set_index("timestamp", inplace=True)
    df["fear_greed"] = df["value"].astype(int)
    df = df[["fear_greed"]].sort_index()

    print(f"  ✅ Fear & Greed : {len(df)} jours ({df.index[0].date()} → {df.index[-1].date()})")
    return df

# ─────────────────────────────────────────
# 2. DOMINANCE BTC + MARKET CAP
# ─────────────────────────────────────────

def get_btc_dominance():
    """Récupère la dominance BTC actuelle via CoinGecko"""
    data = cg.get_global()
    dominance = data["market_cap_percentage"]["btc"]
    total_mcap = data["total_market_cap"]["usd"]

    print(f"  ✅ BTC Dominance : {dominance:.1f}%")
    print(f"  ✅ Market Cap total : ${total_mcap/1e12:.2f}T")

    return {
        "btc_dominance": round(dominance, 2),
        "total_market_cap": total_mcap
    }

# ─────────────────────────────────────────
# 3. MERGE AVEC OHLCV
# ─────────────────────────────────────────

def enrich_with_external(df):
    """Ajoute Fear & Greed au dataframe OHLCV"""
    fg = get_fear_greed()

    # Resample en 4H pour matcher le dataframe OHLCV
    fg_4h = fg.resample("4h").ffill()

    # Merge
    df = df.join(fg_4h, how="left")
    df["fear_greed"] = df["fear_greed"].ffill()

    # Catégories utiles pour le ML
    df["is_fear"]    = (df["fear_greed"] < 30).astype(int)  # peur extrême → opportunité achat
    df["is_greed"]   = (df["fear_greed"] > 70).astype(int)  # avidité → risque vente
    df["fg_change"]  = df["fear_greed"].diff()               # momentum du sentiment

    # Dominance BTC actuelle (valeur statique ajoutée)
    dom = get_btc_dominance()
    df["btc_dominance"] = dom["btc_dominance"]

    print(f"  ✅ Données externes ajoutées au dataframe")
    return df

if __name__ == "__main__":
    from data.fetcher import get_ohlcv
    from indicators.technicals import add_indicators

    df = get_ohlcv(symbol="BTCUSDT")
    df = add_indicators(df)
    df = enrich_with_external(df)

    print(f"\n📊 Aperçu des données enrichies :")
    print(df[["close", "rsi", "fear_greed", "is_fear", "is_greed", "btc_dominance"]].tail(5))