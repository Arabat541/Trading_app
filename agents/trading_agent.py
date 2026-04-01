# agents/trading_agent.py

from data.fetcher import get_ohlcv
from indicators.technicals import add_indicators
from notifications.telegram import notify
from strategies.ml_strategy import predict as ml_predict
from execution.binance_executor import buy, sell, get_balance
from datetime import datetime
import json
import os

PARAMS = {
    "BTCUSDT": {"rsi": 40, "sl": 0.05, "tp": 0.06},
    "ETHUSDT": {"rsi": 45, "sl": 0.03, "tp": 0.10},
    "SOLUSDT": {"rsi": 40, "sl": 0.04, "tp": 0.10},
    "BNBUSDT": {"rsi": 40, "sl": 0.03, "tp": 0.10},
}

# Budget par trade en USDT
TRADE_AMOUNT = 200

def generate_signal(df, rsi_threshold, symbol):
    last = df.iloc[-1]
    prev = df.iloc[-2]
    ema200 = df["close"].ewm(span=200).mean().iloc[-1]

    rsi_buy  = (last["rsi"] < rsi_threshold and
                last["macd_diff"] > prev["macd_diff"] and
                last["close"] > ema200)
    rsi_sell = (last["rsi"] > rsi_threshold + 15 and
                last["macd_diff"] < prev["macd_diff"])

    ml_signal, ml_proba = ml_predict(df, symbol)

    if rsi_buy and ml_signal == "BUY" and ml_proba > 0.6:
        return "BUY", ml_proba
    elif rsi_sell and ml_signal == "SELL" and ml_proba < 0.4:
        return "SELL", ml_proba
    else:
        return "HOLD", ml_proba

class TradingAgent:

    def run(self):
        results = []
        alerts = []

        # Vérifie le solde USDT disponible
        usdt_balance = get_balance("USDT")
        print(f"\n  💰 Solde USDT disponible : {usdt_balance:.2f}")

        for symbol, params in PARAMS.items():
            df = get_ohlcv(symbol=symbol, interval="4h")
            df = add_indicators(df)
            signal, ml_proba = generate_signal(df, params["rsi"], symbol)

            order = None

            # Exécution automatique
            if signal == "BUY" and usdt_balance >= TRADE_AMOUNT:
                print(f"  🟢 BUY {symbol} — {TRADE_AMOUNT} USDT")
                order = buy(symbol=symbol, usdt_amount=TRADE_AMOUNT)
                usdt_balance -= TRADE_AMOUNT

            elif signal == "SELL":
                print(f"  🔴 SELL {symbol}")
                order = sell(symbol=symbol, usdt_amount=TRADE_AMOUNT)

            result = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": symbol,
                "price": round(df["close"].iloc[-1], 2),
                "rsi": round(df["rsi"].iloc[-1], 2),
                "macd_diff": round(df["macd_diff"].iloc[-1], 2),
                "ml_proba": float(ml_proba),
                "signal": signal,
                "sl": params["sl"],
                "tp": params["tp"],
                "order_status": order["status"] if order else None
            }
            results.append(result)

            if signal != "HOLD":
                icon = "🟢" if signal == "BUY" else "🔴"
                alerts.append(
                    f"{icon} {signal} {symbol}\n"
                    f"   Prix     : {result['price']} USDT\n"
                    f"   RSI      : {result['rsi']}\n"
                    f"   ML proba : {ml_proba:.1%}\n"
                    f"   SL       : {params['sl'] * 100}%\n"
                    f"   TP       : {params['tp'] * 100}%\n"
                    f"   Ordre    : {result['order_status']}"
                )

        if alerts:
            message = "🤖 TRADING AGENT\n" + "─" * 25 + "\n"
            message += "\n\n".join(alerts)
            notify(message)

        self._log(results)
        return results

    def _log(self, results):
        os.makedirs("logs", exist_ok=True)
        log_file = "logs/trades.json"
        logs = []
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)
        logs.extend(results)
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)

if __name__ == "__main__":
    agent = TradingAgent()
    results = agent.run()

    print(f"\n{'='*50}")
    print(f"  🤖 TRADING AGENT - RSI + ML + EXECUTION")
    print(f"{'='*50}")
    for r in results:
        icon = "🟢" if r["signal"] == "BUY" else "🔴" if r["signal"] == "SELL" else "⚪"
        order = f"[{r['order_status']}]" if r["order_status"] else ""
        print(f"  {icon} {r['symbol']:<10} {r['price']:>10} USDT  RSI:{r['rsi']:>6}  ML:{r['ml_proba']:.1%}  {r['signal']} {order}")
    print(f"{'='*50}\n")