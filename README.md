# 🤖 Trading App — Bot Crypto Automatisé

Bot de trading automatisé pour Binance Testnet combinant analyse technique (RSI, MACD, Bollinger Bands), machine learning (XGBoost) et alertes Telegram en temps réel.

## Fonctionnalités

- **Stratégie hybride RSI + ML** — Signaux confirmés par indicateurs techniques ET classification XGBoost (confiance > 60%)
- **4 paires suivies** — BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT en bougies 4H
- **Exécution automatique** — Ordres market sur Binance Testnet avec stop-loss / take-profit par symbole
- **Alertes Telegram** — Notifications instantanées à chaque signal (prix, RSI, confiance ML)
- **Backtesting** — Grid search via Vectorbt (RSI seuils × SL × TP)
- **Dashboard web** — Interface Flask temps réel avec graphiques RSI et historique des trades
- **Cache intelligent** — Données OHLCV en Parquet avec TTL de 60 min
- **Données externes** — Fear & Greed Index + BTC dominance pour enrichir les features ML

## Architecture

```
Trading app/
├── main.py                     # Point d'entrée — lance l'agent toutes les 4h
├── agents/
│   └── trading_agent.py        # Logique principale : signaux + exécution + logs
├── data/
│   ├── fetcher.py              # Téléchargement OHLCV Binance (3 ans)
│   ├── cache.py                # Cache Parquet avec TTL
│   └── external.py             # Fear & Greed, BTC dominance
├── indicators/
│   └── technicals.py           # RSI, MACD, Bollinger Bands
├── strategies/
│   ├── ml_strategy.py          # XGBoost classifier + feature engineering
│   └── rsi_strategy.py         # Stratégie RSI + MACD pure
├── execution/
│   └── binance_executor.py     # Ordres market, calcul quantité, LOT_SIZE
├── notifications/
│   └── telegram.py             # Alertes Telegram async
├── backtest/
│   └── engine.py               # Grid search Vectorbt
├── dashboard/
│   └── app.py                  # Interface web Flask (port 5000)
├── models/                     # Modèles XGBoost entraînés (.pkl)
├── logs/
│   └── trades.json             # Historique des trades
└── data/cache/                 # Cache OHLCV (.parquet)
```

## Installation

```bash
git clone https://github.com/Arabat541/Trading_app.git
cd Trading_app
python3 -m venv venv
source venv/bin/activate
pip install python-binance pandas numpy ta xgboost scikit-learn vectorbt flask python-telegram-bot pycoingecko python-dotenv
```

## Configuration

Créer un fichier `.env` à la racine :

```env
BINANCE_API_KEY=your_testnet_api_key
BINANCE_API_SECRET=your_testnet_api_secret
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

> Clés Testnet : https://testnet.binance.vision/

## Utilisation

```bash
# Lancer le bot (analyse toutes les 4h)
python main.py

# Backtester les paramètres optimaux
python -m backtest.engine

# Entraîner les modèles ML
python -m strategies.ml_strategy

# Lancer le dashboard web
python dashboard/app.py
# → http://localhost:5000
```

## Paramètres par symbole

| Symbole  | Seuil RSI | Stop-Loss | Take-Profit |
|----------|-----------|-----------|-------------|
| BTCUSDT  | 40        | 5%        | 6%          |
| ETHUSDT  | 45        | 3%        | 10%         |
| SOLUSDT  | 40        | 4%        | 10%         |
| BNBUSDT  | 40        | 3%        | 10%         |

Taille fixe par trade : **200 USDT**

## Stack technique

| Composant       | Technologie                     |
|-----------------|---------------------------------|
| API Broker      | python-binance (Testnet)        |
| Indicateurs     | ta (technical-analysis)         |
| ML              | XGBoost + scikit-learn          |
| Backtesting     | Vectorbt                        |
| Dashboard       | Flask + Chart.js                |
| Notifications   | python-telegram-bot             |
| Données externes| pycoingecko                     |
| Cache           | Parquet (pandas)                |

## Licence

Usage personnel — Testnet uniquement.
