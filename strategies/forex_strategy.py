# strategies/forex_strategy.py

import pandas as pd
import ta
from data.forex_fetcher import get_forex_yfinance
from data.cache import load_cache, save_cache

FOREX_PARAMS = {
    "EUR_USD": {"rsi": 45, "sl": 0.0015, "tp": 0.003},   # 15 pips SL, 30 pips TP
    "GBP_USD": {"rsi": 45, "sl": 0.0020, "tp": 0.004},   # 20 pips SL, 40 pips TP
    "XAU_USD": {"rsi": 45, "sl": 0.005,  "tp": 0.010},   # Or : 0.5% SL, 1% TP
}

def add_forex_indicators(df):
    df = df.copy()
    df["rsi"]        = ta.momentum.RSIIndicator(df["close"], window=14).rsi()
    macd             = ta.trend.MACD(df["close"])
    df["macd"]       = macd.macd()
    df["macd_signal"]= macd.macd_signal()
    df["macd_diff"]  = macd.macd_diff()
    df["ema50"]      = df["close"].ewm(span=50).mean()
    df["ema200"]     = df["close"].ewm(span=200).mean()
    bb               = ta.volatility.BollingerBands(df["close"])
    df["bb_upper"]   = bb.bollinger_hband()
    df["bb_lower"]   = bb.bollinger_lband()
    df["atr"]        = ta.volatility.AverageTrueRange(
                           df["high"], df["low"], df["close"]
                       ).average_true_range()
    df.dropna(inplace=True)
    return df

def generate_forex_signal(df, rsi_threshold=45):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Tendance haussière confirmée
    trend_up = last["ema50"] > last["ema200"]
    trend_dn = last["ema50"] < last["ema200"]

    # Signal BUY
    if (last["rsi"] < rsi_threshold and
        last["macd_diff"] > prev["macd_diff"] and
        trend_up):
        return "BUY"

    # Signal SELL
    elif (last["rsi"] > (100 - rsi_threshold) and
          last["macd_diff"] < prev["macd_diff"] and
          trend_dn):
        return "SELL"

    return "HOLD"

if __name__ == "__main__":
    pairs = ["EUR_USD", "GBP_USD", "XAU_USD"]

    print(f"\n{'='*50}")
    print(f"  💱 FOREX AGENT - SIGNAUX")
    print(f"{'='*50}")

    for pair in pairs:
        df = get_forex_yfinance(pair)
        if df is None:
            continue
        df = add_forex_indicators(df)
        params = FOREX_PARAMS.get(pair, {"rsi": 45})
        signal = generate_forex_signal(df, params["rsi"])

        icon = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
        print(f"  {icon} {pair:<10} {df['close'].iloc[-1]:.5f}  "
              f"RSI:{df['rsi'].iloc[-1]:.1f}  "
              f"EMA50{'>'if df['ema50'].iloc[-1]>df['ema200'].iloc[-1] else '<'}EMA200  "
              f"{signal}")

    print(f"{'='*50}\n")