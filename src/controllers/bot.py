from globals import Globals
from bot.base_bot import BaseBot
from bot.pychat_bot import PyChatBot
from bot.gemini_bot import GeminiBot

LIST_BOTS : list[BaseBot] = [
    PyChatBot,
    GeminiBot
]

def handle_bots(chat_id, message, user):
    with Globals.app.app_context():
        for i in LIST_BOTS:
            bot = i()
            bot.handle(chat_id, message, user)