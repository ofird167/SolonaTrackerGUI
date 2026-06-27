import os
import sys
import json
import re
import time
import subprocess
import threading
import requests
import tkinter as tk
from tkinter import ttk, filedialog
import gui_styles
from gui_styles import APP_ICON_BASE64, setup_styles
from gui_dialogs import MessageBoxWrapper, CustomAddAddressDialog

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except Exception:
    TRAY_AVAILABLE = False


messagebox = None

# Paths
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, "secrets", ".env")
STATE_PATH = os.path.join(BASE_DIR, "secrets", "tracked.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "tracker.log")

FONT_SIZES = {
    "Small": 8,
    "Medium": 10,
    "Large": 12
}

TRANSLATIONS = {
    "English": {
        "title": "Solana Telegram Tracker Configurator",
        "success": "Success",
        "error": "Error",
        "settings_credentials": " Credentials & Preferences ",
        "wallet_manager": " Wallet Manager ",
        "live_console": " Live Console & Logs ",
        "backup_license": " Backup & License ",
        "app_settings": " App Settings ",
        "connection_credentials": "Connection Credentials",
        "telegram_token": "Telegram Token:",
        "telegram_chat_id": "Telegram Chat ID:",
        "solana_rpc_url": "Solana RPC URL:",
        "test_connections": "Test Connections",
        "save_connection": "Save Connection",
        "bot_preferences": "Bot Preferences",
        "default_currency": "Default Currency:",
        "summary_interval": "Summary Interval:",
        "save_preferences": "Save Preferences",
        "status_interval": "Status Interval:",
        "whale_threshold": "Whale Threshold (%):",
        "show_coin_link": "Show Coin Link (Dexscreener)",
        "show_market_cap": "Show Market Cap",
        "auto_start": "Auto-start Tracker Bot on launch (Skips UI clicking & Telegram /start)",
        "wallet_address_manager": "Wallet Address Manager (Requires Chat ID to be saved)",
        "user_wallets": "User Wallets (Tracks All Tokens)",
        "add_wallet": "Add Wallet",
        "copy": "Copy",
        "remove": "Remove",
        "token_accounts": "Token Accounts (Tracks Single Token)",
        "add_token_account": "Add Token Account",
        "start_bot": "Start Tracker Bot",
        "stop_bot": "Stop Tracker Bot",
        "clear_console": "Clear Console",
        "exit": "Exit",
        "status_stopped": "● Status: Stopped",
        "status_running": "● Running | Uptime: {uptime}",
        "backup_restore": "Backup & Restore",
        "export_list": "Export Tracked List",
        "import_list": "Import Tracked List",
        "about_license": "About & Open Source License",
        "ui_settings_title": "UI & Environment Settings",
        "language": "Language:",
        "font_size": "Font Size:",
        "theme": "Theme Mode:",
        "save_settings": "Save Settings",
        "hint_chat_id": "Hint: Group Chat IDs usually begin with a minus sign (e.g. -100123456789)",
        "show": "Show",
        "hide": "Hide",
        "testing": "Testing...",
        "auto_scroll": "Auto-scroll",
        "copied": "Address copied to clipboard!",
        "backup_desc": "Export or import your list of tracked wallets to backup your settings or sync configuration across files.",
        "success_pref": "Preferences saved successfully.",
        "success_conn": "Connection parameters saved successfully.",
        "success_import": "Configuration successfully imported and merged.",
        "success_export": "Configuration successfully exported to: ",
        "add_user_wallet_success": "Added wallet: {name}",
        "remove_wallet_success": "Removed wallet: {name}",
        "launch_success": "Tracker process launched.",
        "setting_saved_success": "Settings saved and applied successfully!",
        "validation_error": "Validation Error",
        "test_error": "Test Error",
        "token_required": "Telegram Bot Token is required to run connection tests.",
        "chat_id_required": "Please save a Telegram Chat ID first.",
        "token_empty": "Telegram Token cannot be empty.",
        "token_warning_title": "Validation Warning",
        "token_warning_msg": "The Telegram Bot Token format looks unusual.\nFormat is typically digits:chars (e.g. 1234567:ABCabc...).\nAre you sure you want to save it?",
        "chat_id_numeric": "Telegram Chat ID must be a numeric value.\nGroup Chat IDs typically start with a minus sign (e.g., -100123456789).",
        "rpc_invalid": "Invalid RPC URL: '{url}'.\nMust start with http:// or https://",
        "summary_interval_pos": "Summary Interval must be a positive integer.",
        "status_interval_pos": "Status Interval must be a positive integer.",
        "whale_threshold_pos": "Whale Threshold must be a positive number.",
        "import_confirm_title": "Confirm Import",
        "import_confirm_msg": "This will merge/overwrite your current tracked configuration with the backup file.\nAre you sure you want to proceed?",
        "import_schema_error": "Invalid backup file schema: missing 'chats' object.",
        "wallet_required": "Please select a wallet address to remove.",
        "wallet_confirm_title": "Confirm Removal",
        "wallet_confirm_msg": "Are you sure you want to remove the tracking configuration for '{name}'?",
        "process_error": "Process Error",
        "process_running": "Tracker bot is already running.",
        "execution_error": "Execution Error",
        "launch_failed": "Failed to start tracker: {error}",
        "ok": "OK",
        "yes": "Yes",
        "no": "No",
        "cancel": "Cancel",
        "add": "Add",
        "add_user_wallet_title": "Add User Wallet",
        "add_token_account_title": "Add Token Account",
        "solana_address": "Solana Address:",
        "custom_name": "Custom Name:",
        "err_address_empty": "Address cannot be empty.",
        "err_invalid_solana_addr": "Invalid Solana address format.",
        "config_error": "Configuration Error",
        "save_error": "Save Error",
        "failed_save_state": "Failed to save tracked.json state: {error}",
        "conn_test_success": "Connection Test Success",
        "conn_test_failure": "Connection Test Failure",
        "failed_save_env": "Failed to save environment variables: {error}",
        "selection_error": "Selection Error",
        "export_warning": "Export Warning",
        "no_tracked_addresses": "No tracked addresses to export.",
        "export_failed": "Failed to export configuration: {error}",
        "import_failed": "Failed to import configuration: {error}",
        "token_save_first": "Please save a Telegram Bot Token first."
    },
    "Russian": {
        "title": "Панель Отслеживания Solana Кошельков",
        "success": "Успех",
        "error": "Ошибка",
        "settings_credentials": " Настройки и Данные ",
        "wallet_manager": " Менеджер Кошельков ",
        "live_console": " Консоль и Логи ",
        "backup_license": " Бэкап и Лицензия ",
        "app_settings": " Настройки Интерфейса ",
        "connection_credentials": "Учетные Данные Подключения",
        "telegram_token": "Токен Telegram:",
        "telegram_chat_id": "Chat ID Telegram:",
        "solana_rpc_url": "Solana RPC URL:",
        "test_connections": "Проверить Подключение",
        "save_connection": "Сохранить Подключение",
        "bot_preferences": "Настройки Бота",
        "default_currency": "Валюта по умолчанию:",
        "summary_interval": "Интервал Сводок:",
        "save_preferences": "Сохранить Настройки",
        "status_interval": "Интервал Статуса:",
        "whale_threshold": "Порог Китов (%):",
        "show_coin_link": "Ссылка на Монету (Dexscreener)",
        "show_market_cap": "Показывать Капитализацию",
        "auto_start": "Автозапуск бота при старте",
        "wallet_address_manager": "Управление Адресами Кошельков",
        "user_wallets": "Пользовательские Кошельки",
        "add_wallet": "Добавить Кошелек",
        "copy": "Копировать",
        "remove": "Удалить",
        "token_accounts": "Аккаунты Токенов",
        "add_token_account": "Добавить Аккаунт Токена",
        "start_bot": "Запустить Бота",
        "stop_bot": "Остановить Бота",
        "clear_console": "Очистить Консоль",
        "exit": "Выход",
        "status_stopped": "● Статус: Остановлен",
        "status_running": "● Запущен | Время: {uptime}",
        "backup_restore": "Резервное Копирование",
        "export_list": "Экспорт Списка",
        "import_list": "Импорт Списка",
        "about_license": "О Программе и Лицензии",
        "ui_settings_title": "Настройки Интерфейса",
        "language": "Язык:",
        "font_size": "Размер Шрифта:",
        "theme": "Тема Оформления:",
        "save_settings": "Сохранить Настройки",
        "hint_chat_id": "ID групп обычно начинаются с минуса (например, -100123456789)",
        "show": "Показать",
        "hide": "Скрыть",
        "testing": "Проверка...",
        "auto_scroll": "Автопрокрутка",
        "copied": "Адрес скопирован в буфер обмена!",
        "backup_desc": "Экспортируйте или импортируйте список отслеживаемых кошельков для резервного копирования настроек.",
        "success_pref": "Настройки успешно сохранены.",
        "success_conn": "Параметры подключения успешно сохранены.",
        "success_import": "Конфигурация успешно импортирована и объединена.",
        "success_export": "Конфигурация успешно экспортирована в: ",
        "add_user_wallet_success": "Добавлен кошелек: {name}",
        "remove_wallet_success": "Удален кошелек: {name}",
        "launch_success": "Процесс отслеживания запущен.",
        "setting_saved_success": "Настройки успешно сохранены и применены!",
        "validation_error": "Ошибка валидации",
        "test_error": "Ошибка проверки",
        "token_required": "Токен Telegram бота обязателен для проверки подключения.",
        "chat_id_required": "Сначала сохраните Telegram Chat ID.",
        "token_empty": "Токен Telegram не может быть пустым.",
        "token_warning_title": "Предупреждение валидации",
        "token_warning_msg": "Формат токена Telegram бота выглядит необычно.\nОбычно формат: цифры:символы.\nВы уверены, что хотите сохранить?",
        "chat_id_numeric": "Chat ID Telegram должен быть числовым.\nID групп обычно начинаются с минуса (например, -100123456789).",
        "rpc_invalid": "Недопустимый RPC URL: '{url}'.\nДолжен начинаться с http:// или https://",
        "summary_interval_pos": "Интервал сводок должен быть положительным целым числом.",
        "status_interval_pos": "Интервал статуса должен быть положительным целым числом.",
        "whale_threshold_pos": "Порог китов должен быть положительным числом.",
        "import_confirm_title": "Подтвердить импорт",
        "import_confirm_msg": "Это объединит/перезапишет вашу текущую конфигурацию с файлом бэкапа.\nПродолжить?",
        "import_schema_error": "Неверная схема файла бэкапа: отсутствует объект 'chats'.",
        "wallet_required": "Выберите кошелек для удаления.",
        "wallet_confirm_title": "Подтвердить удаление",
        "wallet_confirm_msg": "Вы уверены, что хотите прекратить отслеживание '{name}'?",
        "process_error": "Ошибка процесса",
        "process_running": "Бот-трекер уже запущен.",
        "execution_error": "Ошибка выполнения",
        "launch_failed": "Не удалось запустить трекер: {error}",
        "ok": "ОК",
        "yes": "Да",
        "no": "Нет",
        "cancel": "Отмена",
        "add": "Добавить",
        "add_user_wallet_title": "Добавить кошелек пользователя",
        "add_token_account_title": "Добавить аккаунт токена",
        "solana_address": "Адрес Solana:",
        "custom_name": "Имя (необязательно):",
        "err_address_empty": "Адрес не может быть пустым.",
        "err_invalid_solana_addr": "Недопустимый формат адреса Solana.",
        "config_error": "Ошибка конфигурации",
        "save_error": "Ошибка сохранения",
        "failed_save_state": "Не удалось сохранить состояние tracked.json: {error}",
        "conn_test_success": "Проверка подключения успешна",
        "conn_test_failure": "Ошибка проверки подключения",
        "failed_save_env": "Не удалось сохранить переменные окружения: {error}",
        "selection_error": "Ошибка выбора",
        "export_warning": "Предупреждение экспорта",
        "no_tracked_addresses": "Нет отслеживаемых адресов для экспорта.",
        "export_failed": "Не удалось экспортировать конфигурацию: {error}",
        "import_failed": "Не удалось импортировать конфигурацию: {error}",
        "token_save_first": "Сначала сохраните токен Telegram бота."
    },
    "Arabic": {
        "title": "لوحة تتبع محفظة سولانا",
        "success": "نجاح",
        "error": "خطأ",
        "settings_credentials": " الإعدادات والاعتمادات ",
        "wallet_manager": " مدير المحفظة ",
        "live_console": " وحدة التحكم والسجلات ",
        "backup_license": " النسخ الاحتياطي والترخيص ",
        "app_settings": " إعدادات التطبيق ",
        "connection_credentials": "بيانات الاتصال",
        "telegram_token": "رمز تليجرام البوت:",
        "telegram_chat_id": "معرف دردشة تليجرام:",
        "solana_rpc_url": "رابط Solana RPC:",
        "test_connections": "اختبار الاتصال",
        "save_connection": "حفظ الاتصال",
        "bot_preferences": "تفضيلات البوت",
        "default_currency": "العملة الافتراضية:",
        "summary_interval": "فترة الملخص:",
        "save_preferences": "حفظ التفضيلات",
        "status_interval": "فترة الحالة:",
        "whale_threshold": "حد الحوت (%):",
        "show_coin_link": "عرض رابط العملة (Dexscreener)",
        "show_market_cap": "عرض القيمة السوقية",
        "auto_start": "بدء تشغيل البوت تلقائيًا عند الإطلاق",
        "wallet_address_manager": "مدير عناوين المحفظة",
        "user_wallets": "محافظ المستخدم (جميع العملات)",
        "add_wallet": "إضافة محفظة",
        "copy": "نسخ",
        "remove": "إزالة",
        "token_accounts": "حسابات العملات (عملة واحدة)",
        "add_token_account": "إضافة حساب عملة",
        "start_bot": "تشغيل البوت",
        "stop_bot": "إيقاف البوت",
        "clear_console": "مسح وحدة التحكم",
        "exit": "خروج",
        "status_stopped": "● الحالة: متوقف",
        "status_running": "● قيد التشغيل | الوقت: {uptime}",
        "backup_restore": "النسخ الاحتياطي والاستعادة",
        "export_list": "تصدير القائمة",
        "import_list": "استيراد القائمة",
        "about_license": "حول البرنامج والترخيص",
        "ui_settings_title": "إعدادات واجهة المستخدم",
        "language": "اللغة:",
        "font_size": "حجم الخط:",
        "theme": "مظهر المظهر:",
        "save_settings": "حفظ الإعدادات",
        "hint_chat_id": "تبدأ معرفات المجموعات عادةً بعلامة ناقص (مثل -100123456789)",
        "show": "عرض",
        "hide": "إخفاء",
        "testing": "جاري الاختبار...",
        "auto_scroll": "التمرير التلقائي",
        "copied": "تم نسخ العنوان إلى الحافظة!",
        "backup_desc": "قم بتصدير أو استيراد قائمة المحافظ المتعقبة للنسخ الاحتياطي للإعدادات.",
        "success_pref": "تم حفظ التفضيلات بنجاح.",
        "success_conn": "تم حفظ معلمات الاتصال بنجاح.",
        "success_import": "تم استيراد التكوين ودمجه بنجاح.",
        "success_export": "تم تصدير التكوين بنجاح إلى: ",
        "add_user_wallet_success": "تمت إضافة المحفظة: {name}",
        "remove_wallet_success": "تمت إزالة المحفظة: {name}",
        "launch_success": "تم إطلاق عملية التتبع.",
        "setting_saved_success": "تم حفظ الإعدادات وتطبيقها بنجاح!",
        "validation_error": "خطأ في التحقق",
        "test_error": "خطأ في الاختبار",
        "token_required": "مطلوب رمز تليجرام البوت لتشغيل اختبارات الاتصال.",
        "chat_id_required": "يرجى حفظ معرف دردشة تليجرام أولاً.",
        "token_empty": "لا يمكن أن يكون رمز تليجرام فارغًا.",
        "token_warning_title": "تحذير التحقق",
        "token_warning_msg": "يبدو تنسيق رمز تليجرام البوت غير عادي.\nهل أنت متأكد أنك تريد حفظه؟",
        "chat_id_numeric": "يجب أن يكون معرف دردشة تليجرام قيمة رقمية.\nتبدأ معرفات المجموعات عادةً بعلامة ناقص.",
        "rpc_invalid": "رابط RPC غير صالح: '{url}'.\nيجب أن يبدأ بـ http:// أو https://",
        "summary_interval_pos": "يجب أن يكون فاصل الملخص عددًا صحيحًا موجبًا.",
        "status_interval_pos": "يجب أن يكون فاصل الحالة عددًا صحيحًا موجبًا.",
        "whale_threshold_pos": "يجب أن يكون حد الحوت رقمًا موجبًا.",
        "import_confirm_title": "تأكيد الاستيراد",
        "import_confirm_msg": "سيؤدي هذا إلى دمج/كتابة التكوين الحالي فوقه بملف النسخ الاحتياطي.\nهل تريد المتابعة؟",
        "import_schema_error": "مخطط ملف نسخ احتياطي غير صالح: مفقود كائن 'chats'.",
        "wallet_required": "يرجى تحديد عنوان المحفظة لإزالته.",
        "wallet_confirm_title": "تأكيد الإزالة",
        "wallet_confirm_msg": "هل أنت متأكد أنك تريد إزالة تكوين التتبع لـ '{name}'؟",
        "process_error": "خطأ في العملية",
        "process_running": "بوت التتبع قيد التشغيل بالفعل.",
        "execution_error": "خطأ في التنفيذ",
        "launch_failed": "فشل بدء تشغيل التتبع: {error}",
        "ok": "موافق",
        "yes": "نعم",
        "no": "لا",
        "cancel": "إلغاء",
        "add": "إضافة",
        "add_user_wallet_title": "إضافة محفظة مستخدم",
        "add_token_account_title": "إضافة حساب عملة",
        "solana_address": "عنوان سولانا:",
        "custom_name": "الاسم المخصص:",
        "err_address_empty": "لا يمكن أن يكون العنوان فارغًا.",
        "err_invalid_solana_addr": "تنسيق عنوان سولانا غير صالح.",
        "config_error": "خطأ في التكوين",
        "save_error": "خطأ في الحفظ",
        "failed_save_state": "فشل حفظ حالة tracked.json: {error}",
        "conn_test_success": "نجاح اختبار الاتصال",
        "conn_test_failure": "فشل اختبار الاتصال",
        "failed_save_env": "فشل حفظ متغيرات البيئة: {error}",
        "selection_error": "خطأ في الاختيار",
        "export_warning": "تحذير التصدير",
        "no_tracked_addresses": "لا توجد عناوين متعقبة للتصدير.",
        "export_failed": "فشل تصدير التكوين: {error}",
        "import_failed": "فشل استيراد التكوين: {error}",
        "token_save_first": "يرجى حفظ رمز تليجرام البوت أولاً."
    }
}

class ConfiguratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solana Telegram Tracker Configurator")
        self.root.geometry("820x720")
        
        # Custom messagebox wrapper
        global messagebox
        messagebox = MessageBoxWrapper(self.root, tr=self.tr)
        
        # Subprocess tracker & watchdog state
        self.tracker_process = None
        self.should_be_running = False
        
        # Load configs & state values
        self.token, self.chat_id, self.rpc_url, self.auto_start = self.load_env_values()
        self.state = self.load_state_values()
        self.cached_balances = {}
        
        # Extract UI settings
        self.settings = self.state.setdefault("settings", {
            "language": "English",
            "font_size": "Medium",
            "theme": "System Sync"
        })
        
        # Setup styles based on loaded settings
        theme_mode = self.settings.get("theme", "System Sync")
        if theme_mode == "System Sync":
            theme_mode = self.detect_linux_theme()
            
        font_size_pt = FONT_SIZES.get(self.settings.get("font_size", "Medium"), 10)
        setup_styles(font_size=font_size_pt, theme=theme_mode, root=self.root)
        
        self.root.configure(bg=gui_styles.BG_MAIN)
        
        # Apply Windows Dark Title Bar natively if win32
        if sys.platform == "win32":
            import ctypes
            try:
                self.root.update_idletasks()
                hwnd = self.root.winfo_id()
                is_dark = (theme_mode == "Dark Mode")
                rendering = ctypes.c_int(1 if is_dark else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(rendering), ctypes.sizeof(rendering))
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(rendering), ctypes.sizeof(rendering))
            except Exception:
                pass
        
        # Create UI
        self.build_ui()
        self.refresh_dashboard_table()
        self.load_balances_async()
        
        # Process monitor loop
        self.check_process()
        self.root.focus_force()
        
        # Check for github updates
        self.check_for_updates()
        
        # Bind window minimization for system tray
        if TRAY_AVAILABLE:
            self.root.bind("<Unmap>", self.on_minimize)
            
        # Auto-start bot if configured
        if self.auto_start == "true":
            if self.chat_id:
                chat_id_str = str(self.chat_id)
                if "chats" in self.state and chat_id_str in self.state["chats"]:
                    self.state["chats"][chat_id_str]["active"] = True
                    self.save_state()
            self.root.after(500, self.start_bot)

    def detect_linux_theme(self):
        try:
            res = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
                capture_output=True, text=True, timeout=1
            )
            if "dark" in res.stdout.lower():
                return "Dark Mode"
        except Exception:
            pass
            
        try:
            res = subprocess.run(
                ["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"],
                capture_output=True, text=True, timeout=1
            )
            if "dark" in res.stdout.lower():
                return "Dark Mode"
        except Exception:
            pass
        return "Light Mode"

    def check_for_updates(self):
        def run_check():
            try:
                url = "https://raw.githubusercontent.com/ofird167/SolonaTrackerGUI/main/version.txt"
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    remote_ver = r.text.strip()
                    if remote_ver and remote_ver != "1.4.0":
                        self.root.after(0, lambda: self.show_update_notification(remote_ver))
            except Exception as e:
                print(f"Failed to check for updates: {e}")
                
        threading.Thread(target=run_check, daemon=True).start()
        
    def show_update_notification(self, version):
        self.update_lbl = ttk.Label(
            self.content_container,
            text=f"🎁 Update Available: v{version}! Click to open GitHub.",
            foreground=gui_styles.ACCENT_GREEN,
            cursor="hand2"
        )
        self.update_lbl.pack(anchor=tk.E, before=self.page_title_lbl, pady=(0, 5))
        self.update_lbl.bind("<Button-1>", lambda e: self.open_github())
        
    def open_github(self):
        import webbrowser
        webbrowser.open("https://github.com/ofird167/SolonaTrackerGUI")

    def create_tray_icon(self):
        if not TRAY_AVAILABLE:
            return
        try:
            width = 64
            height = 64
            image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            dc = ImageDraw.Draw(image)
            dc.ellipse((8, 8, 56, 56), fill=(16, 185, 129))
            dc.ellipse((20, 20, 44, 44), fill=(255, 255, 255))
            
            menu = pystray.Menu(
                pystray.MenuItem("Show", self.restore_from_tray, default=True),
                pystray.MenuItem("Exit", self.clean_exit)
            )
            self.tray_icon = pystray.Icon("SolanaTracker", image, "Solana Tracker", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Failed to create tray icon: {e}")

    def minimize_to_tray(self):
        self.root.withdraw()
        if not hasattr(self, "tray_icon") or self.tray_icon is None:
            self.create_tray_icon()

    def restore_from_tray(self, icon=None, item=None):
        self.root.deiconify()
        self.root.focus_force()

    def on_minimize(self, event):
        if self.root.state() == "iconic":
            self.minimize_to_tray()

    def tr(self, key):
        lang = self.settings.get("language", "English")
        return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, TRANSLATIONS["English"].get(key, ""))

    def build_ui(self):
        try:
            self.icon_img = tk.PhotoImage(data=APP_ICON_BASE64)
            self.icon_img_small = self.icon_img.subsample(16, 16)
            self.root.iconphoto(True, self.icon_img_small, self.icon_img)
        except Exception:
            pass

        # Left Sidebar Navigation Panel
        self.sidebar_frame = tk.Frame(self.root, bg=gui_styles.BG_CARD, width=220, bd=0, highlightthickness=0)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)
        
        # Brand logo/title area
        brand_frame = tk.Frame(self.sidebar_frame, bg=gui_styles.BG_CARD, pady=25)
        brand_frame.pack(fill=tk.X)
        
        try:
            logo_canvas = tk.Canvas(brand_frame, width=32, height=32, bg=gui_styles.BG_CARD, bd=0, highlightthickness=0)
            logo_canvas.pack(side=tk.LEFT, padx=(20, 10))
            logo_canvas.create_oval(2, 2, 30, 30, fill=gui_styles.ACCENT_GREEN, outline="")
            logo_canvas.create_oval(8, 8, 24, 24, fill="#ffffff", outline="")
        except Exception:
            pass
            
        brand_title = tk.Label(brand_frame, text="Solana Tracker", bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_COLOR, font=("Helvetica", 13, "bold"))
        brand_title.pack(side=tk.LEFT)
        
        tk.Frame(self.sidebar_frame, bg=gui_styles.BG_CARD, height=15).pack(fill=tk.X)
        
        # Sidebar navigation buttons
        self.nav_buttons = {}
        pages = [
            ("dashboard", "📊  Dashboard"),
            ("wallets", "👛  " + self.tr("wallet_manager")),
            ("settings", "⚙️  " + self.tr("settings_credentials")),
            ("logs", "📋  " + self.tr("live_console")),
            ("backup", "💾  " + self.tr("backup_license"))
        ]
        
        for name, label in pages:
            btn = tk.Button(
                self.sidebar_frame,
                text=label,
                anchor=tk.W,
                padx=25,
                pady=12,
                bg=gui_styles.BG_CARD,
                fg=gui_styles.TEXT_MUTED,
                activebackground="#1c1c1f" if self.settings.get("theme", "Dark Mode") == "Dark Mode" else "#e4e4e7",
                activeforeground=gui_styles.TEXT_COLOR,
                bd=0,
                relief=tk.FLAT,
                font=("Helvetica", 10, "bold"),
                cursor="hand2",
                command=lambda n=name: self.show_page(n)
            )
            btn.pack(fill=tk.X)
            gui_styles.bind_hover(btn, "#161618" if self.settings.get("theme", "Dark Mode") == "Dark Mode" else "#f4f4f5", gui_styles.BG_CARD)
            self.nav_buttons[name] = btn
            
        footer_lbl = tk.Label(self.sidebar_frame, text="v1.4.0 • Release", bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_MUTED, font=("Helvetica", 8))
        footer_lbl.pack(side=tk.BOTTOM, pady=15)
        
        # Right Content Panel Container
        self.content_container = tk.Frame(self.root, bg=gui_styles.BG_MAIN, padx=15, pady=10)
        self.content_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Title of current page
        self.page_title_lbl = tk.Label(self.content_container, text="Dashboard Overview", bg=gui_styles.BG_MAIN, fg=gui_styles.ACCENT_GREEN, font=("Helvetica", 16, "bold"))
        self.page_title_lbl.pack(anchor=tk.W, pady=(5, 15))
        
        # Page Frames (stored inside content_container)
        self.page_frames = {}
        for name in ("dashboard", "wallets", "settings", "logs", "backup"):
            f = tk.Frame(self.content_container, bg=gui_styles.BG_MAIN)
            self.page_frames[name] = f
            
        # Hide them initially
        for f in self.page_frames.values():
            f.pack_forget()

        # Define page frames aliases for easy backward compatibility
        self.tab_settings = self.page_frames["settings"]
        self.tab_wallets = self.page_frames["wallets"]
        self.tab_logs = self.page_frames["logs"]
        self.tab_backup = self.page_frames["backup"]
        
        # --- PAGE 1: Dashboard Overview ---
        dash_frame = self.page_frames["dashboard"]
        
        # Cards Frame (row of metrics cards)
        cards_frame = tk.Frame(dash_frame, bg=gui_styles.BG_MAIN)
        cards_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Card 1: Tracked Wallets
        c1 = ttk.Frame(cards_frame, style="Card.TFrame")
        c1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        c1_inner = tk.Frame(c1, bg=gui_styles.BG_CARD, padx=15, pady=12)
        c1_inner.pack(fill=tk.BOTH, expand=True)
        self.dash_wallets_lbl = ttk.Label(c1_inner, text="Total Wallets Tracked", style="MetricLbl.TLabel")
        self.dash_wallets_lbl.pack(anchor=tk.W)
        self.dash_wallets_val = ttk.Label(c1_inner, text="0", style="MetricVal.TLabel")
        self.dash_wallets_val.pack(anchor=tk.W, pady=(5, 0))
        
        # Card 2: Active Alert Channels
        c2 = ttk.Frame(cards_frame, style="Card.TFrame")
        c2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        c2_inner = tk.Frame(c2, bg=gui_styles.BG_CARD, padx=15, pady=12)
        c2_inner.pack(fill=tk.BOTH, expand=True)
        self.dash_channels_lbl = ttk.Label(c2_inner, text="Active Alert Channels", style="MetricLbl.TLabel")
        self.dash_channels_lbl.pack(anchor=tk.W)
        self.dash_channels_val = ttk.Label(c2_inner, text="1 Connected", style="MetricVal.TLabel", foreground=gui_styles.ACCENT_BLUE)
        self.dash_channels_val.pack(anchor=tk.W, pady=(5, 0))
        
        # Card 3: Total Solana Balance
        c3 = ttk.Frame(cards_frame, style="Card.TFrame")
        c3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        c3_inner = tk.Frame(c3, bg=gui_styles.BG_CARD, padx=15, pady=12)
        c3_inner.pack(fill=tk.BOTH, expand=True)
        self.dash_balance_lbl = ttk.Label(c3_inner, text="Total Solana Balance", style="MetricLbl.TLabel")
        self.dash_balance_lbl.pack(anchor=tk.W)
        self.dash_sol_val = ttk.Label(c3_inner, text="0.00 SOL", style="MetricVal.TLabel")
        self.dash_sol_val.pack(anchor=tk.W, pady=(5, 0))
        
        # Card 4: Tracked Token Accounts
        c4 = ttk.Frame(cards_frame, style="Card.TFrame")
        c4.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        c4_inner = tk.Frame(c4, bg=gui_styles.BG_CARD, padx=15, pady=12)
        c4_inner.pack(fill=tk.BOTH, expand=True)
        self.dash_tokens_lbl = ttk.Label(c4_inner, text="Tracked Token Accounts", style="MetricLbl.TLabel")
        self.dash_tokens_lbl.pack(anchor=tk.W)
        self.dash_tokens_val = ttk.Label(c4_inner, text="0", style="MetricVal.TLabel")
        self.dash_tokens_val.pack(anchor=tk.W, pady=(5, 0))
        
        # Main Table Card Container
        main_table_card = ttk.Frame(dash_frame, style="Card.TFrame")
        main_table_card.pack(fill=tk.BOTH, expand=True)
        main_table_inner = tk.Frame(main_table_card, bg=gui_styles.BG_CARD, padx=15, pady=15)
        main_table_inner.pack(fill=tk.BOTH, expand=True)
        
        # Top Title & Buttons Bar
        top_bar = tk.Frame(main_table_inner, bg=gui_styles.BG_CARD)
        top_bar.pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_table_title = ttk.Label(top_bar, text="Tracked Wallets & Token Accounts", style="CardLabel.TLabel")
        self.lbl_table_title.pack(side=tk.LEFT, anchor=tk.W)
        
        # Right Actions Buttons
        top_btn_frame = tk.Frame(top_bar, bg=gui_styles.BG_CARD)
        top_btn_frame.pack(side=tk.RIGHT)
        
        self.dash_add_btn = ttk.Button(top_btn_frame, text="+ Add New Wallet", style="Green.TButton", command=self.add_new_wallet_unified)
        self.dash_add_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.dash_refresh_btn = ttk.Button(top_btn_frame, text="Refresh Data", style="Blue.TButton", command=self.load_balances_async)
        self.dash_refresh_btn.pack(side=tk.LEFT)
        
        # Table Column Headers Frame
        headers_frame = tk.Frame(main_table_inner, bg=gui_styles.BG_CARD, pady=5)
        headers_frame.pack(fill=tk.X)
        
        # Add thin separator line
        tk.Frame(main_table_inner, bg=gui_styles.BORDER_COLOR, height=1).pack(fill=tk.X, pady=(0, 8))
        
        # Canvas and scrollbar for scrollable rows
        self.table_canvas = tk.Canvas(main_table_inner, bg=gui_styles.BG_CARD, bd=0, highlightthickness=0)
        self.table_scrollbar = ttk.Scrollbar(main_table_inner, orient="vertical", command=self.table_canvas.yview)
        self.scrollable_rows_frame = tk.Frame(self.table_canvas, bg=gui_styles.BG_CARD)
        
        self.scrollable_rows_frame.bind(
            "<Configure>",
            lambda e: self.table_canvas.configure(
                scrollregion=self.table_canvas.bbox("all")
            )
        )
        
        self.table_canvas.create_window((0, 0), window=self.scrollable_rows_frame, anchor="nw")
        self.table_canvas.configure(yscrollcommand=self.table_scrollbar.set)
        
        self.table_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.table_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def _on_mousewheel(event):
            self.table_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        self.table_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- PAGE 2: Settings & Credentials ---
        conn_card = ttk.Frame(self.tab_settings, style="Card.TFrame")
        conn_card.pack(fill=tk.X, pady=(0, 10))
        conn_inner = tk.Frame(conn_card, bg=gui_styles.BG_CARD, padx=12, pady=10)
        conn_inner.pack(fill=tk.X)
        
        self.lbl_credentials_title = ttk.Label(conn_inner, text=self.tr("connection_credentials"), style="CardLabel.TLabel")
        self.lbl_credentials_title.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        
        # Telegram Token
        self.lbl_tg_token = ttk.Label(conn_inner, text=self.tr("telegram_token"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_tg_token.grid(row=1, column=0, sticky=tk.W)
        self.token_var = tk.StringVar(value=self.token)
        self.token_entry = tk.Entry(conn_inner, textvariable=self.token_var, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, show="*", bd=1, relief=tk.SOLID)
        self.token_entry.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)
        
        self.show_token_btn = ttk.Button(conn_inner, text=self.tr("show"), width=6, style="Gray.TButton", command=self.toggle_token_visibility)
        self.show_token_btn.grid(row=1, column=2, sticky=tk.W)
        
        # Chat ID
        self.lbl_chat_id = ttk.Label(conn_inner, text=self.tr("telegram_chat_id"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_chat_id.grid(row=2, column=0, sticky=tk.W)
        self.chat_id_var = tk.StringVar(value=self.chat_id)
        self.chat_id_entry = tk.Entry(conn_inner, textvariable=self.chat_id_var, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, show="*", bd=1, relief=tk.SOLID)
        self.chat_id_entry.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=5)
        
        self.show_chat_id_btn = ttk.Button(conn_inner, text=self.tr("show"), width=6, style="Gray.TButton", command=self.toggle_chat_id_visibility)
        self.show_chat_id_btn.grid(row=2, column=2, sticky=tk.W)
        
        self.chat_id_hint = ttk.Label(conn_inner, text=self.tr("hint_chat_id"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_MUTED, font=("Helvetica", 8))
        self.chat_id_hint.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=10, pady=(0, 5))
        
        # Solana RPC URL Combobox with presets
        self.lbl_solana_rpc = ttk.Label(conn_inner, text=self.tr("solana_rpc_url"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_solana_rpc.grid(row=4, column=0, sticky=tk.W)
        self.rpc_url_var = tk.StringVar(value=self.rpc_url)
        rpc_presets = [
            "https://api.mainnet-beta.solana.com",
            "https://api.ankr.com/solana",
            "https://solana-api.projectserum.com"
        ]
        self.rpc_url_combobox = ttk.Combobox(conn_inner, textvariable=self.rpc_url_var, values=rpc_presets)
        self.rpc_url_combobox.grid(row=4, column=1, columnspan=2, sticky=tk.EW, padx=10, pady=5)
        
        # Premium Builders
        builder_frame = tk.Frame(conn_inner, bg=gui_styles.BG_CARD)
        builder_frame.grid(row=5, column=1, columnspan=2, sticky=tk.EW, padx=10, pady=2)
        
        self.helius_lbl = ttk.Label(builder_frame, text="Helius Key:", background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_MUTED, font=("Helvetica", 8))
        self.helius_lbl.pack(side=tk.LEFT, padx=(0, 2))
        self.helius_var = tk.StringVar()
        self.helius_entry = tk.Entry(builder_frame, textvariable=self.helius_var, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, bd=1, relief=tk.SOLID, width=12, font=("Helvetica", 8))
        self.helius_entry.pack(side=tk.LEFT, padx=(0, 8))
        self.helius_var.trace_add("write", lambda *a: self.build_premium_rpc("helius"))
        
        self.qn_endpoint_lbl = ttk.Label(builder_frame, text="QuickNode Key/ID:", background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_MUTED, font=("Helvetica", 8))
        self.qn_endpoint_lbl.pack(side=tk.LEFT, padx=(0, 2))
        self.qn_var = tk.StringVar()
        self.qn_entry = tk.Entry(builder_frame, textvariable=self.qn_var, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, bd=1, relief=tk.SOLID, width=12, font=("Helvetica", 8))
        self.qn_entry.pack(side=tk.LEFT)
        self.qn_var.trace_add("write", lambda *a: self.build_premium_rpc("quicknode"))
        
        # Buttons Frame on Row 6
        btn_conn_frame = tk.Frame(conn_inner, bg=gui_styles.BG_CARD)
        btn_conn_frame.grid(row=6, column=1, columnspan=2, sticky=tk.E, pady=(5, 0))
        
        self.test_conn_btn = ttk.Button(btn_conn_frame, text=self.tr("test_connections"), style="Gray.TButton", command=self.test_connections)
        self.test_conn_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.save_conn_btn = ttk.Button(btn_conn_frame, text=self.tr("save_connection"), style="Blue.TButton", command=self.save_connections)
        self.save_conn_btn.pack(side=tk.LEFT)
        
        conn_inner.columnconfigure(1, weight=1)
 
        # Preferences Card
        pref_card = ttk.Frame(self.tab_settings, style="Card.TFrame")
        pref_card.pack(fill=tk.X, pady=(10, 0))
        pref_inner = tk.Frame(pref_card, bg=gui_styles.BG_CARD, padx=12, pady=10)
        pref_inner.pack(fill=tk.X)
        
        self.lbl_pref_title = ttk.Label(pref_inner, text=self.tr("bot_preferences"), style="CardLabel.TLabel")
        self.lbl_pref_title.grid(row=0, column=0, columnspan=5, sticky=tk.W, pady=(0, 10))
        
        # Display Currency
        self.lbl_default_currency = ttk.Label(pref_inner, text=self.tr("default_currency"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_default_currency.grid(row=1, column=0, sticky=tk.W)
        self.currency_var = tk.StringVar(value=self.get_chat_pref("currency", "USD"))
        currencies = ["USD", "NIS", "CAD", "EUR", "GBP", "AUD"]
        self.currency_menu = ttk.Combobox(pref_inner, textvariable=self.currency_var, values=currencies, width=10, state="readonly")
        self.currency_menu.grid(row=1, column=1, sticky=tk.EW, padx=10, pady=5)
        
        # Interval
        self.lbl_summary_interval = ttk.Label(pref_inner, text=self.tr("summary_interval"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_summary_interval.grid(row=1, column=2, sticky=tk.W)
        self.interval_var = tk.StringVar(value=str(self.get_chat_pref("interval", 1)))
        intervals = ["1", "5", "15", "30", "60", "120", "240", "480"]
        self.interval_menu = ttk.Combobox(pref_inner, textvariable=self.interval_var, values=intervals, width=10, state="readonly")
        self.interval_menu.grid(row=1, column=3, sticky=tk.EW, padx=10, pady=5)
        
        # Save Preferences Button
        self.save_pref_btn = ttk.Button(pref_inner, text=self.tr("save_preferences"), style="Blue.TButton", command=self.save_preferences)
        self.save_pref_btn.grid(row=1, column=4, rowspan=3, padx=(20, 0), sticky=tk.NS)
        
        # Status Interval
        self.lbl_status_interval = ttk.Label(pref_inner, text=self.tr("status_interval"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_status_interval.grid(row=2, column=0, sticky=tk.W)
        self.status_interval_var = tk.StringVar(value=str(self.get_chat_pref("status_interval", 5)))
        status_intervals = ["1", "5", "10", "15", "30", "60"]
        self.status_interval_menu = ttk.Combobox(pref_inner, textvariable=self.status_interval_var, values=status_intervals, width=10, state="readonly")
        self.status_interval_menu.grid(row=2, column=1, sticky=tk.EW, padx=10, pady=5)
        
        # Whale Threshold
        self.lbl_whale_threshold = ttk.Label(pref_inner, text=self.tr("whale_threshold"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_whale_threshold.grid(row=2, column=2, sticky=tk.W)
        self.whale_threshold_var = tk.StringVar(value=str(self.get_chat_pref("whale_threshold", 1.0)))
        self.whale_threshold_entry = tk.Entry(pref_inner, textvariable=self.whale_threshold_var, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, bd=1, relief=tk.SOLID, width=12)
        self.whale_threshold_entry.grid(row=2, column=3, sticky=tk.EW, padx=10, pady=5)
        
        # Daily Summary
        self.daily_summary_enabled_var = tk.BooleanVar(value=self.get_chat_pref("daily_summary_enabled", False))
        self.daily_summary_check = tk.Checkbutton(
            pref_inner,
            text="Daily Snapshot (HH:MM):",
            variable=self.daily_summary_enabled_var,
            bg=gui_styles.BG_CARD,
            fg=gui_styles.TEXT_COLOR,
            selectcolor=gui_styles.BG_MAIN,
            activebackground=gui_styles.BG_CARD,
            activeforeground=gui_styles.TEXT_COLOR,
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0
        )
        self.daily_summary_check.grid(row=3, column=0, sticky=tk.W, pady=5)
        
        self.daily_summary_time_var = tk.StringVar(value=self.get_chat_pref("daily_summary_time", "00:00"))
        self.daily_summary_entry = tk.Entry(pref_inner, textvariable=self.daily_summary_time_var, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, bd=1, relief=tk.SOLID, width=8)
        self.daily_summary_entry.grid(row=3, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Noise Threshold
        self.lbl_noise_threshold = ttk.Label(pref_inner, text="Noise Threshold (USD):", background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_noise_threshold.grid(row=3, column=2, sticky=tk.W)
        self.noise_threshold_var = tk.StringVar(value=str(self.get_chat_pref("noise_threshold", 0.0)))
        self.noise_threshold_entry = tk.Entry(pref_inner, textvariable=self.noise_threshold_var, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, bd=1, relief=tk.SOLID, width=12)
        self.noise_threshold_entry.grid(row=3, column=3, sticky=tk.EW, padx=10, pady=5)
        
        # Show Coin Link Checkbox
        self.show_coin_link_var = tk.BooleanVar(value=self.get_chat_pref("show_coin_link", True))
        self.show_coin_link_check = tk.Checkbutton(
            pref_inner,
            text=self.tr("show_coin_link"),
            variable=self.show_coin_link_var,
            bg=gui_styles.BG_CARD,
            fg=gui_styles.TEXT_COLOR,
            selectcolor=gui_styles.BG_MAIN,
            activebackground=gui_styles.BG_CARD,
            activeforeground=gui_styles.TEXT_COLOR,
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0
        )
        self.show_coin_link_check.grid(row=4, column=0, sticky=tk.W, pady=(5, 0))
        
        # Show Market Cap Checkbox
        self.show_market_cap_var = tk.BooleanVar(value=self.get_chat_pref("show_market_cap", True))
        self.show_market_cap_check = tk.Checkbutton(
            pref_inner,
            text=self.tr("show_market_cap"),
            variable=self.show_market_cap_var,
            bg=gui_styles.BG_CARD,
            fg=gui_styles.TEXT_COLOR,
            selectcolor=gui_styles.BG_MAIN,
            activebackground=gui_styles.BG_CARD,
            activeforeground=gui_styles.TEXT_COLOR,
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0
        )
        self.show_market_cap_check.grid(row=4, column=1, sticky=tk.W, pady=(5, 0))
        
        # Auto-start Service Checkbox
        self.auto_start_var = tk.BooleanVar(value=(self.auto_start == "true"))
        self.auto_start_check = tk.Checkbutton(
            pref_inner, 
            text=self.tr("auto_start"), 
            variable=self.auto_start_var, 
            bg=gui_styles.BG_CARD, 
            fg=gui_styles.TEXT_COLOR, 
            selectcolor=gui_styles.BG_MAIN, 
            activebackground=gui_styles.BG_CARD, 
            activeforeground=gui_styles.TEXT_COLOR,
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0
        )
        self.auto_start_check.grid(row=4, column=2, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        pref_inner.columnconfigure(1, weight=1)
        pref_inner.columnconfigure(3, weight=1)

        # --- PAGE 3: Wallet Manager ---
        wallet_card = ttk.Frame(self.tab_wallets, style="Card.TFrame")
        wallet_card.pack(fill=tk.BOTH, expand=True)
        wallet_inner = tk.Frame(wallet_card, bg=gui_styles.BG_CARD, padx=12, pady=10)
        wallet_inner.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_wallet_manager = ttk.Label(wallet_inner, text=self.tr("wallet_address_manager"), style="CardLabel.TLabel")
        self.lbl_wallet_manager.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Left Panel - User Wallets (u)
        user_frame = tk.Frame(wallet_inner, bg=gui_styles.BG_CARD)
        user_frame.grid(row=1, column=0, sticky=tk.NSEW, padx=(0, 10))
        self.lbl_user_wallets = ttk.Label(user_frame, text=self.tr("user_wallets"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_MUTED)
        self.lbl_user_wallets.pack(anchor=tk.W, pady=(0, 3))
        
        user_list_frame = tk.Frame(user_frame, bg=gui_styles.BG_CARD)
        user_list_frame.pack(fill=tk.BOTH, expand=True)
        user_scroll = ttk.Scrollbar(user_list_frame)
        user_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.user_listbox = tk.Listbox(user_list_frame, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, selectbackground=gui_styles.ACCENT_BLUE, bd=1, relief=tk.SOLID, selectforeground="#ffffff", highlightthickness=0, height=12, yscrollcommand=user_scroll.set)
        self.user_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        user_scroll.config(command=self.user_listbox.yview)
        self.user_listbox.bind("<Double-1>", lambda e: self.copy_selected_address(self.user_listbox, self.user_wallets_map))
        
        btn_user_frame = tk.Frame(user_frame, bg=gui_styles.BG_CARD, pady=5)
        btn_user_frame.pack(fill=tk.X)
        self.btn_add_user_wallet = ttk.Button(btn_user_frame, text=self.tr("add_wallet"), style="Green.TButton", command=self.add_user_wallet)
        self.btn_add_user_wallet.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_copy_user_wallet = ttk.Button(btn_user_frame, text=self.tr("copy"), style="Gray.TButton", command=lambda: self.copy_selected_address(self.user_listbox, self.user_wallets_map))
        self.btn_copy_user_wallet.pack(side=tk.LEFT, padx=(0, 5))
        self.btn_remove_user_wallet = ttk.Button(btn_user_frame, text=self.tr("remove"), style="Red.TButton", command=self.remove_user_wallet)
        self.btn_remove_user_wallet.pack(side=tk.LEFT)
        
        # Right Panel - Specific Tokens (w)
        token_frame = tk.Frame(wallet_inner, bg=gui_styles.BG_CARD)
        token_frame.grid(row=1, column=1, sticky=tk.NSEW, padx=(10, 0))
        self.lbl_token_accounts = ttk.Label(token_frame, text=self.tr("token_accounts"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_MUTED)
        self.lbl_token_accounts.pack(anchor=tk.W, pady=(0, 3))
        
        token_list_frame = tk.Frame(token_frame, bg=gui_styles.BG_CARD)
        token_list_frame.pack(fill=tk.BOTH, expand=True)
        token_scroll = ttk.Scrollbar(token_list_frame)
        token_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.token_listbox = tk.Listbox(token_list_frame, bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, selectbackground=gui_styles.ACCENT_BLUE, bd=1, relief=tk.SOLID, selectforeground="#ffffff", highlightthickness=0, height=12, yscrollcommand=token_scroll.set)
        self.token_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        token_scroll.config(command=self.token_listbox.yview)
        self.token_listbox.bind("<Double-1>", lambda e: self.copy_selected_address(self.token_listbox, self.token_wallets_map))
        
        btn_token_frame = tk.Frame(token_frame, bg=gui_styles.BG_CARD, pady=5)
        btn_token_frame.pack(fill=tk.X)
        self.btn_add_token_wallet = ttk.Button(btn_token_frame, text=self.tr("add_token_account"), style="Green.TButton", command=self.add_token_wallet)
        self.btn_add_token_wallet.pack(side=tk.LEFT)
        self.btn_copy_token_wallet = ttk.Button(btn_token_frame, text=self.tr("copy"), style="Gray.TButton", command=lambda: self.copy_selected_address(self.token_listbox, self.token_wallets_map))
        self.btn_copy_token_wallet.pack(side=tk.LEFT, padx=(5, 5))
        self.btn_remove_token_wallet = ttk.Button(btn_token_frame, text=self.tr("remove"), style="Red.TButton", command=self.remove_token_wallet)
        self.btn_remove_token_wallet.pack(side=tk.LEFT)
        
        self.wallet_status_lbl = ttk.Label(wallet_inner, text="", font=("Helvetica", 9), background=gui_styles.BG_CARD, foreground=gui_styles.ACCENT_BLUE)
        self.wallet_status_lbl.grid(row=2, column=0, columnspan=2, pady=(5, 0))
        
        wallet_inner.rowconfigure(1, weight=1)
        wallet_inner.columnconfigure(0, weight=1)
        wallet_inner.columnconfigure(1, weight=1)
        
        self.update_wallet_lists()

        # --- PAGE 4: Live Console & Logs ---
        console_frame = tk.Frame(self.tab_logs, bg=gui_styles.BG_MAIN)
        console_frame.pack(fill=tk.X, side=tk.TOP, pady=(0, 10))
        
        self.start_btn = ttk.Button(console_frame, text=self.tr("start_bot"), style="Green.TButton", command=self.start_bot)
        self.start_btn.pack(side=tk.LEFT)
        
        self.stop_btn = ttk.Button(console_frame, text=self.tr("stop_bot"), style="Red.TButton", command=self.stop_bot, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        self.btn_clear_console = ttk.Button(console_frame, text=self.tr("clear_console"), style="Gray.TButton", command=self.clear_log_display)
        self.btn_clear_console.pack(side=tk.LEFT)
        
        self.status_lbl = ttk.Label(console_frame, text=self.tr("status_stopped"), font=("Helvetica", 10, "bold"), foreground=gui_styles.ACCENT_RED)
        self.status_lbl.pack(side=tk.RIGHT, padx=20)
        
        # Filter Dropdown
        self.log_filter_var = tk.StringVar(value="All")
        self.log_filter_menu = ttk.Combobox(console_frame, textvariable=self.log_filter_var, values=["All", "Info", "Warning", "Error"], width=10, state="readonly")
        self.log_filter_menu.pack(side=tk.LEFT, padx=10)
        self.log_filter_menu.bind("<<ComboboxSelected>>", lambda e: self.refresh_logs())
        
        # Auto-scroll Checkbox
        self.log_autoscroll_var = tk.BooleanVar(value=True)
        self.log_autoscroll_check = tk.Checkbutton(
            console_frame,
            text=self.tr("auto_scroll"),
            variable=self.log_autoscroll_var,
            bg=gui_styles.BG_MAIN,
            fg=gui_styles.TEXT_COLOR,
            selectcolor=gui_styles.BG_CARD,
            activebackground=gui_styles.BG_MAIN,
            activeforeground=gui_styles.TEXT_COLOR,
            font=("Helvetica", 10),
            bd=0,
            highlightthickness=0
        )
        self.log_autoscroll_check.pack(side=tk.LEFT)
        
        self.btn_exit = ttk.Button(console_frame, text=self.tr("exit"), style="Gray.TButton", command=self.clean_exit)
        self.btn_exit.pack(side=tk.RIGHT)
        
        log_frame = tk.Frame(self.tab_logs, bg=gui_styles.BG_MAIN)
        log_frame.pack(fill=tk.BOTH, expand=True)
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text = tk.Text(log_frame, bg="#0d0d0f" if self.settings.get("theme", "Dark Mode") == "Dark Mode" else "#f4f4f5", fg="#a9a9b3" if self.settings.get("theme", "Dark Mode") == "Dark Mode" else "#27272a", insertbackground=gui_styles.TEXT_COLOR, state=tk.DISABLED, font=("Consolas", gui_styles.FONT_SIZE - 1 if gui_styles.FONT_SIZE > 8 else 8), bd=1, relief=tk.SOLID, yscrollcommand=log_scroll.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        self.log_text.tag_config("info", foreground="#60a5fa")
        self.log_text.tag_config("warning", foreground="#fbbf24")
        self.log_text.tag_config("error", foreground="#f87171")
        
        self.logs_visible = False

        # --- PAGE 5: Backup & License (Combined with App Settings) ---
        # Container frame inside Tab Backup
        backup_scroll_container = tk.Frame(self.tab_backup, bg=gui_styles.BG_MAIN)
        backup_scroll_container.pack(fill=tk.BOTH, expand=True)
        
        # GUI App Settings Card
        ui_card = ttk.Frame(backup_scroll_container, style="Card.TFrame")
        ui_card.pack(fill=tk.X, pady=(0, 10))
        ui_inner = tk.Frame(ui_card, bg=gui_styles.BG_CARD, padx=12, pady=12)
        ui_inner.pack(fill=tk.X)
        
        self.lbl_ui_title = ttk.Label(ui_inner, text=self.tr("ui_settings_title"), style="CardLabel.TLabel")
        self.lbl_ui_title.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 12))
        
        # Language Selector
        self.lbl_lang = ttk.Label(ui_inner, text=self.tr("language"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_lang.grid(row=1, column=0, sticky=tk.W, pady=8)
        self.lang_var = tk.StringVar(value=self.settings.get("language", "English"))
        self.lang_menu = ttk.Combobox(ui_inner, textvariable=self.lang_var, values=["English", "Russian", "Arabic"], width=15, state="readonly")
        self.lang_menu.grid(row=1, column=1, sticky=tk.W, padx=15, pady=8)
        
        # Font Size Selector
        self.lbl_font_size = ttk.Label(ui_inner, text=self.tr("font_size"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_font_size.grid(row=2, column=0, sticky=tk.W, pady=8)
        self.font_size_var = tk.StringVar(value=self.settings.get("font_size", "Medium"))
        self.font_size_menu = ttk.Combobox(ui_inner, textvariable=self.font_size_var, values=["Small", "Medium", "Large"], width=15, state="readonly")
        self.font_size_menu.grid(row=2, column=1, sticky=tk.W, padx=15, pady=8)
        
        # Theme Selector
        self.lbl_theme = ttk.Label(ui_inner, text=self.tr("theme"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_COLOR)
        self.lbl_theme.grid(row=3, column=0, sticky=tk.W, pady=8)
        self.theme_var = tk.StringVar(value=self.settings.get("theme", "System Sync"))
        self.theme_menu = ttk.Combobox(ui_inner, textvariable=self.theme_var, values=["Dark Mode", "Light Mode", "System Sync"], width=15, state="readonly")
        self.theme_menu.grid(row=3, column=1, sticky=tk.W, padx=15, pady=8)
        
        # Save Settings Button
        self.btn_save_settings = ttk.Button(ui_inner, text=self.tr("save_settings"), style="Blue.TButton", command=self.save_ui_settings)
        self.btn_save_settings.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(15, 0))
        
        # Backup / Restore Card
        backup_card = ttk.Frame(backup_scroll_container, style="Card.TFrame")
        backup_card.pack(fill=tk.X, pady=(0, 10))
        backup_inner = tk.Frame(backup_card, bg=gui_styles.BG_CARD, padx=12, pady=12)
        backup_inner.pack(fill=tk.X)
        
        self.lbl_backup_restore = ttk.Label(backup_inner, text=self.tr("backup_restore"), style="CardLabel.TLabel")
        self.lbl_backup_restore.pack(anchor=tk.W, pady=(0, 5))
        self.lbl_backup_desc = ttk.Label(backup_inner, text=self.tr("backup_desc"), background=gui_styles.BG_CARD, foreground=gui_styles.TEXT_MUTED, font=("Helvetica", 9))
        self.lbl_backup_desc.pack(anchor=tk.W, pady=(0, 15))
        
        btn_back_frame = tk.Frame(backup_inner, bg=gui_styles.BG_CARD)
        btn_back_frame.pack(fill=tk.X, anchor=tk.W)
        
        self.btn_export = ttk.Button(btn_back_frame, text=self.tr("export_list"), style="Blue.TButton", command=self.export_config)
        self.btn_export.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_import = ttk.Button(btn_back_frame, text=self.tr("import_list"), style="Gray.TButton", command=self.import_config)
        self.btn_import.pack(side=tk.LEFT)
        
        # License Card
        license_card = ttk.Frame(backup_scroll_container, style="Card.TFrame")
        license_card.pack(fill=tk.BOTH, expand=True)
        license_inner = tk.Frame(license_card, bg=gui_styles.BG_CARD, padx=12, pady=12)
        license_inner.pack(fill=tk.BOTH, expand=True)
        
        self.lbl_about_license = ttk.Label(license_inner, text=self.tr("about_license"), style="CardLabel.TLabel")
        self.lbl_about_license.pack(anchor=tk.W, pady=(0, 5))
        
        about_text = (
            "Solana Telegram Tracker Configurator v1.4.0\n"
            "An open-source transaction monitoring system for Solana wallets.\n"
            "Created by Ofir (c) 2026.\n\n"
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
        
        license_textbox = tk.Text(license_inner, bg="#0d0d0f" if self.settings.get("theme", "Dark Mode") == "Dark Mode" else "#ffffff", fg=gui_styles.TEXT_MUTED, font=("Consolas", 8), wrap=tk.WORD, bd=1, relief=tk.SOLID, height=6)
        license_textbox.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        license_textbox.insert(tk.END, about_text)
        license_textbox.config(state=tk.DISABLED)
        
        # Default to Dashboard Page on startup
        self.show_page("dashboard")

    def show_page(self, name):
        for f in self.page_frames.values():
            f.pack_forget()
        for btn in self.nav_buttons.values():
            btn.config(fg=gui_styles.TEXT_MUTED, bg=gui_styles.BG_CARD)
            
        self.page_frames[name].pack(fill=tk.BOTH, expand=True)
        self.nav_buttons[name].config(fg=gui_styles.TEXT_COLOR, bg="#1c1c1f" if self.settings.get("theme", "Dark Mode") == "Dark Mode" else "#e4e4e7")
        
        title_map = {
            "dashboard": "Dashboard Overview",
            "wallets": "Tracked Wallets & Tokens Manager",
            "settings": "Settings & Credentials",
            "logs": "Live Console Stream",
            "backup": "Backup & App Configuration"
        }
        self.page_title_lbl.config(text=title_map.get(name, "Dashboard"))
        
        if name in ("logs", "dashboard"):
            self.logs_visible = True
            self.refresh_logs()
        else:
            self.logs_visible = False

    def update_dashboard_metrics(self):
        if not hasattr(self, "dash_wallets_val"):
            return
        w_count = 0
        t_count = 0
        if self.chat_id:
            chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
            tracked = chat_data.get("tracked", {})
            for addr, info in tracked.items():
                if info.get("type") == "token":
                    t_count += 1
                else:
                    w_count += 1
        self.dash_wallets_val.config(text=str(w_count))
        self.dash_tokens_val.config(text=str(t_count))

    def save_ui_settings(self):
        self.settings["language"] = self.lang_var.get()
        self.settings["font_size"] = self.font_size_var.get()
        self.settings["theme"] = self.theme_var.get()
        
        self.save_state()
        
        theme_mode = self.settings.get("theme", "System Sync")
        if theme_mode == "System Sync":
            theme_mode = self.detect_linux_theme()
            
        font_size_pt = FONT_SIZES.get(self.settings["font_size"], 10)
        setup_styles(font_size=font_size_pt, theme=theme_mode, root=self.root)
        
        if sys.platform == "win32":
            import ctypes
            try:
                self.root.update_idletasks()
                hwnd = self.root.winfo_id()
                is_dark = (theme_mode == "Dark Mode")
                rendering = ctypes.c_int(1 if is_dark else 0)
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(rendering), ctypes.sizeof(rendering))
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(rendering), ctypes.sizeof(rendering))
            except Exception:
                pass
                
        self.apply_theme_and_fonts()
        messagebox.showinfo("Success", "Settings saved and applied successfully!")

    def add_new_wallet_unified(self):
        from gui_dialogs import CustomAddAddressDialog
        dialog = CustomAddAddressDialog(self.root, title="Add New Address", tr=self.tr)
        self.root.wait_window(dialog)
        
        if not dialog.result:
            return
            
        address, name = dialog.result
        if not address:
            return
            
        # Detect type on-chain
        detected_type = self.identify_address_on_chain(address)
        if detected_type == "OTHER_PROGRAM":
            messagebox.showerror("Error", "This address is owned by a program contract and cannot be tracked.")
            return
        elif detected_type == "INVALID_OR_EMPTY":
            messagebox.showerror("Error", "Invalid Solana address or account info could not be retrieved.")
            return
            
        addr_type = "user" if detected_type == "WALLET" else "token"
        
        # Add to state
        chat_id_str = str(self.chat_id)
        if chat_id_str not in self.state["chats"]:
            self.state["chats"][chat_id_str] = {"tracked": {}}
        
        owner_addr = None
        token_mint = None
        if addr_type == "token":
            try:
                url = [u.strip() for u in self.rpc_url.split(",")][0]
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAccountInfo",
                    "params": [address, {"encoding": "jsonParsed"}]
                }
                r = requests.post(url, json=payload, timeout=5)
                if r.status_code == 200:
                    res = r.json()
                    val = res.get("result", {}).get("value")
                    if val:
                        parsed_data = val.get("data", {})
                        if isinstance(parsed_data, dict) and parsed_data.get("parsed"):
                            info_node = parsed_data["parsed"].get("info", {})
                            owner_addr = info_node.get("owner")
                            token_mint = info_node.get("mint")
            except Exception:
                pass
                
        tracked_entry = {
            "type": addr_type,
            "name": name
        }
        if owner_addr:
            tracked_entry["owner"] = owner_addr
        if token_mint:
            tracked_entry["mint"] = token_mint
            
        self.state["chats"][chat_id_str]["tracked"][address] = tracked_entry
        self.save_state()
        
        self.update_wallet_lists()
        self.refresh_dashboard_table()
        self.update_dashboard_metrics()
        self.load_balances_async()
        
        type_lbl = "User Wallet" if addr_type == "user" else "Specific Token Account"
        messagebox.showinfo("Success", f"Successfully added {type_lbl}:\n{address}")

    def load_balances_async(self):
        def worker():
            if not self.chat_id or not self.rpc_url:
                return
            chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
            tracked = chat_data.get("tracked", {})
            url = [u.strip() for u in self.rpc_url.split(",")][0]
            
            total_sol = 0.0
            temp_balances = {}
            
            for addr, info in list(tracked.items()):
                if info.get("type") == "user":
                    try:
                        payload = {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "getBalance",
                            "params": [addr]
                        }
                        r = requests.post(url, json=payload, timeout=5)
                        if r.status_code == 200:
                            res = r.json()
                            if "result" in res and res["result"].get("value") is not None:
                                bal = res["result"]["value"] / 1e9
                                total_sol += bal
                                temp_balances[addr] = bal
                    except Exception:
                        pass
            
            self.root.after(0, lambda: self.update_balances_ui(total_sol, temp_balances))
            
        threading.Thread(target=worker, daemon=True).start()

    def update_balances_ui(self, total_sol, temp_balances):
        self.cached_balances = temp_balances
        if hasattr(self, "dash_sol_val"):
            self.dash_sol_val.config(text=f"{total_sol:,.2f} SOL")
        self.refresh_dashboard_table()

    def refresh_dashboard_table(self):
        if not hasattr(self, "scrollable_rows_frame"):
            return
            
        for child in self.scrollable_rows_frame.winfo_children():
            child.destroy()
            
        if not self.chat_id:
            return
            
        chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
        tracked = chat_data.get("tracked", {})
        
        for idx, (addr, info) in enumerate(tracked.items()):
            name = info.get("name", "Unnamed")
            addr_type = info.get("type", "user")
            
            # Row Frame Card
            row_card = ttk.Frame(self.scrollable_rows_frame, style="Card.TFrame")
            row_card.pack(fill=tk.X, pady=3, padx=2)
            row_inner = tk.Frame(row_card, bg=gui_styles.BG_CARD, padx=10, pady=8)
            row_inner.pack(fill=tk.X)
            
            # Column 0: Type Indicator
            type_lbl_text = "👛  Wallet" if addr_type == "user" else "🪙  Token"
            type_lbl = tk.Label(row_inner, text=type_lbl_text, bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_COLOR, font=("Helvetica", 9, "bold"), width=12, anchor=tk.W)
            type_lbl.pack(side=tk.LEFT, padx=5)
            
            # Column 1: Name and Address
            name_addr_text = f"{name} ({addr[:4]}...{addr[-4:]})"
            name_lbl = tk.Label(row_inner, text=name_addr_text, bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_COLOR, font=("Helvetica", 9, "bold"), anchor=tk.W)
            name_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            
            # Column 2: SOL Balance or Mint
            if addr_type == "user":
                bal_val = self.cached_balances.get(addr, 0.0)
                bal_text = f"{bal_val:,.2f} SOL"
            else:
                mint_val = info.get("mint", "N/A")
                bal_text = f"Mint: {mint_val[:4]}...{mint_val[-4:]}" if mint_val != "N/A" else "Token Account"
                
            bal_lbl = tk.Label(row_inner, text=bal_text, bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_MUTED, font=("Helvetica", 9), width=30, anchor=tk.W)
            bal_lbl.pack(side=tk.LEFT, padx=5)
            
            # Column 3: Telegram Alert Status Pill
            status_text = "Active"
            theme_mode = self.settings.get("theme", "System Sync")
            if theme_mode == "System Sync":
                theme_mode = self.detect_linux_theme()
            status_bg = "#dcfce7" if theme_mode == "Light Mode" else "#064e3b"
            status_fg = "#166534" if theme_mode == "Light Mode" else "#34d399"
            
            status_pill = tk.Label(row_inner, text=status_text, bg=status_bg, fg=status_fg, font=("Helvetica", 8, "bold"), padx=8, pady=2, bd=0, relief=tk.FLAT)
            status_pill.pack(side=tk.LEFT, padx=15)
            
            # Column 4: Actions (Copy / Delete)
            btn_frame = tk.Frame(row_inner, bg=gui_styles.BG_CARD)
            btn_frame.pack(side=tk.RIGHT, padx=5)
            
            copy_btn = ttk.Button(btn_frame, text="Copy", width=6, style="Gray.TButton", command=lambda a=addr: self.copy_address_to_clipboard(a))
            copy_btn.pack(side=tk.LEFT, padx=(0, 5))
            
            delete_btn = ttk.Button(btn_frame, text="Delete", width=8, style="Red.TButton", command=lambda a=addr: self.delete_address_from_dashboard(a))
            delete_btn.pack(side=tk.LEFT)

    def copy_address_to_clipboard(self, address):
        self.root.clipboard_clear()
        self.root.clipboard_append(address)
        self.root.update()
        messagebox.showinfo("Success", f"Copied to clipboard:\n{address}")

    def delete_address_from_dashboard(self, address):
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to remove this address?\n{address}"):
            chat_id_str = str(self.chat_id)
            if chat_id_str in self.state["chats"] and address in self.state["chats"][chat_id_str]["tracked"]:
                del self.state["chats"][chat_id_str]["tracked"][address]
                self.save_state()
                self.update_wallet_lists()
                self.refresh_dashboard_table()
                self.update_dashboard_metrics()
                messagebox.showinfo("Deleted", "Address removed successfully.")

    def apply_theme_and_fonts(self):
        self.root.configure(bg=gui_styles.BG_MAIN)
        font_size_pt = FONT_SIZES.get(self.settings.get("font_size", "Medium"), 10)
        normal_font = ("Helvetica", font_size_pt)
        console_font = ("Consolas", font_size_pt - 1 if font_size_pt > 8 else 8)
        
        self.apply_translations()
        
        theme_mode = self.settings.get("theme", "System Sync")
        if theme_mode == "System Sync":
            theme_mode = self.detect_linux_theme()
            
        def update_widget(w):
            widget_class = w.winfo_class()
            if widget_class == "Frame":
                curr_bg = w.cget("bg")
                if curr_bg in ["#121214", "#f4f4f5"]:
                    w.configure(bg=gui_styles.BG_MAIN)
                elif curr_bg in ["#1a1a1e", "#ffffff"]:
                    w.configure(bg=gui_styles.BG_CARD)
                else:
                    w.configure(bg=gui_styles.BG_MAIN)
            elif widget_class == "Listbox":
                w.configure(bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, selectbackground=gui_styles.ACCENT_BLUE, font=normal_font)
            elif widget_class == "Entry":
                w.configure(bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, font=normal_font)
            elif widget_class == "Text":
                if w == self.log_text:
                    w.configure(bg="#0d0d0f" if theme_mode == "Dark Mode" else "#f4f4f5", fg="#a9a9b3" if theme_mode == "Dark Mode" else "#27272a", insertbackground=gui_styles.TEXT_COLOR, font=console_font)
                else:
                    w.configure(bg="#0d0d0f" if theme_mode == "Dark Mode" else "#ffffff", fg=gui_styles.TEXT_MUTED, font=console_font)
            elif widget_class == "Checkbutton":
                w.configure(bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_COLOR, selectcolor=gui_styles.BG_MAIN, activebackground=gui_styles.BG_CARD, activeforeground=gui_styles.TEXT_COLOR, font=normal_font)
            elif widget_class == "Label":
                curr_bg = w.cget("bg")
                if curr_bg in ["#1a1a1e", "#ffffff"]:
                    w.configure(bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_COLOR, font=normal_font)
                else:
                    w.configure(bg=gui_styles.BG_MAIN, fg=gui_styles.TEXT_COLOR, font=normal_font)
            for child in w.winfo_children():
                update_widget(child)
        update_widget(self.root)

    def build_premium_rpc(self, provider):
        if provider == "helius":
            key = self.helius_var.get().strip()
            if key:
                self.qn_var.set("")
                self.rpc_url_var.set(f"https://mainnet.helius-rpc.com/?api-key={key}")
        elif provider == "quicknode":
            val = self.qn_var.get().strip()
            if val:
                self.helius_var.set("")
                if val.startswith("http"):
                    self.rpc_url_var.set(val)
                else:
                    self.rpc_url_var.set(f"https://api.solana-mainnet.quiknode.pro/{val}/")

    def apply_translations(self):
        if hasattr(self, "nav_buttons"):
            self.nav_buttons["dashboard"].config(text="📊  Dashboard")
            self.nav_buttons["wallets"].config(text="👛  " + self.tr("wallet_manager"))
            self.nav_buttons["settings"].config(text="⚙️  " + self.tr("settings_credentials"))
            self.nav_buttons["logs"].config(text="📋  " + self.tr("live_console"))
            self.nav_buttons["backup"].config(text="💾  " + self.tr("backup_license"))
        self.lbl_credentials_title.config(text=self.tr("connection_credentials"))
        self.lbl_tg_token.config(text=self.tr("telegram_token"))
        self.lbl_chat_id.config(text=self.tr("telegram_chat_id"))
        self.lbl_solana_rpc.config(text=self.tr("solana_rpc_url"))
        self.test_conn_btn.config(text=self.tr("test_connections"))
        self.save_conn_btn.config(text=self.tr("save_connection"))
        self.chat_id_hint.config(text=self.tr("hint_chat_id"))
        
        self.lbl_pref_title.config(text=self.tr("bot_preferences"))
        self.lbl_default_currency.config(text=self.tr("default_currency"))
        self.lbl_summary_interval.config(text=self.tr("summary_interval"))
        self.save_pref_btn.config(text=self.tr("save_preferences"))
        self.lbl_status_interval.config(text=self.tr("status_interval"))
        self.lbl_whale_threshold.config(text=self.tr("whale_threshold"))
        self.show_coin_link_check.config(text=self.tr("show_coin_link"))
        self.show_market_cap_check.config(text=self.tr("show_market_cap"))
        self.auto_start_check.config(text=self.tr("auto_start"))
        
        self.lbl_wallet_manager.config(text=self.tr("wallet_address_manager"))
        self.lbl_user_wallets.config(text=self.tr("user_wallets"))
        self.btn_add_user_wallet.config(text=self.tr("add_wallet"))
        self.btn_copy_user_wallet.config(text=self.tr("copy"))
        self.btn_remove_user_wallet.config(text=self.tr("remove"))
        self.lbl_token_accounts.config(text=self.tr("token_accounts"))
        self.btn_add_token_wallet.config(text=self.tr("add_token_account"))
        self.btn_copy_token_wallet.config(text=self.tr("copy"))
        self.btn_remove_token_wallet.config(text=self.tr("remove"))
        
        self.start_btn.config(text=self.tr("start_bot"))
        self.stop_btn.config(text=self.tr("stop_bot"))
        self.btn_clear_console.config(text=self.tr("clear_console"))
        self.btn_exit.config(text=self.tr("exit"))
        
        self.update_status_label()
        
        self.lbl_backup_restore.config(text=self.tr("backup_restore"))
        self.btn_export.config(text=self.tr("export_list"))
        self.btn_import.config(text=self.tr("import_list"))
        self.lbl_about_license.config(text=self.tr("about_license"))
        
        self.lbl_ui_title.config(text=self.tr("ui_settings_title"))
        self.lbl_lang.config(text=self.tr("language"))
        self.lbl_font_size.config(text=self.tr("font_size"))
        self.lbl_theme.config(text=self.tr("theme"))
        self.btn_save_settings.config(text=self.tr("save_settings"))
        
        if self.token_entry.cget("show") == "*":
            self.show_token_btn.config(text=self.tr("show"))
        else:
            self.show_token_btn.config(text=self.tr("hide"))
            
        if self.chat_id_entry.cget("show") == "*":
            self.show_chat_id_btn.config(text=self.tr("show"))
        else:
            self.show_chat_id_btn.config(text=self.tr("hide"))

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
            lock_path = STATE_PATH + ".lock"
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
                with open(STATE_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                pass
            finally:
                try:
                    os.rmdir(lock_path)
                except Exception:
                    pass
        return {"chats": {}, "global_last_signatures": {}}

    def save_state(self):
        os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
        lock_path = STATE_PATH + ".lock"
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
            fresh_state = {"chats": {}, "global_last_signatures": {}}
            if os.path.exists(STATE_PATH):
                try:
                    with open(STATE_PATH, "r") as f:
                        fresh_state = json.load(f)
                except Exception:
                    pass
            fresh_state["chats"] = self.state.get("chats", {})
            fresh_state["settings"] = self.settings
            self.state = fresh_state
            
            with open(STATE_PATH, "w") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            messagebox.showerror(self.tr("save_error"), self.tr("failed_save_state").format(error=e))
        finally:
            try:
                os.rmdir(lock_path)
            except Exception:
                pass

    def get_chat_pref(self, key, default):
        if not self.chat_id:
            return default
        chat_id_str = str(self.chat_id)
        chat_data = self.state.get("chats", {}).get(chat_id_str, {})
        return chat_data.get(key, default)

    def toggle_token_visibility(self):
        if self.token_entry.cget("show") == "*":
            self.token_entry.config(show="")
            self.show_token_btn.config(text=self.tr("hide"))
        else:
            self.token_entry.config(show="*")
            self.show_token_btn.config(text=self.tr("show"))

    def toggle_chat_id_visibility(self):
        if self.chat_id_entry.cget("show") == "*":
            self.chat_id_entry.config(show="")
            self.show_chat_id_btn.config(text=self.tr("hide"))
        else:
            self.chat_id_entry.config(show="*")
            self.show_chat_id_btn.config(text=self.tr("show"))

    def test_connections(self):
        token = self.token_var.get().replace('\r', '').replace('\n', '').strip()
        chat_id = self.chat_id_var.get().replace('\r', '').replace('\n', '').strip()
        rpc_url = self.rpc_url_var.get().replace('\r', '').replace('\n', '').strip()
        
        if not token:
            messagebox.showwarning(self.tr("test_error"), self.tr("token_required"))
            return
            
        self.test_conn_btn.config(state=tk.DISABLED, text=self.tr("testing"))
        
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
                results.append(f"🟢 Solana RPC: Connected successfully ({latency_ms}ms).")
            else:
                success = False
                err_str = "; ".join(rpc_errors)
                results.append(f"🔴 Solana RPC: Failed ({err_str})")
                
            # 2. Test Telegram Bot Token
            tg_token_ok = False
            try:
                response = requests.get(f"https://api.telegram.org/bot{token}/getMe", timeout=5)
                if response.status_code == 200:
                    res_json = response.json()
                    if res_json.get("ok"):
                        tg_token_ok = True
                        results.append("🟢 Telegram Bot Token: Valid.")
                    else:
                        results.append("🔴 Telegram Bot Token: Invalid response from API.")
            except Exception as e:
                results.append(f"🔴 Telegram Bot Token: Failed ({str(e)})")
                
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
                                results.append("🟢 Telegram Chat ID: Valid (Test message delivered).")
                            else:
                                success = False
                                results.append(f"🔴 Telegram Chat ID: Failed to send message ({res_json.get('description')})")
                        else:
                            success = False
                            results.append(f"🔴 Telegram Chat ID: HTTP {response.status_code} ({response.text})")
                    except Exception as e:
                        success = False
                        results.append(f"🔴 Telegram Chat ID: Failed ({str(e)})")
                else:
                    success = False
                    results.append("🔴 Telegram Chat ID: Cannot test (invalid bot token).")
            else:
                results.append("ℹ️ Telegram Chat ID: Empty (skipped test).")
                
            # Invoke callback on main thread
            self.root.after(0, lambda: self.show_test_results(success, results))
            
        threading.Thread(target=run_test, daemon=True).start()

    def show_test_results(self, success, results):
        self.test_conn_btn.config(state=tk.NORMAL, text=self.tr("test_connections"))
        message_str = "\n".join(results)
        if success:
            messagebox.showinfo(self.tr("conn_test_success"), message_str)
        else:
            messagebox.showerror(self.tr("conn_test_failure"), message_str)

    def save_connections(self):
        token = self.token_var.get().replace('\r', '').replace('\n', '').strip()
        chat_id = self.chat_id_var.get().replace('\r', '').replace('\n', '').strip()
        rpc_url = self.rpc_url_var.get().replace('\r', '').replace('\n', '').strip()
        
        if not token:
            messagebox.showwarning(self.tr("validation_error"), self.tr("token_empty"))
            return
            
        # Validate Telegram Bot Token format
        if not re.match(r"^\d+:[A-Za-z0-9_-]{35,}$", token):
            if not messagebox.askyesno(self.tr("token_warning_title"), self.tr("token_warning_msg")):
                return
                
        # Validate Telegram Chat ID format
        if chat_id and not re.match(r"^-?\d+$", chat_id):
            messagebox.showerror(self.tr("validation_error"), self.tr("chat_id_numeric"))
            return
            
        # Validate Solana RPC URLs
        urls = [u.strip() for u in rpc_url.split(",")]
        for url in urls:
            if not (url.startswith("http://") or url.startswith("https://")):
                messagebox.showerror(self.tr("validation_error"), self.tr("rpc_invalid").format(url=url))
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
                        "last_summary_time": time.time(),
                        "last_status_time": 0.0,
                        "status_txs": [],
                        "tracked": {},
                        "accumulated_txs": []
                    }
                else:
                    self.state["chats"][chat_id_str]["active"] = True
                self.save_state()
            
            self.update_wallet_lists()
            messagebox.showinfo(self.tr("success"), self.tr("success_conn"))
        except Exception as e:
            messagebox.showerror(self.tr("error"), self.tr("failed_save_env").format(error=e))

    def save_preferences(self):
        if not self.chat_id:
            messagebox.showwarning(self.tr("config_error"), self.tr("chat_id_required"))
            return
            
        curr = self.currency_var.get()
        
        try:
            intv = int(self.interval_var.get())
            if intv < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror(self.tr("validation_error"), self.tr("summary_interval_pos"))
            return
            
        try:
            s_intv = int(self.status_interval_var.get())
            if s_intv < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror(self.tr("validation_error"), self.tr("status_interval_pos"))
            return
            
        try:
            w_thresh = float(self.whale_threshold_var.get())
            if w_thresh <= 0.0:
                raise ValueError()
        except ValueError:
            messagebox.showerror(self.tr("validation_error"), self.tr("whale_threshold_pos"))
            return
            
        daily_enabled = self.daily_summary_enabled_var.get()
        daily_time = self.daily_summary_time_var.get().strip()
        if daily_enabled and not re.match(r"^\d{2}:\d{2}$", daily_time):
            messagebox.showerror(self.tr("validation_error"), "Daily Snapshot Time must be in HH:MM format (e.g. 00:00).")
            return
            
        try:
            noise_thresh = float(self.noise_threshold_var.get())
            if noise_thresh < 0.0:
                raise ValueError()
        except ValueError:
            messagebox.showerror(self.tr("validation_error"), "Noise Threshold must be a non-negative number.")
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
            messagebox.showerror(self.tr("error"), self.tr("failed_save_env").format(error=e))
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
                "daily_summary_enabled": False,
                "daily_summary_time": "00:00",
                "noise_threshold": 0.0,
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
        self.state["chats"][chat_id_str]["daily_summary_enabled"] = daily_enabled
        self.state["chats"][chat_id_str]["daily_summary_time"] = daily_time
        self.state["chats"][chat_id_str]["noise_threshold"] = noise_thresh
        
        self.save_state()
        messagebox.showinfo(self.tr("success"), self.tr("success_pref"))

    def update_wallet_lists(self):
        self.user_listbox.delete(0, tk.END)
        self.token_listbox.delete(0, tk.END)
        
        if not self.chat_id:
            return
            
        chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
        tracked = chat_data.get("tracked", {})
        
        self.user_wallets_map = []
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
        self.update_dashboard_metrics()

    def identify_address_on_chain(self, address_str):
        try:
            if not self.rpc_url:
                return "UNKNOWN"
            url = [u.strip() for u in self.rpc_url.split(",")][0]
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [address_str, {"encoding": "jsonParsed"}]
            }
            r = requests.post(url, json=payload, timeout=5)
            if r.status_code == 200:
                res = r.json()
                if res and res.get("result") and res["result"].get("value"):
                    val = res["result"]["value"]
                    owner = val.get("owner")
                    if owner == "11111111111111111111111111111111":
                        return "WALLET"
                    elif owner in ("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "TokenzQdBNbkh56NSs27s376uaR659755iy3Bbz6n26"):
                        return "TOKEN"
                    else:
                        return "OTHER"
            return "WALLET"
        except Exception:
            return "UNKNOWN"

    def add_address(self, addr_type):
        if not self.chat_id:
            messagebox.showwarning(self.tr("config_error"), self.tr("chat_id_required"))
            return
            
        dialog = CustomAddAddressDialog(self.root, addr_type, tr=self.tr)
        self.root.wait_window(dialog)
        
        if not dialog.result:
            return
            
        address, name = dialog.result
        
        detected = self.identify_address_on_chain(address)
        if addr_type == "user" and detected == "TOKEN":
            if not messagebox.askyesno("Mismatch Detected", f"Address {address[:8]}... appears to be a Token Account on-chain, not a User Wallet.\n\nDo you want to add it as a Specific Token Account instead?"):
                return
            addr_type = "token"
        elif addr_type == "token" and detected == "WALLET":
            if not messagebox.askyesno("Mismatch Detected", f"Address {address[:8]}... appears to be a User Wallet on-chain, not a Token Account.\n\nDo you want to add it as a User Wallet instead?"):
                return
            addr_type = "user"
        elif detected == "OTHER":
            messagebox.showerror("Error", f"Address {address[:8]}... appears to be owned by a custom program contract and cannot be tracked as a wallet/token account.")
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
            
        if "tracked" not in self.state["chats"][chat_id_str]:
            self.state["chats"][chat_id_str]["tracked"] = {}
            
        self.state["chats"][chat_id_str]["tracked"][address] = {
            "name": name,
            "type": addr_type
        }
        
        self.save_state()
        self.update_wallet_lists()
        self.wallet_status_lbl.config(text=self.tr("add_user_wallet_success").format(name=name), foreground=gui_styles.ACCENT_GREEN)

    def add_user_wallet(self):
        self.add_address("user")

    def add_token_wallet(self):
        self.add_address("token")

    def remove_address(self, listbox, wallets_map, label):
        if not self.chat_id:
            return
        idx = listbox.curselection()
        if not idx:
            messagebox.showwarning(self.tr("selection_error"), self.tr("wallet_required"))
            return
            
        address = wallets_map[idx[0]]
        chat_id_str = str(self.chat_id)
        chat_data = self.state.get("chats", {}).get(chat_id_str, {})
        name = chat_data.get("tracked", {}).get(address, {}).get("name", "Unnamed")
        
        if not messagebox.askyesno(self.tr("wallet_confirm_title"), self.tr("wallet_confirm_msg").format(name=name)):
            return
            
        if chat_id_str in self.state["chats"] and "tracked" in self.state["chats"][chat_id_str]:
            if address in self.state["chats"][chat_id_str]["tracked"]:
                del self.state["chats"][chat_id_str]["tracked"][address]
                self.save_state()
                
        self.update_wallet_lists()
        label.config(text=self.tr("remove_wallet_success").format(name=name), foreground=gui_styles.ACCENT_RED)

    def remove_user_wallet(self):
        self.remove_address(self.user_listbox, self.user_wallets_map, self.wallet_status_lbl)

    def remove_token_wallet(self):
        self.remove_address(self.token_listbox, self.token_wallets_map, self.wallet_status_lbl)

    def copy_selected_address(self, listbox, wallets_map):
        idx = listbox.curselection()
        if not idx:
            return
        address = wallets_map[idx[0]]
        self.root.clipboard_clear()
        self.root.clipboard_append(address)
        self.wallet_status_lbl.config(text=self.tr("copied"), foreground=gui_styles.ACCENT_BLUE)

    def clear_log_display(self):
        try:
            if os.path.exists(LOG_PATH):
                with open(LOG_PATH, "w") as f:
                    f.write("")
        except Exception as e:
            print(f"Failed to clear log file: {e}")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def export_config(self):
        if not self.chat_id:
            messagebox.showwarning(self.tr("config_error"), self.tr("chat_id_required"))
            return
        chat_id_str = str(self.chat_id)
        chat_data = self.state.get("chats", {}).get(chat_id_str, {})
        if not chat_data.get("tracked"):
            messagebox.showwarning(self.tr("export_warning"), self.tr("no_tracked_addresses"))
            return
            
        export_data = {
            "chats": {
                chat_id_str: chat_data
            },
            "global_last_signatures": self.state.get("global_last_signatures", {})
        }
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All Files", "*.*")]
        )
        if not filename:
            return
            
        try:
            with open(filename, "w") as f:
                json.dump(export_data, f, indent=4)
            messagebox.showinfo(self.tr("success"), self.tr("success_export") + os.path.basename(filename))
        except Exception as e:
            messagebox.showerror(self.tr("error"), self.tr("export_failed").format(error=e))

    def import_config(self):
        filename = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All Files", "*.*")]
        )
        if not filename:
            return
            
        try:
            with open(filename, "r") as f:
                imported_data = json.load(f)
                
            if not isinstance(imported_data, dict) or "chats" not in imported_data:
                messagebox.showerror(self.tr("error"), self.tr("import_schema_error"))
                return
                
            if not messagebox.askyesno(self.tr("import_confirm_title"), self.tr("import_confirm_msg")):
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
            messagebox.showinfo(self.tr("success"), self.tr("success_import"))
        except Exception as e:
            messagebox.showerror(self.tr("error"), self.tr("import_failed").format(error=e))

    def read_log_tail(self):
        if not os.path.exists(LOG_PATH):
            return []
        try:
            file_size = os.path.getsize(LOG_PATH)
            chunk_size = 8192
            with open(LOG_PATH, "rb") as f:
                if file_size > chunk_size:
                    f.seek(file_size - chunk_size)
                    content_bytes = f.read()
                    content = content_bytes.decode("utf-8", errors="replace")
                    lines = content.splitlines()
                    if len(lines) > 1:
                        return lines[1:]
                    return lines
                else:
                    content_bytes = f.read()
                    content = content_bytes.decode("utf-8", errors="replace")
                    return content.splitlines()
        except Exception as e:
            return [f"Error reading logs: {e}"]

    def refresh_logs(self):
        if not self.logs_visible:
            return
            
        filter_level = self.log_filter_var.get().upper()
        raw_lines = self.read_log_tail()
        
        filtered_lines = []
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            
            level = "ALL"
            if " - INFO - " in line:
                level = "INFO"
            elif " - WARNING - " in line:
                level = "WARNING"
            elif " - ERROR - " in line or " - CRITICAL - " in line:
                level = "ERROR"
            
            if filter_level == "ALL" or filter_level == level:
                filtered_lines.append((line, level.lower() if level != "ALL" else None))
                
        tail = filtered_lines[-40:]
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        for line_str, tag in tail:
            self.log_text.insert(tk.END, line_str + "\n", tag)
            
        self.log_text.config(state=tk.DISABLED)
        if self.log_autoscroll_var.get():
            self.log_text.see(tk.END)

        if hasattr(self, "dash_log_text"):
            self.dash_log_text.config(state=tk.NORMAL)
            self.dash_log_text.delete("1.0", tk.END)
            for line_str, tag in tail[-10:]:
                self.dash_log_text.insert(tk.END, line_str + "\n", tag)
            self.dash_log_text.config(state=tk.DISABLED)
            self.dash_log_text.see(tk.END)
        
        # Schedule next log refresh in 2 seconds
        if self.logs_visible:
            self.root.after(2000, self.refresh_logs)

    # Process Management
    def start_bot(self):
        if self.tracker_process and self.tracker_process.poll() is None:
            messagebox.showwarning(self.tr("process_error"), self.tr("process_running"))
            return
            
        if not self.token:
            messagebox.showwarning(self.tr("config_error"), self.tr("token_save_first"))
            return
            
        self.should_be_running = True
        try:
            if getattr(sys, 'frozen', False):
                exe_name = "tracker.exe" if sys.platform == "win32" else "tracker"
                tracker_path = os.path.join(BASE_DIR, exe_name)
                if not os.path.exists(tracker_path):
                    tracker_path = os.path.join(os.path.dirname(sys.executable), exe_name)
                self.tracker_process = subprocess.Popen(
                    [tracker_path],
                    cwd=BASE_DIR,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
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
            self.update_status_label()
            logger_msg = "Tracker process launched."
            print(logger_msg)
        except Exception as e:
            messagebox.showerror(self.tr("execution_error"), self.tr("launch_failed").format(error=e))

    def stop_bot(self):
        self.should_be_running = False
        if self.tracker_process and self.tracker_process.poll() is None:
            self.tracker_process.terminate()
            self.tracker_process.wait()
            self.tracker_process = None
            
        self.bot_start_time = None
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.update_status_label()

    def check_process(self):
        if self.tracker_process:
            status = self.tracker_process.poll()
            if status is not None: # Stopped unexpectedly
                self.tracker_process = None
                self.bot_start_time = None
                self.start_btn.config(state=tk.NORMAL)
                self.stop_btn.config(state=tk.DISABLED)
                if self.should_be_running:
                    print("Watchdog: Tracker process stopped unexpectedly. Restarting...")
                    self.start_bot()
        else:
            if self.should_be_running:
                print("Watchdog: Tracker process not running but should be. Starting...")
                self.start_bot()
        self.update_status_label()
        self.root.after(1000, self.check_process)

    def update_status_label(self):
        if self.tracker_process and self.tracker_process.poll() is None:
            uptime = int(time.time() - (self.bot_start_time or time.time()))
            h = uptime // 3600
            m = (uptime % 3600) // 60
            s = uptime % 60
            uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
            
            if not hasattr(self, "pulse_state"):
                self.pulse_state = True
            self.pulse_state = not self.pulse_state
            dot_color = gui_styles.ACCENT_GREEN if self.pulse_state else ("#059669" if self.settings.get("theme") == "Light Mode" else "#047857")
            
            running_text = self.tr("status_running").format(uptime=uptime_str)
            self.status_lbl.config(text=running_text, foreground=dot_color)
            if hasattr(self, "dash_status_val"):
                self.dash_status_val.config(text=f"Active ({uptime_str})", foreground=gui_styles.ACCENT_GREEN)
        else:
            self.status_lbl.config(text=self.tr("status_stopped"), foreground=gui_styles.ACCENT_RED)
            if hasattr(self, "dash_status_val"):
                self.dash_status_val.config(text="Stopped", foreground=gui_styles.ACCENT_RED)

    def clean_exit(self, icon=None, item=None):
        if hasattr(self, "tray_icon") and self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.stop_bot()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfiguratorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.clean_exit)
    root.mainloop()
