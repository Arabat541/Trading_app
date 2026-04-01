# backtest/engine.py

import vectorbt as vbt
import pandas as pd
from data.fetcher import get_ohlcv
from indicators.technicals import add_indicators

def run_backtest(symbol="BTCUSDT", interval="4h"):
    # 1. Données
    df = get_ohlcv(symbol=symbol, interval=interval)
    df = add_indicators(df)

    # 2. Filtre de tendance
    df["ema200"] = df["close"].ewm(span=200).mean()

    close = df["close"]

    # 3. Grid search
    rsi_thresholds = [40, 45, 50, 55]
    sl_values = [0.02, 0.03, 0.04, 0.05]
    tp_values = [0.04, 0.06, 0.08, 0.10]

    best = {"profit": -999, "params": {}}

    for rsi in rsi_thresholds:
        for sl in sl_values:
            for tp in tp_values:
                entries = (
                    (df["rsi"] < rsi) &
                    (df["macd_diff"] > df["macd_diff"].shift(1)) &
                    (df["close"] > df["ema200"])
                )
                exits = (
                    (df["rsi"] > rsi + 15) &
                    (df["macd_diff"] < df["macd_diff"].shift(1))
                )
                pf = vbt.Portfolio.from_signals(
                    close, entries, exits,
                    init_cash=1000, fees=0.001,
                    sl_stop=sl, tp_stop=tp
                )
                profit = pf.total_return() * 100
                if profit > best["profit"]:
                    best["profit"] = profit
                    best["params"] = {"rsi": rsi, "sl": sl, "tp": tp}
                    best["drawdown"] = pf.max_drawdown() * 100
                    best["trades"] = pf.trades.count()

    print(f"\n{'='*40}")
    print(f"  🏆 MEILLEURS PARAMÈTRES - {symbol}")
    print(f"{'='*40}")
    print(f"  RSI seuil   : {best['params']['rsi']}")
    print(f"  Stop Loss   : {best['params']['sl'] * 100}%")
    print(f"  Take Profit : {best['params']['tp'] * 100}%")
    print(f"  Profit      : {best['profit']:.2f}%")
    print(f"  Drawdown    : {best['drawdown']:.2f}%")
    print(f"  Trades      : {best['trades']}")
    print(f"{'='*40}\n")

    return best

if __name__ == "__main__":
    for symbol in ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]:
        run_backtest(symbol=symbol)