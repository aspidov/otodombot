# otodombot

Skeleton project for parsing [otodom.pl](https://www.otodom.pl) and notifying about good listings.

## Components

- `scraper/` – Playwright based crawler for listings.
- `db/` – SQLite database via SQLAlchemy.
- `evaluation/` – modules for location and ChatGPT evaluation.
- `notifications/` – Telegram bot notifier.
- `scheduler/` – APScheduler based periodic tasks.
- Price history is stored for each listing and updated when prices change.
- Listing ID is parsed from the listing page and stored for reference.

## Usage

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the bot:

```bash
python -m otodombot.main
```
