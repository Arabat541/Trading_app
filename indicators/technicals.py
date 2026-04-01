# indicators/technicals.py

import ta

def add_indicators(df):
    # RSI
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    # MACD
    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"] = macd.macd_diff()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["close"])
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_mid"] = bb.bollinger_mavg()

    # Supprime les lignes sans valeurs (début du dataset)
    df.dropna(inplace=True)

    return df

if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from data.fetcher import get_ohlcv

    df = get_ohlcv()
    df = add_indicators(df)
    print(df[["close", "rsi", "macd", "bb_upper", "bb_lower"]].tail(5))
    print(f"\n✅ Indicateurs calculés sur {len(df)} bougies")