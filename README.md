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

Get your Telegram chat ID:

```bash
python -m otodombot.chat_id_bot
```
Send any message to the bot and it will respond with your chat ID.

### Configuration

Search conditions and crawler settings can be customized via `config.json` in the project root. Room counts may be specified as a single number or a list of numbers; these are automatically converted to the values expected by Otodom. Example:

```json
{
  "search": {
    "max_price": 1000000,
    "rooms": [2, 3],
    "market": "secondary",
    "min_area": 40,
    "sorts": ["DEFAULT", "LATEST"]
  },
  "headless": true
  ,"commute": {
    "pois": ["Central Station", "Main Office"],
    "day": "Tuesday",
    "time": "09:00",
    "thresholds": {
      "Central Station": 20,
      "Main Office": 30
    }
  }
}
```

The `headless` flag controls whether Playwright runs the browser without a visible window.
The `sorts` option defines which sorting modes to fetch (e.g. `"DEFAULT"` or `"LATEST"`). Listings are collected for each specified mode in one session.
`commute` config defines destinations for public transit time estimation. The bot will
calculate travel times from each listing to these addresses for the specified day and time.
If the times to all points do not exceed the optional `thresholds` values (in minutes),
the bot sends the listing details and photos to Telegram.

### Environment variables

API keys and tokens are loaded from environment variables. Create a `.env` file in the project root (see `.env.example`) with the following keys:

```env
OPENAI_API_KEY=your-openai-key
GOOGLE_API_KEY=your-google-api-key
TELEGRAM_TOKEN=your-telegram-token
TELEGRAM_CHAT_ID=your-chat-id
```

The application automatically loads this file on startup if present.
