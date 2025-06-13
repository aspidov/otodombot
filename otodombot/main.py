from .db.database import init_db
from .scheduler.tasks import start_scheduler


def main():
    init_db()
    start_scheduler()
    input("Scheduler started. Press Enter to exit...\n")


if __name__ == "__main__":
    main()
