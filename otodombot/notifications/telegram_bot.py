from typing import Iterable
import asyncio
import logging
from pathlib import Path
from telegram import Bot, InputMediaPhoto


def notify(token: str, chat_id: str | Iterable[str], messages: Iterable[str]):
    """Send plain text messages to one or multiple chat IDs."""

    chat_ids = [chat_id] if isinstance(chat_id, str) else list(chat_id)

    async def _send():
        bot = Bot(token=token)
        for cid in chat_ids:
            for msg in messages:
                logging.debug("Sending message to %s", cid)
                await bot.send_message(chat_id=cid, text=msg, parse_mode="HTML")

    asyncio.run(_send())


def notify_listing(
    token: str,
    chat_id: str | Iterable[str],
    text: str,
    photos: Iterable[str] | None = None,
):
    """Send a listing notification with optional photos to one or multiple chat IDs."""

    chat_ids = [chat_id] if isinstance(chat_id, str) else list(chat_id)

    async def _send():
        bot = Bot(token=token)
        if photos:
            photo_list = list(photos)[:10]
            for cid in chat_ids:
                media = []
                files = []
                for idx, item in enumerate(photo_list):
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
                await bot.send_media_group(chat_id=cid, media=media)
                logging.debug("Sent media group to %s", cid)
                for f in files:
                    f.close()
        else:
            for cid in chat_ids:
                logging.debug("Sending listing to %s", cid)
                await bot.send_message(chat_id=cid, text=text, parse_mode="HTML")

    asyncio.run(_send())
