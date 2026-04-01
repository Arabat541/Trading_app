# main.py

import time
import schedule
from agents.trading_agent import TradingAgent

agent = TradingAgent()

def job():
    print("\n⏰ Analyse en cours...")
    agent.run()

# Lance une analyse immédiatement
job()

# Puis toutes les 4 heures
schedule.every(4).hours.do(job)

print("🤖 Agent en cours d'exécution... (Ctrl+C pour arrêter)")

while True:
    schedule.run_pending()
    time.sleep(60)