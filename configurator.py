import os
import sys
import json
import re
import time
import subprocess
import threading
import requests
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog


# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "secrets", ".env")
STATE_PATH = os.path.join(BASE_DIR, "secrets", "tracked.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "tracker.log")

# Colors
BG_MAIN = "#121214"
BG_CARD = "#1a1a1e"
TEXT_COLOR = "#e1e1e6"
TEXT_MUTED = "#8d8d99"
ACCENT_GREEN = "#10b981"
ACCENT_BLUE = "#3b82f6"
ACCENT_RED = "#ef4444"
BORDER_COLOR = "#29292e"

class CustomAddAddressDialog(tk.Toplevel):
    def __init__(self, parent, addr_type, title="Add Tracked Address"):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x220")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.transient(parent)
        self.grab_set()
        
        self.addr_type = addr_type
        self.result = None
        
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        dw = self.winfo_width()
        dh = self.winfo_height()
        x = px + (pw - dw) // 2
        y = py + (ph - dh) // 2
        self.geometry(f"+{x}+{y}")
        
        lbl_title = ttk.Label(self, text=f"Add {'User Wallet' if addr_type == 'user' else 'Token Account'}", font=("Helvetica", 12, "bold"), background=BG_MAIN, foreground=TEXT_COLOR)
        lbl_title.pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        form_frame = tk.Frame(self, bg=BG_MAIN)
        form_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(form_frame, text="Solana Address:", background=BG_MAIN, foreground=TEXT_COLOR).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.addr_var = tk.StringVar()
        self.addr_entry = tk.Entry(form_frame, textvariable=self.addr_var, bg=BG_CARD, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, bd=1, relief=tk.SOLID, width=35)
        self.addr_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        self.addr_entry.focus()
        
        ttk.Label(form_frame, text="Custom Name:", background=BG_MAIN, foreground=TEXT_COLOR).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(form_frame, textvariable=self.name_var, bg=BG_CARD, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, bd=1, relief=tk.SOLID, width=35)
        self.name_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        self.err_lbl = ttk.Label(form_frame, text="", background=BG_MAIN, foreground=ACCENT_RED, font=("Helvetica", 8))
        self.err_lbl.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        btn_frame = tk.Frame(self, bg=BG_MAIN)
        btn_frame.pack(fill=tk.X, padx=20, pady=(15, 0), side=tk.BOTTOM)
        
        btn_cancel = ttk.Button(btn_frame, text="Cancel", style="Gray.TButton", command=self.destroy, width=10)
        btn_cancel.pack(side=tk.RIGHT, padx=(5, 0))
        
        btn_add = ttk.Button(btn_frame, text="Add", style="Green.TButton", command=self.validate_and_submit, width=10)
        btn_add.pack(side=tk.RIGHT)
        
        self.bind("<Return>", lambda e: self.validate_and_submit())
        self.bind("<Escape>", lambda e: self.destroy())

    def validate_and_submit(self):
        address = self.addr_var.get().strip()
        name = self.name_var.get().strip()
        
        if not address:
            self.err_lbl.config(text="Address cannot be empty.")
            return
            
        if not re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address):
            self.err_lbl.config(text="Invalid Solana address format.")
            return
            
        if not name:
            name = f"{address[:4]}...{address[-4:]}"
            
        self.result = (address, name)
        self.destroy()

class ConfiguratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solana Telegram Tracker Configurator")
        self.root.geometry("820x720")
        self.root.configure(bg=BG_MAIN)
        
        # Subprocess tracker
        self.tracker_process = None
        
        # Load configs
        self.token, self.chat_id, self.rpc_url = self.load_env_values()
        self.state = self.load_state_values()
        
        # Create UI
        self.setup_styles()
        self.build_ui()
        
        # Process monitor loop
        self.check_process()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        # Configure overall widget properties
        style.configure(".", bg=BG_MAIN, fg=TEXT_COLOR, font=("Helvetica", 10))
        
        # Card style
        style.configure("Card.TFrame", background=BG_CARD, bordercolor=BORDER_COLOR, relief="solid", borderwidth=1)
        style.configure("CardLabel.TLabel", background=BG_CARD, foreground=TEXT_COLOR, font=("Helvetica", 10, "bold"))
        style.configure("Header.TLabel", background=BG_MAIN, foreground=ACCENT_GREEN, font=("Helvetica", 16, "bold"))
        
        # Buttons
        style.configure("Green.TButton", background=ACCENT_GREEN, foreground="#ffffff", font=("Helvetica", 10, "bold"), borderwidth=0)
        style.map("Green.TButton", background=[("active", "#059669")])
        
        style.configure("Blue.TButton", background=ACCENT_BLUE, foreground="#ffffff", font=("Helvetica", 10, "bold"), borderwidth=0)
        style.map("Blue.TButton", background=[("active", "#2563eb")])
        
        style.configure("Red.TButton", background=ACCENT_RED, foreground="#ffffff", font=("Helvetica", 10, "bold"), borderwidth=0)
        style.map("Red.TButton", background=[("active", "#dc2626")])
        
        style.configure("Gray.TButton", background="#3e3e42", foreground=TEXT_COLOR, font=("Helvetica", 10), borderwidth=0)
        style.map("Gray.TButton", background=[("active", "#4e4e54")])

    def build_ui(self):
        # Configure min size of root window
        self.root.minsize(800, 600)
        
        # Create Canvas and Scrollbar for vertical scrolling
        self.canvas = tk.Canvas(self.root, bg=BG_MAIN, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        
        self.main_container = tk.Frame(self.canvas, bg=BG_MAIN, padx=20, pady=15)
        
        # Configure canvas window
        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.main_container, anchor="nw")
        
        # Bind events for scrolling and resizing
        self.main_container.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Bind mouse wheel (cross-platform)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack canvas and scrollbar
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 1. Header Title
        title_lbl = ttk.Label(self.main_container, text="🧿 Solana Wallet Tracker Panel", style="Header.TLabel")
        title_lbl.pack(anchor=tk.W, pady=(0, 15))
        
        # 2. Connection Settings Card
        conn_card = ttk.Frame(self.main_container, style="Card.TFrame")
        conn_card.pack(fill=tk.X, pady=(0, 15), padx=1)
        conn_inner = tk.Frame(conn_card, bg=BG_CARD, padx=12, pady=10)
        conn_inner.pack(fill=tk.X)
        
        ttk.Label(conn_inner, text="Connection Credentials", style="CardLabel.TLabel").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Telegram Token
        ttk.Label(conn_inner, text="Telegram Token:", background=BG_CARD, foreground=TEXT_COLOR).grid(row=1, column=0, sticky=tk.W)
        self.token_var = tk.StringVar(value=self.token)
        self.token_entry = tk.Entry(conn_inner, textvariable=self.token_var, bg=BG_MAIN, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, show="*", bd=1, relief=tk.SOLID)
        self.token_entry.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)
        
        self.show_token_btn = ttk.Button(conn_inner, text="Show", width=6, style="Gray.TButton", command=self.toggle_token_visibility)
        self.show_token_btn.grid(row=1, column=2, sticky=tk.W)
        
        # Chat ID
        ttk.Label(conn_inner, text="Telegram Chat ID:", background=BG_CARD, foreground=TEXT_COLOR).grid(row=2, column=0, sticky=tk.W)
        self.chat_id_var = tk.StringVar(value=self.chat_id)
        self.chat_id_entry = tk.Entry(conn_inner, textvariable=self.chat_id_var, bg=BG_MAIN, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, bd=1, relief=tk.SOLID)
        self.chat_id_entry.grid(row=2, column=1, columnspan=2, sticky=tk.EW, padx=10, pady=5)
        
        # Chat ID Hint
        self.chat_id_hint = ttk.Label(conn_inner, text="Hint: Group Chat IDs usually begin with a minus sign (e.g. -100123456789)", background=BG_CARD, foreground=TEXT_MUTED, font=("Helvetica", 8))
        self.chat_id_hint.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=10, pady=(0, 5))
        
        # Solana RPC URL
        ttk.Label(conn_inner, text="Solana RPC URL:", background=BG_CARD, foreground=TEXT_COLOR).grid(row=4, column=0, sticky=tk.W)
        self.rpc_url_var = tk.StringVar(value=self.rpc_url)
        self.rpc_url_entry = tk.Entry(conn_inner, textvariable=self.rpc_url_var, bg=BG_MAIN, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, bd=1, relief=tk.SOLID)
        self.rpc_url_entry.grid(row=4, column=1, columnspan=2, sticky=tk.EW, padx=10, pady=5)
        
        # Buttons Frame on Row 5
        btn_conn_frame = tk.Frame(conn_inner, bg=BG_CARD)
        btn_conn_frame.grid(row=5, column=1, columnspan=2, sticky=tk.E, pady=(5, 0))
        
        self.test_conn_btn = ttk.Button(btn_conn_frame, text="Test Connections", style="Gray.TButton", command=self.test_connections)
        self.test_conn_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        save_conn_btn = ttk.Button(btn_conn_frame, text="Save Connection", style="Blue.TButton", command=self.save_connections)
        save_conn_btn.pack(side=tk.LEFT)
        
        conn_inner.columnconfigure(1, weight=1)
 
        # 3. Preferences Card
        pref_card = ttk.Frame(self.main_container, style="Card.TFrame")
        pref_card.pack(fill=tk.X, pady=(0, 15), padx=1)
        pref_inner = tk.Frame(pref_card, bg=BG_CARD, padx=12, pady=10)
        pref_inner.pack(fill=tk.X)
        
        ttk.Label(pref_inner, text="Bot Preferences", style="CardLabel.TLabel").grid(row=0, column=0, columnspan=5, sticky=tk.W, pady=(0, 10))
        
        # Display Currency
        ttk.Label(pref_inner, text="Default Currency:", background=BG_CARD, foreground=TEXT_COLOR).grid(row=1, column=0, sticky=tk.W)
        self.currency_var = tk.StringVar(value=self.get_chat_pref("currency", "USD"))
        currencies = ["USD", "NIS", "CAD", "EUR", "GBP", "AUD"]
        self.currency_menu = ttk.Combobox(pref_inner, textvariable=self.currency_var, values=currencies, width=10, state="readonly")
        self.currency_menu.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)
        
        # Interval
        ttk.Label(pref_inner, text="Summary Interval:", background=BG_CARD, foreground=TEXT_COLOR).grid(row=1, column=2, sticky=tk.W)
        self.interval_var = tk.StringVar(value=str(self.get_chat_pref("interval", 1)))
        intervals = ["1", "5", "15", "30", "60", "120", "240", "480"]
        self.interval_menu = ttk.Combobox(pref_inner, textvariable=self.interval_var, values=intervals, width=10, state="readonly")
        self.interval_menu.grid(row=1, column=3, sticky=tk.EW, padx=10, pady=5)
        
        # Save Preferences Button
        save_pref_btn = ttk.Button(pref_inner, text="Save Preferences", style="Blue.TButton", command=self.save_preferences)
        save_pref_btn.grid(row=1, column=4, padx=(20, 0))
        
        pref_inner.columnconfigure(1, weight=1)
        pref_inner.columnconfigure(3, weight=1)

        # 4. Wallet Manager Card
        wallet_card = ttk.Frame(self.main_container, style="Card.TFrame")
        wallet_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15), padx=1)
        wallet_inner = tk.Frame(wallet_card, bg=BG_CARD, padx=12, pady=10)
        wallet_inner.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(wallet_inner, text="Wallet Address Manager (Requires Chat ID to be saved)", style="CardLabel.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Left Panel - User Wallets (u)
        user_frame = tk.Frame(wallet_inner, bg=BG_CARD)
        user_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        ttk.Label(user_frame, text="User Wallets (Tracks All Tokens)", background=BG_CARD, foreground=TEXT_MUTED).pack(anchor=tk.W, pady=(0, 3))
        
        self.user_listbox = tk.Listbox(user_frame, bg=BG_MAIN, fg=TEXT_COLOR, selectbackground=ACCENT_BLUE, bd=1, relief=tk.SOLID, selectforeground="#ffffff", highlightthickness=0, height=8)
        self.user_listbox.pack(fill=tk.BOTH, expand=True)
        self.user_listbox.bind("<Double-1>", lambda e: self.copy_selected_address(self.user_listbox, self.user_wallets_map))
        
        btn_user_frame = tk.Frame(user_frame, bg=BG_CARD, pady=5)
        btn_user_frame.pack(fill=tk.X)
        ttk.Button(btn_user_frame, text="Add Wallet", style="Green.TButton", command=self.add_user_wallet).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_user_frame, text="Copy", style="Gray.TButton", command=lambda: self.copy_selected_address(self.user_listbox, self.user_wallets_map)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_user_frame, text="Remove", style="Red.TButton", command=self.remove_user_wallet).pack(side=tk.LEFT)
        
        # Right Panel - Specific Tokens (w)
        token_frame = tk.Frame(wallet_inner, bg=BG_CARD)
        token_frame.grid(row=1, column=1, sticky=tk.NSEW, padx=(10, 0))
        ttk.Label(token_frame, text="Token Accounts (Tracks Single Token)", background=BG_CARD, foreground=TEXT_MUTED).pack(anchor=tk.W, pady=(0, 3))
        
        self.token_listbox = tk.Listbox(token_frame, bg=BG_MAIN, fg=TEXT_COLOR, selectbackground=ACCENT_BLUE, bd=1, relief=tk.SOLID, selectforeground="#ffffff", highlightthickness=0, height=8)
        self.token_listbox.pack(fill=tk.BOTH, expand=True)
        self.token_listbox.bind("<Double-1>", lambda e: self.copy_selected_address(self.token_listbox, self.token_wallets_map))
        
        btn_token_frame = tk.Frame(token_frame, bg=BG_CARD, pady=5)
        btn_token_frame.pack(fill=tk.X)
        ttk.Button(btn_token_frame, text="Add Token Account", style="Green.TButton", command=self.add_token_wallet).pack(side=tk.LEFT)
        ttk.Button(btn_token_frame, text="Copy", style="Gray.TButton", command=lambda: self.copy_selected_address(self.token_listbox, self.token_wallets_map)).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(btn_token_frame, text="Remove", style="Red.TButton", command=self.remove_token_wallet).pack(side=tk.LEFT)
        
        wallet_inner.rowconfigure(1, weight=1)
        wallet_inner.columnconfigure(0, weight=1)
        wallet_inner.columnconfigure(1, weight=1)
        
        self.update_wallet_lists()
 
        # 5. Live Logs Display (Collapsible text)
        self.logs_visible = False
        self.log_frame = tk.Frame(self.main_container, bg=BG_MAIN)
        self.log_text = tk.Text(self.log_frame, height=8, bg="#0d0d0f", fg="#a9a9b3", insertbackground=TEXT_COLOR, state=tk.DISABLED, font=("Consolas", 9), bd=1, relief=tk.SOLID)
        self.log_text.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Log coloring tags
        self.log_text.tag_config("info", foreground="#60a5fa")     # Soft blue
        self.log_text.tag_config("warning", foreground="#fbbf24")  # Soft yellow
        self.log_text.tag_config("error", foreground="#f87171")    # Soft red
        
        # 6. Bottom Execution Console
        console_frame = tk.Frame(self.main_container, bg=BG_MAIN)
        console_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        
        # Left side - Controls
        self.start_btn = ttk.Button(console_frame, text="Start Tracker Bot", style="Green.TButton", command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT)
        
        self.stop_btn = ttk.Button(console_frame, text="Stop Tracker Bot", style="Red.TButton", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        self.logs_btn = ttk.Button(console_frame, text="View Logs", style="Gray.TButton", command=self.toggle_logs)
        self.logs_btn.pack(side=tk.LEFT)
        
        # Right side - Status and Exit
        ttk.Button(console_frame, text="Exit Configuration", style="Gray.TButton", command=self.clean_exit).pack(side=tk.RIGHT)
        
        self.status_lbl = ttk.Label(console_frame, text="● Status: Stopped", font=("Helvetica", 10, "bold"), foreground=ACCENT_RED)
        self.status_lbl.pack(side=tk.RIGHT, padx=20)

    # Scrolling Helpers
    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame_id, width=event.width)
        req_height = self.main_container.winfo_reqheight()
        if req_height < event.height:
            self.canvas.itemconfig(self.canvas_frame_id, height=event.height)

    def _on_mousewheel(self, event):
        if event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        else:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # State Loaders
    def load_env_values(self):
        token = ""
        chat_id = ""
        rpc_url = "https://api.mainnet-beta.solana.com"
        if os.path.exists(ENV_PATH):
            try:
                with open(ENV_PATH, "r") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip()
                            if k == "TELEGRAM_BOT_TOKEN":
                                token = v
                            elif k == "TELEGRAM_CHAT_ID":
                                chat_id = v
                            elif k == "SOLANA_RPC_URL":
                                rpc_url = v
            except Exception as e:
                print(f"Error loading env: {e}")
        return token, chat_id, rpc_url

    def load_state_values(self):
        if os.path.exists(STATE_PATH):
            try:
                with open(STATE_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"chats": {}, "global_last_signatures": {}}

    def save_state(self):
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        try:
            with open(STATE_PATH, "w") as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save tracked.json state: {e}")

    def get_chat_pref(self, key, default):
        if not self.chat_id:
            return default
        chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
        return chat_data.get(key, default)

    # Actions
    def toggle_token_visibility(self):
        if self.token_entry.cget("show") == "*":
            self.token_entry.config(show="")
            self.show_token_btn.config(text="Hide")
        else:
            self.token_entry.config(show="*")
            self.show_token_btn.config(text="Show")

    def test_connections(self):
        token = self.token_var.get().strip()
        chat_id = self.chat_id_var.get().strip()
        rpc_url = self.rpc_url_var.get().strip()
        
        if not token:
            messagebox.showwarning("Test Error", "Telegram Bot Token is required to run connection tests.")
            return
            
        self.test_conn_btn.config(state=tk.DISABLED, text="Testing...")
        
        def run_test():
            results = []
            success = True
            
            # 1. Test Solana RPC URLs
            rpc_urls = [u.strip() for u in rpc_url.split(",")]
            rpc_ok = False
            rpc_errors = []
            for u in rpc_urls:
                if not (u.startswith("http://") or u.startswith("https://")):
                    rpc_errors.append(f"Invalid URL schema: {u}")
                    continue
                try:
                    # Solana JSON-RPC post request
                    payload = {"jsonrpc": "2.0", "id": 1, "method": "getSlot"}
                    response = requests.post(u, json=payload, timeout=5)
                    if response.status_code == 200:
                        res_json = response.json()
                        if "result" in res_json:
                            rpc_ok = True
                            break
                        else:
                            rpc_errors.append(f"{u}: Invalid JSON-RPC response")
                    else:
                        rpc_errors.append(f"{u}: HTTP {response.status_code}")
                except Exception as e:
                    rpc_errors.append(f"{u}: {str(e)}")
            
            if rpc_ok:
                results.append("✅ Solana RPC: Connected successfully.")
            else:
                success = False
                err_str = "; ".join(rpc_errors)
                results.append(f"❌ Solana RPC: Failed ({err_str})")
                
            # 2. Test Telegram Bot Token
            tg_token_ok = False
            try:
                response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get("ok"):
                        tg_token_ok = True
                        bot_name = res_json.get("result", {}).get("username", "Bot")
                        results.append(f"✅ Telegram Bot Token: Valid (@{bot_name}).")
                    else:
                        results.append("❌ Telegram Bot Token: Invalid response from API.")
            except Exception as e:
                results.append(f"❌ Telegram Bot Token: Failed ({str(e)})")
                
            # 3. Test Telegram Chat ID
            if chat_id:
                if tg_token_ok:
                    try:
                        test_msg = "🔔 *Solana Wallet Tracker Connection Test*\n\nYour bot configuration parameters are verified and working! 🟢"
                        payload = {"chat_id": chat_id, "text": test_msg, "parse_mode": "Markdown"}
                        response = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload, timeout=5)
                        if response.status_code == 200:
                            res_json = response.json()
                            if res_json.get("ok"):
                                results.append("✅ Telegram Chat ID: Valid (Test message delivered).")
                            else:
                                success = False
                                results.append(f"❌ Telegram Chat ID: Failed to send message ({res_json.get('description')})")
                        else:
                            success = False
                            results.append(f"❌ Telegram Chat ID: HTTP {response.status_code} ({response.text})")
                    except Exception as e:
                        success = False
                        results.append(f"❌ Telegram Chat ID: Failed ({str(e)})")
                else:
                    success = False
                    results.append("❌ Telegram Chat ID: Cannot test (invalid bot token).")
            else:
                results.append("ℹ️ Telegram Chat ID: Empty (skipped test).")
                
            # Invoke callback on main thread
            self.root.after(0, lambda: self.show_test_results(success, results))
            
        threading.Thread(target=run_test, daemon=True).start()

    def show_test_results(self, success, results):
        self.test_conn_btn.config(state=tk.NORMAL, text="Test Connections")
        message_str = "\n".join(results)
        if success:
            messagebox.showinfo("Connection Test Success", message_str)
        else:
            messagebox.showerror("Connection Test Failure", message_str)

    def save_connections(self):
        token = self.token_var.get().strip()
        chat_id = self.chat_id_var.get().strip()
        rpc_url = self.rpc_url_var.get().strip()
        
        if not token:
            messagebox.showwarning("Validation Error", "Telegram Token cannot be empty.")
            return
            
        # Validate Telegram Bot Token format
        if not re.match(r"^\d+:[A-Za-z0-9_-]{35,}$", token):
            if not messagebox.askyesno("Validation Warning", "The Telegram Bot Token format looks unusual.\nFormat is typically digits:chars (e.g. 1234567:ABCabc...).\nAre you sure you want to save it?"):
                return
                
        # Validate Telegram Chat ID format (must be an integer, negative for groups)
        if chat_id and not re.match(r"^-?\d+$", chat_id):
            messagebox.showerror("Validation Error", "Telegram Chat ID must be a numeric value.\nGroup Chat IDs typically start with a minus sign (e.g., -100123456789).")
            return
            
        # Validate Solana RPC URLs
        urls = [u.strip() for u in rpc_url.split(",")]
        for url in urls:
            if not (url.startswith("http://") or url.startswith("https://")):
                messagebox.showerror("Validation Error", f"Invalid RPC URL: '{url}'.\nMust start with http:// or https://")
                return
                
        # Write to env
        os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
        try:
            with open(ENV_PATH, "w") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={token}\n")
                f.write(f"TELEGRAM_CHAT_ID={chat_id}\n")
                f.write(f"SOLANA_RPC_URL={rpc_url}\n")
            
            # Update internal variables
            self.token = token
            self.chat_id = chat_id
            self.rpc_url = rpc_url
            
            # Add chat config if not present in state
            if chat_id:
                chat_id_str = str(chat_id)
                if "chats" not in self.state:
                    self.state["chats"] = {}
                if chat_id_str not in self.state["chats"]:
                    self.state["chats"][chat_id_str] = {
                        "active": True,
                        "currency": "USD",
                        "interval": 1,
                        "last_summary_time": time.time() if "time" in sys.modules else 0.0,
                        "tracked": {},
                        "accumulated_txs": []
                    }
                    self.save_state()
            
            self.update_wallet_lists()
            messagebox.showinfo("Success", "Connection parameters saved successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save environment variables: {e}")

    def save_preferences(self):
        if not self.chat_id:
            messagebox.showwarning("Configuration Error", "Please save a Telegram Chat ID first.")
            return
            
        curr = self.currency_var.get()
        intv = int(self.interval_var.get())
        
        chat_id_str = str(self.chat_id)
        if "chats" not in self.state:
            self.state["chats"] = {}
        if chat_id_str not in self.state["chats"]:
            self.state["chats"][chat_id_str] = {
                "active": True,
                "currency": "USD",
                "interval": 1,
                "tracked": {},
                "accumulated_txs": []
            }
            
        self.state["chats"][chat_id_str]["currency"] = curr
        self.state["chats"][chat_id_str]["interval"] = intv
        self.save_state()
        messagebox.showinfo("Success", "Preferences saved successfully.")

    def update_wallet_lists(self):
        self.user_listbox.delete(0, tk.END)
        self.token_listbox.delete(0, tk.END)
        
        if not self.chat_id:
            return
            
        chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
        tracked = chat_data.get("tracked", {})
        
        self.user_wallets_map = [] # indices match listbox rows
        self.token_wallets_map = []
        
        for addr, info in tracked.items():
            name = info.get("name", "Unnamed")
            addr_type = info.get("type", "user")
            
            display_str = f"{name} ({addr[:4]}...{addr[-4:]})"
            if addr_type == "user":
                self.user_listbox.insert(tk.END, display_str)
                self.user_wallets_map.append(addr)
            else:
                self.token_listbox.insert(tk.END, display_str)
                self.token_wallets_map.append(addr)

    def add_address(self, addr_type):
        if not self.chat_id:
            messagebox.showwarning("Configuration Error", "Please set and save a Chat ID first.")
            return
            
        dialog = CustomAddAddressDialog(self.root, addr_type)
        self.root.wait_window(dialog)
        
        if not dialog.result:
            return
            
        address, name = dialog.result
        
        chat_id_str = str(self.chat_id)
        if "chats" not in self.state:
            self.state["chats"] = {}
        if chat_id_str not in self.state["chats"]:
            self.state["chats"][chat_id_str] = {
                "active": True,
                "currency": "USD",
                "interval": 1,
                "tracked": {},
                "accumulated_txs": []
            }
            
        self.state["chats"][chat_id_str]["tracked"][address] = {
            "type": addr_type,
            "name": name
        }
        
        # Set signature offset so we don't fetch historical transactions on start
        if "global_last_signatures" not in self.state:
            self.state["global_last_signatures"] = {}
        if address not in self.state["global_last_signatures"]:
            # Default to None, bot will fetch current signatures on launch
            self.state["global_last_signatures"][address] = None
            
        self.save_state()
        self.update_wallet_lists()

    def add_user_wallet(self):
        self.add_address("user")

    def add_token_wallet(self):
        self.add_address("wallet")

    def remove_address(self, listbox, wallets_map):
        if not self.chat_id:
            return
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an address to remove.")
            return
            
        addr = wallets_map[selected[0]]
        chat_id_str = str(self.chat_id)
        
        if messagebox.askyesno("Confirm Removal", f"Are you sure you want to stop tracking:\n{addr}?"):
            if chat_id_str in self.state.get("chats", {}):
                tracked = self.state["chats"][chat_id_str].get("tracked", {})
                if addr in tracked:
                    del tracked[addr]
                    self.save_state()
                    self.update_wallet_lists()

    def remove_user_wallet(self):
        self.remove_address(self.user_listbox, self.user_wallets_map)

    def remove_token_wallet(self):
        self.remove_address(self.token_listbox, self.token_wallets_map)

    def copy_selected_address(self, listbox, wallets_map):
        selected = listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an address to copy.")
            return
            
        addr = wallets_map[selected[0]]
        self.root.clipboard_clear()
        self.root.clipboard_append(addr)
        self.root.update()
        
        # Temporary status message showing success
        original_status = self.status_lbl.cget("text")
        original_fg = self.status_lbl.cget("foreground")
        self.status_lbl.config(text="📋 Address copied to clipboard!", foreground=ACCENT_BLUE)
        self.root.after(2000, lambda: self.status_lbl.config(text=original_status, foreground=original_fg))

    # Log View
    def toggle_logs(self):
        if self.logs_visible:
            self.log_frame.pack_forget()
            self.logs_btn.config(text="View Logs")
            self.logs_visible = False
        else:
            self.log_frame.pack(fill=tk.BOTH, expand=True, side=tk.BOTTOM, pady=(5, 0))
            self.logs_btn.config(text="Hide Logs")
            self.logs_visible = True
            self.refresh_logs()

    def refresh_logs(self):
        if not self.logs_visible:
            return
            
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        
        if os.path.exists(LOG_PATH):
            try:
                with open(LOG_PATH, "r") as f:
                    lines = f.readlines()
                    # Show last 40 lines
                    tail = lines[-40:]
                    for line in tail:
                        # Find level
                        tag = None
                        if " - INFO - " in line:
                            tag = "info"
                        elif " - WARNING - " in line:
                            tag = "warning"
                        elif " - ERROR - " in line or " - CRITICAL - " in line:
                            tag = "error"
                        
                        self.log_text.insert(tk.END, line, tag)
            except Exception as e:
                self.log_text.insert(tk.END, f"Error reading logs: {e}\n", "error")
        else:
            self.log_text.insert(tk.END, "Log file not created yet. Start the bot to generate logs.\n")
            
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        
        # Schedule next log refresh in 2 seconds
        if self.logs_visible:
            self.root.after(2000, self.refresh_logs)

    # Process Management
    def start_bot(self):
        if self.tracker_process and self.tracker_process.poll() is None:
            messagebox.showwarning("Process Error", "Tracker bot is already running.")
            return
            
        if not self.token:
            messagebox.showwarning("Configuration Error", "Please save a Telegram Bot Token first.")
            return
            
        # Execute tracker in background
        try:
            if getattr(sys, 'frozen', False):
                # Running as a packaged exe
                tracker_path = os.path.join(BASE_DIR, "tracker.exe")
                if not os.path.exists(tracker_path):
                    tracker_path = os.path.join(os.path.dirname(sys.executable), "tracker.exe")
                self.tracker_process = subprocess.Popen(
                    [tracker_path],
                    cwd=BASE_DIR,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Run tracker.py using the same python interpreter
                self.tracker_process = subprocess.Popen(
                    [sys.executable, "tracker.py"],
                    cwd=BASE_DIR,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            self.bot_start_time = time.time()
            self.pulse_state = True
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_lbl.config(text="● Running | Uptime: 00:00:00", foreground=ACCENT_GREEN)
            logger_msg = "Tracker process launched."
            print(logger_msg)
        except Exception as e:
            messagebox.showerror("Execution Error", f"Failed to start tracker: {e}")

    def stop_bot(self):
        if self.tracker_process and self.tracker_process.poll() is None:
            self.tracker_process.terminate()
            self.tracker_process.wait()
            self.tracker_process = None
            
        self.bot_start_time = None
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_lbl.config(text="● Status: Stopped", foreground=ACCENT_RED)

    def check_process(self):
        if self.tracker_process:
            status = self.tracker_process.poll()
            if status is not None: # Stopped
                self.tracker_process = None
                self.bot_start_time = None
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                self.status_lbl.config(text="● Status: Stopped", foreground=ACCENT_RED)
            else:
                # Running, update uptime and pulse dot
                if not hasattr(self, "bot_start_time") or self.bot_start_time is None:
                    self.bot_start_time = time.time()
                
                uptime = int(time.time() - self.bot_start_time)
                h = uptime // 3600
                m = (uptime % 3600) // 60
                s = uptime % 60
                uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
                
                if not hasattr(self, "pulse_state"):
                    self.pulse_state = True
                self.pulse_state = not self.pulse_state
                
                # Toggle between bright green and dim green to represent status pulse
                dot_color = ACCENT_GREEN if self.pulse_state else "#047857"
                self.status_lbl.config(text=f"● Running | Uptime: {uptime_str}", foreground=dot_color)
        else:
            self.status_lbl.config(text="● Status: Stopped", foreground=ACCENT_RED)
                
        # Loop every 1 second
        self.root.after(1000, self.check_process)

    def clean_exit(self):
        self.stop_bot()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfiguratorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.clean_exit)
    root.mainloop()
