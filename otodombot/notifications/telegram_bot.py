from typing import Iterable
from telegram import Bot


def notify(token: str, chat_id: str, messages: Iterable[str]):
    bot = Bot(token=token)
    for msg in messages:
        bot.send_message(chat_id=chat_id, text=msg)
