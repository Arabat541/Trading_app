# agents/retrain.py

from data.fetcher import get_ohlcv
from indicators.technicals import add_indicators
from data.external import enrich_with_external
from strategies.ml_strategy import train
from notifications.telegram import notify
from datetime import datetime

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

def retrain_all():
    print(f"\n🔄 Réentraînement des modèles — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    results = []

    for symbol in SYMBOLS:
        try:
            print(f"\n  📥 {symbol}...")
            # force_refresh=True → nouvelles données à chaque réentraînement
            df = get_ohlcv(symbol=symbol, force_refresh=True)
            df = add_indicators(df)
            df = enrich_with_external(df)
            train(df, symbol=symbol)
            results.append(f"✅ {symbol} — réentraîné")
        except Exception as e:
            results.append(f"❌ {symbol} — erreur : {e}")

    message = "🔄 RÉENTRAÎNEMENT MODÈLES ML\n"
    message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    message += "─" * 25 + "\n"
    message += "\n".join(results)
    notify(message)

    print("\n✅ Réentraînement terminé")
    return results

if __name__ == "__main__":
    retrain_all()