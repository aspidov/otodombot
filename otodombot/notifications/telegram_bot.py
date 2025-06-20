from typing import Iterable
import asyncio
from pathlib import Path
from telegram import Bot, InputMediaPhoto


def notify(token: str, chat_id: str, messages: Iterable[str]):
    async def _send():
        bot = Bot(token=token)
        for msg in messages:
            await bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")

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
            media = []
            files = []
            for idx, item in enumerate(list(photos)[:10]):
                if Path(item).exists():
                    f = open(item, "rb")
                    files.append(f)
                    photo_input = f
                else:
                    photo_input = item
                if idx == 0:
                    media.append(InputMediaPhoto(photo_input, caption=text, parse_mode="HTML"))
                else:
                    media.append(InputMediaPhoto(photo_input))
            await bot.send_media_group(chat_id=chat_id, media=media)
            for f in files:
                f.close()
        else:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")

    asyncio.run(_send())
