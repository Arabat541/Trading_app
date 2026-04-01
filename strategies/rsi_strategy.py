# strategies/rsi_strategy.py

def generate_signal(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Signal BUY : RSI sort de la zone de survente + MACD haussier
    if last["rsi"] < 40 and last["macd_diff"] > prev["macd_diff"]:
        return "BUY"

    # Signal SELL : RSI entre en zone de surachat + MACD baissier
    elif last["rsi"] > 60 and last["macd_diff"] < prev["macd_diff"]:
        return "SELL"

    else:
        return "HOLD"

if __name__ == "__main__":
    import sys
    sys.path.append(".")
    from data.fetcher import get_ohlcv
    from indicators.technicals import add_indicators

    df = get_ohlcv()
    df = add_indicators(df)
    signal = generate_signal(df)

    print(f"📊 RSI actuel     : {df['rsi'].iloc[-1]:.2f}")
    print(f"📊 MACD diff      : {df['macd_diff'].iloc[-1]:.2f}")
    print(f"🎯 Signal         : {signal}")
    print(f"💰 Prix actuel    : {df['close'].iloc[-1]:.2f} USDT")