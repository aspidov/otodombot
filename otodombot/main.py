import logging
from dotenv import load_dotenv

from .db.database import init_db
from .scheduler.tasks import start_scheduler


def main():
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler("otodombot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    init_db()
    start_scheduler()
    input("Scheduler started. Press Enter to exit...\n")


if __name__ == "__main__":
    main()
