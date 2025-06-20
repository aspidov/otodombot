import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


async def send_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply with the chat ID of the current conversation."""
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id, text=f"Chat ID: {chat_id}")


def main() -> None:
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_TOKEN not set")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", send_chat_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_chat_id))
    application.run_polling()


if __name__ == "__main__":
    main()
