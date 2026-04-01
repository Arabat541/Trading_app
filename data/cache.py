# data/cache.py

import pandas as pd
import os
from datetime import datetime, timedelta

CACHE_DIR = "data/cache"
CACHE_DURATION_MINUTES = 60

def get_cache_path(symbol, interval):
    return f"{CACHE_DIR}/{symbol}_{interval}.parquet"

def is_cache_valid(path):
    if not os.path.exists(path):
        return False
    modified = datetime.fromtimestamp(os.path.getmtime(path))
    return datetime.now() - modified < timedelta(minutes=CACHE_DURATION_MINUTES)

def load_cache(symbol, interval):
    path = get_cache_path(symbol, interval)
    if is_cache_valid(path):
        df = pd.read_parquet(path)
        print(f"  📦 Cache {symbol} {interval} ({len(df)} bougies)")
        return df
    return None

def save_cache(df, symbol, interval):
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = get_cache_path(symbol, interval)
    df.to_parquet(path)