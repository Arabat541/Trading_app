# agents/position_manager.py

import json
import os
from datetime import datetime

POSITIONS_FILE = "logs/positions.json"

# Règles de gestion du risque
MAX_POSITIONS = 2        # max 2 trades ouverts simultanément
MAX_CAPITAL_PER_TRADE = 200   # max 200 USDT par trade
MAX_DAILY_LOSS = 500     # stop trading si perte > 500 USDT/jour
CAPITAL_TOTAL = 10000    # capital total disponible

def load_positions():
    if not os.path.exists(POSITIONS_FILE):
        return []
    with open(POSITIONS_FILE, "r") as f:
        return json.load(f)

def save_positions(positions):
    os.makedirs("logs", exist_ok=True)
    with open(POSITIONS_FILE, "w") as f:
        json.dump(positions, f, indent=2)

def get_open_positions():
    return [p for p in load_positions() if p["status"] == "OPEN"]

def is_already_open(symbol):
    open_pos = get_open_positions()
    return any(p["symbol"] == symbol for p in open_pos)

def can_open_trade(symbol):
    open_pos = get_open_positions()

    # Vérifications
    if is_already_open(symbol):
        print(f"  ⚠️  Position déjà ouverte sur {symbol}")
        return False

    if len(open_pos) >= MAX_POSITIONS:
        print(f"  ⚠️  Max positions atteint ({MAX_POSITIONS})")
        return False

    if daily_loss() >= MAX_DAILY_LOSS:
        print(f"  🛑 Perte journalière max atteinte — trading stoppé")
        return False

    return True

def daily_loss():
    positions = load_positions()
    today = datetime.now().strftime("%Y-%m-%d")
    losses = [
        p.get("pnl", 0) for p in positions
        if p["status"] == "CLOSED" and
        p.get("close_time", "").startswith(today) and
        p.get("pnl", 0) < 0
    ]
    return abs(sum(losses))

def open_position(symbol, price, signal, sl, tp):
    if not can_open_trade(symbol):
        return None

    position = {
        "id": f"{symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "symbol": symbol,
        "entry_price": price,
        "quantity": MAX_CAPITAL_PER_TRADE / price,
        "signal": signal,
        "sl_price": round(price * (1 - sl), 2),
        "tp_price": round(price * (1 + tp), 2),
        "open_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "close_time": None,
        "close_price": None,
        "pnl": None,
        "pnl_pct": None,
        "status": "OPEN"
    }

    positions = load_positions()
    positions.append(position)
    save_positions(positions)

    print(f"  📂 Position ouverte : {symbol} @ {price}")
    print(f"     SL : {position['sl_price']} | TP : {position['tp_price']}")
    return position

def close_position(symbol, current_price, reason="SIGNAL"):
    positions = load_positions()
    closed = None

    for p in positions:
        if p["symbol"] == symbol and p["status"] == "OPEN":
            pnl = (current_price - p["entry_price"]) * p["quantity"]
            pnl_pct = (current_price - p["entry_price"]) / p["entry_price"] * 100

            p["status"] = "CLOSED"
            p["close_price"] = current_price
            p["close_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            p["pnl"] = round(pnl, 2)
            p["pnl_pct"] = round(pnl_pct, 2)
            p["close_reason"] = reason
            closed = p
            break

    save_positions(positions)

    if closed:
        icon = "✅" if closed["pnl"] > 0 else "❌"
        print(f"  {icon} Position fermée : {symbol} | PnL: {closed['pnl']:+.2f} USDT ({closed['pnl_pct']:+.2f}%)")

    return closed

def check_sl_tp(current_prices):
    """Vérifie si SL ou TP est atteint pour les positions ouvertes"""
    open_pos = get_open_positions()
    closed = []

    for p in open_pos:
        symbol = p["symbol"]
        price = current_prices.get(symbol)
        if not price:
            continue

        if price <= p["sl_price"]:
            result = close_position(symbol, price, reason="STOP_LOSS")
            if result:
                closed.append(result)

        elif price >= p["tp_price"]:
            result = close_position(symbol, price, reason="TAKE_PROFIT")
            if result:
                closed.append(result)

    return closed

def get_summary():
    positions = load_positions()
    open_pos = [p for p in positions if p["status"] == "OPEN"]
    closed_pos = [p for p in positions if p["status"] == "CLOSED"]

    total_pnl = sum(p.get("pnl", 0) for p in closed_pos if p.get("pnl"))
    wins = len([p for p in closed_pos if p.get("pnl", 0) > 0])
    losses = len([p for p in closed_pos if p.get("pnl", 0) < 0])
    win_rate = (wins / len(closed_pos) * 100) if closed_pos else 0

    return {
        "open": len(open_pos),
        "closed": len(closed_pos),
        "total_pnl": round(total_pnl, 2),
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 1)
    }

if __name__ == "__main__":
    summary = get_summary()
    open_pos = get_open_positions()

    print(f"\n{'='*45}")
    print(f"  📊 POSITIONS SUMMARY")
    print(f"{'='*45}")
    print(f"  Positions ouvertes : {summary['open']}")
    print(f"  Positions fermées  : {summary['closed']}")
    print(f"  PnL total          : {summary['total_pnl']:+.2f} USDT")
    print(f"  Win rate           : {summary['win_rate']}%")
    print(f"  Wins / Losses      : {summary['wins']} / {summary['losses']}")
    print(f"{'='*45}")

    if open_pos:
        print(f"\n  📂 POSITIONS OUVERTES :")
        for p in open_pos:
            print(f"  {p['symbol']:<10} entry:{p['entry_price']} SL:{p['sl_price']} TP:{p['tp_price']}")
    print()