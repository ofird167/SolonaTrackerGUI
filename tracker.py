import os
import sys
import json
import time
import re
import logging
from logging.handlers import RotatingFileHandler
import traceback
import io
import threading
import requests
import datetime
from dotenv import load_dotenv


# Set up paths
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "logs", "tracker.log")
STATE_FILE = os.path.join(BASE_DIR, "secrets", "tracked.json")

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

# Load environment variables
ENV_PATH = os.path.join(BASE_DIR, "secrets", ".env")
load_dotenv(ENV_PATH)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Custom Formatter to censor Bot Token in logs and stdout
class CensorFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, token=None):
        super().__init__(fmt, datefmt)
        self.token = token
        
    def format(self, record):
        orig_msg = super().format(record)
        if self.token and self.token in orig_msg:
            return orig_msg.replace(self.token, "[BOT_TOKEN_CENSORED]")
        return orig_msg

# Configure logging
logger = logging.getLogger("tracker")
logger.setLevel(logging.INFO)

fh = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=3, encoding='utf-8')
fh.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)

fmt_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = CensorFormatter(fmt_str, token=TELEGRAM_BOT_TOKEN)
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# Shared State
state = {"chats": {}, "global_last_signatures": {}}
state_lock = threading.Lock()

import contextlib

@contextlib.contextmanager
def disk_state_lock():
    lock_path = STATE_FILE + ".lock"
    import time
    start_time = time.time()
    while True:
        try:
            os.mkdir(lock_path)
            break
        except FileExistsError:
            if time.time() - start_time > 5.0:
                try:
                    os.rmdir(lock_path)
                except Exception:
                    pass
            time.sleep(0.1)
    try:
        yield
    finally:
        try:
            os.rmdir(lock_path)
        except Exception:
            pass

def safe_read_state_file(fallback_state):
    if os.path.exists(STATE_FILE):
        try:
            with disk_state_lock():
                with open(STATE_FILE, "r") as f:
                    return json.load(f)
        except Exception:
            pass
    return fallback_state

def load_state():
    global state
    with state_lock:
        state = safe_read_state_file({"chats": {}, "global_last_signatures": {}})

def migrate_tracked_json_types():
    logger.info("Checking and migrating tracked address types on-chain...")
    with state_lock:
        migrated = False
        chats = state.get("chats", {})
        for chat_id, chat_data in chats.items():
            tracked = chat_data.get("tracked", {})
            for addr, info in list(tracked.items()):
                t_type = info.get("type", "user")
                
                # Standardize old "wallet" label to "token"
                if t_type == "wallet":
                    info["type"] = "token"
                    t_type = "token"
                    migrated = True
                
                # Check actual type on-chain
                detected = identify_address(addr)
                if detected == "TOKEN" and t_type == "user":
                    logger.info(f"Auto-migrating {addr} from User Wallet ('user') to Specific Token Account ('token')")
                    info["type"] = "token"
                    try:
                        res = solana_client._call("getAccountInfo", [addr, {"encoding": "jsonParsed"}])
                        if res and res.get("value"):
                            val = res["value"]
                            parsed_data = val.get("data", {})
                            if isinstance(parsed_data, dict) and parsed_data.get("parsed"):
                                info_node = parsed_data["parsed"].get("info", {})
                                info["owner"] = info_node.get("owner")
                                info["mint"] = info_node.get("mint")
                    except Exception:
                        pass
                    migrated = True
                elif detected == "WALLET" and t_type == "token":
                    logger.info(f"Auto-migrating {addr} from Specific Token Account ('token') to User Wallet ('user')")
                    info["type"] = "user"
                    info.pop("owner", None)
                    info.pop("mint", None)
                    migrated = True
                    
        if migrated:
            save_state_unlocked()
            logger.info("On-chain address type migrations completed and saved to secrets/tracked.json.")

def save_state_unlocked():
    try:
        with disk_state_lock():
            fresh_state = {"chats": {}, "global_last_signatures": {}}
            if os.path.exists(STATE_FILE):
                try:
                    with open(STATE_FILE, "r") as f:
                        fresh_state = json.load(f)
                except Exception:
                    pass
            
            fresh_state["global_last_signatures"] = state.get("global_last_signatures", {})
            for chat_id, chat_data in state.get("chats", {}).items():
                if chat_id not in fresh_state["chats"]:
                    fresh_state["chats"][chat_id] = chat_data
                else:
                    fresh_state["chats"][chat_id].update(chat_data)
            
            state.update(fresh_state)
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")

def save_state():
    with state_lock:
        save_state_unlocked()

def get_default_chat_state():
    return {
        "active": True,
        "currency": "USD",
        "interval": 1,
        "status_interval": 5,
        "whale_threshold": 1.0,
        "show_coin_link": True,
        "show_market_cap": True,
        "last_summary_time": time.time(),
        "last_status_time": 0.0,
        "status_txs": [],
        "tracked": {},
        "accumulated_txs": []
    }

# Solana RPC Client
class SolanaClient:
    def __init__(self, rpc_url):
        # Support comma-separated RPC URLs
        self.rpc_urls = [u.strip() for u in rpc_url.split(",")] if rpc_url else []
        if not self.rpc_urls:
            self.rpc_urls = ["https://api.mainnet-beta.solana.com"]
        self.current_index = 0
        self.session = requests.Session()
        
    def _call(self, method, params):
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params
        }
        for attempt in range(max(3, len(self.rpc_urls))):
            current_url = self.rpc_urls[self.current_index]
            try:
                r = self.session.post(
                    current_url, 
                    json=payload, 
                    headers={"Content-Type": "application/json"}, 
                    timeout=12
                )
                if r.status_code == 429:
                    logger.warning(f"Rate limited (429) by RPC {current_url}.")
                    if len(self.rpc_urls) > 1:
                        self.current_index = (self.current_index + 1) % len(self.rpc_urls)
                        logger.info(f"Switching to backup RPC: {self.rpc_urls[self.current_index]}")
                    time.sleep(1)
                    continue
                r.raise_for_status()
                res = r.json()
                if "error" in res:
                    logger.error(f"Solana RPC internal error on {method}: {res['error']}")
                    return None
                return res.get("result")
            except Exception as e:
                logger.warning(f"Solana RPC network error on {method} using {current_url}: {e}")
                if len(self.rpc_urls) > 1:
                    self.current_index = (self.current_index + 1) % len(self.rpc_urls)
                    logger.info(f"Switching to backup RPC: {self.rpc_urls[self.current_index]}")
                time.sleep(1)
        return None
        
    def get_signatures_for_address(self, address, limit=5):
        return self._call("getSignaturesForAddress", [address, {"limit": limit}])
        
    def get_transaction(self, signature):
        return self._call("getTransaction", [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0}])
        
    def get_balance(self, address):
        res = self._call("getBalance", [address])
        if res:
            return res.get("value", 0) / 1e9
        return 0.0

    def get_token_accounts(self, address):
        params = [
            address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ]
        return self._call("getTokenAccountsByOwner", params)

# Global variables for clients/cache
rpc_url = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
solana_client = SolanaClient(rpc_url)

# Hot reload state
last_env_mtime = 0.0

def check_hot_reload():
    global last_env_mtime, TELEGRAM_BOT_TOKEN, solana_client, rpc_url
    if os.path.exists(ENV_PATH):
        try:
            mtime = os.path.getmtime(ENV_PATH)
            if last_env_mtime == 0.0:
                last_env_mtime = mtime
            elif mtime > last_env_mtime:
                logger.info("Detected change in secrets/.env. Hot reloading configuration...")
                last_env_mtime = mtime
                load_dotenv(ENV_PATH, override=True)
                
                # Update tokens
                TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
                # Update logging formatter with new token if necessary
                formatter.token = TELEGRAM_BOT_TOKEN
                
                new_rpc = os.getenv("SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
                if new_rpc != rpc_url:
                    logger.info(f"Updating Solana Client RPC URL from {rpc_url} to {new_rpc}")
                    rpc_url = new_rpc
                    solana_client = SolanaClient(rpc_url)
        except Exception as e:
            logger.error(f"Failed to hot reload env: {e}")

def get_mint_for_token_account(address):
    # Cache to avoid calling RPC repeatedly
    if not hasattr(get_mint_for_token_account, "cache"):
        get_mint_for_token_account.cache = {}
    if address in get_mint_for_token_account.cache:
        return get_mint_for_token_account.cache[address]
    try:
        res = solana_client._call("getAccountInfo", [address, {"encoding": "jsonParsed"}])
        if res and res.get("value"):
            parsed_data = res["value"].get("data", {})
            if isinstance(parsed_data, dict) and parsed_data.get("parsed"):
                mint = parsed_data["parsed"].get("info", {}).get("mint")
                if mint:
                    get_mint_for_token_account.cache[address] = mint
                    return mint
    except Exception as e:
        logger.warning(f"Failed to get mint for token account {address}: {e}")
    return None

def classify_transaction(sol_change, token_changes, account_keys):
    # Check staking program IDs in account keys
    staking_programs = {
        "Config1111111111111111111111111111111111111",
        "Stake11111111111111111111111111111111111111"
    }
    has_stake_program = any(k in staking_programs for k in account_keys)
    if has_stake_program:
        return "🥩 Stake"
        
    # Check if there is both an inflow and an outflow
    inflow = False
    outflow = False
    
    if sol_change > 0.005:
        inflow = True
    elif sol_change < -0.005:
        outflow = True
        
    for mint, details in token_changes.items():
        change = details.get("change", 0.0)
        if change > 0.0001:
            inflow = True
        elif change < -0.0001:
            outflow = True
            
    if inflow and outflow:
        return "🔄 Trade"
    elif inflow:
        return "⚡ Transfer (Receive)"
    elif outflow:
        return "⚡ Transfer (Send)"
    return "⚡ Transfer"

token_metadata_cache = {}
fiat_rates_cache = {'rates': {}, 'last_update': 0.0}

def get_sol_price():
    now = time.time()
    if "SOL" in token_metadata_cache:
        cached = token_metadata_cache["SOL"]
        if now - cached['last_update'] < 300:
            return cached['price']
            
    url = "https://api.jup.ag/tokens/v2/search?query=So11111111111111111111111111111111111111112"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        res = r.json()
        if res and isinstance(res, list) and len(res) > 0:
            data = res[0]
            price = data.get("usdPrice")
            if price is not None:
                price = float(price)
                token_metadata_cache["SOL"] = {
                    'symbol': "SOL",
                    'price': price,
                    'last_update': now
                }
                return price
    except Exception as e:
        logger.warning(f"Failed to fetch SOL price: {e}")
        
    if "SOL" in token_metadata_cache:
        return token_metadata_cache["SOL"]['price']
    return 150.0

def get_token_metadata(mint):
    if mint == "So11111111111111111111111111111111111111112":
        return "SOL", get_sol_price()
        
    now = time.time()
    if mint in token_metadata_cache:
        cached = token_metadata_cache[mint]
        if now - cached['last_update'] < 300:
            return cached['symbol'], cached['price']
            
    # Hardcode stablecoins to avoid rate limits/failures
    if mint == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v":
        return "USDC", 1.0
    if mint == "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB":
        return "USDT", 1.0
        
    url = f"https://api.jup.ag/tokens/v2/search?query={mint}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        res = r.json()
        if res and isinstance(res, list) and len(res) > 0:
            data = res[0]
            symbol = data.get("symbol", f"{mint[:4]}...{mint[-4:]}")
            price = data.get("usdPrice")
            price = float(price) if price is not None else 0.0
            token_metadata_cache[mint] = {
                'symbol': symbol,
                'price': price,
                'last_update': now
            }
            return symbol, price
    except Exception as e:
        logger.warning(f"Failed to fetch metadata for {mint}: {e}")
        
    return f"{mint[:4]}...{mint[-4:]}", 0.0

# Caches for Dexscreener and RugCheck data to avoid rate limits
dex_market_cache = {}
rugcheck_cache = {}

def get_dex_market_data(mint):
    if mint == "So11111111111111111111111111111111111111112":
        return "https://dexscreener.com/solana/So11111111111111111111111111111111111111112", None
        
    now = time.time()
    if mint in dex_market_cache:
        cached = dex_market_cache[mint]
        if now - cached['last_update'] < 300: # 5 min cache
            return cached['url'], cached['mcap']
            
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        res = r.json()
        pairs = res.get("pairs")
        if pairs and isinstance(pairs, list) and len(pairs) > 0:
            solana_pairs = [p for p in pairs if p.get("chainId") == "solana"]
            if solana_pairs:
                # Sort by liquidity USD descending if present
                solana_pairs.sort(key=lambda p: p.get("liquidity", {}).get("usd", 0.0), reverse=True)
                main_pair = solana_pairs[0]
                
                pair_url = main_pair.get("url")
                mcap = main_pair.get("marketCap")
                if mcap is None:
                    mcap = main_pair.get("fdv")
                
                if not pair_url:
                    pair_url = f"https://dexscreener.com/solana/{mint}"
                    
                dex_market_cache[mint] = {
                    'url': pair_url,
                    'mcap': mcap,
                    'last_update': now
                }
                return pair_url, mcap
    except Exception as e:
        logger.warning(f"Failed to fetch Dexscreener data for {mint}: {e}")
        
    fallback_url = f"https://dexscreener.com/solana/{mint}"
    return fallback_url, None

def get_rugcheck_report(mint):
    if mint == "So11111111111111111111111111111111111111112":
        return {}
        
    now = time.time()
    if mint in rugcheck_cache:
        cached = rugcheck_cache[mint]
        if now - cached['last_update'] < 300: # 5 min cache
            return cached['report']
            
    url = f"https://api.rugcheck.xyz/v1/tokens/{mint}/report"
    try:
        r = requests.get(url, timeout=8)
        if r.status_code == 200:
            report = r.json()
            rugcheck_cache[mint] = {
                'report': report,
                'last_update': now
            }
            return report
    except Exception as e:
        logger.warning(f"Failed to fetch RugCheck report for {mint}: {e}")
        
    return {}

def get_bundled_percentage(report):
    if not report:
        return 0.0
    risks = report.get("risks", [])
    for r in risks:
        name = r.get("name", "").lower()
        if "bundled" in name or "insider" in name:
            val = r.get("value", "")
            if "%" in val:
                try:
                    return float(val.replace("%", "").strip())
                except Exception:
                    pass
    # Fallback to summing top insider holders
    top_holders = report.get("topHolders", [])
    insider_pct = sum(h.get("pct", 0.0) for h in top_holders if h.get("insider") is True)
    return insider_pct

def get_kol_count(report):
    if not report:
        return 0
    kol_wallets = set()
    known_accounts = report.get("knownAccounts", {})
    for acc, details in known_accounts.items():
        acc_type = details.get("type", "").lower()
        acc_name = details.get("name", "").lower()
        if "kol" in acc_type or "kol" in acc_name or "influencer" in acc_type or "influencer" in acc_name:
            kol_wallets.add(acc)
            
    top_holders = report.get("topHolders", [])
    for h in top_holders:
        owner = h.get("owner")
        if owner in known_accounts:
            details = known_accounts[owner]
            acc_type = details.get("type", "").lower()
            acc_name = details.get("name", "").lower()
            if "kol" in acc_type or "kol" in acc_name or "influencer" in acc_type or "influencer" in acc_name:
                kol_wallets.add(owner)
                
    return len(kol_wallets)

def get_whale_count(report, threshold_pct=1.0):
    if not report:
        return 0
    top_holders = report.get("topHolders", [])
    whale_count = 0
    for h in top_holders:
        pct = h.get("pct", 0.0)
        if pct >= threshold_pct:
            whale_count += 1
    return whale_count

def format_mcap(mcap_value):
    if mcap_value is None:
        return "N/A"
    try:
        val = float(mcap_value)
        if val >= 1e9:
            return f"${val/1e9:,.1f}B"
        elif val >= 1e6:
            return f"${val/1e6:,.1f}M"
        elif val >= 1e3:
            return f"${val/1e3:,.1f}K"
        else:
            return f"${val:,.0f}"
    except Exception:
        return "N/A"

def get_fiat_rates():
    now = time.time()
    if now - fiat_rates_cache['last_update'] < 3600 and fiat_rates_cache['rates']:
        return fiat_rates_cache['rates']
        
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        res = r.json()
        if res.get("result") == "success":
            rates = res.get("rates", {})
            fiat_rates_cache['rates'] = rates
            fiat_rates_cache['last_update'] = now
            return rates
    except Exception as e:
        logger.warning(f"Failed to fetch fiat exchange rates: {e}")
        
    return fiat_rates_cache.get('rates', {})

def convert_usd(amount_usd, target_currency):
    rates = get_fiat_rates()
    curr = target_currency.upper()
    if curr == "NIS":
        curr = "ILS"
        
    rate = rates.get(curr)
    if rate:
        return amount_usd * rate, target_currency.upper()
    return amount_usd, "USD"

def format_currency(amount_usd, target_currency):
    val, symbol = convert_usd(amount_usd, target_currency)
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "ILS": "₪",
        "NIS": "₪",
        "CAD": "CA$",
        "AUD": "A$"
    }
    sym = symbols.get(symbol, f" {symbol}")
    if sym.startswith(" "):
        return f"{val:,.2f}{sym}"
    else:
        return f"{sym}{val:,.2f}"

# Telegram API wrapper
def make_telegram_request(method, data=None, files=None):
    if not TELEGRAM_BOT_TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN configured.")
        return None
        
    if method == "sendMessage" and data and "chat_id" in data:
        cid = str(data["chat_id"])
        with state_lock:
            is_silent = state.get("chats", {}).get(cid, {}).get("silent_alerts", False)
        if is_silent:
            data["disable_notification"] = True
            
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"
    try:
        if files:
            r = requests.post(url, data=data, files=files, timeout=20)
        else:
            r = requests.post(url, json=data, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"Telegram API request failed for {method}: {e}")
        return None


def format_duration(minutes):
    if minutes >= 60:
        hrs = minutes // 60
        mins = minutes % 60
        if mins == 0:
            return f"{hrs}:00 hour{'s' if hrs > 1 else ''}"
        return f"{hrs}:{mins:02d} hour{'s' if hrs > 1 else ''}"
    else:
        return f"{minutes} minutes"

def reply_to(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    make_telegram_request("sendMessage", data=payload)

def send_cleanup_reply(chat_id, text, reply_markup=None):
    chat_id_str = str(chat_id)
    with state_lock:
        last_msg_id = state.get("chats", {}).get(chat_id_str, {}).get("last_bot_msg_id")
        
    if last_msg_id:
        try:
            make_telegram_request("deleteMessage", data={"chat_id": chat_id, "message_id": last_msg_id})
        except Exception:
            pass
            
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    res = make_telegram_request("sendMessage", data=payload)
    if res and res.get("ok"):
        msg_id = res.get("result", {}).get("message_id")
        with state_lock:
            current_state = safe_read_state_file(state)
            if chat_id_str in current_state.get("chats", {}):
                current_state["chats"][chat_id_str]["last_bot_msg_id"] = msg_id
                state = current_state
                save_state_unlocked()

def send_dashboard(chat_id):
    global state
    text = (
        "⚙️ <b>Solana Tracker Control Panel</b>\n\n"
        "Use the buttons below to interact with the tracker bot from your phone without typing commands."
    )
    # Check current active state to show correct text
    chat_id_str = str(chat_id)
    with state_lock:
        active = state.get("chats", {}).get(chat_id_str, {}).get("active", True)
    pause_btn_text = "⏸️ Pause Bot" if active else "▶️ Resume Bot"
    pause_callback = "pause_bot" if active else "resume_bot"
    
    markup = {
        "inline_keyboard": [
            [
                {"text": "📊 Portfolio", "callback_data": "refresh_balance"},
                {"text": "⚡ Refresh Logs", "callback_data": "refresh_logs"}
            ],
            [
                {"text": "⚙️ Settings Summary", "callback_data": "dashboard_settings"},
                {"text": pause_btn_text, "callback_data": pause_callback}
            ]
        ]
    }
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "reply_markup": markup
    }
    res = make_telegram_request("sendMessage", data=payload)
    if res and res.get("ok"):
        msg_id = res.get("result", {}).get("message_id")
        try:
            make_telegram_request("pinChatMessage", data={"chat_id": chat_id, "message_id": msg_id, "disable_notification": True})
        except Exception:
            pass
        with state_lock:
            current_state = safe_read_state_file(state)
            if chat_id_str in current_state.get("chats", {}):
                current_state["chats"][chat_id_str]["dashboard_message_id"] = msg_id
                state = current_state
                save_state_unlocked()

def update_dashboard_markup(chat_id, message_id, active):
    pause_btn_text = "⏸️ Pause Bot" if active else "▶️ Resume Bot"
    pause_callback = "pause_bot" if active else "resume_bot"
    markup = {
        "inline_keyboard": [
            [
                {"text": "📊 Portfolio", "callback_data": "refresh_balance"},
                {"text": "⚡ Refresh Logs", "callback_data": "refresh_logs"}
            ],
            [
                {"text": "⚙️ Settings Summary", "callback_data": "dashboard_settings"},
                {"text": pause_btn_text, "callback_data": pause_callback}
            ]
        ]
    }
    make_telegram_request("editMessageReplyMarkup", data={
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": markup
    })

startup_time = time.time()
recent_alerts = []
recent_alerts_lock = threading.Lock()

def register_telegram_commands():
    commands = [
        {"command": "start", "description": "Show the control dashboard"},
        {"command": "status", "description": "Show current tracker health and stats"},
        {"command": "last", "description": "Retrieve the 5 most recent transaction alerts"},
        {"command": "alert", "description": "Toggle Silent vs Active alert mode"},
        {"command": "interval", "description": "Set summary alert frequency"},
        {"command": "help", "description": "Show helper menu"}
    ]
    make_telegram_request("setMyCommands", data={"commands": commands})


def handle_status_command(chat_id):
    uptime_seconds = int(time.time() - startup_time)
    h = uptime_seconds // 3600
    m = (uptime_seconds % 3600) // 60
    s = uptime_seconds % 60
    uptime_str = f"{h}h {m}m {s}s"
    
    slot = None
    try:
        slot = solana_client._call("getSlot", [])
    except Exception:
        pass
        
    status_text = "🟢" if slot else "🔴"
    slot_str = str(slot) if slot else "N/A"
    
    report = f"🤖 <b>Status:</b> {status_text} | ⏳ <b>Uptime:</b> {uptime_str} | 📦 <b>Last Slot:</b> {slot_str}"
    send_cleanup_reply(chat_id, report)

def handle_last_command(chat_id):
    with recent_alerts_lock:
        alerts = list(recent_alerts)
    if not alerts:
        send_cleanup_reply(chat_id, "ℹ️ No transaction alerts have been recorded since the bot started.")
        return
        
    send_cleanup_reply(chat_id, f"📋 <b>Last {len(alerts)} Transactions:</b>")
    for msg in alerts:
        payload = {
            "chat_id": chat_id,
            "text": msg["text"],
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if msg.get("reply_markup"):
            payload["reply_markup"] = msg["reply_markup"]
        make_telegram_request("sendMessage", data=payload)

def handle_alert_command(chat_id):
    chat_id_str = str(chat_id)
    with state_lock:
        current_state = safe_read_state_file(state)
        if chat_id_str in current_state.get("chats", {}):
            current = current_state["chats"][chat_id_str].get("silent_alerts", False)
            new_val = not current
            current_state["chats"][chat_id_str]["silent_alerts"] = new_val
            state = current_state
            save_state_unlocked()
    mode_str = "🔇 Silent Mode (No Sound)" if new_val else "🔊 Active Mode (With Sound)"
    send_cleanup_reply(chat_id, f"🔔 Alert notification mode changed to: <b>{mode_str}</b>")

def identify_address(address_str):
    try:
        res = solana_client._call("getAccountInfo", [address_str, {"encoding": "jsonParsed"}])
        if not res or res.get("value") is None:
            if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address_str):
                return "WALLET"
            return "INVALID_OR_EMPTY"
            
        val = res["value"]
        owner = val.get("owner")
        
        if owner == "11111111111111111111111111111111":
            return "WALLET"
        elif owner in ("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "TokenzQdBNbkh56NSs27s376uaR659755iy3Bbz6n26"):
            return "TOKEN"
        else:
            return "OTHER_PROGRAM"
    except Exception:
        return "ERROR"

def add_wallet_flow(chat_id, addr_type, address, custom_name):
    if not re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address):
        send_cleanup_reply(chat_id, "❌ Invalid Solana address base58 format.")
        return
        
    owner_addr = None
    token_mint = None
    detected_type = addr_type
    
    try:
        res = solana_client._call("getAccountInfo", [address, {"encoding": "jsonParsed"}])
        if res and res.get("value"):
            val = res["value"]
            owner = val.get("owner")
            if owner in ("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "TokenzQdBNbkh56NSs27s376uaR659755iy3Bbz6n26"):
                detected_type = "token"
                parsed_data = val.get("data", {})
                if isinstance(parsed_data, dict) and parsed_data.get("parsed"):
                    info_node = parsed_data["parsed"].get("info", {})
                    owner_addr = info_node.get("owner")
                    token_mint = info_node.get("mint")
            else:
                detected_type = "user"
    except Exception as e:
        logger.warning(f"Error auto-detecting wallet type for {address}: {e}")

    sigs = solana_client.get_signatures_for_address(address, limit=1)
    last_sig = sigs[0].get("signature") if sigs and len(sigs) > 0 else None
    
    with state_lock:
        chat_id_str = str(chat_id)
        if "chats" not in state:
            state["chats"] = {}
        if chat_id_str not in state["chats"]:
            state["chats"][chat_id_str] = get_default_chat_state()
            
        tracked_entry = {
            "type": detected_type,
            "name": custom_name
        }
        if owner_addr:
            tracked_entry["owner"] = owner_addr
        if token_mint:
            tracked_entry["mint"] = token_mint
            
        state["chats"][chat_id_str]["tracked"][address] = tracked_entry
        
        if "global_last_signatures" not in state:
            state["global_last_signatures"] = {}
        if address not in state["global_last_signatures"] or not state["global_last_signatures"][address]:
            state["global_last_signatures"][address] = last_sig
        save_state_unlocked()
        
    type_lbl = "User Wallet" if detected_type == "user" else "Specific Token Account"
    extra_info = ""
    if detected_type == "token":
        extra_info += f"\nOwner: <code>{owner_addr}</code>" if owner_addr else ""
        extra_info += f"\nMint: <code>{token_mint}</code>" if token_mint else ""
    send_cleanup_reply(chat_id, f"✅ Tracking added for {type_lbl}:\n<code>{address}</code>{extra_info}\nName: <code>{custom_name}</code>")




def send_help(chat_id):
    text = (
        "👋 <b>Solana Wallet Tracker Bot Help</b>\n\n"
        "<b>Core Commands:</b>\n"
        "• <code>/start</code> - Display the Control Panel Dashboard\n"
        "• <code>/status</code> - Show bot health, uptime, and current slot\n"
        "• <code>/last</code> - Show the 5 most recent transaction alerts\n"
        "• <code>/alert</code> - Toggle Silent vs Active alert mode\n\n"
        "<b>Smart Input Shortcuts (No commands needed!):</b>\n"
        "• Send any <b>Solana Address</b> to start tracking it automatically\n"
        "• Send any <b>number</b> (e.g. <code>50</code> or <code>$10.5</code>) to set the minimum alert USD threshold\n"
        "• Type <code>add [address] [name]</code> to add a wallet with a custom name\n"
        "• Type <code>price [token]</code> (e.g. <code>price SOL</code>) to get the current price"
    )
    reply_to(chat_id, text)


# Balance formatter
def format_balance(chat_id):
    with state_lock:
        chat_data = state.get("chats", {}).get(str(chat_id), {})
        
    tracked = chat_data.get("tracked", {})
    if not tracked:
        return "No wallets are currently tracked in this chat. Use <code>/add &lt;address&gt;</code> to start."
        
    currency = chat_data.get("currency", "USD")
    sol_price = get_sol_price()
    
    lines = ["💰 <b>Current Wallet Balances</b>\n"]
    total_usd_all = 0.0
    
    for addr, info in tracked.items():
        name = info.get("name", "Unnamed")
        addr_type = info.get("type", "user")
        
        if addr_type == "token":
            mint_addr = get_mint_for_token_account(addr)
            link = f"https://solscan.io/token/{mint_addr}" if mint_addr else f"https://solscan.io/account/{addr}"
        else:
            link = f"https://solscan.io/account/{addr}"
            
        lines.append(f"👤 <b>{name}</b> (<a href='{link}'><code>{addr[:4]}...{addr[-4:]}</code></a>) [<i>{addr_type}</i>]")
        
        # We will list assets inside a code block for clean alignment
        table_rows = []
        table_rows.append(f"{'Asset':<8} {'Amount':<10} {'Value'}")
        table_rows.append("─" * 28)
        
        # SOL Balance
        sol_bal = solana_client.get_balance(addr)
        sol_val_usd = sol_bal * sol_price
        total_usd_all += sol_val_usd
        table_rows.append(f"{'SOL':<8} {sol_bal:<10,.4f} {format_currency(sol_val_usd, currency)}")
        
        # Token Balances
        token_accounts = solana_client.get_token_accounts(addr)
        if token_accounts:
            for item in token_accounts.get("value", []):
                parsed = item.get("account", {}).get("data", {}).get("parsed", {})
                info_node = parsed.get("info", {})
                mint = info_node.get("mint")
                amount_info = info_node.get("tokenAmount", {})
                amount = float(amount_info.get("uiAmount", 0.0))
                
                if amount > 0.0001:
                    symbol, price = get_token_metadata(mint)
                    val_usd = amount * price
                    total_usd_all += val_usd
                    table_rows.append(f"{symbol[:6]:<8} {amount:<10,.2f} {format_currency(val_usd, currency)}")
                    
        lines.append("<pre>" + "\n".join(table_rows) + "</pre>")
        lines.append("")
        
    lines.append(f"<b>Total Value: {format_currency(total_usd_all, currency)}</b>")
    return "\n".join(lines)


def format_status_report(chat_id, clear_after=False):
    global state
    with state_lock:
        chat_data = state.get("chats", {}).get(str(chat_id), {})
    
    tracked = chat_data.get("tracked", {})
    if not tracked:
        return "No wallets are currently tracked in this chat. Use <code>/add &lt;address&gt;</code> to start."
        
    currency = chat_data.get("currency", "USD")
    sol_price = get_sol_price()
    whale_threshold = chat_data.get("whale_threshold", 1.0)
    show_coin_link = chat_data.get("show_coin_link", True)
    show_market_cap = chat_data.get("show_market_cap", True)
    
    # Extract accumulated transactions for the status interval
    status_txs = chat_data.get("status_txs", [])
    
    lines = []
    
    for addr, info in tracked.items():
        name = info.get("name", addr)
        # If the name is just the address, show truncated address
        if name == addr:
            name = f"{addr[:4]}...{addr[-4:]}"
            
        addr_type = info.get("type", "user")
        
        if addr_type == "token":
            mint_addr = get_mint_for_token_account(addr)
            link = f"https://solscan.io/token/{mint_addr}" if mint_addr else f"https://solscan.io/account/{addr}"
        else:
            link = f"https://solscan.io/account/{addr}"
            
        solscan_link = f"<a href='{link}'>Solscan</a>"
        lines.append(f"Scan complete for <b>{name}</b> - {solscan_link}")
        
        # Aggregate buys/sells of tokens for this wallet since last status interval
        wallet_txs = [tx for tx in status_txs if tx.get("address") == addr]
        net_changes = {} # mint -> token_change
        for tx in wallet_txs:
            token_changes = tx.get("token_changes", {})
            for mint, details in token_changes.items():
                if mint not in net_changes:
                    net_changes[mint] = 0.0
                net_changes[mint] += details.get("change", 0.0)
                
        # Non-zero token accounts & active scanned tokens
        tokens_scanned = set()
        
        if addr_type == "user":
            # Show SOL
            sol_bal = solana_client.get_balance(addr)
            sol_val_usd = sol_bal * sol_price
            lines.append(f"  • SOL: {sol_bal:,.4f} SOL ({format_currency(sol_val_usd, currency)})")
            
            # Show token balances
            token_accounts = solana_client.get_token_accounts(addr)
            if token_accounts:
                for item in token_accounts.get("value", []):
                    parsed = item.get("account", {}).get("data", {}).get("parsed", {})
                    info_node = parsed.get("info", {})
                    mint = info_node.get("mint")
                    amount_info = info_node.get("tokenAmount", {})
                    amount = float(amount_info.get("uiAmount", 0.0))
                    
                    if amount > 0.0001:
                        tokens_scanned.add(mint)
                        symbol, price = get_token_metadata(mint)
                        val_usd = amount * price
                        
                        # Get RugCheck & Dexscreener data
                        pair_url, mcap_val = get_dex_market_data(mint)
                        report = get_rugcheck_report(mint)
                        bundled_val = get_bundled_percentage(report)
                        kol_val = get_kol_count(report)
                        whale_val = get_whale_count(report, whale_threshold)
                        
                        mcap_str = format_currency(mcap_val, currency) if mcap_val else "N/A"
                        
                        # Coin link
                        if show_coin_link and pair_url:
                            symbol_str = f"<a href='{pair_url}'>{symbol}</a>"
                        else:
                            symbol_str = symbol
                            
                        if show_market_cap:
                            lines.append(f"  • <b>{symbol_str}</b>: {amount:,.4f} ({format_currency(val_usd, currency)}) [💰 MC: {mcap_str}]")
                        else:
                            lines.append(f"  • <b>{symbol_str}</b>: {amount:,.4f} ({format_currency(val_usd, currency)})")
                            
                        # Show accumulated trades in this interval
                        net_tok = net_changes.get(mint, 0.0)
                        if net_tok > 0.0:
                            lines.append(f"    📈 bought: +{net_tok:,.2f} {symbol}")
                        elif net_tok < 0.0:
                            lines.append(f"    📉 sold: -{abs(net_tok):,.2f} {symbol}")
                            
                        lines.append(f"    🚨 Bundled: {bundled_val:.2f}% | 🔑 KOLs: {kol_val} | 🐳 Whales: {whale_val}")
        else:
            # Specific token account
            try:
                res = solana_client._call("getAccountInfo", [addr, {"encoding": "jsonParsed"}])
                if res and res.get("value"):
                    parsed_data = res["value"].get("data", {})
                    if isinstance(parsed_data, dict) and parsed_data.get("parsed"):
                        info_node = parsed_data["parsed"].get("info", {})
                        mint = info_node.get("mint")
                        amount_info = info_node.get("tokenAmount", {})
                        amount = float(amount_info.get("uiAmount", 0.0))
                        
                        symbol, price = get_token_metadata(mint)
                        val_usd = amount * price
                        
                        pair_url, mcap_val = get_dex_market_data(mint)
                        report = get_rugcheck_report(mint)
                        bundled_val = get_bundled_percentage(report)
                        kol_val = get_kol_count(report)
                        whale_val = get_whale_count(report, whale_threshold)
                        
                        mcap_str = format_currency(mcap_val, currency) if mcap_val else "N/A"
                        
                        if show_coin_link and pair_url:
                            symbol_str = f"<a href='{pair_url}'>{symbol}</a>"
                        else:
                            symbol_str = symbol
                            
                        if show_market_cap:
                            lines.append(f"  • <b>{symbol_str}</b>: {amount:,.4f} ({format_currency(val_usd, currency)}) [💰 MC: {mcap_str}]")
                        else:
                            lines.append(f"  • <b>{symbol_str}</b>: {amount:,.4f} ({format_currency(val_usd, currency)})")
                            
                        # Show accumulated trades in this interval
                        net_tok = net_changes.get(mint, 0.0)
                        if net_tok > 0.0:
                            lines.append(f"    📈 bought: +{net_tok:,.2f} {symbol}")
                        elif net_tok < 0.0:
                            lines.append(f"    📉 sold: -{abs(net_tok):,.2f} {symbol}")
                            
                        lines.append(f"    🚨 Bundled: {bundled_val:.2f}% | 🔑 KOLs: {kol_val} | 🐳 Whales: {whale_val}")
            except Exception as e:
                lines.append(f"  • Failed to read token account info: {e}")
                
        lines.append("")
        
    if clear_after:
        with state_lock:
            # We fetch state from file to prevent concurrent overwrite issues
            current_state = safe_read_state_file(state)
                
            cid_str = str(chat_id)
            if cid_str in current_state.get("chats", {}):
                current_state["chats"][cid_str]["status_txs"] = []
                current_state["chats"][cid_str]["last_status_time"] = time.time()
                state = current_state
                save_state_unlocked()
                
    return "\n".join(lines).strip()

def format_daily_summary(chat_id):
    global state
    with state_lock:
        chat_data = state.get("chats", {}).get(str(chat_id), {})
    tracked = chat_data.get("tracked", {})
    if not tracked:
        return "No wallets tracked. Cannot generate portfolio snapshot."
        
    currency = chat_data.get("currency", "USD")
    sol_price = get_sol_price()
    
    # Calculate current total value
    total_val_usd = 0.0
    token_holdings = {} # mint -> (symbol, amount, usd_val)
    
    lines = [
        "📊 <b>Daily Portfolio Snapshot</b>",
        f"📅 Date: <code>{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</code>",
        "─" * 24
    ]
    
    for addr, info in tracked.items():
        # SOL Balance
        sol_bal = solana_client.get_balance(addr)
        sol_val = sol_bal * sol_price
        total_val_usd += sol_val
        if "SOL" not in token_holdings:
            token_holdings["SOL"] = ("SOL", 0.0, 0.0)
        t_sym, t_amt, t_val = token_holdings["SOL"]
        token_holdings["SOL"] = ("SOL", t_amt + sol_bal, t_val + sol_val)
        
        # Token accounts
        try:
            token_accounts = solana_client.get_token_accounts(addr)
            if token_accounts:
                for item in token_accounts.get("value", []):
                    parsed = item.get("account", {}).get("data", {}).get("parsed", {})
                    info_node = parsed.get("info", {})
                    mint = info_node.get("mint")
                    amount = float(info_node.get("tokenAmount", {}).get("uiAmount", 0.0))
                    if amount > 0.0001:
                        symbol, price = get_token_metadata(mint)
                        val = amount * price
                        total_val_usd += val
                        if mint not in token_holdings:
                            token_holdings[mint] = (symbol, 0.0, 0.0)
                        t_sym, t_amt, t_val = token_holdings[mint]
                        token_holdings[mint] = (symbol, t_amt + amount, t_val + val)
        except Exception as e:
            logger.warning(f"Error fetching token accounts for snapshot {addr}: {e}")
                    
    # Read/compare history
    last_snapshots = chat_data.get("snapshots", {})
    prev_val_usd = None
    if last_snapshots:
        sorted_dates = sorted(last_snapshots.keys(), reverse=True)
        if sorted_dates:
            prev_val_usd = last_snapshots[sorted_dates[0]]
            
    # Format PnL
    curr_formatted = format_currency(total_val_usd, currency)
    lines.append(f"💰 <b>Total Portfolio Value:</b> {curr_formatted}")
    
    if prev_val_usd is not None:
        pnl_usd = total_val_usd - prev_val_usd
        pnl_pct = (pnl_usd / prev_val_usd * 100) if prev_val_usd > 0 else 0.0
        pnl_formatted = format_currency(pnl_usd, currency)
        sign = "+" if pnl_usd >= 0 else ""
        emoji = "📈" if pnl_usd >= 0 else "📉"
        lines.append(f"{emoji} <b>24h PnL:</b> {sign}{pnl_formatted} ({sign}{pnl_pct:.2f}%)")
    else:
        lines.append("📈 <b>24h PnL:</b> Initial snapshot recorded. (PnL tracking starts tomorrow!)")
        
    # Store snapshot in state
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    with state_lock:
        current_state = safe_read_state_file(state)
        chat_id_str = str(chat_id)
        if chat_id_str in current_state.get("chats", {}):
            if "snapshots" not in current_state["chats"][chat_id_str]:
                current_state["chats"][chat_id_str]["snapshots"] = {}
            current_state["chats"][chat_id_str]["snapshots"][today_str] = total_val_usd
            snaps = current_state["chats"][chat_id_str]["snapshots"]
            if len(snaps) > 30:
                oldest_date = sorted(snaps.keys())[0]
                del snaps[oldest_date]
            state = current_state
            save_state_unlocked()
        
    lines.append("")
    lines.append("🪙 <b>Top Holdings:</b>")
    
    # Sort holdings by value descending
    sorted_holdings = sorted(token_holdings.items(), key=lambda x: x[1][2], reverse=True)
    
    # Format table alignment with code block
    table_lines = []
    table_lines.append(f"{'Token':<10} {'Amount':<12} {'Value'}")
    table_lines.append("─" * 35)
    for mint, (symbol, amount, val) in sorted_holdings[:5]:
        amt_str = f"{amount:,.2f}"
        val_str = format_currency(val, currency)
        table_lines.append(f"{symbol[:8]:<10} {amt_str:<12} {val_str}")
        
    lines.append("<pre>" + "\n".join(table_lines) + "</pre>")
    return "\n".join(lines)

# Export config
def handle_export(chat_id):
    with state_lock:
        chat_data = state.get("chats", {}).get(str(chat_id), {})
        
    export_data = {
        "currency": chat_data.get("currency", "USD"),
        "interval": chat_data.get("interval", 1),
        "tracked": chat_data.get("tracked", {})
    }
    
    try:
        file_bytes = json.dumps(export_data, indent=2).encode('utf-8')
        bio = io.BytesIO(file_bytes)
        bio.name = f"tracker_config_{chat_id}.json"
        
        make_telegram_request("sendDocument", data={
            "chat_id": chat_id,
            "caption": "📥 Here is your exported config file."
        }, files={"document": bio})
    except Exception as e:
        logger.error(f"Export failed: {e}")
        reply_to(chat_id, "❌ Export failed.")

# Import config
def handle_import(chat_id, document):
    file_id = document.get("file_id")
    file_name = document.get("file_name", "config.json")
    
    if not file_name.endswith(".json"):
        reply_to(chat_id, "❌ Please upload a valid JSON config file.")
        return
        
    reply_to(chat_id, "⏳ Importing configuration...")
    res = make_telegram_request("getFile", data={"file_id": file_id})
    if not res or not res.get("ok"):
        reply_to(chat_id, "❌ Failed to retrieve file from Telegram.")
        return
        
    file_path = res.get("result", {}).get("file_path")
    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
    
    try:
        r = requests.get(download_url, timeout=15)
        r.raise_for_status()
        imported = r.json()
    except Exception as e:
        logger.error(f"Import parse failed: {e}")
        reply_to(chat_id, "❌ Failed to parse JSON file.")
        return
        
    if not isinstance(imported, dict):
        reply_to(chat_id, "❌ Invalid JSON data structure.")
        return
        
    currency = imported.get("currency", "USD").upper()
    if len(currency) != 3:
        currency = "USD"
        
    try:
        interval = int(imported.get("interval", 1))
        if interval < 1:
            interval = 1
    except Exception:
        interval = 1
        
    imported_tracked = imported.get("tracked", {})
    if not isinstance(imported_tracked, dict):
        reply_to(chat_id, "❌ Invalid tracked wallets list format.")
        return
        
    valid_tracked = {}
    addresses_to_initialize = []
    
    for addr, info in imported_tracked.items():
        if not isinstance(info, dict):
            continue
        if not re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", addr):
            continue
        t_type = info.get("type", "user")
        if t_type in ("token", "wallet"):
            t_type = "token"
        else:
            t_type = "user"
        name = info.get("name", f"{addr[:4]}...{addr[-4:]}")
        
        valid_tracked[addr] = {"type": t_type, "name": name}
        addresses_to_initialize.append(addr)
        
    if not valid_tracked:
        reply_to(chat_id, "❌ No valid tracked wallets found.")
        return
        
    # Set signature offsets
    for addr in addresses_to_initialize:
        with state_lock:
            existing = state.get("global_last_signatures", {}).get(addr)
        if not existing:
            sigs = solana_client.get_signatures_for_address(addr, limit=1)
            last_sig = sigs[0].get("signature") if sigs and len(sigs) > 0 else None
            with state_lock:
                if "global_last_signatures" not in state:
                    state["global_last_signatures"] = {}
                state["global_last_signatures"][addr] = last_sig
                
    # Update State
    with state_lock:
        chat_id_str = str(chat_id)
        if "chats" not in state:
            state["chats"] = {}
        if chat_id_str not in state["chats"]:
            state["chats"][chat_id_str] = get_default_chat_state()
        state["chats"][chat_id_str]["currency"] = currency
        state["chats"][chat_id_str]["interval"] = interval
        state["chats"][chat_id_str]["tracked"].update(valid_tracked)
        save_state_unlocked()
        
    reply_to(chat_id, f"✅ Configuration imported successfully!\n• Currency: <b>{currency}</b>\n• Interval: <b>{interval} minutes</b>\n• Merged <b>{len(valid_tracked)}</b> addresses.")

def format_transaction_group(wallet_name, address, wallet_type, events, currency, show_coin_link=True, show_market_cap=True, whale_threshold=1.0, concise=False):
    icon = "👛" if wallet_type == "user" else "🧿"
    
    # Group events by token mint
    mint_groups = {} # mint -> { 'sigs': [], 'token_change': 0.0, 'sol_change': 0.0, 'value_usd': 0.0 }
    sol_only_events = []
    
    for ev in events:
        sig = ev["sig"]
        sol_change = ev["sol_change"]
        token_changes = ev["token_changes"]
        value_usd = ev["value_usd"]
        
        if not token_changes:
            sol_only_events.append(ev)
        else:
            for mint, details in token_changes.items():
                if mint not in mint_groups:
                    mint_groups[mint] = {
                        'sigs': [],
                        'token_change': 0.0,
                        'sol_change': 0.0,
                        'value_usd': 0.0
                    }
                if sig not in mint_groups[mint]['sigs']:
                    mint_groups[mint]['sigs'].append(sig)
                mint_groups[mint]['token_change'] += details['change']
                mint_groups[mint]['sol_change'] += sol_change
                mint_groups[mint]['value_usd'] += value_usd
 
    messages = []
    
    # Format token mint groups
    for mint, data in mint_groups.items():
        sigs = data['sigs']
        tx_count = len(sigs)
        tok_change = data['token_change']
        sol_change = data['sol_change']
        val_usd = data['value_usd']
        
        symbol, _ = get_token_metadata(mint)
        mint_short = mint[:6]
        
        val_str = format_currency(val_usd, currency)
        
        # Determine emoji and action
        if len(events) == 1:
            tx_type = events[0].get("tx_type", "⚡ Transfer")
            if "Trade" in tx_type:
                if tok_change > 0:
                    emoji = "🟢"
                    action = "Buy"
                else:
                    emoji = "🔴"
                    action = "Sell"
            elif "Receive" in tx_type:
                emoji = "📥"
                action = "Transfer (Received)"
            elif "Send" in tx_type:
                emoji = "📤"
                action = "Transfer (Sent)"
            elif "Stake" in tx_type:
                emoji = "🥩"
                action = "Stake / Unstake"
            else:
                emoji = "⚡"
                action = "Transfer"
        else:
            # Grouped summary
            if tok_change > 0:
                emoji = "🟢"
                action = "Accumulated Buy"
            else:
                emoji = "🔴"
                action = "Accumulated Sell"
            
        if wallet_type == "token":
            mint_addr = get_mint_for_token_account(address)
            solscan_url = f"https://solscan.io/token/{mint_addr}" if mint_addr else f"https://solscan.io/account/{address}"
        else:
            solscan_url = f"https://solscan.io/account/{address}"
            
        solscan_link = f"<a href='{solscan_url}'>Solscan</a>"
        pair_url, mcap_val = get_dex_market_data(mint)
        
        if concise:
            header = f"{icon} <b>{wallet_name}</b> ({solscan_link})"
            count_str = f"{tx_count} " if tx_count > 1 else ""
            body = f"{emoji} {count_str}<b>{action}:</b> {abs(tok_change):,.2f} {symbol} ({mint_short}) ({val_str})"
            
            tx_lines = []
            for sig in sigs[:5]:
                tx_lines.append(f"🔗 <a href='https://solscan.io/tx/{sig}'>{sig[:6]}</a>")
            if len(sigs) > 5:
                tx_lines.append(f"(+{len(sigs) - 5} more)")
                
            msg = "\n".join([header, body, ""] + tx_lines)
        else:
            report = get_rugcheck_report(mint)
            bundled_val = get_bundled_percentage(report)
            kol_val = get_kol_count(report)
            whale_val = get_whale_count(report, whale_threshold)
            
            # Coin link
            if show_coin_link and pair_url:
                symbol_str = f"<a href='{pair_url}'>{symbol}</a>"
            else:
                symbol_str = symbol
                
            mcap_str = format_currency(mcap_val, currency) if mcap_val else "N/A"
            header = f"Scan complete for <b>{wallet_name}</b> - {solscan_link}"
            
            body_lines = [
                f"{emoji} <b>{action}:</b> {abs(tok_change):,.2f} {symbol_str} ({val_str})",
                f"🚨 <b>Bundled:</b> {bundled_val:.2f}%",
                f"🔑 <b>KOLs:</b> {kol_val} | 🐳 <b>Whales:</b> {whale_val}"
            ]
            if show_market_cap:
                body_lines.insert(1, f"💰 <b>Market Cap:</b> {mcap_str}")
                
            body = "\n".join(body_lines)
            
            tx_lines = []
            for sig in sigs[:5]:
                tx_lines.append(f"🔗 <a href='https://solscan.io/tx/{sig}'>{sig[:6]}</a>")
            if len(sigs) > 5:
                tx_lines.append(f"(+{len(sigs) - 5} more)")
                
            msg = "\n".join([header, "", body, ""] + tx_lines)
            
        buttons = []
        row = []
        row.append({"text": "🌐 Solscan", "url": solscan_url})
        if pair_url:
            row.append({"text": "📈 Chart", "url": pair_url})
        buttons.append(row)
        reply_markup = {"inline_keyboard": buttons}
        
        messages.append({"text": msg, "reply_markup": reply_markup})
            
    # Format SOL only events
    if sol_only_events:
        sigs = [ev["sig"] for ev in sol_only_events]
        tx_count = len(sigs)
        total_sol = sum(ev["sol_change"] for ev in sol_only_events)
        total_val = sum(ev["value_usd"] for ev in sol_only_events)
        val_str = format_currency(total_val, currency)
        
        # Determine emoji and action
        if len(sol_only_events) == 1:
            tx_type = sol_only_events[0].get("tx_type", "⚡ Transfer")
            if "Receive" in tx_type:
                emoji = "📥"
                action = "Received"
            elif "Send" in tx_type:
                emoji = "📤"
                action = "Sent"
            elif "Stake" in tx_type:
                emoji = "🥩"
                action = "Stake / Unstake"
            else:
                emoji = "⚡"
                action = "Transfer"
        else:
            emoji = "🟢" if total_sol > 0 else "🔴"
            action = "received" if total_sol > 0 else "sent"
            
        solscan_url = f"https://solscan.io/account/{address}"
        solscan_link = f"<a href='{solscan_url}'>Solscan</a>"
        
        if concise:
            header = f"{icon} <b>{wallet_name}</b> ({solscan_link})"
            body = f"{emoji} <b>{action}:</b> {abs(total_sol):,.4f} SOL ({val_str})"
            
            tx_lines = []
            for sig in sigs[:5]:
                tx_lines.append(f"🔗 <a href='https://solscan.io/tx/{sig}'>{sig[:6]}</a>")
            if len(sigs) > 5:
                tx_lines.append(f"(+{len(sigs) - 5} more)")
                
            msg = "\n".join([header, body, ""] + tx_lines)
        else:
            header = f"Scan complete for <b>{wallet_name}</b> - {solscan_link}"
            body = f"{emoji} <b>{action}:</b> {abs(total_sol):,.4f} SOL ({val_str})"
            
            tx_lines = []
            for sig in sigs[:5]:
                tx_lines.append(f"🔗 <a href='https://solscan.io/tx/{sig}'>{sig[:6]}</a>")
            if len(sigs) > 5:
                tx_lines.append(f"(+{len(sigs) - 5} more)")
                
            msg = "\n".join([header, "", body, ""] + tx_lines)
            
        pair_url = "https://dexscreener.com/solana/So11111111111111111111111111111111111111112"
        buttons = []
        row = []
        row.append({"text": "🌐 Solscan", "url": solscan_url})
        row.append({"text": "📈 Chart", "url": pair_url})
        buttons.append(row)
        reply_markup = {"inline_keyboard": buttons}
        
        messages.append({"text": msg, "reply_markup": reply_markup})
            
    return messages


# Alert sender
# Batch queue for 60s alerts
batch_queue = {}
batch_lock = threading.Lock()

def send_transaction_alert(chat_id, event, currency):
    wallet_type = "user"
    show_coin_link = True
    show_market_cap = True
    whale_threshold = 1.0
    with state_lock:
        chat_data = state.get("chats", {}).get(str(chat_id), {})
        addr_info = chat_data.get("tracked", {}).get(event["address"], {})
        wallet_type = addr_info.get("type", "user")
        show_coin_link = chat_data.get("show_coin_link", True)
        show_market_cap = chat_data.get("show_market_cap", True)
        whale_threshold = chat_data.get("whale_threshold", 1.0)
        
    messages = format_transaction_group(
        event["wallet_name"], event["address"], wallet_type, [event], currency,
        show_coin_link=show_coin_link, show_market_cap=show_market_cap, whale_threshold=whale_threshold,
        concise=True
    )
    for msg in messages:
        with recent_alerts_lock:
            recent_alerts.append(msg)
            if len(recent_alerts) > 5:
                recent_alerts.pop(0)
        payload = {
            "chat_id": chat_id,
            "text": msg["text"],
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        if msg.get("reply_markup"):
            payload["reply_markup"] = msg["reply_markup"]
        make_telegram_request("sendMessage", data=payload)

def send_batched_alert(chat_id_str, events, currency):
    # Group events by address
    addr_groups = {}
    for ev in events:
        addr = ev["address"]
        if addr not in addr_groups:
            addr_groups[addr] = []
        addr_groups[addr].append(ev)
        
    for addr, ev_list in addr_groups.items():
        with state_lock:
            chat_data = state.get("chats", {}).get(chat_id_str, {})
            addr_info = chat_data.get("tracked", {}).get(addr, {})
            wallet_type = addr_info.get("type", "user")
            wallet_name = addr_info.get("name", "Unnamed")
            show_coin_link = chat_data.get("show_coin_link", True)
            show_market_cap = chat_data.get("show_market_cap", True)
            whale_threshold = chat_data.get("whale_threshold", 1.0)
            
        messages = format_transaction_group(
            wallet_name, addr, wallet_type, ev_list, currency,
            show_coin_link=show_coin_link, show_market_cap=show_market_cap,
            whale_threshold=whale_threshold, concise=True
        )
        for msg in messages:
            with recent_alerts_lock:
                recent_alerts.append(msg)
                if len(recent_alerts) > 5:
                    recent_alerts.pop(0)
            payload = {
                "chat_id": int(chat_id_str),
                "text": msg["text"],
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            if msg.get("reply_markup"):
                payload["reply_markup"] = msg["reply_markup"]
            make_telegram_request("sendMessage", data=payload)

# Summary sender
def send_chat_summary(chat_id, chat_data):
    txs = chat_data.get("accumulated_txs", [])
    if not txs:
        return
        
    currency = chat_data.get("currency", "USD")
    show_coin_link = chat_data.get("show_coin_link", True)
    show_market_cap = chat_data.get("show_market_cap", True)
    whale_threshold = chat_data.get("whale_threshold", 1.0)
    
    # Group transactions by wallet address
    wallet_groups = {}
    for tx in txs:
        addr = tx["address"]
        if addr not in wallet_groups:
            wallet_groups[addr] = []
        wallet_groups[addr].append(tx)
        
    for addr, events in wallet_groups.items():
        with state_lock:
            addr_info = chat_data.get("tracked", {}).get(addr, {})
            wallet_type = addr_info.get("type", "user")
            wallet_name = addr_info.get("name", "Unnamed")
            
        messages = format_transaction_group(
            wallet_name, addr, wallet_type, events, currency,
            show_coin_link=show_coin_link, show_market_cap=show_market_cap, whale_threshold=whale_threshold,
            concise=True
        )
        for msg in messages:
            payload = {
                "chat_id": chat_id,
                "text": msg["text"],
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            if msg.get("reply_markup"):
                payload["reply_markup"] = msg["reply_markup"]
            make_telegram_request("sendMessage", data=payload)


def flush_accumulated_txs(chat_id):
    global state
    with state_lock:
        chat_id_str = str(chat_id)
        if chat_id_str not in state.get("chats", {}):
            return
        chat_data = state["chats"][chat_id_str]
        txs_to_send = list(chat_data.get("accumulated_txs", []))
        if not txs_to_send:
            return
            
    send_chat_summary(chat_id, chat_data)
    
    with state_lock:
        current_state = safe_read_state_file(state)
            
        chat_state = current_state.get("chats", {}).get(chat_id_str, {})
        current_txs = chat_state.get("accumulated_txs", [])
        
        sent_sigs = {tx["sig"] for tx in txs_to_send}
        remaining_txs = [tx for tx in current_txs if tx["sig"] not in sent_sigs]
        
        state = current_state
        state["chats"][chat_id_str]["accumulated_txs"] = remaining_txs
        state["chats"][chat_id_str]["last_summary_time"] = time.time()
        save_state_unlocked()

# Msg dispatch handler
def handle_telegram_message(msg):
    chat = msg.get("chat", {})
    chat_id = chat.get("id")
    if not chat_id:
        return
        
    text = msg.get("text", "").strip()
    document = msg.get("document")
    caption = msg.get("caption", "").strip()
    
    if document and (text == "/import" or caption == "/import"):
        handle_import(chat_id, document)
        return
        
    # Ensure chat state exists
    chat_id_str = str(chat_id)
    with state_lock:
        if "chats" not in state:
            state["chats"] = {}
        if chat_id_str not in state["chats"]:
            state["chats"][chat_id_str] = get_default_chat_state()
            save_state_unlocked()

    if not text.startswith("/"):
        lower_text = text.lower()
        
        # Check "price [token]"
        if lower_text.startswith("price "):
            token_query = text[6:].strip()
            if token_query:
                try:
                    mint = token_query
                    if mint.upper() == "SOL":
                        mint = "So11111111111111111111111111111111111111112"
                    elif mint.upper() == "USDC":
                        mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
                    elif mint.upper() == "USDT":
                        mint = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
                        
                    symbol, price = get_token_metadata(mint)
                    if price > 0:
                        send_cleanup_reply(chat_id, f"🪙 <b>{symbol} Price:</b> <code>${price:,.6f} USD</code>")
                    else:
                        url = f"https://api.jup.ag/tokens/v2/search?query={token_query}"
                        r = requests.get(url, timeout=5)
                        res = r.json()
                        if res and isinstance(res, list) and len(res) > 0:
                            data = res[0]
                            sym = data.get("symbol")
                            p = float(data.get("usdPrice", 0.0))
                            send_cleanup_reply(chat_id, f"🪙 <b>{sym} Price:</b> <code>${p:,.6f} USD</code>")
                        else:
                            send_cleanup_reply(chat_id, f"❌ Could not find price for token: <b>{token_query}</b>")
                except Exception as e:
                    send_cleanup_reply(chat_id, f"❌ Failed to fetch price: {e}")
            return
            
        # Check "add [address]" alias
        if lower_text.startswith("add "):
            parts = text.split()
            if len(parts) >= 2:
                address = parts[1]
                custom_name = " ".join(parts[2:]).strip() if len(parts) > 2 else f"{address[:4]}...{address[-4:]}"
                add_wallet_flow(chat_id, "u", address, custom_name)
            else:
                send_cleanup_reply(chat_id, "❌ Usage: <code>add &lt;address&gt; [name]</code>")
            return
            
        # Check if raw input is a Solana Address (Interactive add)
        if re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", text):
            addr_type = identify_address(text)
            if addr_type == "WALLET":
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Yes, Add Wallet", "callback_data": f"confirm_add_u_{text}"},
                            {"text": "❌ Cancel", "callback_data": "cancel_add"}
                        ]
                    ]
                }
                send_cleanup_reply(chat_id, f"👛 <b>Detected Wallet Address:</b>\n<code>{text}</code>\n\nAdd this wallet to your watchlist?", reply_markup=markup)
            elif addr_type == "TOKEN":
                markup = {
                    "inline_keyboard": [
                        [
                            {"text": "✅ Yes, Add Token Account", "callback_data": f"confirm_add_t_{text}"},
                            {"text": "❌ Cancel", "callback_data": "cancel_add"}
                        ]
                    ]
                }
                send_cleanup_reply(chat_id, f"🧿 <b>Detected Token Account:</b>\n<code>{text}</code>\n\nAdd this token account to your watchlist?", reply_markup=markup)
            else:
                send_cleanup_reply(chat_id, "❌ I couldn't identify that as a valid Solana wallet or token address on-chain.")
            return
            
        # Check if raw input is a numeric threshold (e.g. 50, $50, 10.5)
        clean_num = text.replace("$", "").strip()
        if re.match(r"^\d+(\.\d+)?$", clean_num):
            try:
                threshold = float(clean_num)
                with state_lock:
                    current_state = safe_read_state_file(state)
                    if chat_id_str in current_state.get("chats", {}):
                        current_state["chats"][chat_id_str]["noise_threshold"] = threshold
                        state = current_state
                        save_state_unlocked()
                send_cleanup_reply(chat_id, f"✅ Alert noise threshold updated to: <b>${threshold:,.2f} USD</b>. Transactions below this value will not trigger alerts.")
            except Exception as e:
                logger.error(f"Failed to update threshold: {e}")
            return
        return
        
    parts = text.split()
    command = parts[0].lower().split("@")[0]
    args = parts[1:]
    
    if command == "/start":
        with state_lock:
            state["chats"][chat_id_str]["active"] = True
            save_state_unlocked()
        send_dashboard(chat_id)
            
    elif command == "/stop":
        with state_lock:
            state["chats"][str(chat_id)]["active"] = False
            save_state_unlocked()
        reply_to(chat_id, "⏹️ Bot alerts disabled. Use /start to reactivate.")
        
    elif command in ("/help", "/h"):
        send_help(chat_id)
        
    elif command == "/status":
        handle_status_command(chat_id)
        
    elif command == "/last":
        handle_last_command(chat_id)
        
    elif command == "/alert":
        handle_alert_command(chat_id)
        
    elif command == "/add":
        if len(args) < 1:
            reply_to(chat_id, "❌ Usage: <code>/add &lt;address&gt; [CUSTOM NAME]</code>")
            return
        address = args[0]
        custom_name = " ".join(args[1:]).strip() if len(args) > 1 else f"{address[:4]}...{address[-4:]}"
        
        if not re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address):
            reply_to(chat_id, "❌ Invalid Solana address base58 format.")
            return
            
        detected_type = identify_address(address)
        if detected_type == "OTHER_PROGRAM":
            reply_to(chat_id, f"❌ Error: <code>{address[:8]}...</code> is owned by a program contract and cannot be tracked.")
            return
            
        addr_type = "user" if detected_type == "WALLET" else "token"
        
        owner_addr = None
        token_mint = None
        if addr_type == "token":
            reply_to(chat_id, "⏳ Resolving token account details on-chain...")
            try:
                res = solana_client._call("getAccountInfo", [address, {"encoding": "jsonParsed"}])
                if res and res.get("value"):
                    val = res["value"]
                    parsed_data = val.get("data", {})
                    if isinstance(parsed_data, dict) and parsed_data.get("parsed"):
                        info_node = parsed_data["parsed"].get("info", {})
                        owner_addr = info_node.get("owner")
                        token_mint = info_node.get("mint")
            except Exception as e:
                logger.warning(f"Failed to resolve owner for token account {address}: {e}")
                
        reply_to(chat_id, "⏳ Fetching latest transaction offset...")
        sigs = solana_client.get_signatures_for_address(address, limit=1)
        last_sig = sigs[0].get("signature") if sigs and len(sigs) > 0 else None
        
        with state_lock:
            tracked_entry = {
                "type": addr_type,
                "name": custom_name
            }
            if owner_addr:
                tracked_entry["owner"] = owner_addr
            if token_mint:
                tracked_entry["mint"] = token_mint
                
            state["chats"][str(chat_id)]["tracked"][address] = tracked_entry
            
            if "global_last_signatures" not in state:
                state["global_last_signatures"] = {}
            if address not in state["global_last_signatures"] or not state["global_last_signatures"][address]:
                state["global_last_signatures"][address] = last_sig
            save_state_unlocked()
            
        type_lbl = "User Wallet" if addr_type == "user" else "Specific Token Account"
        extra_info = ""
        if addr_type == "token":
            extra_info += f"\nOwner: <code>{owner_addr}</code>" if owner_addr else ""
            extra_info += f"\nMint: <code>{token_mint}</code>" if token_mint else ""
        reply_to(chat_id, f"✅ Tracking added for {type_lbl}:\n<code>{address}</code>{extra_info}\nName: <code>{custom_name}</code>")
        
    elif command == "/remove":
        if not args:
            reply_to(chat_id, "❌ Usage: <code>/remove &lt;address_or_custom_name&gt;</code>")
            return
        target = " ".join(args).strip()
        removed_addresses = []
        with state_lock:
            chat_data = state["chats"][str(chat_id)]
            tracked = chat_data.get("tracked", {})
            
            if target in tracked:
                name = tracked[target].get("name", target)
                del tracked[target]
                removed_addresses.append((target, name))
            else:
                to_remove = []
                for addr, info in tracked.items():
                    name = info.get("name", "")
                    if name.strip().lower() == target.lower():
                        to_remove.append((addr, name))
                for addr, name in to_remove:
                    del tracked[addr]
                    removed_addresses.append((addr, name))
            
            if removed_addresses:
                save_state_unlocked()
                
        if removed_addresses:
            lines = []
            for addr, name in removed_addresses:
                lines.append(f"🗑️ Stopped tracking <b>{name}</b> (<code>{addr}</code>).")
            reply_to(chat_id, "\n".join(lines))
        else:
            reply_to(chat_id, f"❌ Address or custom name '<code>{target}</code>' is not tracked in this chat.")
                
    elif command == "/name":
        if not args:
            reply_to(chat_id, "❌ Usage: <code>/name &lt;address_or_current_name&gt; &lt;new_name&gt;</code>")
            return
            
        full_args_str = " ".join(args).strip()
        
        with state_lock:
            chat_data = state["chats"][str(chat_id)]
            tracked = chat_data.get("tracked", {})
            
            target_addr = None
            new_name = None
            
            # Scenario 1: First argument is a direct Solana address in tracked
            first_arg = args[0]
            if first_arg in tracked and len(args) > 1:
                target_addr = first_arg
                new_name = " ".join(args[1:]).strip()
            
            # Scenario 2: Find a matching current nickname at the start of the argument string
            if not target_addr:
                # Sort tracked names by length descending to match longest nickname first
                sorted_wallets = sorted(
                    tracked.items(),
                    key=lambda item: len(item[1].get("name", "")),
                    reverse=True
                )
                for addr, info in sorted_wallets:
                    current_name = info.get("name", "").strip()
                    if not current_name:
                        continue
                    pattern = r"^" + re.escape(current_name) + r"(?:\s+(.*))?$"
                    match = re.match(pattern, full_args_str, re.IGNORECASE)
                    if match:
                        target_addr = addr
                        new_name = match.group(1).strip() if match.group(1) else ""
                        break
                        
            if not target_addr:
                reply_to(chat_id, "❌ Could not find a tracked wallet matching the address or current nickname provided.")
                return
                
            if not new_name:
                reply_to(chat_id, "❌ Usage: <code>/name &lt;address_or_current_name&gt; &lt;new_name&gt;</code>")
                return
                
            tracked[target_addr]["name"] = new_name
            save_state_unlocked()
            
        reply_to(chat_id, f"✏️ Wallet renamed to <b>{new_name}</b>.")
                
    elif command == "/show":
        with state_lock:
            tracked = state["chats"][str(chat_id)].get("tracked", {})
        if not tracked:
            reply_to(chat_id, "📋 No addresses tracked yet.")
            return
        lines = ["📋 <b>Tracked wallets:</b>"]
        for addr, info in tracked.items():
            name = info.get("name", "Unnamed")
            addr_type = info.get("type", "user")
            if addr_type == "wallet":
                owner = info.get("owner")
                owner_str = f" (Owner: {owner})" if owner else ""
                lines.append(f"🧿 <b>{name}</b>{owner_str} (<a href='https://solscan.io/account/{addr}'>Solscan</a>) (threshold: 0)")
            else:
                lines.append(f"👛 <b>{name}</b> (<a href='https://solscan.io/account/{addr}'>Solscan</a>) (threshold: 0)")
        reply_to(chat_id, "\n".join(lines))
        
    elif command == "/balance":
        reply_to(chat_id, "⏳ Loading balances from network...")
        try:
            bal_str = format_balance(chat_id)
            markup = {
                "inline_keyboard": [
                    [{"text": "🔄 Refresh Balance", "callback_data": "refresh_balance"}]
                ]
            }
            reply_to(chat_id, bal_str, reply_markup=markup)
        except Exception as e:
            logger.error(f"Balance check failed: {e}")
            reply_to(chat_id, "❌ Failed to fetch wallet balances.")
            
    elif command == "/currency":
        if not args:
            with state_lock:
                curr = state["chats"][str(chat_id)].get("currency", "USD")
            reply_to(chat_id, f"💱 Current currency: <b>{curr}</b>")
            return
        curr = args[0].upper()
        if len(curr) != 3:
            reply_to(chat_id, "❌ Currency must be 3 letters (e.g. USD, NIS, CAD).")
            return
        with state_lock:
            state["chats"][str(chat_id)]["currency"] = curr
            save_state_unlocked()
        reply_to(chat_id, f"💱 Currency changed to <b>{curr}</b>.")
        
    elif command == "/interval":
        if not args:
            with state_lock:
                intv = state["chats"][str(chat_id)].get("interval", 1)
            reply_to(chat_id, f"⏱️ Current interval: <b>{format_duration(intv)}</b>")
            return
        try:
            intv = int(args[0])
            if intv < 1:
                raise ValueError()
        except ValueError:
            reply_to(chat_id, "❌ Interval must be a positive integer (at least 1 minute).")
            return
        with state_lock:
            state["chats"][str(chat_id)]["interval"] = intv
            state["chats"][str(chat_id)]["last_summary_time"] = time.time()
            save_state_unlocked()
            
        # Flush any accumulated logs immediately
        flush_accumulated_txs(chat_id)
        
        if intv == 1:
            reply_to(chat_id, "⏱️ Interval set to 1 min. Realtime alerts activated.")
        else:
            reply_to(chat_id, f"⏱️ Interval set to <b>{format_duration(intv)}</b>. Accumulating logs.")
            

    else:
        reply_to(chat_id, "❌ Unknown command. Type /help for assistance.")

def read_log_tail():
    try:
        # LOG_FILE is defined in tracker.py as 'logs/tracker.log' or similar
        # Let's inspect where LOG_FILE is defined or default to 'logs/tracker.log'
        import os
        log_path = LOG_FILE if 'LOG_FILE' in globals() else 'logs/tracker.log'
        if not os.path.exists(log_path):
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w') as f:
                f.write("Log initialized.\n")
        with open(log_path, "r") as f:
            lines = f.readlines()
        return [line.strip() for line in lines]
    except Exception:
        return ["No logs available."]

def handle_callback_query(cb):
    cb_id = cb.get("id")
    chat = cb.get("message", {}).get("chat", {})
    chat_id = chat.get("id")
    data = cb.get("data", "")
    
    make_telegram_request("answerCallbackQuery", data={"callback_query_id": cb_id})
    
    if data == "refresh_balance":
        if chat_id:
            msg_id = cb.get("message", {}).get("message_id")
            make_telegram_request("editMessageText", data={
                "chat_id": chat_id,
                "message_id": msg_id,
                "text": "⏳ Refreshing balances from network...",
                "parse_mode": "HTML"
            })
            try:
                bal_str = format_balance(chat_id)
                markup = {
                    "inline_keyboard": [
                        [{"text": "🔄 Refresh Balance", "callback_data": "refresh_balance"}]
                    ]
                }
                make_telegram_request("editMessageText", data={
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "text": bal_str,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                    "reply_markup": markup
                })
            except Exception as e:
                logger.error(f"Async balance refresh failed: {e}")
                make_telegram_request("editMessageText", data={
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "text": "❌ Failed to refresh wallet balances.",
                    "parse_mode": "HTML"
                })
    elif data == "refresh_logs":
        if chat_id:
            raw_lines = read_log_tail()
            log_lines = raw_lines[-5:]
            log_text = "📋 <b>Last 5 Log Entries:</b>\n<pre>" + "\n".join(log_lines) + "</pre>"
            send_cleanup_reply(chat_id, log_text)
            
    elif data == "dashboard_settings":
        if chat_id:
            with state_lock:
                chat_data = state.get("chats", {}).get(str(chat_id), {})
            lines = [
                "⚙️ <b>Tracker Settings Summary:</b>",
                f"• Currency: <code>{chat_data.get('currency', 'USD')}</code>",
                f"• Summary Interval: <code>{format_duration(chat_data.get('interval', 1))}</code>",
                f"• Status Scan Interval: <code>{format_duration(chat_data.get('status_interval', 5))}</code>",
                f"• Whale Threshold: <code>{chat_data.get('whale_threshold', 1.0)} SOL</code>",
                f"• Noise Threshold: <code>{chat_data.get('noise_threshold', 0.0)} USD</code>",
                f"• Daily Summary: <code>{'Enabled (' + chat_data.get('daily_summary_time', '00:00') + ')' if chat_data.get('daily_summary_enabled') else 'Disabled'}</code>",
                f"• Alert Mode: <code>{'🔇 Silent' if chat_data.get('silent_alerts') else '🔊 Active'}</code>"
            ]
            send_cleanup_reply(chat_id, "\n".join(lines))
            
    elif data == "pause_bot":
        if chat_id:
            chat_id_str = str(chat_id)
            with state_lock:
                current_state = safe_read_state_file(state)
                if chat_id_str in current_state.get("chats", {}):
                    current_state["chats"][chat_id_str]["active"] = False
                    state = current_state
                    save_state_unlocked()
            msg_id = cb.get("message", {}).get("message_id")
            update_dashboard_markup(chat_id, msg_id, active=False)
            send_cleanup_reply(chat_id, "⏸️ Notifications paused for this chat.")
            
    elif data == "resume_bot":
        if chat_id:
            chat_id_str = str(chat_id)
            with state_lock:
                current_state = safe_read_state_file(state)
                if chat_id_str in current_state.get("chats", {}):
                    current_state["chats"][chat_id_str]["active"] = True
                    state = current_state
                    save_state_unlocked()
            msg_id = cb.get("message", {}).get("message_id")
            update_dashboard_markup(chat_id, msg_id, active=True)
            send_cleanup_reply(chat_id, "▶️ Notifications resumed for this chat.")
            
    elif data.startswith("confirm_add_u_"):
        address = data[14:]
        if chat_id:
            add_wallet_flow(chat_id, "u", address, f"{address[:4]}...{address[-4:]}")
            msg_id = cb.get("message", {}).get("message_id")
            try:
                make_telegram_request("deleteMessage", data={"chat_id": chat_id, "message_id": msg_id})
            except Exception:
                pass
                
    elif data.startswith("confirm_add_t_"):
        address = data[14:]
        if chat_id:
            add_wallet_flow(chat_id, "token", address, f"{address[:4]}...{address[-4:]}")
            msg_id = cb.get("message", {}).get("message_id")
            try:
                make_telegram_request("deleteMessage", data={"chat_id": chat_id, "message_id": msg_id})
            except Exception:
                pass
                
    elif data == "cancel_add":
        if chat_id:
            msg_id = cb.get("message", {}).get("message_id")
            try:
                make_telegram_request("editMessageText", data={
                    "chat_id": chat_id,
                    "message_id": msg_id,
                    "text": "❌ Action cancelled.",
                    "parse_mode": "HTML"
                })
            except Exception:
                pass

# Bot Loops
def telegram_bot_loop():
    offset = None
    logger.info("Telegram updates polling thread started.")
    while True:
        try:
            params = {"timeout": 10}
            if offset is not None:
                params["offset"] = offset
            res = make_telegram_request("getUpdates", data=params)
            if res and res.get("ok"):
                for update in res.get("result", []):
                    offset = update.get("update_id") + 1
                    if "message" in update:
                        msg = update["message"]
                        threading.Thread(target=handle_telegram_message, args=(msg,), daemon=True).start()
                    elif "callback_query" in update:
                        cb = update["callback_query"]
                        threading.Thread(target=handle_callback_query, args=(cb,), daemon=True).start()
            else:
                time.sleep(2)
        except Exception as e:
            logger.error(f"Error in telegram loop: {e}")
            time.sleep(2)

def parse_and_dispatch_transaction(address, tx, sig):
    meta = tx.get("meta", {})
    if not meta or meta.get("err") is not None:
        return
        
    transaction = tx.get("transaction", {})
    message = transaction.get("message", {})
    account_keys = []
    if "accountKeys" in message:
        for k in message["accountKeys"]:
            if isinstance(k, str):
                account_keys.append(k)
            elif isinstance(k, dict) and "pubkey" in k:
                account_keys.append(k["pubkey"])
                
    sol_change = 0.0
    if address in account_keys:
        idx = account_keys.index(address)
        pre_bal = meta.get("preBalances", [])
        post_bal = meta.get("postBalances", [])
        if idx < len(pre_bal) and idx < len(post_bal):
            sol_change = (post_bal[idx] - pre_bal[idx]) / 1e9
            
    token_changes = {}
    
    def is_account_matched(item, addr, keys):
        if item.get("owner") == addr:
            return True
        idx = item.get("accountIndex")
        if idx is not None and idx < len(keys):
            return keys[idx] == addr
        return False
        
    pre_balances = {}
    post_balances = {}
    
    for item in meta.get("preTokenBalances", []):
        if is_account_matched(item, address, account_keys):
            mint = item.get("mint")
            ui_amount = item.get("uiTokenAmount", {}).get("uiAmount", 0.0)
            decimals = item.get("uiTokenAmount", {}).get("decimals", 0)
            pre_balances[mint] = (ui_amount if ui_amount is not None else 0.0, decimals)
            
    for item in meta.get("postTokenBalances", []):
        if is_account_matched(item, address, account_keys):
            mint = item.get("mint")
            ui_amount = item.get("uiTokenAmount", {}).get("uiAmount", 0.0)
            decimals = item.get("uiTokenAmount", {}).get("decimals", 0)
            post_balances[mint] = (ui_amount if ui_amount is not None else 0.0, decimals)
            
    all_mints = set(pre_balances.keys()) | set(post_balances.keys())
    for mint in all_mints:
        pre_val, pre_dec = pre_balances.get(mint, (0.0, 0))
        post_val, post_dec = post_balances.get(mint, (0.0, 0))
        dec = post_dec if post_dec else pre_dec
        diff = post_val - pre_val
        if abs(diff) > 1e-9:
            token_changes[mint] = {'change': diff, 'decimals': dec}
            
    if abs(sol_change) <= 0.005 and not token_changes:
        return
        
    sol_price = get_sol_price()
    
    with state_lock:
        chats_to_notify = []
        for chat_id, chat_data in state.get("chats", {}).items():
            if not chat_data.get("active", True):
                continue
            if address in chat_data.get("tracked", {}):
                chats_to_notify.append((chat_id, chat_data))
                
    for chat_id, chat_data in chats_to_notify:
        wallet_info = chat_data["tracked"][address]
        wallet_name = wallet_info.get("name", "Unnamed")
        currency = chat_data.get("currency", "USD")
        
        event = {
            "sig": sig,
            "sol_change": sol_change,
            "token_changes": {},
            "value_usd": 0.0,
            "wallet_name": wallet_name,
            "address": address,
            "tx_type": classify_transaction(sol_change, token_changes, account_keys)
        }
        
        for mint, details in token_changes.items():
            symbol, price = get_token_metadata(mint)
            event["token_changes"][mint] = {
                "change": details['change'],
                "symbol": symbol,
                "price_usd": price
            }
            
        if abs(sol_change) > 0.005:
            event["value_usd"] = abs(sol_change) * sol_price
        else:
            total_tok_val = 0.0
            for mint, tok in event["token_changes"].items():
                total_tok_val += abs(tok["change"]) * tok["price_usd"]
            event["value_usd"] = total_tok_val
            
        # Check noise threshold (Alert threshold)
        noise_threshold = chat_data.get("noise_threshold", 0.0)
        if event["value_usd"] < noise_threshold:
            logger.info(f"Skipping alert for signature {sig}: value ${event['value_usd']:.2f} is below noise threshold ${noise_threshold:.2f}")
            continue

        # Always accumulate transactions in status_txs for the status interval/scans
        with state_lock:
            chat_id_str = str(chat_id)
            if "status_txs" not in state["chats"][chat_id_str]:
                state["chats"][chat_id_str]["status_txs"] = []
            state["chats"][chat_id_str]["status_txs"].append(event)
            
        interval = chat_data.get("interval", 1)
        if interval == 1:
            with batch_lock:
                if chat_id_str not in batch_queue:
                    batch_queue[chat_id_str] = []
                batch_queue[chat_id_str].append((time.time(), event, currency))
        else:
            with state_lock:
                if "accumulated_txs" not in state["chats"][chat_id_str]:
                    state["chats"][chat_id_str]["accumulated_txs"] = []
                state["chats"][chat_id_str]["accumulated_txs"].append(event)
                
        with state_lock:
            save_state_unlocked()

failed_sigs_cache = {}

def solana_poller_loop():
    logger.info("Solana wallet transactions poller started.")
    global failed_sigs_cache
    while True:
        try:
            load_state()
            with state_lock:
                unique_addresses = set()
                for chat_id, chat_data in state.get("chats", {}).items():
                    if chat_data.get("active", True):
                        unique_addresses.update(chat_data.get("tracked", {}).keys())
            
            for address in unique_addresses:
                with state_lock:
                    last_sig = state.get("global_last_signatures", {}).get(address)
                    
                sigs = solana_client.get_signatures_for_address(address, limit=50)
                if not sigs:
                    continue
                    
                new_sigs = []
                for item in sigs:
                    sig = item.get("signature")
                    if sig == last_sig:
                        break
                    new_sigs.append(sig)
                    
                if not new_sigs:
                    continue
                    
                new_sigs.reverse()
                names = []
                with state_lock:
                    for cid, cdata in state.get("chats", {}).items():
                        tracked = cdata.get("tracked", {})
                        if address in tracked:
                            names.append(tracked[address].get("name", address[:8]))
                name_str = " / ".join(list(set(names))) if names else address[:8]
                logger.info(f"Retrieved {len(new_sigs)} new transaction(s) for {name_str}...")
                
                last_successful_sig = last_sig
                for sig in new_sigs:
                    tx = solana_client.get_transaction(sig)
                    if not tx:
                        retries = failed_sigs_cache.get(sig, 0) + 1
                        failed_sigs_cache[sig] = retries
                        if retries >= 3:
                            logger.error(f"Failed to fetch transaction {sig} 3 times. Skipping to prevent poller block.")
                            last_successful_sig = sig
                            if sig in failed_sigs_cache:
                                del failed_sigs_cache[sig]
                            continue
                        else:
                            logger.warning(f"Failed to fetch transaction details for {sig} (attempt {retries}). Retrying in next cycle.")
                            break
                    
                    if sig in failed_sigs_cache:
                        del failed_sigs_cache[sig]
                    parse_and_dispatch_transaction(address, tx, sig)
                    last_successful_sig = sig
                    time.sleep(0.5)
                    
                if last_successful_sig != last_sig:
                    with state_lock:
                        if "global_last_signatures" not in state:
                            state["global_last_signatures"] = {}
                        state["global_last_signatures"][address] = last_successful_sig
                        save_state_unlocked()
                    
        except Exception as e:
            logger.error(f"Error in Solana poller cycle: {e}")
            logger.error(traceback.format_exc())
            
        time.sleep(25)

def summary_scheduler_loop():
    logger.info("Summary/Status scheduler thread started.")
    global state
    while True:
        try:
            check_hot_reload()
            load_state()
            now = time.time()
            chats_for_summary = []
            chats_for_status = []
            chats_for_daily_summary = []
            
            with state_lock:
                for chat_id, chat_data in state.get("chats", {}).items():
                    if not chat_data.get("active", True):
                        continue
                        
                    # 1. Summary logic check
                    interval = chat_data.get("interval", 1)
                    if interval > 1:
                        cooldown = interval * 60
                        last_summary = chat_data.get("last_summary_time", 0.0)
                        if last_summary == 0.0:
                            state["chats"][chat_id]["last_summary_time"] = now
                        elif now - last_summary >= cooldown:
                            chats_for_summary.append((chat_id, chat_data))
                            
                    # 2. Status logic check
                    s_interval = chat_data.get("status_interval", 5)
                    last_status = chat_data.get("last_status_time", 0.0)
                    if last_status == 0.0:
                        state["chats"][chat_id]["last_status_time"] = 1.0
                        save_state_unlocked()
                    elif now - last_status >= s_interval * 60:
                        chats_for_status.append(chat_id)
                        
                    # 3. Daily summary check
                    daily_enabled = chat_data.get("daily_summary_enabled", False)
                    if daily_enabled:
                        summary_time_str = chat_data.get("daily_summary_time", "00:00")
                        try:
                            sh, sm = map(int, summary_time_str.split(":"))
                        except Exception:
                            sh, sm = 0, 0
                        local_dt = datetime.datetime.fromtimestamp(now)
                        target_dt = local_dt.replace(hour=sh, minute=sm, second=0, microsecond=0)
                        last_date = chat_data.get("last_daily_summary_date", "")
                        today_str = local_dt.strftime("%Y-%m-%d")
                        if local_dt >= target_dt and last_date != today_str:
                            chats_for_daily_summary.append(chat_id)
                        
            # Process batched alerts
            with batch_lock:
                for chat_id_str, queue in list(batch_queue.items()):
                    if not queue:
                        continue
                    first_event_time = queue[0][0]
                    last_event_time = queue[-1][0]
                    if (now - first_event_time >= 60) or (now - last_event_time >= 15):
                        events_to_send = [item[1] for item in queue]
                        currency = queue[0][2]
                        batch_queue[chat_id_str] = []
                        threading.Thread(target=send_batched_alert, args=(chat_id_str, events_to_send, currency), daemon=True).start()
                        
            # Process scheduled summaries
            for chat_id, chat_data in chats_for_summary:
                txs_to_send = list(chat_data.get("accumulated_txs", []))
                if not txs_to_send:
                    with state_lock:
                        state["chats"][str(chat_id)]["last_summary_time"] = now
                        save_state_unlocked()
                    continue
                    
                send_chat_summary(chat_id, chat_data)
                
                with state_lock:
                    current_state = safe_read_state_file(state)
                        
                    chat_state = current_state.get("chats", {}).get(str(chat_id), {})
                    current_txs = chat_state.get("accumulated_txs", [])
                    
                    sent_sigs = {tx["sig"] for tx in txs_to_send}
                    remaining_txs = [tx for tx in current_txs if tx["sig"] not in sent_sigs]
                    
                    state = current_state
                    state["chats"][str(chat_id)]["last_summary_time"] = now
                    state["chats"][str(chat_id)]["accumulated_txs"] = remaining_txs
                    save_state_unlocked()
                    
            # Process daily portfolio snapshots
            for chat_id in chats_for_daily_summary:
                try:
                    summary_text = format_daily_summary(chat_id)
                    reply_to(chat_id, summary_text)
                    with state_lock:
                        current_state = safe_read_state_file(state)
                        cid_str = str(chat_id)
                        if cid_str in current_state.get("chats", {}):
                            current_state["chats"][cid_str]["last_daily_summary_date"] = datetime.datetime.fromtimestamp(now).strftime("%Y-%m-%d")
                            state = current_state
                            save_state_unlocked()
                except Exception as e:
                    logger.error(f"Daily summary failed for chat {chat_id}: {e}")
                    
            # Process scheduled status scans
            for chat_id in chats_for_status:
                try:
                    with state_lock:
                        chat_data = state.get("chats", {}).get(str(chat_id), {})
                        status_txs = list(chat_data.get("status_txs", []))
                        currency = chat_data.get("currency", "USD")
                        show_coin_link = chat_data.get("show_coin_link", True)
                        show_market_cap = chat_data.get("show_market_cap", True)
                        whale_threshold = chat_data.get("whale_threshold", 1.0)
                    
                    if status_txs:
                        # Group transactions by wallet address
                        wallet_groups = {}
                        for tx in status_txs:
                            addr = tx["address"]
                            if addr not in wallet_groups:
                                wallet_groups[addr] = []
                            wallet_groups[addr].append(tx)
                            
                        for addr, events in wallet_groups.items():
                            with state_lock:
                                addr_info = chat_data.get("tracked", {}).get(addr, {})
                                wallet_type = addr_info.get("type", "user")
                                wallet_name = addr_info.get("name", "Unnamed")
                                
                            messages = format_transaction_group(
                                wallet_name, addr, wallet_type, events, currency,
                                show_coin_link=show_coin_link, show_market_cap=show_market_cap,
                                whale_threshold=whale_threshold, concise=False
                            )
                            for msg in messages:
                                payload = {
                                    "chat_id": chat_id,
                                    "text": msg["text"],
                                    "parse_mode": "HTML",
                                    "disable_web_page_preview": True
                                }
                                if msg.get("reply_markup"):
                                    payload["reply_markup"] = msg["reply_markup"]
                                make_telegram_request("sendMessage", data=payload)

                                
                    # Clear status_txs and update last_status_time
                    with state_lock:
                        current_state = safe_read_state_file(state)
                        cid_str = str(chat_id)
                        if cid_str in current_state.get("chats", {}):
                            current_state["chats"][cid_str]["status_txs"] = []
                            current_state["chats"][cid_str]["last_status_time"] = now
                            state = current_state
                            save_state_unlocked()
                except Exception as e:
                    logger.error(f"Scheduled status report failed for chat {chat_id}: {e}")
                    # Prevent spinning if report repeatedly fails
                    with state_lock:
                        current_state = safe_read_state_file(state)
                        cid_str = str(chat_id)
                        if cid_str in current_state.get("chats", {}):
                            current_state["chats"][cid_str]["last_status_time"] = time.time()
                            state = current_state
                            save_state_unlocked()
                            
        except Exception as e:
            logger.error(f"Error in summary scheduler: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    import socket
    try:
        # Bind to a local port to prevent multiple bot instances from running concurrently
        instance_lock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        instance_lock.bind(("127.0.0.1", 49000))
    except OSError:
        print("Error: Another instance of Tracker Bot is already running.")
        sys.exit(1)

    logger.info("Starting Solana Wallet Tracker Bot...")
    load_state()
    migrate_tracked_json_types()
    try:
        register_telegram_commands()
    except Exception as e:
        logger.warning(f"Failed to register command list: {e}")

    
    t_tg = threading.Thread(target=telegram_bot_loop, daemon=True)
    t_tg.start()
    
    t_sol = threading.Thread(target=solana_poller_loop, daemon=True)
    t_sol.start()
    
    t_sum = threading.Thread(target=summary_scheduler_loop, daemon=True)
    t_sum.start()
    
    logger.info("Wallet Tracker Bot threads initialized.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down cleanly.")
        save_state()
        sys.exit(0)
