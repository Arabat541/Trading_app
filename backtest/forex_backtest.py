# backtest/forex_backtest.py

import vectorbt as vbt
from data.forex_fetcher import get_forex_yfinance
from strategies.forex_strategy import add_forex_indicators

def run_forex_backtest(pair="EUR_USD"):
    df = get_forex_yfinance(pair, force_refresh=False)
    if df is None:
        return

    df = add_forex_indicators(df)

    close = df["close"]

    # Grid search
    rsi_thresholds = [40, 45, 50, 55]
    sl_values      = [0.001, 0.002, 0.003, 0.005]
    tp_values      = [0.002, 0.004, 0.006, 0.010]

    best = {"profit": -999, "params": {}}

    for rsi in rsi_thresholds:
        for sl in sl_values:
            for tp in tp_values:
                entries = (
                    (df["rsi"] < rsi) &
                    (df["macd_diff"] > df["macd_diff"].shift(1)) &
                    (df["ema50"] > df["ema200"])
                )
                exits = (
                    (df["rsi"] > (100 - rsi)) &
                    (df["macd_diff"] < df["macd_diff"].shift(1))
                )

                pf = vbt.Portfolio.from_signals(
                    close, entries, exits,
                    init_cash=10000,
                    fees=0.0001,  # 1 pip de spread
                    sl_stop=sl,
                    tp_stop=tp
                )

                profit = pf.total_return() * 100
                if profit > best["profit"]:
                    best["profit"]   = profit
                    best["params"]   = {"rsi": rsi, "sl": sl, "tp": tp}
                    best["drawdown"] = pf.max_drawdown() * 100
                    best["trades"]   = pf.trades.count()

    print(f"\n{'='*40}")
    print(f"  🏆 BACKTEST FOREX - {pair}")
    print(f"{'='*40}")
    print(f"  RSI seuil   : {best['params']['rsi']}")
    print(f"  Stop Loss   : {best['params']['sl'] * 100:.2f}%")
    print(f"  Take Profit : {best['params']['tp'] * 100:.2f}%")
    print(f"  Profit      : {best['profit']:.2f}%")
    print(f"  Drawdown    : {best['drawdown']:.2f}%")
    print(f"  Trades      : {best['trades']}")
    print(f"{'='*40}\n")

    return best

if __name__ == "__main__":
    for pair in ["EUR_USD", "GBP_USD", "XAU_USD"]:
        run_forex_backtest(pair)