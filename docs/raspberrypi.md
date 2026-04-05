# Deploying Otodombot on Raspberry Pi

This document describes how to run the backend, frontend, and scraper as `systemd` services.

## Prerequisites

1. Install Python 3 and `git` (usually already present on Raspberry Pi).
2. Clone the repository into the `pi` user's home directory:
   ```bash
   git clone https://github.com/yourname/otodombot.git
   cd otodombot
   ```
3. Install `uv`, then sync dependencies and install Playwright browsers:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   uv sync
   uv run playwright install
   ```
4. Copy `.env.example` to `.env` and fill in your API keys.

## Installing services

The `scripts` directory contains service files and an install script. Run it as `root`:

```bash
sudo ./scripts/install_services.sh
```

The script substitutes the current project path into the templates, copies the files to `/etc/systemd/system/`, and enables three services:
- `otodombot-backend.service` – FastAPI-based API (port 8000).
- `otodombot-scraper.service` – main bot with scraper and scheduler.
- `otodombot-frontend.service` – static file server for the map (port 8081).

The services are started automatically after installation. Check their status with `systemctl status <service>`.

## Access

- Open `http://<PI-IP>:8081` in a browser to see the map with listings.
- The backend is available at `http://<PI-IP>:8000`.

You can change the ports by editing the corresponding `*.service` files before running the install script.
