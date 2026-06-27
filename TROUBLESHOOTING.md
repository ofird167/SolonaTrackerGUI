# Troubleshooting Guide - Solana Telegram Tracker

This guide details resolutions for common issues encountered during setup, configuration, or runtime of the Solana Wallet Tracker Bot and Configurator GUI.

---

## 1. RPC Connection & Rate-Limiting Issues

Public RPC endpoints (e.g., `https://api.mainnet-beta.solana.com`) are heavily rate-limited and often return `HTTP 429 Too Many Requests` or timeout errors.

### Symptoms
* Logs show `Error in Solana poller cycle: HTTP 429` or `Connection timeout`.
* Transaction alerts are delayed or skipped entirely.

### Resolution
* **Use Premium RPC Providers:** Switch to dedicated providers like Helius, QuickNode, or Triton.
* **Premium Builders:** In the Configurator GUI, you can input your Helius or QuickNode API key directly, and the app will generate and apply the premium endpoint for you.
* **Test Connections:** Always click the "Test Connections" button in the configurator to verify latency before saving.

---

## 2. Telegram Bot & Delivery Failures

If you aren't receiving alerts in Telegram, the issue is typically related to invalid credentials or chat configurations.

### Symptoms
* Logs show `Telegram API request failed for sendMessage: Unauthorized (401)` or `Chat not found (400)`.

### Resolution
* **Validate Bot Token:** Double-check your bot token from `@BotFather`. It must look like `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`.
* **Initiate Bot Chat:** Ensure you have started the bot in your chat/group by typing `/start` first. Telegram bots cannot message users who haven't initiated contact.
* **Group Chat IDs:** If tracking inside a group, the Chat ID must begin with a minus sign (typically `-100...`, e.g., `-100123456789`).

---

## 3. System Tray & Backend Compatibility (Linux)

Under Linux, `pystray` may encounter backend GTK/AppIndicator warnings or errors if python-gi bindings or GTK libraries are missing in headless or customized environments.

### Symptoms
* Console displays `ValueError: Namespace Gtk not available` on startup or minimization.

### Resolution
* The configurator uses a graceful fallback: if the system tray backend is unavailable, the application will perform a standard window minimization to the taskbar without crashing.
* To enable full system tray support on Debian/Ubuntu systems, install the dependencies:
  ```bash
  sudo apt-get install python3-gi python3-gi-cairo gir1.2-appindicator3-0.1
  ```

---

## 4. Hot Reloading Configurations

The bot tracks changes to the `secrets/.env` configuration dynamically.

### Symptoms
* Modifying settings in the GUI does not seem to take effect in the bot process.

### Resolution
* The bot checks for `.env` updates every 25 seconds during its polling loop.
* Ensure you click the "Save Connection" or "Save Preferences" button inside the configurator to write changes to disk so the bot can reload them.
