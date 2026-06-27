import os
import sys
import time
import json
import re
import subprocess
import threading
import requests
import flet as ft

# Directory and Path Resolutions
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    
ENV_PATH = os.path.join(BASE_DIR, "secrets", ".env")
STATE_PATH = os.path.join(BASE_DIR, "secrets", "tracked.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "tracker.log")

# Font Sizes mapping
FONT_SIZES = {
    "Small": 12,
    "Medium": 14,
    "Large": 16
}

# Translations Dictionary
TRANSLATIONS = {
    "English": {
        "title": "Solana Telegram Tracker Configurator",
        "success": "Success",
        "error": "Error",
        "settings_credentials": "Credentials & Preferences",
        "wallet_manager": "Wallet Manager",
        "live_console": "Live Console & Logs",
        "backup_license": "Backup & License",
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
        "auto_start": "Auto-start Tracker Bot on launch",
        "wallet_address_manager": "Wallet Address Manager",
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
        "success_export": "Configuration successfully exported.",
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
        "token_warning_msg": "The Telegram Bot Token format looks unusual. Are you sure you want to save it?",
        "chat_id_numeric": "Telegram Chat ID must be a numeric value.",
        "rpc_invalid": "Invalid RPC URL. Must start with http:// or https://",
        "summary_interval_pos": "Summary Interval must be a positive integer.",
        "status_interval_pos": "Status Interval must be a positive integer.",
        "whale_threshold_pos": "Whale Threshold must be a positive number.",
        "import_confirm_title": "Confirm Import",
        "import_confirm_msg": "This will merge/overwrite your current tracked configuration with the backup file. Proceed?",
        "import_schema_error": "Invalid backup file schema: missing 'chats' object.",
        "wallet_required": "Please select a wallet address to remove.",
        "wallet_confirm_title": "Confirm Removal",
        "wallet_confirm_msg": "Are you sure you want to remove this tracking configuration?",
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
        "settings_credentials": "Настройки и Данные",
        "wallet_manager": "Менеджер Кошельков",
        "live_console": "Консоль и Логи",
        "backup_license": "Бэкап и Лицензия",
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
        "success_export": "Конфигурация успешно экспортирована.",
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
        "token_warning_msg": "Формат токена Telegram бота выглядит необычно. Сохранить?",
        "chat_id_numeric": "Chat ID Telegram должен быть числовым.",
        "rpc_invalid": "Недопустимый RPC URL. Должен начинаться с http:// или https://",
        "summary_interval_pos": "Интервал сводок должен быть положительным целым числом.",
        "status_interval_pos": "Интервал статуса должен быть положительным целым числом.",
        "whale_threshold_pos": "Порог китов должен быть положительным числом.",
        "import_confirm_title": "Подтвердить импорт",
        "import_confirm_msg": "Это объединит/перезапишет вашу текущую конфигурацию с файлом бэкапа. Продолжить?",
        "import_schema_error": "Неверная схема файла бэкапа: отсутствует объект 'chats'.",
        "wallet_required": "Выберите кошелек для удаления.",
        "wallet_confirm_title": "Подтвердить удаление",
        "wallet_confirm_msg": "Вы уверены, что хотите прекратить отслеживание кошелька?",
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
        "settings_credentials": "الإعدادات والاعتمادات",
        "wallet_manager": "مدير المحفظة",
        "live_console": "وحدة التحكم والسجلات",
        "backup_license": "النسخ الاحتياطي والترخيص",
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
        "success_export": "تم تصدير التكوين بنجاح.",
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
        "token_warning_msg": "يبدو تنسيق رمز تليجرام البوت غير عادي. هل تريد حفظه؟",
        "chat_id_numeric": "يجب أن يكون معرف دردشة تليجرام قيمة رقمية.",
        "rpc_invalid": "رابط RPC غير صالح. يجب أن يبدأ بـ http:// أو https://",
        "summary_interval_pos": "يجب أن يكون فاصل الملخص عددًا صحيحًا موجبًا.",
        "status_interval_pos": "يجب أن يكون فاصل الحالة عددًا صحيحًا موجبًا.",
        "whale_threshold_pos": "يجب أن يكون حد الحوت رقمًا موجبًا.",
        "import_confirm_title": "تأكيد الاستيراد",
        "import_confirm_msg": "سيؤدي هذا إلى دمج/كتابة التكوين الحالي فوقه بملف النسخ الاحتياطي. هل تريد المتابعة؟",
        "import_schema_error": "مخطط ملف نسخ احتياطي غير صالح: مفقود كائن 'chats'.",
        "wallet_required": "يرجى تحديد عنوان المحفظة لإزالته.",
        "wallet_confirm_title": "تأكيد الإزالة",
        "wallet_confirm_msg": "هل أنت متأكد أنك تريد إزالة تكوين التتبع؟",
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

class FletConfiguratorApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "Solana Telegram Tracker Configurator"
        self.page.window.width = 980
        self.page.window.height = 720
        self.page.window.min_width = 800
        self.page.window.min_height = 600
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#121214"
        
        # State variables
        self.tracker_process = None
        self.should_be_running = False
        self.bot_start_time = None
        self.cached_balances = {}
        self.logs_visible = False
        
        # Load env & database state
        self.token, self.chat_id, self.rpc_url, self.auto_start = self.load_env_values()
        self.state = self.load_state_values()
        
        # Kill any orphaned tracker processes still running from previous sessions
        self.kill_all_tracker_processes()
        
        self.settings = self.state.setdefault("settings", {
            "language": "English",
            "font_size": "Medium",
            "theme": "System Sync"
        })
        
        # Apply theme settings
        self.apply_theme_settings()
        
        # Build UI Structure
        self.build_ui()
        
        # Start Threads
        self.check_process_loop()
        self.load_balances_async()
        
        # Auto-start bot on launch
        if self.auto_start == "true":
            if self.chat_id:
                chat_id_str = str(self.chat_id)
                if "chats" in self.state and chat_id_str in self.state["chats"]:
                    self.state["chats"][chat_id_str]["active"] = True
                    self.save_state()
            self.start_bot()

    def tr(self, key):
        lang = self.settings.get("language", "English")
        return TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, TRANSLATIONS["English"].get(key, ""))

    def apply_theme_settings(self):
        theme_mode = self.settings.get("theme", "System Sync")
        if theme_mode == "System Sync":
            theme_mode = self.detect_linux_theme()
            
        if theme_mode == "Light Mode":
            self.page.theme_mode = ft.ThemeMode.LIGHT
            self.page.bgcolor = "#f4f4f5"
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
            self.page.bgcolor = "#121214"
            
        font_size_pt = FONT_SIZES.get(self.settings.get("font_size", "Medium"), 14)
        # Apply page-wide default text style
        self.page.theme = ft.Theme(
            text_theme=ft.TextTheme(
                body_medium=ft.TextStyle(size=font_size_pt)
            )
        )

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
        return "Light Mode"

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
            except Exception:
                pass
        return token, chat_id, rpc_url, auto_start

    def save_env_values(self):
        os.makedirs(os.path.dirname(ENV_PATH), exist_ok=True)
        try:
            with open(ENV_PATH, "w") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={self.token}\n")
                f.write(f"TELEGRAM_CHAT_ID={self.chat_id}\n")
                f.write(f"SOLANA_RPC_URL={self.rpc_url}\n")
                f.write(f"AUTO_START_BOT={self.auto_start}\n")
            return True
        except Exception as e:
            self.show_popup("Error", f"Failed to save environment variables: {e}")
            return False

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
                json.dump(self.state, f, indent=4)
        except Exception as e:
            self.show_popup("Error", f"Failed to save tracked.json state: {e}")

    def show_popup(self, title, message):
        def close_dialog(e):
            dialog.open = False
            self.page.update()
            
        dialog = ft.AlertDialog(
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Text(message),
            actions=[ft.TextButton(self.tr("ok"), on_click=close_dialog)],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def build_ui(self):
        # 1. Left Sidebar Navigation Panel
        sidebar_color = "#1a1a1e" if self.page.theme_mode == ft.ThemeMode.DARK else "#ffffff"
        
        # Sidebar Header / Brand Logo
        sidebar_header = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color="#10b981", size=22),
                ft.Text("Solana Tracker", size=16, weight=ft.FontWeight.BOLD, color="#e1e1e6" if self.page.theme_mode == ft.ThemeMode.DARK else "#18181b")
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.Padding(0, 30, 0, 30),
            bgcolor=sidebar_color
        )
        
        # Sidebar Menu Items
        self.nav_items = {
            "dashboard": ft.Container(content=ft.Text("📊  Dashboard", weight=ft.FontWeight.BOLD), padding=12, border_radius=8, on_click=lambda e: self.navigate_to("dashboard")),
            "wallets": ft.Container(content=ft.Text("👛  " + self.tr("wallet_manager"), weight=ft.FontWeight.BOLD), padding=12, border_radius=8, on_click=lambda e: self.navigate_to("wallets")),
            "settings": ft.Container(content=ft.Text("⚙️  " + self.tr("settings_credentials"), weight=ft.FontWeight.BOLD), padding=12, border_radius=8, on_click=lambda e: self.navigate_to("settings")),
            "logs": ft.Container(content=ft.Text("📋  " + self.tr("live_console"), weight=ft.FontWeight.BOLD), padding=12, border_radius=8, on_click=lambda e: self.navigate_to("logs")),
            "backup": ft.Container(content=ft.Text("💾  " + self.tr("backup_license"), weight=ft.FontWeight.BOLD), padding=12, border_radius=8, on_click=lambda e: self.navigate_to("backup")),
        }
        
        menu_column = ft.Column(
            [self.nav_items[k] for k in self.nav_items],
            spacing=5
        )
        
        sidebar_footer = ft.Container(
            content=ft.Text("v1.4.0 • Release", size=10, color="#8d8d99"),
            alignment=ft.Alignment(0, 0),
            padding=ft.Padding(0, 20, 0, 20)
        )
        
        self.sidebar = ft.Container(
            content=ft.Column([
                sidebar_header,
                ft.Container(content=menu_column, padding=10),
                sidebar_footer
            ]),
            width=220,
            bgcolor=sidebar_color,
            border=ft.Border(right=ft.BorderSide(1, "#29292e"))
        )
        
        # 2. Page Content Containers
        self.page_views = {
            "dashboard": self.build_dashboard_view(),
            "wallets": self.build_wallets_view(),
            "settings": self.build_settings_view(),
            "logs": self.build_logs_view(),
            "backup": self.build_backup_view(),
        }
        
        self.active_title = ft.Text("Dashboard Overview", size=20, weight=ft.FontWeight.BOLD, color="#10b981")
        self.content_area = ft.Container(
            content=self.page_views["dashboard"],
            expand=True,
            padding=20,
        )
        
        right_panel = ft.Column([
            ft.Container(content=self.active_title, padding=ft.Padding(0, 0, 0, 15)),
            self.content_area
        ], expand=True)
        
        # Root layout structure
        self.page.add(
            ft.Row([
                self.sidebar,
                right_panel
            ], expand=True, spacing=0, vertical_alignment="stretch")
        )
        
        # Default Highlight
        self.navigate_to("dashboard")

    def navigate_to(self, target_name):
        self.logs_visible = (target_name == "logs")
        
        # Clean highlight states
        for name, item in self.nav_items.items():
            if name == target_name:
                item.bgcolor = "#1c1c1f" if self.page.theme_mode == ft.ThemeMode.DARK else "#e4e4e7"
                item.content.color = "#10b981"
            else:
                item.bgcolor = "transparent"
                item.content.color = "#8d8d99"
                
        # Switch Active views
        self.content_area.content = self.page_views[target_name]
        
        title_map = {
            "dashboard": "Dashboard Overview",
            "wallets": "Tracked Wallets & Token Accounts",
            "settings": "Settings & Credentials",
            "logs": "Live Console Logs Feed",
            "backup": "Backup & System Settings"
        }
        self.active_title.value = title_map[target_name]
        
        # Update metric counts dynamically
        self.update_metrics_values()
        
        self.page.update()

    def update_metrics_values(self):
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
                    
        if hasattr(self, "val_wallets"):
            self.val_wallets.value = str(w_count)
        if hasattr(self, "val_tokens"):
            self.val_tokens.value = str(t_count)

    # PAGE VIEWS GENERATION
    def build_dashboard_view(self):
        card_bg = "#1a1a1e" if self.page.theme_mode == ft.ThemeMode.DARK else "#ffffff"
        text_color = "#e1e1e6" if self.page.theme_mode == ft.ThemeMode.DARK else "#18181b"
        
        # KPI 1: Wallets
        self.val_wallets = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#10b981")
        kpi_wallets = ft.Container(
            content=ft.Column([
                ft.Text("Total Wallets Tracked", color="#8d8d99", size=12),
                self.val_wallets
            ], spacing=5),
            bgcolor=card_bg, padding=15, border_radius=10, expand=True,
            border=ft.Border.all(width=1, color="#29292e")
        )
        
        # KPI 2: Active Alert Channel
        self.val_channels = ft.Text("1 Connected", size=24, weight=ft.FontWeight.BOLD, color="#3b82f6")
        kpi_channels = ft.Container(
            content=ft.Column([
                ft.Text("Active Alert Channels", color="#8d8d99", size=12),
                self.val_channels
            ], spacing=5),
            bgcolor=card_bg, padding=15, border_radius=10, expand=True,
            border=ft.Border.all(width=1, color="#29292e")
        )
        
        # KPI 3: Total SOL Balance
        self.val_sol = ft.Text("0.00 SOL", size=24, weight=ft.FontWeight.BOLD, color="#e1e1e6")
        kpi_sol = ft.Container(
            content=ft.Column([
                ft.Text("Total Solana Balance", color="#8d8d99", size=12),
                self.val_sol
            ], spacing=5),
            bgcolor=card_bg, padding=15, border_radius=10, expand=True,
            border=ft.Border.all(width=1, color="#29292e")
        )
        
        # KPI 4: Token watch count
        self.val_tokens = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#e1e1e6")
        kpi_tokens = ft.Container(
            content=ft.Column([
                ft.Text("Tracked Token Accounts", color="#8d8d99", size=12),
                self.val_tokens
            ], spacing=5),
            bgcolor=card_bg, padding=15, border_radius=10, expand=True,
            border=ft.Border.all(width=1, color="#29292e")
        )
        
        kpi_row = ft.Row([kpi_wallets, kpi_channels, kpi_sol, kpi_tokens], spacing=10)
        
        headers_row = ft.Container(
            content=ft.Row([
                ft.Text("#", color="#8d8d99", size=11, weight=ft.FontWeight.BOLD, width=30),
                ft.Text("", color="#8d8d99", size=11, weight=ft.FontWeight.BOLD, width=40),
                ft.Text("Type", color="#8d8d99", size=11, weight=ft.FontWeight.BOLD, width=80),
                ft.Text("Wallet/Token", color="#8d8d99", size=11, weight=ft.FontWeight.BOLD, expand=True),
                ft.Text("Balance / Mint", color="#8d8d99", size=11, weight=ft.FontWeight.BOLD, width=180),
                ft.Text("Status", color="#8d8d99", size=11, weight=ft.FontWeight.BOLD, width=100),
                ft.Text("Actions", color="#8d8d99", size=11, weight=ft.FontWeight.BOLD, width=100, text_align=ft.TextAlign.RIGHT)
            ]),
            padding=ft.Padding(10, 0, 10, 0)
        )
        
        # Table List View
        self.dashboard_list = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Controls Bar
        controls_row = ft.Container(
            content=ft.Row([
                ft.Text("Tracked Watchlist", size=15, weight=ft.FontWeight.BOLD, color=text_color),
                ft.Row([
                    ft.ElevatedButton("+ Add New Wallet", bgcolor="#10b981", color="#ffffff", on_click=self.open_add_dialog),
                    ft.IconButton(icon=ft.Icons.REFRESH, icon_color="#3b82f6", on_click=lambda e: self.load_balances_async())
                ])
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(0, 0, 0, 10)
        )
        
        table_card = ft.Container(
            content=ft.Column([
                controls_row,
                headers_row,
                ft.Divider(color="#29292e"),
                self.dashboard_list
            ], expand=True),
            bgcolor=card_bg,
            padding=15,
            border_radius=12,
            border=ft.Border.all(width=1, color="#29292e"),
            expand=True
        )
        
        return ft.Column([kpi_row, table_card], expand=True, spacing=15)

    def refresh_dashboard_table(self):
        self.dashboard_list.controls.clear()
        
        if not self.chat_id:
            self.page.update()
            return
            
        chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
        tracked = chat_data.get("tracked", {})
        
        idx = 1
        for addr, info in tracked.items():
            name = info.get("name", "Unnamed")
            addr_type = info.get("type", "user")
            
            # 1. Type label
            type_text = "SOL" if addr_type == "user" else "Token"
            type_color = "#3b82f6" if addr_type == "user" else "#10b981"
            
            # 2. Icon Avatar (Wallet vs Whale vs Token Logo)
            if addr_type == "user":
                bal_val = self.cached_balances.get(addr, 0.0)
                is_whale = bal_val >= 100.0
                icon_obj = ft.Icons.WAVES if is_whale else ft.Icons.ACCOUNT_BALANCE_WALLET
                icon_color = "#3b82f6" if is_whale else "#10b981"
                bg_color = "#1d3557" if is_whale else "#132d24"
                avatar = ft.Container(
                    content=ft.Icon(icon_obj, color=icon_color, size=14),
                    width=24,
                    height=24,
                    border_radius=12,
                    bgcolor=bg_color,
                    alignment=ft.Alignment(0, 0)
                )
            else:
                mint = info.get("mint", "So11111111111111111111111111111111111111112")
                logo_url = f"https://token.jup.ag/img/by-mint/{mint}"
                avatar = ft.Container(
                    content=ft.Image(
                        src=logo_url,
                        width=20,
                        height=20,
                        fit="contain",
                        error_content=ft.Icon(ft.Icons.LOCAL_OFFER, color="#10b981", size=14)
                    ),
                    width=24,
                    height=24,
                    border_radius=12,
                    bgcolor="#1c1c1f",
                    alignment=ft.Alignment(0, 0)
                )
                
            # 3. Address display name
            addr_display = ft.Column([
                ft.Text(name, size=13, weight=ft.FontWeight.BOLD),
                ft.Text(f"{addr[:6]}...{addr[-6:]}", size=11, color="#8d8d99")
            ], spacing=2, expand=True)
            
            # 4. Balances
            if addr_type == "user":
                bal_val = self.cached_balances.get(addr, 0.0)
                bal_text = f"{bal_val:,.2f} SOL"
            else:
                mint = info.get("mint") or "N/A"
                bal_text = f"{mint[:4]}...{mint[-4:]}" if mint != "N/A" else "Token"
                
            # 5. Status Pill
            status_pill = ft.Container(
                content=ft.Text("Active", color="#34d399", size=10, weight=ft.FontWeight.BOLD),
                bgcolor="#064e3b",
                padding=ft.Padding(10, 4, 10, 4),
                border_radius=12
            )
            
            # 6. Action Buttons Row
            actions = ft.Row([
                ft.IconButton(icon=ft.Icons.CONTENT_COPY, icon_color="#8d8d99", icon_size=16, tooltip="Copy Address", on_click=lambda e, a=addr: self.copy_to_clipboard(a)),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ef4444", icon_size=16, tooltip="Remove Wallet", on_click=lambda e, a=addr: self.delete_wallet_dashboard(a))
            ], spacing=2, alignment=ft.MainAxisAlignment.END)
            
            # Build Row container
            row_container = ft.Container(
                content=ft.Row([
                    ft.Text(f"{idx}.", size=12, color="#8d8d99", width=30),
                    avatar,
                    ft.Container(content=ft.Text(type_text, size=12, weight=ft.FontWeight.BOLD, color=type_color), width=80),
                    addr_display,
                    ft.Text(bal_text, size=13, width=180),
                    status_pill,
                    ft.Container(content=actions, width=100)
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#111613" if self.page.theme_mode == ft.ThemeMode.DARK else "#ffffff",
                padding=10,
                border_radius=8,
                border=ft.Border.all(width=1, color="#1e2924" if self.page.theme_mode == ft.ThemeMode.DARK else "#e4e4e7")
            )
            self.dashboard_list.controls.append(row_container)
            idx += 1
            
        self.page.update()

    def copy_to_clipboard(self, address):
        self.page.set_clipboard(address)
        self.show_popup("Copied", "Address copied to clipboard successfully!")

    def delete_wallet_dashboard(self, address):
        chat_id_str = str(self.chat_id)
        if chat_id_str in self.state["chats"] and address in self.state["chats"][chat_id_str]["tracked"]:
            del self.state["chats"][chat_id_str]["tracked"][address]
            self.save_state()
            self.update_wallet_lists()
            self.refresh_dashboard_table()
            self.update_metrics_values()
            self.show_popup("Success", "Address removed from database.")

    def open_add_dialog(self, e):
        # Dialog Inputs
        addr_input = ft.TextField(label="Solana Address", border_color="#29292e", bgcolor="#121214", width=350)
        name_input = ft.TextField(label="Custom Nickname (Optional)", border_color="#29292e", bgcolor="#121214", width=350)
        
        def on_add_confirm(e):
            address = addr_input.value.strip()
            name = name_input.value.strip() or f"{address[:4]}...{address[-4:]}"
            
            if not address or not re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address):
                self.show_popup("Error", "Invalid Solana Address format.")
                return
                
            # Classify address on-chain
            detected_type = self.identify_address_on_chain(address)
            if detected_type == "OTHER_PROGRAM":
                self.show_popup("Error", "This contract address cannot be tracked.")
                return
            elif detected_type == "INVALID_OR_EMPTY":
                self.show_popup("Error", "Account info could not be resolved from Solana RPC.")
                return
                
            addr_type = "user" if detected_type == "WALLET" else "token"
            
            chat_id_str = str(self.chat_id)
            if chat_id_str not in self.state["chats"]:
                self.state["chats"][chat_id_str] = {"tracked": {}}
                
            owner_addr = None
            token_mint = None
            if addr_type == "token":
                urls = [u.strip() for u in self.rpc_url.split(",") if u.strip()]
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getAccountInfo",
                    "params": [address, {"encoding": "jsonParsed"}]
                }
                for url in urls:
                    try:
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
                                    break
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
            self.update_metrics_values()
            self.load_balances_async()
            
            dialog.open = False
            self.page.update()
            
            type_lbl = "User Wallet" if addr_type == "user" else "Specific Token Account"
            self.show_popup("Success", f"Successfully added {type_lbl} to watchlist!")

        def close_dialog(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Add Tracked Address", weight=ft.FontWeight.BOLD),
            content=ft.Column([addr_input, name_input], tight=True, spacing=12),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.ElevatedButton("Add Address", bgcolor="#10b981", color="#ffffff", on_click=on_add_confirm)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()

    def identify_address_on_chain(self, address_str):
        if not self.rpc_url:
            return "UNKNOWN"
        urls = [u.strip() for u in self.rpc_url.split(",") if u.strip()]
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAccountInfo",
            "params": [address_str, {"encoding": "jsonParsed"}]
        }
        for url in urls:
            try:
                r = requests.post(url, json=payload, timeout=5)
                if r.status_code == 200:
                    res = r.json()
                    if "result" in res and res["result"].get("value") is not None:
                        val = res["result"]["value"]
                        owner = val.get("owner")
                        if owner == "11111111111111111111111111111111":
                            return "WALLET"
                        elif owner in ["TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"]:
                            return "TOKEN"
                        else:
                            return "OTHER_PROGRAM"
                    else:
                        return "INVALID_OR_EMPTY"
            except Exception:
                continue
        return "UNKNOWN"

    def load_balances_async(self):
        def worker():
            if not self.chat_id or not self.rpc_url:
                return
            chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
            tracked = chat_data.get("tracked", {})
            urls = [u.strip() for u in self.rpc_url.split(",") if u.strip()]
            
            total_sol = 0.0
            temp_balances = {}
            
            for addr, info in list(tracked.items()):
                if info.get("type") == "user":
                    payload = {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getBalance",
                        "params": [addr]
                    }
                    for url in urls:
                        try:
                            r = requests.post(url, json=payload, timeout=5)
                            if r.status_code == 200:
                                res = r.json()
                                if "result" in res and res["result"].get("value") is not None:
                                    bal = res["result"]["value"] / 1e9
                                    total_sol += bal
                                    temp_balances[addr] = bal
                                    break
                        except Exception:
                            continue
            
            self.cached_balances = temp_balances
            
            # Safely refresh UI metrics card and rows
            if hasattr(self, "val_sol"):
                self.val_sol.value = f"{total_sol:,.2f} SOL"
            self.refresh_dashboard_table()
            
        threading.Thread(target=worker, daemon=True).start()

    def build_wallets_view(self):
        # We also support direct visual wallet manager lists as back compatibility
        card_bg = "#1a1a1e" if self.page.theme_mode == ft.ThemeMode.DARK else "#ffffff"
        
        self.user_wallets_col = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
        self.token_accounts_col = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO, expand=True)
        
        user_container = ft.Container(
            content=ft.Column([
                ft.Text("User Wallets Watchlist", size=13, color="#8d8d99", weight=ft.FontWeight.BOLD),
                self.user_wallets_col
            ], expand=True),
            bgcolor=card_bg, padding=12, border_radius=8, expand=True,
            border=ft.Border.all(width=1, color="#29292e")
        )
        
        token_container = ft.Container(
            content=ft.Column([
                ft.Text("Token Accounts Watchlist", size=13, color="#8d8d99", weight=ft.FontWeight.BOLD),
                self.token_accounts_col
            ], expand=True),
            bgcolor=card_bg, padding=12, border_radius=8, expand=True,
            border=ft.Border.all(width=1, color="#29292e")
        )
        
        self.update_wallet_lists()
        
        return ft.Row([user_container, token_container], expand=True, spacing=15)

    def update_wallet_lists(self):
        self.user_wallets_col.controls.clear()
        self.token_accounts_col.controls.clear()
        
        if not self.chat_id:
            return
            
        chat_data = self.state.get("chats", {}).get(str(self.chat_id), {})
        tracked = chat_data.get("tracked", {})
        
        for addr, info in tracked.items():
            name = info.get("name", "Unnamed")
            addr_type = info.get("type", "user")
            
            row = ft.Container(
                content=ft.Row([
                    ft.Text(f"{name} ({addr[:4]}...{addr[-4:]})", size=12, weight=ft.FontWeight.BOLD),
                    ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ef4444", icon_size=14, on_click=lambda e, a=addr: self.delete_wallet_dashboard(a))
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                padding=6,
                border_radius=6,
                bgcolor="#121214" if self.page.theme_mode == ft.ThemeMode.DARK else "#f4f4f5"
            )
            
            if addr_type == "user":
                self.user_wallets_col.controls.append(row)
            else:
                self.token_accounts_col.controls.append(row)

    def build_settings_view(self):
        card_bg = "#1a1a1e" if self.page.theme_mode == ft.ThemeMode.DARK else "#ffffff"
        text_color = "#e1e1e6" if self.page.theme_mode == ft.ThemeMode.DARK else "#18181b"
        
        # Credentials Form Fields
        self.token_field = ft.TextField(label="Telegram Bot Token", password=True, can_reveal_password=True, value=self.token, border_color="#29292e")
        self.chat_field = ft.TextField(label="Telegram Chat ID", value=self.chat_id, border_color="#29292e")
        self.rpc_field = ft.TextField(label="Solana RPC URL Preset", value=self.rpc_url, border_color="#29292e")
        
        # Connection Save Frame
        conn_box = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.VPN_KEY, color="#3b82f6", size=18), ft.Text("Connection Credentials", size=14, weight=ft.FontWeight.BOLD, color=text_color)], spacing=10),
                self.token_field,
                self.chat_field,
                self.rpc_field,
                ft.Row([
                    ft.ElevatedButton("Test Connections", bgcolor="#3e3e42", color=text_color, on_click=self.test_connections),
                    ft.ElevatedButton("Save Credentials", bgcolor="#3b82f6", color="#ffffff", on_click=self.save_connections)
                ], alignment=ft.MainAxisAlignment.END)
            ], spacing=10),
            bgcolor=card_bg, padding=15, border_radius=10, border=ft.Border.all(width=1, color="#29292e")
        )
        
        # Preferences Form Fields
        self.currency_field = ft.Dropdown(
            label="Default Currency",
            options=[ft.dropdown.Option(c) for c in ["USD", "NIS", "CAD", "EUR", "GBP", "AUD"]],
            value=self.get_chat_pref("currency", "USD"),
            border_color="#29292e"
        )
        
        self.interval_field = ft.Dropdown(
            label="Summary Interval (Minutes)",
            options=[ft.dropdown.Option(i) for i in ["1", "5", "15", "30", "60", "120", "240", "480"]],
            value=str(self.get_chat_pref("interval", 1)),
            border_color="#29292e"
        )
        
        self.status_int_field = ft.Dropdown(
            label="Status Interval (Minutes)",
            options=[ft.dropdown.Option(i) for i in ["1", "5", "10", "15", "30", "60"]],
            value=str(self.get_chat_pref("status_interval", 5)),
            border_color="#29292e"
        )
        
        self.whale_field = ft.TextField(label="Whale Threshold (% of supply)", value=str(self.get_chat_pref("whale_threshold", 1.0)), border_color="#29292e")
        self.daily_time_field = ft.TextField(label="Daily Snapshot Time (HH:MM)", value=self.get_chat_pref("daily_summary_time", "00:00"), border_color="#29292e")
        self.noise_field = ft.TextField(label="Noise Threshold (USD Alert Filter)", value=str(self.get_chat_pref("noise_threshold", 0.0)), border_color="#29292e")
        
        self.chk_coin_link = ft.Checkbox(label="Show Coin Links (Dexscreener)", value=self.get_chat_pref("show_coin_link", True))
        self.chk_market_cap = ft.Checkbox(label="Show Token Market Cap", value=self.get_chat_pref("show_market_cap", True))
        self.chk_auto_start = ft.Checkbox(label="Auto-start bot service on launch", value=(self.auto_start == "true"))
        
        # Preferences Save Frame
        pref_box = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.SETTINGS, color="#3b82f6", size=18), ft.Text("Bot Alert Configurations & Thresholds", size=14, weight=ft.FontWeight.BOLD, color=text_color)], spacing=10),
                ft.Row([self.currency_field, self.interval_field], spacing=10),
                ft.Row([self.status_int_field, self.whale_field], spacing=10),
                ft.Row([self.daily_time_field, self.noise_field], spacing=10),
                ft.Column([self.chk_coin_link, self.chk_market_cap, self.chk_auto_start], spacing=5),
                ft.Row([
                    ft.ElevatedButton("Save Preferences", bgcolor="#3b82f6", color="#ffffff", on_click=self.save_preferences)
                ], alignment=ft.MainAxisAlignment.END)
            ], spacing=10),
            bgcolor=card_bg, padding=15, border_radius=10, border=ft.Border.all(width=1, color="#29292e")
        )
        
        return ft.Column([conn_box, pref_box], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    def test_connections(self, e):
        tg_token = self.token_field.value.strip()
        rpc_urls = [u.strip() for u in self.rpc_field.value.strip().split(",") if u.strip()]
        
        if not tg_token:
            self.show_popup("Error", "Telegram Bot Token is required to test connectivity.")
            return
            
        def worker():
            # Test Telegram API Connection
            tg_ok = False
            try:
                r = requests.get(f"https://api.telegram.org/bot{tg_token}/getMe", timeout=5)
                tg_ok = (r.status_code == 200)
            except Exception:
                pass
                
            # Test Solana RPC Connection
            sol_ok = False
            lat = 999
            for rpc_url in rpc_urls:
                try:
                    t0 = time.time()
                    payload = {"jsonrpc": "2.0", "id": 1, "method": "getSlot"}
                    r = requests.post(rpc_url, json=payload, timeout=5)
                    if r.status_code == 200:
                        sol_ok = True
                        lat = int((time.time() - t0) * 1000)
                        break
                except Exception:
                    continue
                
            msg = f"Telegram Bot Status: {'[OK] Success' if tg_ok else '[FAILED] Incorrect Token'}\n"
            msg += f"Solana RPC Status: {'[OK] Connected' if sol_ok else '[FAILED] No Response'}"
            if sol_ok:
                msg += f" (Latency: {lat}ms)"
                
            self.show_popup("Connection Test Results", msg)
            
        threading.Thread(target=worker, daemon=True).start()

    def save_connections(self, e):
        self.token = self.token_field.value.strip()
        self.chat_id = self.chat_field.value.strip()
        self.rpc_url = self.rpc_field.value.strip()
        
        if not self.token or not self.chat_id:
            self.show_popup("Error", "Telegram token and chat ID are required.")
            return
            
        if self.save_env_values():
            self.show_popup("Success", "Connection credentials saved to secrets/.env successfully!")
            self.update_wallet_lists()
            self.refresh_dashboard_table()

    def get_chat_pref(self, key, default):
        if not self.chat_id:
            return default
        chat_id_str = str(self.chat_id)
        chat_data = self.state.get("chats", {}).get(chat_id_str, {})
        return chat_data.get(key, default)

    def save_preferences(self, e):
        if not self.chat_id:
            self.show_popup("Error", "Save credentials containing Telegram Chat ID first.")
            return
            
        chat_id_str = str(self.chat_id)
        chat_data = self.state.setdefault("chats", {}).setdefault(chat_id_str, {})
        
        chat_data["currency"] = self.currency_field.value
        chat_data["interval"] = int(self.interval_field.value)
        chat_data["status_interval"] = int(self.status_int_field.value)
        
        try:
            chat_data["whale_threshold"] = float(self.whale_field.value.strip())
        except ValueError:
            chat_data["whale_threshold"] = 1.0
            
        chat_data["daily_summary_time"] = self.daily_time_field.value.strip()
        chat_data["daily_summary_enabled"] = (self.daily_time_field.value.strip() != "00:00")
        
        try:
            chat_data["noise_threshold"] = float(self.noise_field.value.strip())
        except ValueError:
            chat_data["noise_threshold"] = 0.0
            
        chat_data["show_coin_link"] = self.chk_coin_link.value
        chat_data["show_market_cap"] = self.chk_market_cap.value
        
        self.auto_start = "true" if self.chk_auto_start.value else "false"
        
        self.save_state()
        self.save_env_values()
        
        self.show_popup("Success", "Preferences saved and synchronized successfully!")

    def build_logs_view(self):
        card_bg = "#1a1a1e" if self.page.theme_mode == ft.ThemeMode.DARK else "#ffffff"
        text_color = "#e1e1e6" if self.page.theme_mode == ft.ThemeMode.DARK else "#18181b"
        
        # Engine Control Buttons
        self.flet_start_btn = ft.ElevatedButton("Start Bot Service", bgcolor="#10b981", color="#ffffff", on_click=lambda e: self.start_bot())
        self.flet_stop_btn = ft.ElevatedButton("Stop Bot Service", bgcolor="#ef4444", color="#ffffff", on_click=lambda e: self.stop_bot(), disabled=True)
        self.flet_status_lbl = ft.Text("● Status: Stopped", color="#ef4444", size=13, weight=ft.FontWeight.BOLD)
        
        # Log Text Area
        self.logs_feed = ft.Text(
            "Logs streaming panel initialization...\n",
            font_family="Consolas",
            size=11,
            color="#a9a9b3" if self.page.theme_mode == ft.ThemeMode.DARK else "#27272a"
        )
        
        log_scroll_container = ft.Container(
            content=ft.Column([self.logs_feed], scroll=ft.ScrollMode.ALWAYS, expand=True),
            bgcolor="#0d0d0f" if self.page.theme_mode == ft.ThemeMode.DARK else "#ffffff",
            padding=15,
            border_radius=8,
            border=ft.Border.all(width=1, color="#29292e"),
            expand=True
        )
        
        # Control Buttons Header
        header_actions = ft.Container(
            content=ft.Row([
                ft.Row([self.flet_start_btn, self.flet_stop_btn, self.flet_status_lbl], spacing=10),
                ft.Row([
                    ft.ElevatedButton("Clear Logs Display", bgcolor="#3e3e42", color=text_color, on_click=self.clear_logs),
                    ft.ElevatedButton("Clean Exit App", bgcolor="#3e3e42", color=text_color, on_click=self.clean_exit)
                ], spacing=10)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(0, 0, 0, 10)
        )
        
        return ft.Column([header_actions, log_scroll_container], expand=True)

    def start_bot(self):
        if self.tracker_process and self.tracker_process.poll() is None:
            self.show_popup("Error", "Tracker engine bot is already running in background.")
            return
            
        if not self.token:
            self.show_popup("Error", "Bot Token is empty. Fill and save connection credentials first.")
            return
            
        self.should_be_running = True
        try:
            if getattr(sys, 'frozen', False):
                exe_name = "tracker.exe" if sys.platform == "win32" else "tracker"
                tracker_path = os.path.join(BASE_DIR, exe_name)
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
            self.flet_start_btn.disabled = True
            self.flet_stop_btn.disabled = False
            self.update_status_ticker()
            self.show_popup("Bot Engine launched", "Tracker Daemon Bot process launched successfully.")
        except Exception as e:
            self.show_popup("Error", f"Failed to start tracker: {e}")

    def kill_all_tracker_processes(self):
        try:
            if sys.platform == "win32":
                os.system("taskkill /f /im tracker.exe >nul 2>&1")
                os.system('wmic process where "commandline like \'%tracker.py%\'" call terminate >nul 2>&1')
            else:
                os.system("pkill -f 'python.*tracker.py' > /dev/null 2>&1")
                os.system("pkill -f 'tracker' > /dev/null 2>&1")
        except Exception:
            pass

    def stop_bot(self):
        self.should_be_running = False
        if self.tracker_process and self.tracker_process.poll() is None:
            self.tracker_process.terminate()
            self.tracker_process.wait()
            self.tracker_process = None
            
        # Clean up any other running tracker processes just in case
        self.kill_all_tracker_processes()
        self.bot_start_time = None
        self.flet_start_btn.disabled = False
        self.flet_stop_btn.disabled = True
        self.update_status_ticker()
        self.show_popup("Bot Stopped", "Tracker Daemon Bot process stopped successfully.")

    def clear_logs(self, e):
        # Truncate physical file
        try:
            with open(LOG_PATH, "w") as f:
                f.truncate(0)
        except Exception:
            pass
        self.logs_feed.value = "Logs console cleared.\n"
        self.page.update()

    def clean_exit(self, e=None):
        self.should_be_running = False
        if self.tracker_process and self.tracker_process.poll() is None:
            try:
                self.tracker_process.terminate()
                self.tracker_process.wait()
            except Exception:
                pass
        sys.exit(0)

    def check_process_loop(self):
        def worker():
            while True:
                time.sleep(1)
                
                # Check subprocess watchdog
                if self.tracker_process:
                    status = self.tracker_process.poll()
                    if status is not None:
                        self.tracker_process = None
                        self.bot_start_time = None
                        self.flet_start_btn.disabled = False
                        self.flet_stop_btn.disabled = True
                        if self.should_be_running:
                            print("Watchdog: Process exited. Auto-restarting...")
                            self.start_bot()
                else:
                    if self.should_be_running:
                        print("Watchdog: Process not running but should be. Starting...")
                        self.start_bot()
                        
                # Update status labels
                self.update_status_ticker()
                
                # Update logs dynamically
                if self.logs_visible:
                    self.stream_logs_feed()
                    
        threading.Thread(target=worker, daemon=True).start()

    def update_status_ticker(self):
        if self.tracker_process and self.tracker_process.poll() is None:
            uptime = int(time.time() - (self.bot_start_time or time.time()))
            h = uptime // 3600
            m = (uptime % 3600) // 60
            s = uptime % 60
            uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
            status_text = f"● Running | Uptime: {uptime_str}"
            
            self.flet_status_lbl.value = status_text
            self.flet_status_lbl.color = "#10b981"
            if hasattr(self, "val_channels"):
                self.val_channels.value = "Active"
                self.val_channels.color = "#10b981"
            if hasattr(self, "dash_status_val"):
                self.dash_status_val.value = f"Active ({uptime_str})"
                self.dash_status_val.color = "#10b981"
        else:
            self.flet_status_lbl.value = "● Status: Stopped"
            self.flet_status_lbl.color = "#ef4444"
            if hasattr(self, "val_channels"):
                self.val_channels.value = "Stopped"
                self.val_channels.color = "#ef4444"
            if hasattr(self, "dash_status_val"):
                self.dash_status_val.value = "Stopped"
                self.dash_status_val.color = "#ef4444"
        self.page.update()

    def stream_logs_feed(self):
        if not os.path.exists(LOG_PATH):
            self.logs_feed.value = "No log file found at logs/tracker.log"
            self.page.update()
            return
            
        try:
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            # Get tail 40 lines
            tail = [line.strip() for line in lines[-40:]]
            self.logs_feed.value = "\n".join(tail)
        except Exception as e:
            self.logs_feed.value = f"Error reading logs: {e}"
        self.page.update()

    def build_backup_view(self):
        card_bg = "#1a1a1e" if self.page.theme_mode == ft.ThemeMode.DARK else "#ffffff"
        text_color = "#e1e1e6" if self.page.theme_mode == ft.ThemeMode.DARK else "#18181b"
        
        # Backup panel buttons
        backup_box = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.BACKUP, color="#3b82f6", size=18), ft.Text("Backup & Restore Data", size=14, weight=ft.FontWeight.BOLD, color=text_color)], spacing=10),
                ft.Text(self.tr("backup_desc"), size=11, color="#8d8d99"),
                ft.Row([
                    ft.ElevatedButton("Export Tracked List", bgcolor="#3b82f6", color="#ffffff", on_click=self.export_config),
                    ft.ElevatedButton("Import Tracked List", bgcolor="#3e3e42", color=text_color, on_click=self.import_config),
                ], spacing=10)
            ], spacing=10),
            bgcolor=card_bg, padding=15, border_radius=10, border=ft.Border.all(width=1, color="#29292e")
        )
        
        # App Settings Card
        self.lang_field = ft.Dropdown(
            label="Language Selection",
            options=[ft.dropdown.Option(lang) for lang in ["English", "Russian", "Arabic"]],
            value=self.settings.get("language", "English"),
            border_color="#29292e"
        )
        self.size_field = ft.Dropdown(
            label="UI Font Size",
            options=[ft.dropdown.Option(sz) for sz in ["Small", "Medium", "Large"]],
            value=self.settings.get("font_size", "Medium"),
            border_color="#29292e"
        )
        self.theme_field = ft.Dropdown(
            label="UI Theme Mode",
            options=[ft.dropdown.Option(th) for th in ["Dark Mode", "Light Mode", "System Sync"]],
            value=self.settings.get("theme", "System Sync"),
            border_color="#29292e"
        )
        
        app_settings_box = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.PALETTE, color="#3b82f6", size=18), ft.Text("Application Visual Settings", size=14, weight=ft.FontWeight.BOLD, color=text_color)], spacing=10),
                self.lang_field,
                self.size_field,
                self.theme_field,
                ft.Row([
                    ft.ElevatedButton("Save Environment UI Settings", bgcolor="#3b82f6", color="#ffffff", on_click=self.save_ui_settings)
                ], alignment=ft.MainAxisAlignment.END)
            ], spacing=10),
            bgcolor=card_bg, padding=15, border_radius=10, border=ft.Border.all(width=1, color="#29292e")
        )
        
        # License Card
        license_text = (
            "Solana Telegram Tracker Configurator v1.4.0 (Flet Engine)\n"
            "Licensed under the MIT License.\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy..."
        )
        license_box = ft.Container(
            content=ft.Column([
                ft.Row([ft.Icon(ft.Icons.INFO, color="#3b82f6", size=18), ft.Text("License & About", size=14, weight=ft.FontWeight.BOLD, color=text_color)], spacing=10),
                ft.Text(license_text, size=11, color="#8d8d99", font_family="Consolas")
            ], spacing=10),
            bgcolor=card_bg, padding=15, border_radius=10, border=ft.Border.all(width=1, color="#29292e")
        )
        
        return ft.Column([backup_box, app_settings_box, license_box], spacing=15, scroll=ft.ScrollMode.AUTO, expand=True)

    def save_ui_settings(self, e):
        self.settings["language"] = self.lang_field.value
        self.settings["font_size"] = self.size_field.value
        self.settings["theme"] = self.theme_field.value
        
        self.save_state()
        self.apply_theme_settings()
        self.show_popup("Success", "UI settings applied successfully! Refreshing panel...")
        
        # Force re-render sidebar buttons
        self.page.controls.clear()
        self.build_ui()
        self.page.update()

    def export_config(self, e):
        if not self.chat_id:
            self.show_popup("Error", "Telegram Chat ID must be configured to export.")
            return
            
        chat_id_str = str(self.chat_id)
        chat_data = self.state.get("chats", {}).get(chat_id_str, {})
        tracked = chat_data.get("tracked", {})
        if not tracked:
            self.show_popup("Warning", "No tracked addresses found to export.")
            return
            
        # Export as a pretty-printed JSON file in root
        export_path = os.path.join(BASE_DIR, "watchlist_backup.json")
        try:
            with open(export_path, "w") as f:
                json.dump({"chats": {chat_id_str: chat_data}}, f, indent=4)
            self.show_popup("Success", f"Configuration exported to:\n{export_path}")
        except Exception as ex:
            self.show_popup("Error", f"Failed to export: {ex}")

    def import_config(self, e):
        import_path = os.path.join(BASE_DIR, "watchlist_backup.json")
        if not os.path.exists(import_path):
            self.show_popup("Error", "No watchlist_backup.json file found to import.")
            return
            
        try:
            with open(import_path, "r") as f:
                imported = json.load(f)
                
            chats = imported.get("chats", {})
            if not chats:
                self.show_popup("Error", "Invalid backup format.")
                return
                
            # Merge chats
            for chat_id, data in chats.items():
                self.state.setdefault("chats", {})[chat_id] = data
                
            self.save_state()
            self.update_wallet_lists()
            self.refresh_dashboard_table()
            self.update_metrics_values()
            self.load_balances_async()
            self.show_popup("Success", "Watchlist configurations imported and merged successfully!")
        except Exception as ex:
            self.show_popup("Error", f"Failed to import: {ex}")


def main(page: ft.Page):
    FletConfiguratorApp(page)

if __name__ == "__main__":
    is_unc = os.getcwd().startswith("\\\\")
    force_web = "--web" in sys.argv or is_unc
    
    # Auto-detect WSL environment where graphics acceleration is frequently broken
    is_wsl = False
    if sys.platform.startswith("linux"):
        try:
            with open("/proc/sys/kernel/osrelease", "r") as f:
                if "microsoft" in f.read().lower():
                    is_wsl = True
        except Exception:
            pass
            
    if is_wsl:
        print("WSL environment detected. Defaulting to local web server mode...")
        force_web = True
    
    # Auto-detect headless Linux environments lacking display drivers
    if sys.platform.startswith("linux") and not is_wsl:
        has_display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        if not has_display:
            print("No graphical display server found (headless environment). Defaulting to web browser mode.")
            force_web = True

    if force_web:
        print("Launching local web server...")
        print("==========================================================")
        print("  Please open the following link in your web browser:")
        print("  --> http://127.0.0.1:8550 <--")
        print("==========================================================")
        try:
            ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
        except Exception as ex:
            try:
                ft.app(target=main, view=ft.AppView.WEB_BROWSER)
            except Exception as ex2:
                print(f"Failed to launch: {ex2}")
    else:
        try:
            # Default to native desktop application window
            import time
            start_time = time.time()
            ft.app(target=main)
            duration = time.time() - start_time
            # If the app exits in less than 4 seconds, it indicates a startup crash (like missing/broken Mesa drivers)
            if duration < 4.0:
                print("Desktop client shut down immediately. This might be due to missing OS graphics drivers.")
                raise RuntimeError("Immediate desktop client exit")
        except Exception as e:
            print(f"Failed to run in desktop mode: {e}")
            print("Falling back to local web server mode...")
            print("==========================================================")
            print("  Please open the following link in your web browser:")
            print("  --> http://127.0.0.1:8550 <--")
            print("==========================================================")
            try:
                ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8550)
            except Exception as ex:
                try:
                    ft.app(target=main, view=ft.AppView.WEB_BROWSER)
                except Exception as ex2:
                    print(f"Failed to launch: {ex2}")
