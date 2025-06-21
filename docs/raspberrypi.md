# Развёртывание Otodombot на Raspberry Pi

В этом документе описан примерный способ запуска бэкенда, фронтенда и скрапера как служб `systemd`.

## Подготовка

1. Установите Python 3 и `git` (на Raspberry Pi они обычно уже есть).
2. Клонируйте репозиторий в домашний каталог пользователя `pi`:
   ```bash
   git clone https://github.com/yourname/otodombot.git
   cd otodombot
   ```
3. Установите зависимости и браузеры Playwright:
   ```bash
   pip3 install -r requirements.txt
   playwright install
   ```
4. Скопируйте `.env.example` в `.env` и впишите свои ключи API.

## Установка служб

В каталоге `scripts` есть сервисные файлы и скрипт для их установки. Выполните его от `root`:

```bash
sudo ./scripts/install_services.sh
```

Скрипт подставит текущий путь к проекту в шаблоны, скопирует файлы в `/etc/systemd/system/` и включит три службы:
- `otodombot-backend.service` – API на FastAPI (порт 8000).
- `otodombot-scraper.service` – основной бот со скрапером и планировщиком.
- `otodombot-frontend.service` – простая статика для карты (порт 8081).

После установки службы уже запущены. Проверить их состояние можно командой `systemctl status <service>`.

## Доступ

- Откройте `http://<IP-PI>:8081` в браузере, чтобы увидеть карту со списком объявлений.
- Бэкенд доступен на `http://<IP-PI>:8000`.

При желании вы можете изменить порты, отредактировав соответствующие `*.service` файлы до запуска скрипта.
