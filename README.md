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
To send notifications to multiple chats, provide several IDs separated by commas or spaces in the `TELEGRAM_CHAT_ID` environment variable.

### Configuration

Search conditions and crawler settings can be customized via `config.json` in the project root. Room counts may be specified as a single number or a list of numbers; these are automatically converted to the values expected by Otodom. Example:

```json
{
  "search": {
    "max_price": 1000000,
    "rooms": [2, 3],
    "min_area": 40,
    "sorts": ["DEFAULT", "LATEST"]
  },
  "base_url": "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie,rynek-wtorny/warszawa",
  "headless": true,
  "reparse_after_days": 7,
  "commute": {
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
`reparse_after_days` specifies how long to wait before revisiting the same listing URL.
The `sorts` option defines which sorting modes to fetch (e.g. `"DEFAULT"` or `"LATEST"`). Listings are collected for each specified mode in one session.
`commute` config defines destinations for public transit time estimation. The bot will
calculate travel times from each listing to these addresses for the specified day and time.
If the times to all points do not exceed the optional `thresholds` values (in minutes),
the bot sends the listing details to Telegram.

### Environment variables

API keys and tokens are loaded from environment variables. Create a `.env` file in the project root (see `.env.example`) with the following keys:

```env
OPENAI_API_KEY=your-openai-key
GOOGLE_API_KEY=your-google-api-key
TELEGRAM_TOKEN=your-telegram-token
# Specify one or more chat IDs separated by commas or spaces
TELEGRAM_CHAT_ID=12345,67890
```

The application automatically loads this file on startup if present.

### Backend and map frontend

A small FastAPI server exposes listing locations so they can be visualized on a map.
Start it with:

```bash
python -m otodombot.backend
```

To avoid browser CORS restrictions, serve the static files via a local web
server instead of opening the HTML file directly. From the `frontend` folder run

```bash
python -m http.server 8081
```

and open [http://localhost:8081](http://localhost:8081) in your browser. The
page fetches data from the API and shows the listings on an OpenStreetMap based
map using Leaflet. Popups include calculated travel times to your configured
points of interest.

### Deploying on Raspberry Pi

Example `systemd` service files and installation script can be found in
`docs/raspberrypi.md`. They allow running the scraper, backend and static
frontend automatically on boot.
