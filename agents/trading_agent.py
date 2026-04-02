# agents/trading_agent.py

from data.fetcher import get_ohlcv
from indicators.technicals import add_indicators
from notifications.telegram import notify
from strategies.ml_strategy import predict as ml_predict
from execution.binance_executor import buy, sell, get_balance, get_price
from agents.position_manager import (
    open_position, close_position,
    check_sl_tp, get_summary, can_open_trade, is_already_open
)
from datetime import datetime
import json
import os

PARAMS = {
    "BTCUSDT": {"rsi": 40, "sl": 0.05, "tp": 0.06},
    "ETHUSDT": {"rsi": 45, "sl": 0.03, "tp": 0.10},
    "SOLUSDT": {"rsi": 40, "sl": 0.04, "tp": 0.10},
    "BNBUSDT": {"rsi": 40, "sl": 0.03, "tp": 0.10},
}

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

        usdt_balance = get_balance("USDT")
        print(f"\n  💰 Solde USDT : {usdt_balance:.2f}")

        # 1. Vérifie SL/TP sur positions ouvertes
        current_prices = {s: get_price(s) for s in PARAMS.keys()}
        closed = check_sl_tp(current_prices)
        for c in closed:
            icon = "✅" if c["pnl"] > 0 else "❌"
            alerts.append(
                f"{icon} {c['close_reason']} {c['symbol']}\n"
                f"   PnL : {c['pnl']:+.2f} USDT ({c['pnl_pct']:+.2f}%)"
            )

        # 2. Analyse chaque paire
        for symbol, params in PARAMS.items():
            df = get_ohlcv(symbol=symbol, interval="4h")
            df = add_indicators(df)
            signal, ml_proba = generate_signal(df, params["rsi"], symbol)
            price = current_prices[symbol]

            order = None

            if signal == "BUY":
                if can_open_trade(symbol) and usdt_balance >= TRADE_AMOUNT:
                    order = buy(symbol=symbol, usdt_amount=TRADE_AMOUNT)
                    if order:
                        open_position(symbol, price, signal, params["sl"], params["tp"])
                        usdt_balance -= TRADE_AMOUNT

            elif signal == "SELL":
                if is_already_open(symbol):
                    order = sell(symbol=symbol, usdt_amount=TRADE_AMOUNT)
                    if order:
                        close_position(symbol, price, reason="SIGNAL")

            result = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "symbol": symbol,
                "price": round(price, 2),
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
                    f"   Prix     : {price} USDT\n"
                    f"   RSI      : {result['rsi']}\n"
                    f"   ML proba : {ml_proba:.1%}\n"
                    f"   SL       : {params['sl'] * 100}%\n"
                    f"   TP       : {params['tp'] * 100}%"
                )

        # 3. Résumé positions
        summary = get_summary()

        if alerts:
            message = "🤖 TRADING AGENT\n" + "─" * 25 + "\n"
            message += "\n\n".join(alerts)
            message += f"\n\n📊 PnL total : {summary['total_pnl']:+.2f} USDT"
            message += f"\n🏆 Win rate  : {summary['win_rate']}%"
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

    summary = get_summary()

    print(f"\n{'='*50}")
    print(f"  🤖 TRADING AGENT - COMPLET")
    print(f"{'='*50}")
    for r in results:
        icon = "🟢" if r["signal"] == "BUY" else "🔴" if r["signal"] == "SELL" else "⚪"
        order = f"[{r['order_status']}]" if r["order_status"] else ""
        print(f"  {icon} {r['symbol']:<10} {r['price']:>10} USDT  RSI:{r['rsi']:>6}  ML:{r['ml_proba']:.1%}  {r['signal']} {order}")
    print(f"{'='*50}")
    print(f"  📊 PnL total  : {summary['total_pnl']:+.2f} USDT")
    print(f"  🏆 Win rate   : {summary['win_rate']}%")
    print(f"  📂 Ouvertes   : {summary['open']}")
    print(f"  ✅ Fermées    : {summary['closed']}")
    print(f"{'='*50}\n")