import os
import sys
import json
import re
import time
import subprocess
import threading
import requests
import tkinter as tk
from tkinter import ttk, simpledialog, filedialog

messagebox = None


# Paths
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "secrets", ".env")
STATE_PATH = os.path.join(BASE_DIR, "secrets", "tracked.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "tracker.log")

from gui_styles import (
    BG_MAIN, BG_CARD, TEXT_COLOR, TEXT_MUTED,
    ACCENT_GREEN, ACCENT_BLUE, ACCENT_RED, BORDER_COLOR,
    APP_ICON_BASE64, setup_styles
)
from gui_dialogs import (
    CustomMessageDialog, CustomConfirmDialog, MessageBoxWrapper, CustomAddAddressDialog
)

class ConfiguratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solana Telegram Tracker Configurator")
        self.root.geometry("820x720")
        self.root.configure(bg=BG_MAIN)
        
        # Borderless main window with custom border
        self.root.overrideredirect(True)
        self.root.config(bd=1, relief=tk.SOLID, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_BLUE)
        
        self.in_map_transition = False
        self.root.bind("<Map>", self.on_map)
        if sys.platform == "win32":
            self.root.after(10, self.set_appwindow)
        
        # Custom messagebox wrapper
        global messagebox
        messagebox = MessageBoxWrapper(self.root)
        
        # Subprocess tracker
        self.tracker_process = None
        
        # Load configs
        self.token, self.chat_id, self.rpc_url, self.auto_start = self.load_env_values()
        self.state = self.load_state_values()
        
        # Create UI
        setup_styles()
        self.build_ui()
        
        # Process monitor loop
        self.check_process()
        self.root.focus_force()
        
        # Auto-start bot if configured
        if self.auto_start == "true":
            if self.chat_id:
                chat_id_str = str(self.chat_id)
                if "chats" in self.state and chat_id_str in self.state["chats"]:
                    self.state["chats"][chat_id_str]["active"] = True
                    self.save_state()
            self.root.after(500, self.start_bot)

    def build_ui(self):
        # Custom Title Bar
        self.title_bar = tk.Frame(self.root, bg=BG_CARD, height=35)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        
        try:
            self.icon_img = tk.PhotoImage(data=APP_ICON_BASE64)
            lbl_icon_bar = tk.Label(self.title_bar, image=self.icon_img, bg=BG_CARD)
            lbl_icon_bar.pack(side=tk.LEFT, padx=(10, 5))
            self.root.iconphoto(True, self.icon_img)
        except Exception:
            pass
            
        lbl_title = tk.Label(self.title_bar, text="Solana Telegram Tracker Configurator", bg=BG_CARD, fg=TEXT_COLOR, font=("Helvetica", 9, "bold"))
        lbl_title.pack(side=tk.LEFT)
        
        # Window controls
        btn_close = tk.Button(
            self.title_bar, 
            text="✕", 
            bg=BG_CARD, 
            fg=TEXT_MUTED, 
            activebackground=ACCENT_RED, 
            activeforeground="#ffffff", 
            bd=0, 
            font=("Helvetica", 9), 
            command=self.clean_exit,
            width=5,
            relief=tk.FLAT
        )
        btn_close.pack(side=tk.RIGHT, fill=tk.Y)
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg="#ffffff"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg=BG_CARD, fg=TEXT_MUTED))
        
        self.is_maximized = False
        self.normal_geom = "820x720"
        
        btn_max = tk.Button(
            self.title_bar, 
            text="🗖", 
            bg=BG_CARD, 
            fg=TEXT_MUTED, 
            activebackground="#29292e", 
            activeforeground=TEXT_COLOR, 
            bd=0, 
            font=("Helvetica", 9), 
            command=self.toggle_maximize,
            width=5,
            relief=tk.FLAT
        )
        btn_max.pack(side=tk.RIGHT, fill=tk.Y)
        btn_max.bind("<Enter>", lambda e: btn_max.config(bg="#2d2d30", fg=TEXT_COLOR))
        btn_max.bind("<Leave>", lambda e: btn_max.config(bg=BG_CARD, fg=TEXT_MUTED))
        
        btn_min = tk.Button(
            self.title_bar, 
            text="—", 
            bg=BG_CARD, 
            fg=TEXT_MUTED, 
            activebackground="#29292e", 
            activeforeground=TEXT_COLOR, 
            bd=0, 
            font=("Helvetica", 9), 
            command=self.minimize_window,
            width=5,
            relief=tk.FLAT
        )
        btn_min.pack(side=tk.RIGHT, fill=tk.Y)
        btn_min.bind("<Enter>", lambda e: btn_min.config(bg="#2d2d30", fg=TEXT_COLOR))
        btn_min.bind("<Leave>", lambda e: btn_min.config(bg=BG_CARD, fg=TEXT_MUTED))
        
        # Dragging logic
        def start_move(e):
            self.drag_x = e.x
            self.drag_y = e.y
        def drag(e):
            if self.is_maximized:
                self.toggle_maximize()
            deltax = e.x - self.drag_x
            deltay = e.y - self.drag_y
            x = self.root.winfo_x() + deltax
            y = self.root.winfo_y() + deltay
            self.root.geometry(f"+{x}+{y}")
            
        self.title_bar.bind("<ButtonPress-1>", start_move)
        self.title_bar.bind("<B1-Motion>", drag)
        lbl_title.bind("<ButtonPress-1>", start_move)
        lbl_title.bind("<B1-Motion>", drag)

        # Configure min size of root window
        self.root.minsize(800, 600)
        
        # Main Container Frame
        self.main_container = tk.Frame(self.root, bg=BG_MAIN, padx=15, pady=10)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header Title
        title_lbl = ttk.Label(self.main_container, text="🧿 Solana Wallet Tracker Panel", style="Header.TLabel")
        title_lbl.pack(anchor=tk.W, pady=(0, 10))
        
        # Notebook Tab Container
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.tab_settings = tk.Frame(self.notebook, bg=BG_MAIN, padx=10, pady=10)
        self.tab_wallets = tk.Frame(self.notebook, bg=BG_MAIN, padx=10, pady=10)
        self.tab_logs = tk.Frame(self.notebook, bg=BG_MAIN, padx=10, pady=10)
        self.tab_backup = tk.Frame(self.notebook, bg=BG_MAIN, padx=10, pady=10)
        
        self.notebook.add(self.tab_settings, text=" Settings & Credentials ")
        self.notebook.add(self.tab_wallets, text=" Wallet Manager ")
        self.notebook.add(self.tab_logs, text=" Live Console & Logs ")
        self.notebook.add(self.tab_backup, text=" Backup & License ")

        # --- TAB 1: Settings & Credentials ---
        conn_card = ttk.Frame(self.tab_settings, style="Card.TFrame")
        conn_card.pack(fill=tk.X, pady=(0, 10))
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
        self.chat_id_entry = tk.Entry(conn_inner, textvariable=self.chat_id_var, bg=BG_MAIN, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, show="*", bd=1, relief=tk.SOLID)
        self.chat_id_entry.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=5)
        
        self.show_chat_id_btn = ttk.Button(conn_inner, text="Show", width=6, style="Gray.TButton", command=self.toggle_chat_id_visibility)
        self.show_chat_id_btn.grid(row=2, column=2, sticky=tk.W)
        
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
 
        # Preferences Card
        pref_card = ttk.Frame(self.tab_settings, style="Card.TFrame")
        pref_card.pack(fill=tk.X, pady=(10, 0))
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
        save_pref_btn.grid(row=1, column=4, rowspan=2, padx=(20, 0), sticky=tk.NS)
        
        # Status Interval
        ttk.Label(pref_inner, text="Status Interval:", background=BG_CARD, foreground=TEXT_COLOR).grid(row=2, column=0, sticky=tk.W)
        self.status_interval_var = tk.StringVar(value=str(self.get_chat_pref("status_interval", 5)))
        status_intervals = ["1", "5", "10", "15", "30", "60"]
        self.status_interval_menu = ttk.Combobox(pref_inner, textvariable=self.status_interval_var, values=status_intervals, width=10, state="readonly")
        self.status_interval_menu.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=5)
        
        # Whale Threshold
        ttk.Label(pref_inner, text="Whale Threshold (%):", background=BG_CARD, foreground=TEXT_COLOR).grid(row=2, column=2, sticky=tk.W)
        self.whale_threshold_var = tk.StringVar(value=str(self.get_chat_pref("whale_threshold", 1.0)))
        self.whale_threshold_entry = tk.Entry(pref_inner, textvariable=self.whale_threshold_var, bg=BG_MAIN, fg=TEXT_COLOR, insertbackground=TEXT_COLOR, bd=1, relief=tk.SOLID, width=12)
        self.whale_threshold_entry.grid(row=2, column=3, sticky=tk.EW, padx=10, pady=5)
        
        # Show Coin Link Checkbox
        self.show_coin_link_var = tk.BooleanVar(value=self.get_chat_pref("show_coin_link", True))
        self.show_coin_link_check = tk.Checkbutton(
            pref_inner,
            text="Show Coin Link (Dexscreener)",
            variable=self.show_coin_link_var,
            bg=BG_CARD,
            fg=TEXT_COLOR,
            selectcolor=BG_MAIN,
            activebackground=BG_CARD,
            activeforeground=TEXT_COLOR,
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0
        )
        self.show_coin_link_check.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Show Market Cap Checkbox
        self.show_market_cap_var = tk.BooleanVar(value=self.get_chat_pref("show_market_cap", True))
        self.show_market_cap_check = tk.Checkbutton(
            pref_inner,
            text="Show Market Cap",
            variable=self.show_market_cap_var,
            bg=BG_CARD,
            fg=TEXT_COLOR,
            selectcolor=BG_MAIN,
            activebackground=BG_CARD,
            activeforeground=TEXT_COLOR,
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0
        )
        self.show_market_cap_check.grid(row=3, column=2, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Auto-start Service Checkbox
        self.auto_start_var = tk.BooleanVar(value=(self.auto_start == "true"))
        self.auto_start_check = tk.Checkbutton(
            pref_inner, 
            text="Auto-start Tracker Bot on launch (Skips UI clicking & Telegram /start)", 
            variable=self.auto_start_var, 
            bg=BG_CARD, 
            fg=TEXT_COLOR, 
            selectcolor=BG_MAIN, 
            activebackground=BG_CARD, 
            activeforeground=TEXT_COLOR,
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0
        )
        self.auto_start_check.grid(row=4, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))
        
        pref_inner.columnconfigure(1, weight=1)
        pref_inner.columnconfigure(3, weight=1)

        # --- TAB 2: Wallet Manager ---
        wallet_card = ttk.Frame(self.tab_wallets, style="Card.TFrame")
        wallet_card.pack(fill=tk.BOTH, expand=True)
        wallet_inner = tk.Frame(wallet_card, bg=BG_CARD, padx=12, pady=10)
        wallet_inner.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(wallet_inner, text="Wallet Address Manager (Requires Chat ID to be saved)", style="CardLabel.TLabel").grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Left Panel - User Wallets (u)
        user_frame = tk.Frame(wallet_inner, bg=BG_CARD)
        user_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        ttk.Label(user_frame, text="User Wallets (Tracks All Tokens)", background=BG_CARD, foreground=TEXT_MUTED).pack(anchor=tk.W, pady=(0, 3))
        
        self.user_listbox = tk.Listbox(user_frame, bg=BG_MAIN, fg=TEXT_COLOR, selectbackground=ACCENT_BLUE, bd=1, relief=tk.SOLID, selectforeground="#ffffff", highlightthickness=0, height=12)
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
        
        self.token_listbox = tk.Listbox(token_frame, bg=BG_MAIN, fg=TEXT_COLOR, selectbackground=ACCENT_BLUE, bd=1, relief=tk.SOLID, selectforeground="#ffffff", highlightthickness=0, height=12)
        self.token_listbox.pack(fill=tk.BOTH, expand=True)
        self.token_listbox.bind("<Double-1>", lambda e: self.copy_selected_address(self.token_listbox, self.token_wallets_map))
        
        btn_token_frame = tk.Frame(token_frame, bg=BG_CARD, pady=5)
        btn_token_frame.pack(fill=tk.X)
        ttk.Button(btn_token_frame, text="Add Token Account", style="Green.TButton", command=self.add_token_wallet).pack(side=tk.LEFT)
        ttk.Button(btn_token_frame, text="Copy", style="Gray.TButton", command=lambda: self.copy_selected_address(self.token_listbox, self.token_wallets_map)).pack(side=tk.LEFT, padx=(5, 5))
        ttk.Button(btn_token_frame, text="Remove", style="Red.TButton", command=self.remove_token_wallet).pack(side=tk.LEFT)
        
        # Status feedback label in Tab 2
        self.wallet_status_lbl = ttk.Label(wallet_inner, text="", font=("Helvetica", 9), background=BG_CARD, foreground=ACCENT_BLUE)
        self.wallet_status_lbl.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        wallet_inner.rowconfigure(1, weight=1)
        wallet_inner.columnconfigure(0, weight=1)
        wallet_inner.columnconfigure(1, weight=1)
        
        self.update_wallet_lists()

        # --- TAB 3: Live Console & Logs ---
        console_frame = tk.Frame(self.tab_logs, bg=BG_MAIN)
        console_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))
        
        self.start_btn = ttk.Button(console_frame, text="Start Tracker Bot", style="Green.TButton", command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT)
        
        self.stop_btn = ttk.Button(console_frame, text="Stop Tracker Bot", style="Red.TButton", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        btn_clear_console = ttk.Button(console_frame, text="Clear Console", style="Gray.TButton", command=self.clear_log_display)
        btn_clear_console.pack(side=tk.LEFT)
        
        ttk.Button(console_frame, text="Exit", style="Gray.TButton", command=self.clean_exit).pack(side=tk.RIGHT)
        
        self.status_lbl = ttk.Label(console_frame, text="● Status: Stopped", font=("Helvetica", 10, "bold"), foreground=ACCENT_RED)
        self.status_lbl.pack(side=tk.RIGHT, padx=20)
        
        self.log_text = tk.Text(self.tab_logs, bg="#0d0d0f", fg="#a9a9b3", insertbackground=TEXT_COLOR, state=tk.DISABLED, font=("Consolas", 9), bd=1, relief=tk.SOLID)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Log coloring tags
        self.log_text.tag_config("info", foreground="#60a5fa")     # Soft blue
        self.log_text.tag_config("warning", foreground="#fbbf24")  # Soft yellow
        self.log_text.tag_config("error", foreground="#f87171")    # Soft red
        
        self.logs_visible = True

        # --- TAB 4: Backup & License ---
        backup_card = ttk.Frame(self.tab_backup, style="Card.TFrame")
        backup_card.pack(fill=tk.X, pady=(0, 10))
        backup_inner = tk.Frame(backup_card, bg=BG_CARD, padx=12, pady=12)
        backup_inner.pack(fill=tk.X)
        
        ttk.Label(backup_inner, text="Backup & Restore", style="CardLabel.TLabel").pack(anchor=tk.W, pady=(0, 5))
        ttk.Label(backup_inner, text="Export or import your list of tracked wallets to backup your settings or sync configuration across files.", background=BG_CARD, foreground=TEXT_MUTED, font=("Helvetica", 9)).pack(anchor=tk.W, pady=(0, 15))
        
        btn_back_frame = tk.Frame(backup_inner, bg=BG_CARD)
        btn_back_frame.pack(fill=tk.X, anchor=tk.W)
        
        btn_export = ttk.Button(btn_back_frame, text="Export Tracked List", style="Blue.TButton", command=self.export_config)
        btn_export.pack(side=tk.LEFT, padx=(0, 10))
        
        btn_import = ttk.Button(btn_back_frame, text="Import Tracked List", style="Gray.TButton", command=self.import_config)
        btn_import.pack(side=tk.LEFT)
        
        license_card = ttk.Frame(self.tab_backup, style="Card.TFrame")
        license_card.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        license_inner = tk.Frame(license_card, bg=BG_CARD, padx=12, pady=12)
        license_inner.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(license_inner, text="About & Open Source License", style="CardLabel.TLabel").pack(anchor=tk.W, pady=(0, 5))
        
        about_text = (
            "Solana Telegram Tracker Configurator v1.1.0\n"
            "An open-source transaction monitoring system for Solana wallets.\n"
            "Created by devops-user (c) 2026.\n\n"
            "Licensed under the MIT License:\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
            "of this software and associated documentation files (the \"Software\"), to deal\n"
            "in the Software without restriction, including without limitation the rights\n"
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
            "copies of the Software, and to permit persons to whom the Software is\n"
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all\n"
            "copies or substantial portions of the Software."
        )
        
        license_textbox = tk.Text(license_inner, bg="#0d0d0f", fg=TEXT_MUTED, font=("Consolas", 8), wrap=tk.WORD, bd=1, relief=tk.SOLID)
        license_textbox.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        license_textbox.insert(tk.END, about_text)
        license_textbox.config(state=tk.DISABLED)


    # State Loaders
    def load_env_values(self):
        token = ""
        chat_id = ""
        rpc_url = "https://api.mainnet-beta.solana.com"
        auto_start = "false"
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
                            elif k == "AUTO_START_BOT":
                                auto_start = v
            except Exception as e:
                print(f"Error loading env: {e}")
        return token, chat_id, rpc_url, auto_start

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
        token = self.token_var.get().replace('\r', '').replace('\n', '').strip()
        chat_id = self.chat_id_var.get().replace('\r', '').replace('\n', '').strip()
        rpc_url = self.rpc_url_var.get().replace('\r', '').replace('\n', '').strip()
        
        if not token:
            messagebox.showwarning("Test Error", "Telegram Bot Token is required to run connection tests.")
            return
            
        self.test_conn_btn.config(state=tk.DISABLED, text="Testing...")
        
        def run_test():
            results = []
            success = True
            
            # 1. Test Solana RPC URLs with Latency check
            rpc_urls = [u.strip() for u in rpc_url.split(",")]
            rpc_ok = False
            rpc_errors = []
            latency_ms = None
            for u in rpc_urls:
                if not (u.startswith("http://") or u.startswith("https://")):
                    rpc_errors.append(f"Invalid URL schema: {u}")
                    continue
                try:
                    payload = {"jsonrpc": "2.0", "id": 1, "method": "getSlot"}
                    start_time = time.time()
                    response = requests.post(u, json=payload, timeout=5)
                    elapsed = (time.time() - start_time) * 1000
                    if response.status_code == 200:
                        res_json = response.json()
                        if "result" in res_json:
                            rpc_ok = True
                            latency_ms = int(elapsed)
                            break
                        else:
                            rpc_errors.append(f"{u}: Invalid JSON-RPC response")
                    else:
                        rpc_errors.append(f"{u}: HTTP {response.status_code}")
                except Exception as e:
                    rpc_errors.append(f"{u}: {str(e)}")
            
            if rpc_ok:
                results.append(f"[✓] Solana RPC: Connected successfully ({latency_ms}ms).")
            else:
                success = False
                err_str = "; ".join(rpc_errors)
                results.append(f"[✗] Solana RPC: Failed ({err_str})")
                
            # 2. Test Telegram Bot Token
            tg_token_ok = False
            try:
                response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get("ok"):
                        tg_token_ok = True
                        bot_name = res_json.get("result", {}).get("username", "Bot")
                        results.append(f"[✓] Telegram Bot Token: Valid (@{bot_name}).")
                    else:
                        results.append("[✗] Telegram Bot Token: Invalid response from API.")
            except Exception as e:
                results.append(f"[✗] Telegram Bot Token: Failed ({str(e)})")
                
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
                                results.append("[✓] Telegram Chat ID: Valid (Test message delivered).")
                            else:
                                success = False
                                results.append(f"[✗] Telegram Chat ID: Failed to send message ({res_json.get('description')})")
                        else:
                            success = False
                            results.append(f"[✗] Telegram Chat ID: HTTP {response.status_code} ({response.text})")
                    except Exception as e:
                        success = False
                        results.append(f"[✗] Telegram Chat ID: Failed ({str(e)})")
                else:
                    success = False
                    results.append("[✗] Telegram Chat ID: Cannot test (invalid bot token).")
            else:
                results.append("[i] Telegram Chat ID: Empty (skipped test).")
                
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
        token = self.token_var.get().replace('\r', '').replace('\n', '').strip()
        chat_id = self.chat_id_var.get().replace('\r', '').replace('\n', '').strip()
        rpc_url = self.rpc_url_var.get().replace('\r', '').replace('\n', '').strip()
        
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
                f.write(f"AUTO_START_BOT={self.auto_start}\n")
            
            # Update internal variables
            self.token = token
            self.chat_id = chat_id
            self.rpc_url = rpc_url
            
            # Add/Activate chat config in state
            if chat_id:
                chat_id_str = str(chat_id)
                if "chats" not in self.state:
                    self.state["chats"] = {}
                if chat_id_str not in self.state["chats"]:
                    self.state["chats"][chat_id_str] = {
                        "active": True,
                        "currency": "USD",
                        "interval": 1,
                        "status_interval": 5,
                        "whale_threshold": 1.0,
                        "show_coin_link": True,
                        "show_market_cap": True,
                        "last_summary_time": time.time() if "time" in sys.modules else 0.0,
                        "last_status_time": 0.0,
                        "status_txs": [],
                        "tracked": {},
                        "accumulated_txs": []
                    }
                else:
                    self.state["chats"][chat_id_str]["active"] = True
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
        
        try:
            intv = int(self.interval_var.get())
            if intv < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Summary Interval must be a positive integer.")
            return
            
        try:
            s_intv = int(self.status_interval_var.get())
            if s_intv < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Status Interval must be a positive integer.")
            return
            
        try:
            w_thresh = float(self.whale_threshold_var.get())
            if w_thresh <= 0.0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Whale Threshold must be a positive number.")
            return
            
        show_link = self.show_coin_link_var.get()
        show_mcap = self.show_market_cap_var.get()
        auto_start_val = "true" if self.auto_start_var.get() else "false"
        
        self.auto_start = auto_start_val
        
        # Write to env
        try:
            with open(ENV_PATH, "w") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={self.token}\n")
                f.write(f"TELEGRAM_CHAT_ID={self.chat_id}\n")
                f.write(f"SOLANA_RPC_URL={self.rpc_url}\n")
                f.write(f"AUTO_START_BOT={self.auto_start}\n")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update environment variables: {e}")
            return
            
        chat_id_str = str(self.chat_id)
        if "chats" not in self.state:
            self.state["chats"] = {}
        if chat_id_str not in self.state["chats"]:
            self.state["chats"][chat_id_str] = {
                "active": True,
                "currency": "USD",
                "interval": 1,
                "status_interval": 5,
                "whale_threshold": 1.0,
                "show_coin_link": True,
                "show_market_cap": True,
                "last_status_time": 0.0,
                "status_txs": [],
                "tracked": {},
                "accumulated_txs": []
            }
        else:
            self.state["chats"][chat_id_str]["active"] = True
            
        self.state["chats"][chat_id_str]["currency"] = curr
        self.state["chats"][chat_id_str]["interval"] = intv
        self.state["chats"][chat_id_str]["status_interval"] = s_intv
        self.state["chats"][chat_id_str]["whale_threshold"] = w_thresh
        self.state["chats"][chat_id_str]["show_coin_link"] = show_link
        self.state["chats"][chat_id_str]["show_market_cap"] = show_mcap
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
        
        self.wallet_status_lbl.config(text="[✓] Address copied to clipboard!")
        self.root.after(2000, lambda: self.wallet_status_lbl.config(text=""))

    def clear_log_display(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def export_config(self):
        filename = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Tracked List",
            initialfile="tracked_backup.json",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All Files", "*.*")]
        )
        if not filename:
            return
            
        try:
            with open(filename, "w") as f:
                json.dump(self.state, f, indent=2)
            messagebox.showinfo("Export Success", f"Configuration successfully exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export configuration: {e}")

    def import_config(self):
        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Import Tracked List",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All Files", "*.*")]
        )
        if not filename:
            return
            
        try:
            with open(filename, "r") as f:
                imported_data = json.load(f)
                
            if not isinstance(imported_data, dict) or "chats" not in imported_data:
                messagebox.showerror("Import Error", "Invalid backup file schema: missing 'chats' object.")
                return
                
            if not messagebox.askyesno("Confirm Import", "This will merge/overwrite your current tracked configuration with the backup file.\nAre you sure you want to proceed?"):
                return
                
            if "chats" in imported_data:
                for cid, cdata in imported_data["chats"].items():
                    if cid not in self.state["chats"]:
                        self.state["chats"][cid] = cdata
                    else:
                        if "tracked" in cdata:
                            if "tracked" not in self.state["chats"][cid]:
                                self.state["chats"][cid]["tracked"] = {}
                            self.state["chats"][cid]["tracked"].update(cdata["tracked"])
                        for k in ("currency", "interval", "active", "status_interval", "whale_threshold", "show_coin_link", "show_market_cap"):
                            if k in cdata:
                                self.state["chats"][cid][k] = cdata[k]
                                
            if "global_last_signatures" in imported_data:
                if "global_last_signatures" not in self.state:
                    self.state["global_last_signatures"] = {}
                self.state["global_last_signatures"].update(imported_data["global_last_signatures"])
                
            self.save_state()
            self.update_wallet_lists()
            messagebox.showinfo("Import Success", "Configuration successfully imported and merged.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import configuration: {e}")

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

    def minimize_window(self):
        self.root.overrideredirect(False)
        self.root.iconify()

    def set_appwindow(self):
        if sys.platform == "win32":
            try:
                import ctypes
                self.root.update_idletasks()
                hwnd = self.root.winfo_id()
                parent_hwnd = ctypes.windll.user32.GetParent(hwnd)
                if parent_hwnd:
                    hwnd = parent_hwnd
                
                style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
                style = style & ~0x00000080  # Remove WS_EX_TOOLWINDOW
                style = style | 0x00040000   # Add WS_EX_APPWINDOW
                ctypes.windll.user32.SetWindowLongW(hwnd, -20, style)
                
                # Prevent recursive Map triggers when deiconifying
                self.in_map_transition = True
                self.root.withdraw()
                self.root.deiconify()
                self.root.after(100, self.reset_map_transition)
            except Exception:
                self.in_map_transition = False

    def reset_map_transition(self):
        self.in_map_transition = False

    def on_map(self, event):
        if getattr(self, "in_map_transition", False):
            return
        self.root.overrideredirect(True)
        if sys.platform == "win32":
            self.set_appwindow()
        
    def toggle_maximize(self):
        if self.is_maximized:
            self.root.geometry(self.normal_geom)
            self.is_maximized = False
        else:
            self.normal_geom = self.root.geometry()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{sw}x{sh-40}+0+0")
            self.is_maximized = True

    def toggle_chat_id_visibility(self):
        if self.chat_id_entry.cget("show") == "*":
            self.chat_id_entry.config(show="")
            self.show_chat_id_btn.config(text="Hide")
        else:
            self.chat_id_entry.config(show="*")
            self.show_chat_id_btn.config(text="Show")

    def clean_exit(self):
        self.stop_bot()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfiguratorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.clean_exit)
    root.mainloop()
