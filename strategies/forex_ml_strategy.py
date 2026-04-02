# strategies/forex_ml_strategy.py

import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib
import os

FOREX_FEATURES = [
    "rsi", "rsi_lag1", "rsi_lag2",
    "macd_diff", "macd_lag1", "macd_lag2",
    "bb_width", "bb_position",
    "price_vs_ema50", "price_vs_ema200", "ema_cross",
    "atr_pct", "price_change", "high_low_pct"
]

def prepare_forex_features(df):
    df = df.copy()

    df["rsi_lag1"]        = df["rsi"].shift(1)
    df["rsi_lag2"]        = df["rsi"].shift(2)
    df["macd_lag1"]       = df["macd_diff"].shift(1)
    df["macd_lag2"]       = df["macd_diff"].shift(2)
    df["bb_width"]        = df["bb_upper"] - df["bb_lower"]
    df["bb_position"]     = (df["close"] - df["bb_lower"]) / df["bb_width"]
    df["price_vs_ema50"]  = (df["close"] - df["ema50"])  / df["ema50"]
    df["price_vs_ema200"] = (df["close"] - df["ema200"]) / df["ema200"]
    df["ema_cross"]       = (df["ema50"] > df["ema200"]).astype(int)
    df["atr_pct"]         = df["atr"] / df["close"]
    df["price_change"]    = df["close"].pct_change()
    df["high_low_pct"]    = (df["high"] - df["low"]) / df["close"]

    df["future_return"]   = df["close"].shift(-6) / df["close"] - 1
    df["target"]          = (df["future_return"] > 0.003).astype(int)

    df = df.dropna(subset=FOREX_FEATURES + ["target"])
    return df

def train_forex(df, pair="EUR_USD"):
    df = prepare_forex_features(df)

    print(f"  📊 {len(df)} échantillons pour {pair}")

    X = df[FOREX_FEATURES]
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
    print(f"  🧠 MODÈLE FOREX ML - {pair}")
    print(f"{'='*40}")
    print(classification_report(y_test, y_pred, target_names=["NO BUY", "BUY"]))

    os.makedirs("models", exist_ok=True)
    joblib.dump(model, f"models/forex_{pair}_model.pkl")
    print(f"  ✅ Modèle sauvegardé → models/forex_{pair}_model.pkl\n")

    return model

def predict_forex(df, pair="EUR_USD"):
    model_path = f"models/forex_{pair}_model.pkl"
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Modèle non trouvé : {model_path}")

    model = joblib.load(model_path)
    df = prepare_forex_features(df)

    last = df[FOREX_FEATURES].iloc[[-1]]
    proba = model.predict_proba(last)[0][1]
    signal = "BUY" if proba > 0.6 else "SELL" if proba < 0.4 else "HOLD"

    return signal, round(proba, 3)

if __name__ == "__main__":
    from data.forex_fetcher import get_forex_yfinance
    from strategies.forex_strategy import add_forex_indicators

    pairs = ["EUR_USD", "GBP_USD", "XAU_USD"]

    for pair in pairs:
        df = get_forex_yfinance(pair)
        if df is None:
            continue
        df = add_forex_indicators(df)
        train_forex(df, pair)

    print("\n📊 PRÉDICTIONS FOREX ACTUELLES")
    print("="*45)
    for pair in pairs:
        df = get_forex_yfinance(pair)
        if df is None:
            continue
        df = add_forex_indicators(df)
        signal, proba = predict_forex(df, pair)
        icon = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
        print(f"  {icon} {pair:<10} {signal:<6} (confiance: {proba:.1%})")
    print("="*45)