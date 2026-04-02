# main.py

from dotenv import load_dotenv
load_dotenv()

import time
import schedule
from agents.trading_agent import TradingAgent
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

# Analyse toutes les 4 heures
schedule.every(4).hours.do(job)

# Rapport quotidien à 8h00 chaque matin
schedule.every().day.at("08:00").do(morning_report)

# Lance immédiatement au démarrage
job()

print("🤖 Agent en cours d'exécution... (Ctrl+C pour arrêter)")

while True:
    schedule.run_pending()
    time.sleep(60)