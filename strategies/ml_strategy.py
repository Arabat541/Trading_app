# strategies/ml_strategy.py

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

def prepare_features(df):
    df = df.copy()

    # Features techniques
    df["rsi_lag1"] = df["rsi"].shift(1)
    df["rsi_lag2"] = df["rsi"].shift(2)
    df["macd_lag1"] = df["macd_diff"].shift(1)
    df["macd_lag2"] = df["macd_diff"].shift(2)
    df["bb_width"] = df["bb_upper"] - df["bb_lower"]
    df["bb_position"] = (df["close"] - df["bb_lower"]) / df["bb_width"]
    df["ema200"] = df["close"].ewm(span=200).mean()
    df["price_vs_ema"] = (df["close"] - df["ema200"]) / df["ema200"]
    df["volume_change"] = df["volume"].pct_change()
    df["price_change"] = df["close"].pct_change()

    # Features externes (si disponibles)
    if "fear_greed" in df.columns:
        df["fg_change"] = df["fear_greed"].diff()
    else:
        df["fear_greed"] = 50
        df["is_fear"] = 0
        df["is_greed"] = 0
        df["fg_change"] = 0
        df["btc_dominance"] = 50

    # Target
    df["future_return"] = df["close"].shift(-6) / df["close"] - 1
    df["target"] = (df["future_return"] > 0.01).astype(int)

    df.dropna(inplace=True)
    return df

FEATURES = [
    # Techniques
    "rsi", "rsi_lag1", "rsi_lag2",
    "macd_diff", "macd_lag1", "macd_lag2",
    "bb_width", "bb_position",
    "price_vs_ema", "volume_change", "price_change",
    # Externes
    "fear_greed", "is_fear", "is_greed", "fg_change",
    "btc_dominance"
]

def train(df, symbol="BTCUSDT"):
    df = prepare_features(df)

    X = df[FEATURES]
    y = df["target"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    ratio = (y_train == 0).sum() / (y_train == 1).sum()

    model = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        scale_pos_weight=ratio,
        eval_metric="logloss",
        random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"\n{'='*40}")
    print(f"  🧠 MODÈLE ML - {symbol}")
    print(f"{'='*40}")
    print(classification_report(y_test, y_pred, target_names=["NO BUY", "BUY"]))

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, f"models/{symbol}_model.pkl")
    print(f"  ✅ Modèle sauvegardé → models/{symbol}_model.pkl\n")

    return model

def predict(df, symbol="BTCUSDT"):
    model_path = f"models/{symbol}_model.pkl"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modèle non trouvé : {model_path}")

    model = joblib.load(model_path)
    df = prepare_features(df)

    last = df[FEATURES].iloc[[-1]]
    proba = model.predict_proba(last)[0][1]
    signal = "BUY" if proba > 0.6 else "SELL" if proba < 0.4 else "HOLD"

    return signal, round(proba, 3)

if __name__ == "__main__":
    from data.fetcher import get_ohlcv
    from indicators.technicals import add_indicators
    from data.external import enrich_with_external

    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]

    for symbol in symbols:
        print(f"\n📥 Entraînement {symbol}...")
        df = get_ohlcv(symbol=symbol)
        df = add_indicators(df)
        df = enrich_with_external(df)
        train(df, symbol=symbol)

    print("\n📊 PRÉDICTIONS ACTUELLES")
    print("="*40)
    for symbol in symbols:
        df = get_ohlcv(symbol=symbol)
        df = add_indicators(df)
        df = enrich_with_external(df)
        signal, proba = predict(df, symbol)
        icon = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
        print(f"  {icon} {symbol:<10} {signal:<6} (confiance: {proba:.1%})")
    print("="*40)