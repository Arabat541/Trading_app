# agents/forex_agent.py

from data.forex_fetcher import get_forex_yfinance
from strategies.forex_strategy import add_forex_indicators, generate_forex_signal
from strategies.forex_ml_strategy import predict_forex
from notifications.telegram import notify
from datetime import datetime
import json
import os

FOREX_PARAMS = {
    "EUR_USD": {"rsi": 40, "sl": 0.002, "tp": 0.006},
    "GBP_USD": {"rsi": 45, "sl": 0.005, "tp": 0.006},
    "XAU_USD": {"rsi": 45, "sl": 0.003, "tp": 0.010},
}

class ForexAgent:

    def run(self):
        results = []
        alerts = []

        for pair, params in FOREX_PARAMS.items():
            df = get_forex_yfinance(pair)
            if df is None:
                continue

            df = add_forex_indicators(df)

            # Signal RSI classique
            rsi_signal = generate_forex_signal(df, params["rsi"])

            # Signal ML
            try:
                ml_signal, ml_proba = predict_forex(df, pair)
            except FileNotFoundError:
                ml_signal, ml_proba = "HOLD", 0.5

            # Double confirmation RSI + ML
            # Exception : XAU avec ML très confiant
            if rsi_signal == "BUY" and ml_signal == "BUY" and ml_proba > 0.6:
                signal = "BUY"
            elif rsi_signal == "SELL" and ml_signal == "SELL" and ml_proba < 0.4:
                signal = "SELL"
            # XAU/USD — ML seul suffit si confiance > 75%
            elif pair == "XAU_USD" and ml_signal == "BUY" and ml_proba > 0.75:
                signal = "BUY"
            elif pair == "XAU_USD" and ml_signal == "SELL" and ml_proba < 0.25:
                signal = "SELL"
            else:
                signal = "HOLD"

            result = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "pair": pair,
                "price": round(df["close"].iloc[-1], 5),
                "rsi": round(df["rsi"].iloc[-1], 2),
                "macd_diff": round(df["macd_diff"].iloc[-1], 6),
                "atr": round(df["atr"].iloc[-1], 6),
                "ml_proba": float(ml_proba),
                "rsi_signal": rsi_signal,
                "signal": signal,
                "sl": params["sl"],
                "tp": params["tp"],
            }
            results.append(result)

            if signal != "HOLD":
                icon = "🟢" if signal == "BUY" else "🔴"
                alerts.append(
                    f"{icon} {signal} {pair}\n"
                    f"   Prix     : {result['price']}\n"
                    f"   RSI      : {result['rsi']}\n"
                    f"   ML proba : {ml_proba:.1%}\n"
                    f"   SL       : {params['sl'] * 100:.2f}%\n"
                    f"   TP       : {params['tp'] * 100:.2f}%"
                )

        if alerts:
            message = "💱 FOREX AGENT\n" + "─" * 25 + "\n"
            message += "\n\n".join(alerts)
            notify(message)

        self._log(results)
        return results

    def _log(self, results):
        os.makedirs("logs", exist_ok=True)
        log_file = "logs/forex_trades.json"
        logs = []
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                logs = json.load(f)
        logs.extend(results)
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=2)

if __name__ == "__main__":
    agent = ForexAgent()
    results = agent.run()

    print(f"\n{'='*55}")
    print(f"  💱 FOREX AGENT - RSI + ML")
    print(f"{'='*55}")
    for r in results:
        icon = "🟢" if r["signal"] == "BUY" else "🔴" if r["signal"] == "SELL" else "⚪"
        print(f"  {icon} {r['pair']:<10} {r['price']:>10}  "
              f"RSI:{r['rsi']:>6}  ML:{r['ml_proba']:.1%}  "
              f"RSI_sig:{r['rsi_signal']:<5}  {r['signal']}")
    print(f"{'='*55}\n")