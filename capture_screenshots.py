import os
import sys
import time
import asyncio
import subprocess
import shutil
from playwright.async_api import async_playwright

BASE_DIR = "/home/ofird/projects/telegramcrypt"
SECRETS_DIR = os.path.join(BASE_DIR, "secrets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

ENV_FILE = os.path.join(SECRETS_DIR, ".env")
TRACKED_FILE = os.path.join(SECRETS_DIR, "tracked.json")
LOG_FILE = os.path.join(LOGS_DIR, "tracker.log")

ENV_BACKUP = ENV_FILE + ".bak"
TRACKED_BACKUP = TRACKED_FILE + ".bak"
LOG_BACKUP = LOG_FILE + ".bak"

# 1. Back up original files
def backup_files():
    print("Backing up original secrets and logs...")
    if os.path.exists(ENV_FILE):
        shutil.copy2(ENV_FILE, ENV_BACKUP)
    if os.path.exists(TRACKED_FILE):
        shutil.copy2(TRACKED_FILE, TRACKED_BACKUP)
    if os.path.exists(LOG_FILE):
        shutil.copy2(LOG_FILE, LOG_BACKUP)

# 2. Write mock files (fully censored)
def write_mock_files():
    print("Writing mock credentials, settings, and logs for screenshots...")
    
    # Mock environment variables
    mock_env = (
        "TELEGRAM_BOT_TOKEN=123456789:ABC_MockToken_XYZ\n"
        "TELEGRAM_CHAT_ID=987654321\n"
        "SOLANA_RPC_URL=https://api.mainnet-beta.solana.com\n"
        "AUTO_START_BOT=false\n"
    )
    with open(ENV_FILE, "w") as f:
        f.write(mock_env)

    # Mock tracked json database
    mock_tracked = {
        "chats": {
            "987654321": {
                "active": True,
                "currency": "USD",
                "interval": 15,
                "status_interval": 5,
                "whale_threshold": 1.0,
                "show_coin_link": True,
                "show_market_cap": True,
                "tracked": {
                    "71HuFmuYAFEFUna2x2R4HJjrFNQHGuagW3gUMFToL9tk": {
                        "type": "user",
                        "name": "trump2"
                    },
                    "Xs3oZwbHvqis4NYcf4YKWmEia2eC84wSiVrcYcTqpH8": {
                        "type": "wallet",
                        "name": "spacex"
                    }
                },
                "accumulated_txs": [],
                "status_txs": []
            }
        },
        "global_last_signatures": {
            "71HuFmuYAFEFUna2x2R4HJjrFNQHGuagW3gUMFToL9tk": "jTzyxoTsJZCt32LXcFJoyagMbojTka8npG2rrv4Q5f7nKEs6cEFZxjTkZfuWYuezXuxVxdN9Lw4nB7tWitvK3Xx",
            "Xs3oZwbHvqis4NYcf4YKWmEia2eC84wSiVrcYcTqpH8": "32aSMT9hcPTvFPkv4CwHKdbLPSopZWhoWpghV5MPq92bdV8xGwunxMNrUt7V1Ge1oDpUn3J8eMBvmbzBA2xAdonH"
        },
        "settings": {
            "language": "English",
            "font_size": "Small",
            "theme": "Dark Mode"
        }
    }
    with open(TRACKED_FILE, "w") as f:
        import json
        json.dump(mock_tracked, f, indent=2)

    # Mock non-sensitive clean tracker log output
    mock_log = (
        "2026-06-27 22:15:00,000 - tracker - INFO - Starting Solana Wallet Tracker Bot...\n"
        "2026-06-27 22:15:00,050 - tracker - INFO - Telegram updates polling thread started.\n"
        "2026-06-27 22:15:00,052 - tracker - INFO - Solana wallet transactions poller started.\n"
        "2026-06-27 22:15:00,055 - tracker - INFO - Summary/Status scheduler thread started.\n"
        "2026-06-27 22:15:00,060 - tracker - INFO - Wallet Tracker Bot threads initialized.\n"
        "2026-06-27 22:15:05,000 - tracker - INFO - Retrieved 2 new transaction(s) for trump2...\n"
        "2026-06-27 22:15:06,120 - tracker - INFO - [MATCH] Found target wallet: 71HuFm... (trump2) | Buy order: 2.5 SOL\n"
        "2026-06-27 22:15:10,000 - tracker - INFO - Retrieved 1 new transaction(s) for spacex...\n"
        "2026-06-27 22:15:11,430 - tracker - INFO - [MATCH] Found target wallet: Xs3oZw... (spacex) | Sell order: 12.0 SOL\n"
    )
    os.makedirs(LOGS_DIR, exist_ok=True)
    with open(LOG_FILE, "w") as f:
        f.write(mock_log)

# 3. Restore original files
def restore_files():
    print("Restoring original secrets and logs...")
    if os.path.exists(ENV_BACKUP):
        if os.path.exists(ENV_FILE):
            os.remove(ENV_FILE)
        shutil.move(ENV_BACKUP, ENV_FILE)
    if os.path.exists(TRACKED_BACKUP):
        if os.path.exists(TRACKED_FILE):
            os.remove(TRACKED_FILE)
        shutil.move(TRACKED_BACKUP, TRACKED_FILE)
    if os.path.exists(LOG_BACKUP):
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        shutil.move(LOG_BACKUP, LOG_FILE)

# 4. Main screenshot routine
async def capture():
    # Kill any existing configurator server
    print("Stopping existing configurator process...")
    subprocess.run(["pkill", "-f", "configurator.py"])
    await asyncio.sleep(2)

    backup_files()
    try:
        write_mock_files()

        # Launch configurator in web server mode
        print("Starting configurator in web server mode with mock configs...")
        proc = subprocess.Popen(
            [os.path.join(BASE_DIR, ".venv/bin/python"), "configurator.py"],
            env=dict(os.environ, DISPLAY="")
        )
        
        # Wait for the web server to boot up
        await asyncio.sleep(6)

        try:
            async with async_playwright() as p:
                print("Launching headless Chromium...")
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": 1024, "height": 1024})
                
                print("Navigating to http://localhost:8550...")
                await page.goto("http://localhost:8550", timeout=15000)
                print("Waiting 6 seconds for rendering...")
                await asyncio.sleep(6)
                
                # 1. Take Dashboard screenshot
                print("Capturing Dashboard view...")
                await page.screenshot(path="assets/screenshot_main.png")
                print("Saved assets/screenshot_main.png")
                
                # 2. Click on Credentials & Preferences (Settings) tab (X=110, Y=220)
                print("Navigating to settings...")
                await page.mouse.click(110, 220)
                await asyncio.sleep(2)
                print("Capturing Settings view...")
                await page.screenshot(path="assets/screenshot_settings.png")
                print("Saved assets/screenshot_settings.png")
                
                # 3. Click on Live Console & Logs tab (X=110, Y=265)
                print("Navigating to logs...")
                await page.mouse.click(110, 265)
                await asyncio.sleep(2)
                print("Capturing Logs view...")
                await page.screenshot(path="assets/screenshot_logs.png")
                print("Saved assets/screenshot_logs.png")
                
                print("All screenshots captured and censored successfully!")
                await browser.close()
        finally:
            print("Stopping mock configurator process...")
            proc.terminate()
            proc.wait()
    finally:
        restore_files()

if __name__ == "__main__":
    asyncio.run(capture())
