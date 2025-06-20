# otodombot

Skeleton project for parsing [otodom.pl](https://www.otodom.pl) and notifying about good listings.

## Components

- `scraper/` – Playwright based crawler for listings.
- `db/` – SQLite database via SQLAlchemy.
- `evaluation/` – modules for location and ChatGPT evaluation.
- `notifications/` – Telegram bot notifier.
- `scheduler/` – APScheduler based periodic tasks.
- Each listing stores its current price directly.
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

### Configuration

Search conditions and crawler settings can be customized via `config.json` in the project root. Room counts may be specified as a single number or a list of numbers; these are automatically converted to the values expected by Otodom. Example:

```json
{
  "search": {
    "max_price": 1000000,
    "rooms": [2, 3],
    "market": "secondary",
    "min_area": 40
  },
  "headless": true
}
```

The `headless` flag controls whether Playwright runs the browser without a visible window.

### Environment variables

API keys and tokens are loaded from environment variables. Create a `.env` file in the project root (see `.env.example`) with the following keys:

```env
OPENAI_API_KEY=your-openai-key
GOOGLE_API_KEY=your-google-api-key
TELEGRAM_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id
```

The application automatically loads this file on startup if present.
