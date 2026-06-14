import sys
import re
import tkinter as tk
from tkinter import ttk
import gui_styles

def apply_dark_title_bar(window):
    if sys.platform == "win32":
        import ctypes
        try:
            window.update_idletasks()
            hwnd = window.winfo_id()
            is_dark = (gui_styles.BG_MAIN == "#121214")
            rendering = ctypes.c_int(1 if is_dark else 0)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(rendering), ctypes.sizeof(rendering))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(rendering), ctypes.sizeof(rendering))
        except Exception:
            pass

class CustomMessageDialog(tk.Toplevel):
    def __init__(self, parent, title, message, dialog_type="info", tr=None):
        super().__init__(parent)
        self.tr = tr or (lambda k: k)
        self.title(title)
        
        # Decide sizing and resizability based on message length
        is_long_message = len(message) > 180
        if is_long_message:
            self.geometry("550x320")
            self.resizable(True, True)
        else:
            self.geometry("450x220")
            self.resizable(False, False)
            
        self.configure(bg=gui_styles.BG_MAIN)
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
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
        
        # Inherit application icon
        try:
            if hasattr(parent, 'icon_img_small') and parent.icon_img_small:
                self.iconphoto(True, parent.icon_img_small, parent.icon_img)
            elif hasattr(parent, 'icon_img') and parent.icon_img:
                self.iconphoto(True, parent.icon_img)
        except Exception:
            pass
            
        apply_dark_title_bar(self)
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        
        # Symbols mapping
        color_map = {
            "info": gui_styles.ACCENT_BLUE,
            "error": gui_styles.ACCENT_RED,
            "warning": "#fbbf24"
        }
        symbol_map = {
            "info": "🟢" if dialog_type == "info" else "[i]",
            "error": "❌" if dialog_type == "error" else "[!]",
            "warning": "⚠️" if dialog_type == "warning" else "[!]"
        }
        accent_color = color_map.get(dialog_type, gui_styles.ACCENT_BLUE)
        accent_symbol = symbol_map.get(dialog_type, "[i]")
        
        content_frame = tk.Frame(self, bg=gui_styles.BG_MAIN)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        lbl_icon = tk.Label(content_frame, text=accent_symbol, bg=gui_styles.BG_MAIN, fg=accent_color, font=("Courier", gui_styles.FONT_SIZE + 10, "bold"))
        lbl_icon.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 15))
        
        if is_long_message:
            text_frame = tk.Frame(content_frame, bg=gui_styles.BG_MAIN)
            text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar = ttk.Scrollbar(text_frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            msg_text = tk.Text(
                text_frame, 
                bg=gui_styles.BG_MAIN, 
                fg=gui_styles.TEXT_COLOR, 
                font=("Helvetica", gui_styles.FONT_SIZE), 
                wrap=tk.WORD, 
                bd=0, 
                highlightthickness=0,
                yscrollcommand=scrollbar.set
            )
            msg_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=msg_text.yview)
            
            msg_text.insert(tk.END, message)
            msg_text.config(state=tk.DISABLED)
        else:
            msg_lbl = tk.Label(
                content_frame, 
                text=message, 
                bg=gui_styles.BG_MAIN, 
                fg=gui_styles.TEXT_COLOR, 
                justify=tk.LEFT, 
                font=("Helvetica", gui_styles.FONT_SIZE + 2 if not is_long_message else gui_styles.FONT_SIZE), 
                wraplength=340
            )
            msg_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.W)
        
        btn_frame = tk.Frame(self, bg=gui_styles.BG_MAIN, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_ok = ttk.Button(btn_frame, text=self.tr("ok"), style="Blue.TButton", command=self.destroy, width=10)
        btn_ok.pack(anchor=tk.CENTER)
        
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

class CustomConfirmDialog(tk.Toplevel):
    def __init__(self, parent, title, message, tr=None):
        super().__init__(parent)
        self.tr = tr or (lambda k: k)
        self.title(title)
        self.geometry("450x220")
        self.resizable(False, False)
        self.configure(bg=gui_styles.BG_MAIN)
        self.transient(parent)
        self.grab_set()
        self.result = False
        
        # Center dialog
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
        
        try:
            if hasattr(parent, 'icon_img_small') and parent.icon_img_small:
                self.iconphoto(True, parent.icon_img_small, parent.icon_img)
            elif hasattr(parent, 'icon_img') and parent.icon_img:
                self.iconphoto(True, parent.icon_img)
        except Exception:
            pass
            
        apply_dark_title_bar(self)
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        
        content_frame = tk.Frame(self, bg=gui_styles.BG_MAIN)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        lbl_icon = tk.Label(content_frame, text="❓", bg=gui_styles.BG_MAIN, fg=gui_styles.ACCENT_BLUE, font=("Courier", gui_styles.FONT_SIZE + 10, "bold"))
        lbl_icon.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 15))
        
        msg_lbl = tk.Label(
            content_frame, 
            text=message, 
            bg=gui_styles.BG_MAIN, 
            fg=gui_styles.TEXT_COLOR, 
            justify=tk.LEFT, 
            font=("Helvetica", gui_styles.FONT_SIZE + 2), 
            wraplength=340
        )
        msg_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.W)
        
        btn_frame = tk.Frame(self, bg=gui_styles.BG_MAIN, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_no = ttk.Button(btn_frame, text=self.tr("no"), style="Gray.TButton", command=self.on_no, width=10)
        btn_no.pack(side=tk.RIGHT, padx=(5, 20))
        
        btn_yes = ttk.Button(btn_frame, text=self.tr("yes"), style="Blue.TButton", command=self.on_yes, width=10)
        btn_yes.pack(side=tk.RIGHT)
        
        self.bind("<Return>", lambda e: self.on_yes())
        self.bind("<Escape>", lambda e: self.on_no())
        
    def on_yes(self):
        self.result = True
        self.destroy()
        
    def on_no(self):
        self.result = False
        self.destroy()

class MessageBoxWrapper:
    def __init__(self, root, tr=None):
        self.root = root
        self.tr = tr or (lambda k: k)
        
    def showinfo(self, title, message):
        CustomMessageDialog(self.root, title, message, "info", tr=self.tr)
        
    def showerror(self, title, message):
        CustomMessageDialog(self.root, title, message, "error", tr=self.tr)
        
    def showwarning(self, title, message):
        CustomMessageDialog(self.root, title, message, "warning", tr=self.tr)
        
    def askyesno(self, title, message):
        dialog = CustomConfirmDialog(self.root, title, message, tr=self.tr)
        self.root.wait_window(dialog)
        return dialog.result

class CustomAddAddressDialog(tk.Toplevel):
    def __init__(self, parent, addr_type, title=None, tr=None):
        super().__init__(parent)
        self.tr = tr or (lambda k: k)
        
        if title is None:
            title = self.tr("add_user_wallet_title") if addr_type == "user" else self.tr("add_token_account_title")
        self.title(title)
        self.geometry("450x260")
        self.resizable(False, False)
        self.configure(bg=gui_styles.BG_MAIN)
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
        
        try:
            if hasattr(parent, 'icon_img_small') and parent.icon_img_small:
                self.iconphoto(True, parent.icon_img_small, parent.icon_img)
            elif hasattr(parent, 'icon_img') and parent.icon_img:
                self.iconphoto(True, parent.icon_img)
        except Exception:
            pass
            
        apply_dark_title_bar(self)
        self.lift()
        self.attributes("-topmost", True)
        self.focus_force()
        
        # Main form UI
        header_text = self.tr("add_user_wallet_title") if addr_type == "user" else self.tr("add_token_account_title")
        lbl_title = ttk.Label(
            self, 
            text=header_text, 
            font=("Helvetica", gui_styles.FONT_SIZE + 2, "bold"), 
            background=gui_styles.BG_MAIN, 
            foreground=gui_styles.TEXT_COLOR
        )
        lbl_title.pack(anchor=tk.W, padx=20, pady=(15, 10))
        
        form_frame = tk.Frame(self, bg=gui_styles.BG_MAIN)
        form_frame.pack(fill=tk.X, padx=20, pady=5)
        
        ttk.Label(form_frame, text=self.tr("solana_address"), background=gui_styles.BG_MAIN, foreground=gui_styles.TEXT_COLOR).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.addr_var = tk.StringVar()
        self.addr_entry = tk.Entry(form_frame, textvariable=self.addr_var, bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, bd=1, relief=tk.SOLID, width=32, font=("Helvetica", gui_styles.FONT_SIZE))
        self.addr_entry.grid(row=0, column=1, padx=(10, 0), pady=5)
        self.addr_entry.focus()
        
        ttk.Label(form_frame, text=self.tr("custom_name"), background=gui_styles.BG_MAIN, foreground=gui_styles.TEXT_COLOR).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(form_frame, textvariable=self.name_var, bg=gui_styles.BG_CARD, fg=gui_styles.TEXT_COLOR, insertbackground=gui_styles.TEXT_COLOR, bd=1, relief=tk.SOLID, width=32, font=("Helvetica", gui_styles.FONT_SIZE))
        self.name_entry.grid(row=1, column=1, padx=(10, 0), pady=5)
        
        self.err_lbl = ttk.Label(form_frame, text="", background=gui_styles.BG_MAIN, foreground=gui_styles.ACCENT_RED, font=("Helvetica", gui_styles.FONT_SIZE - 2 if gui_styles.FONT_SIZE > 9 else 8))
        self.err_lbl.grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        
        btn_frame = tk.Frame(self, bg=gui_styles.BG_MAIN)
        btn_frame.pack(fill=tk.X, padx=20, pady=(15, 0), side=tk.BOTTOM)
        
        btn_cancel = ttk.Button(btn_frame, text=self.tr("cancel"), style="Gray.TButton", command=self.destroy, width=10)
        btn_cancel.pack(side=tk.RIGHT, padx=(5, 0))
        
        btn_add = ttk.Button(btn_frame, text=self.tr("add"), style="Green.TButton", command=self.validate_and_submit, width=10)
        btn_add.pack(side=tk.RIGHT)
        
        self.bind("<Return>", lambda e: self.validate_and_submit())
        self.bind("<Escape>", lambda e: self.destroy())
 
    def validate_and_submit(self):
        address = self.addr_var.get().strip()
        name = self.name_var.get().strip()
        
        if not address:
            self.err_lbl.config(text=self.tr("err_address_empty"))
            return
            
        if not re.match(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$", address):
            self.err_lbl.config(text=self.tr("err_invalid_solana_addr"))
            return
            
        if not name:
            name = f"{address[:4]}...{address[-4:]}"
            
        self.result = (address, name)
        self.destroy()
