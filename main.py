# main.py

from dotenv import load_dotenv
load_dotenv()

import time
import schedule
from agents.trading_agent import TradingAgent
from agents.forex_agent import ForexAgent
from agents.retrain import retrain_all
from notifications.daily_report import generate_daily_report
from notifications.telegram import notify

crypto_agent = TradingAgent()
forex_agent = ForexAgent()

def crypto_job():
    print("\n⏰ Analyse Crypto...")
    crypto_agent.run()

def forex_job():
    print("\n💱 Analyse Forex...")
    forex_agent.run()

def morning_report():
    print("\n📊 Rapport quotidien...")
    report = generate_daily_report()
    notify(report)

def weekly_retrain():
    print("\n🔄 Réentraînement hebdomadaire...")
    retrain_all()

# Crypto toutes les 4h
schedule.every(4).hours.do(crypto_job)

# Forex toutes les 4h (décalé de 30min)
schedule.every(4).hours.do(forex_job)

# Rapport quotidien à 8h
schedule.every().day.at("08:00").do(morning_report)

# Réentraînement chaque lundi à 6h
schedule.every().monday.at("06:00").do(weekly_retrain)

# Lancement immédiat
crypto_job()
forex_job()

print("\n🤖 Agents en cours d'exécution... (Ctrl+C pour arrêter)")

while True:
    schedule.run_pending()
    time.sleep(60)