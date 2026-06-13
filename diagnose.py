import os
import sys
import json
import requests
from dotenv import load_dotenv

# Set paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "secrets", ".env")

print("==============================================")
echo_msg = "        Solana Tracker Diagnostics Tool       "
print(echo_msg)
print("==============================================\n")

# 1. Load Env
if not os.path.exists(ENV_PATH):
    print("❌ [ENV] secrets/.env file NOT found!")
    print("Please run configurator.py or create secrets/.env manually.")
    sys.exit(1)

load_dotenv(ENV_PATH)
token = os.getenv("TELEGRAM_BOT_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")

print("✅ [ENV] Configuration loaded successfully.")
print(f"  • Telegram Token: {'Configured' if token else 'NOT Configured'}")
print(f"  • Chat ID: {chat_id if chat_id else 'NOT Configured'}")
print(f"  • Solana RPC: {rpc_url}\n")

# 2. Test Solana RPC
print("⏳ [RPC] Testing Solana RPC connection...")
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "getHealth",
    "params": []
}
try:
    r = requests.post(rpc_url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
    r.raise_for_status()
    res = r.json()
    if res.get("result") == "ok":
        print("✅ [RPC] RPC node is healthy.")
    else:
        print(f"⚠️ [RPC] Health response unexpected: {res}")
except Exception as e:
    print(f"❌ [RPC] Failed to connect to Solana RPC: {e}")

# Test SOL balance lookup
payload_bal = {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "getBalance",
    "params": ["11111111111111111111111111111111"]
}
try:
    r = requests.post(rpc_url, json=payload_bal, headers={"Content-Type": "application/json"}, timeout=8)
    r.raise_for_status()
    res = r.json()
    val = res.get("result", {}).get("value", 0) / 1e9
    print(f"✅ [RPC] SOL balance query verified (System Account balance: {val} SOL).\n")
except Exception as e:
    print(f"❌ [RPC] SOL balance query failed: {e}\n")

# 3. Test Jupiter Price API
print("⏳ [JUPITER] Querying SOL price from Jupiter Price API...")
jup_url = "https://price.jup.ag/v6/price?ids=So11111111111111111111111111111111111111112"
try:
    r = requests.get(jup_url, timeout=5)
    r.raise_for_status()
    res = r.json()
    price = res.get("data", {}).get("So11111111111111111111111111111111111111112", {}).get("price")
    if price:
        print(f"✅ [JUPITER] Price lookup works. 1 SOL = ${price:,.2f} USD.\n")
    else:
        print(f"❌ [JUPITER] Price look returned empty data: {res}\n")
except Exception as e:
    print(f"❌ [JUPITER] Connection failed: {e}\n")

# 4. Test Exchange Rate API
print("⏳ [EXCHANGE] Querying exchange rates from open.er-api.com...")
rate_url = "https://open.er-api.com/v6/latest/USD"
try:
    r = requests.get(rate_url, timeout=5)
    r.raise_for_status()
    res = r.json()
    if res.get("result") == "success":
        rates = res.get("rates", {})
        print("✅ [EXCHANGE] Exchange rates loaded successfully.")
        print(f"  • USD/NIS: {rates.get('ILS', 'N/A')}")
        print(f"  • USD/CAD: {rates.get('CAD', 'N/A')}")
        print(f"  • USD/EUR: {rates.get('EUR', 'N/A')}\n")
    else:
        print(f"❌ [EXCHANGE] API returned error state: {res.get('result')}\n")
except Exception as e:
    print(f"❌ [EXCHANGE] Connection failed: {e}\n")

# 5. Test Telegram Token
if token:
    print("⏳ [TELEGRAM] Verifying Telegram Bot API Token...")
    tg_url = f"https://api.telegram.org/bot{token}/getMe"
    try:
        r = requests.get(tg_url, timeout=8)
        r.raise_for_status()
        res = r.json()
        if res.get("ok"):
            bot_info = res.get("result", {})
            print(f"✅ [TELEGRAM] Token is VALID.")
            print(f"  • Bot Name: {bot_info.get('first_name')}")
            print(f"  • Username: @{bot_info.get('username')}")
        else:
            print(f"❌ [TELEGRAM] Token is INVALID: {res}\n")
    except Exception as e:
        print(f"❌ [TELEGRAM] Failed to connect to Telegram: {e}\n")
else:
    print("⚠️ [TELEGRAM] Telegram Bot Token is empty. Skipping bot verification.\n")

# 6. Send Test Message if Chat ID exists
if token and chat_id:
    print(f"⏳ [TELEGRAM] Sending test notification to Chat ID: {chat_id}...")
    send_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload_msg = {
        "chat_id": chat_id,
        "text": "🧿 <b>Solana Wallet Tracker Diagnostics</b>\n\nConnection test was successful! The bot is ready to monitor transactions.",
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(send_url, json=payload_msg, timeout=8)
        r.raise_for_status()
        res = r.json()
        if res.get("ok"):
            print("✅ [TELEGRAM] Test message sent successfully. Please check your Telegram chat!\n")
        else:
            print(f"❌ [TELEGRAM] Failed to send message: {res}\n")
    except Exception as e:
        print(f"❌ [TELEGRAM] Test message failed: {e}\n")
else:
    print("⚠️ [TELEGRAM] Chat ID is empty or token missing. Skipping test message.\n")

print("==============================================")
print("              Diagnostics Finished            ")
print("==============================================")
