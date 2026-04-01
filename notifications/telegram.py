# notifications/telegram.py

import asyncio
from telegram import Bot
from telegram.request import HTTPXRequest
from dotenv import load_dotenv
import os
load_dotenv()

TOKEN   = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

async def send_message(text):
    request = HTTPXRequest(
        connect_timeout=30,
        read_timeout=30,
        write_timeout=30
    )
    bot = Bot(token=TOKEN, request=request)
    await bot.send_message(chat_id=CHAT_ID, text=text)

def notify(text):
    asyncio.run(send_message(text))

if __name__ == "__main__":
    notify("🤖 Trading Agent connecté avec succès !")