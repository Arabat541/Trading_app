# execution/binance_executor.py

from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv
import os

load_dotenv()

def get_client():
    return Client(
        api_key=os.getenv("BINANCE_API_KEY"),
        api_secret=os.getenv("BINANCE_API_SECRET"),
        testnet=True
    )

def get_balance(asset="USDT"):
    client = get_client()
    account = client.get_account()
    for b in account["balances"]:
        if b["asset"] == asset:
            return float(b["free"])
    return 0.0

def get_price(symbol="BTCUSDT"):
    client = get_client()
    ticker = client.get_symbol_ticker(symbol=symbol)
    return float(ticker["price"])

def calculate_quantity(symbol, usdt_amount):
    client = get_client()
    price = get_price(symbol)
    info = client.get_symbol_info(symbol)

    step_size = None
    for f in info["filters"]:
        if f["filterType"] == "LOT_SIZE":
            step_size = float(f["stepSize"])
            break

    quantity = usdt_amount / price
    if step_size:
        precision = len(str(step_size).rstrip("0").split(".")[-1])
        quantity = round(quantity - (quantity % step_size), precision)

    return quantity

def buy(symbol="BTCUSDT", usdt_amount=100):
    client = get_client()
    try:
        quantity = calculate_quantity(symbol, usdt_amount)
        order = client.order_market_buy(symbol=symbol, quantity=quantity)
        print(f"  ✅ BUY {symbol} | qty: {quantity} | status: {order['status']}")
        return order
    except BinanceAPIException as e:
        print(f"  ❌ Erreur BUY {symbol}: {e}")
        return None

def sell(symbol="BTCUSDT", usdt_amount=100):
    client = get_client()
    try:
        quantity = calculate_quantity(symbol, usdt_amount)
        order = client.order_market_sell(symbol=symbol, quantity=quantity)
        print(f"  ✅ SELL {symbol} | qty: {quantity} | status: {order['status']}")
        return order
    except BinanceAPIException as e:
        print(f"  ❌ Erreur SELL {symbol}: {e}")
        return None

if __name__ == "__main__":
    print("\n" + "="*40)
    print("  💰 BINANCE TESTNET - SOLDES")
    print("="*40)

    assets = ["USDT", "BTC", "ETH", "SOL", "BNB"]
    for asset in assets:
        balance = get_balance(asset)
        if balance > 0:
            print(f"  {asset:<6} : {balance:.4f}")

    print("="*40)
    print(f"\n  BTC prix actuel : {get_price('BTCUSDT'):.2f} USDT")
    print(f"  ETH prix actuel : {get_price('ETHUSDT'):.2f} USDT\n")