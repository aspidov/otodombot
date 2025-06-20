from typing import Iterable
import asyncio
from telegram import Bot, InputMediaPhoto


def notify(token: str, chat_id: str, messages: Iterable[str]):
    async def _send():
        bot = Bot(token=token)
        for msg in messages:
            await bot.send_message(chat_id=chat_id, text=msg)

    asyncio.run(_send())


def notify_listing(
    token: str,
    chat_id: str,
    text: str,
    photos: Iterable[str] | None = None,
):
    async def _send():
        bot = Bot(token=token)
        if photos:
            files = []
            media = []
            for idx, path in enumerate(list(photos)[:10]):
                f = open(path, "rb")
                files.append(f)
                if idx == 0:
                    media.append(InputMediaPhoto(f, caption=text))
                else:
                    media.append(InputMediaPhoto(f))
            await bot.send_media_group(chat_id=chat_id, media=media)
            for f in files:
                f.close()
        else:
            await bot.send_message(chat_id=chat_id, text=text)

    asyncio.run(_send())
