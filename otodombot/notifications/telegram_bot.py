from typing import Iterable
from telegram import Bot


def notify(token: str, chat_id: str, messages: Iterable[str]):
    bot = Bot(token=token)
    for msg in messages:
        bot.send_message(chat_id=chat_id, text=msg)


def notify_listing(
    token: str,
    chat_id: str,
    text: str,
    photos: Iterable[str] | None = None,
):
    bot = Bot(token=token)
    if photos:
        for path in list(photos)[:10]:
            with open(path, "rb") as f:
                bot.send_photo(chat_id=chat_id, photo=f)
    bot.send_message(chat_id=chat_id, text=text)
