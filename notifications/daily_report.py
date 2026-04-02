# notifications/daily_report.py

from agents.position_manager import get_summary, get_open_positions, load_positions
from notifications.telegram import notify
from execution.binance_executor import get_balance, get_price
from datetime import datetime

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

def generate_daily_report():
    summary = get_summary()
    open_pos = get_open_positions()
    today = datetime.now().strftime("%Y-%m-%d")

    # Trades du jour
    all_positions = load_positions()
    today_trades = [
        p for p in all_positions
        if p.get("open_time", "").startswith(today)
    ]

    # Solde actuel
    usdt_balance = get_balance("USDT")

    # Prix actuels
    prices = {}
    for symbol in SYMBOLS:
        prices[symbol] = get_price(symbol)

    # PnL non réalisé sur positions ouvertes
    unrealized_pnl = 0
    for p in open_pos:
        current = prices.get(p["symbol"], p["entry_price"])
        unrealized_pnl += (current - p["entry_price"]) * p["quantity"]

    # Construction du message
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    message = f"📊 RAPPORT QUOTIDIEN\n"
    message += f"🕐 {now}\n"
    message += "─" * 25 + "\n\n"

    # Portefeuille
    message += f"💰 PORTEFEUILLE\n"
    message += f"   Solde USDT     : {usdt_balance:.2f} USDT\n"
    message += f"   PnL réalisé    : {summary['total_pnl']:+.2f} USDT\n"
    message += f"   PnL non réalisé: {unrealized_pnl:+.2f} USDT\n\n"

    # Performance
    message += f"📈 PERFORMANCE\n"
    message += f"   Win rate       : {summary['win_rate']}%\n"
    message += f"   Trades gagnants: {summary['wins']}\n"
    message += f"   Trades perdants: {summary['losses']}\n"
    message += f"   Total trades   : {summary['closed']}\n\n"

    # Trades du jour
    message += f"📅 TRADES AUJOURD'HUI : {len(today_trades)}\n"
    if today_trades:
        for t in today_trades:
            status = "🟢 OPEN" if t["status"] == "OPEN" else (
                "✅ WIN" if t.get("pnl", 0) > 0 else "❌ LOSS"
            )
            pnl_str = f"{t['pnl']:+.2f} USDT" if t.get("pnl") else "en cours"
            message += f"   {t['symbol']:<10} {status} | {pnl_str}\n"

    # Positions ouvertes
    message += f"\n📂 POSITIONS OUVERTES : {len(open_pos)}\n"
    if open_pos:
        for p in open_pos:
            current = prices.get(p["symbol"], p["entry_price"])
            pnl = (current - p["entry_price"]) * p["quantity"]
            pnl_pct = (current - p["entry_price"]) / p["entry_price"] * 100
            icon = "📈" if pnl > 0 else "📉"
            message += f"   {icon} {p['symbol']:<10} {pnl:+.2f} USDT ({pnl_pct:+.2f}%)\n"
    else:
        message += f"   Aucune position ouverte\n"

    # Prix du marché
    message += f"\n💹 MARCHÉ\n"
    for symbol, price in prices.items():
        message += f"   {symbol:<10} {price:.2f} USDT\n"

    return message

if __name__ == "__main__":
    report = generate_daily_report()
    print(report)
    notify(report)
    print("✅ Rapport envoyé sur Telegram")