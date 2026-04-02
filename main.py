# main.py

from dotenv import load_dotenv
load_dotenv()

import time
import schedule
from agents.trading_agent import TradingAgent
from agents.retrain import retrain_all
from notifications.daily_report import generate_daily_report
from notifications.telegram import notify

agent = TradingAgent()

def job():
    print("\n⏰ Analyse en cours...")
    agent.run()

def morning_report():
    print("\n📊 Envoi rapport quotidien...")
    report = generate_daily_report()
    notify(report)

def weekly_retrain():
    print("\n🔄 Réentraînement hebdomadaire...")
    retrain_all()

# Analyse toutes les 4 heures
schedule.every(4).hours.do(job)

# Rapport quotidien à 8h00
schedule.every().day.at("08:00").do(morning_report)

# Réentraînement chaque lundi à 6h00
schedule.every().monday.at("06:00").do(weekly_retrain)

# Lance immédiatement au démarrage
job()

print("🤖 Agent en cours d'exécution... (Ctrl+C pour arrêter)")

while True:
    schedule.run_pending()
    time.sleep(60)