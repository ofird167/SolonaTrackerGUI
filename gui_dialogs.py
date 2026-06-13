import re
import tkinter as tk
from tkinter import ttk
from gui_styles import (
    BG_MAIN, BG_CARD, TEXT_COLOR, TEXT_MUTED, 
    ACCENT_GREEN, ACCENT_BLUE, ACCENT_RED, BORDER_COLOR
)

class CustomMessageDialog(tk.Toplevel):
    def __init__(self, parent, title, message, dialog_type="info"):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x180")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.transient(parent)
        self.grab_set()
        
        # Border
        self.config(bd=1, relief=tk.SOLID, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_BLUE)
        self.overrideredirect(True)
        
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
        
        # Title bar
        title_bar = tk.Frame(self, bg=BG_CARD, height=30)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        
        lbl_title = tk.Label(title_bar, text=title, bg=BG_CARD, fg=TEXT_COLOR, font=("Helvetica", 9, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=10)
        
        btn_close = tk.Button(
            title_bar, 
            text="✕", 
            bg=BG_CARD, 
            fg=TEXT_MUTED, 
            activebackground=ACCENT_RED, 
            activeforeground="#ffffff", 
            bd=0, 
            font=("Helvetica", 9), 
            command=self.destroy,
            width=3,
            relief=tk.FLAT
        )
        btn_close.pack(side=tk.RIGHT, fill=tk.Y)
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg="#ffffff"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg=BG_CARD, fg=TEXT_MUTED))
        
        # Dragging logic
        def start_move(e):
            self.x = e.x
            self.y = e.y
        def drag(e):
            deltax = e.x - self.x
            deltay = e.y - self.y
            self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")
        title_bar.bind("<ButtonPress-1>", start_move)
        title_bar.bind("<B1-Motion>", drag)
        lbl_title.bind("<ButtonPress-1>", start_move)
        lbl_title.bind("<B1-Motion>", drag)
        
        # Symbols mapping to avoid emoji box issues on Linux
        color_map = {
            "info": ACCENT_BLUE,
            "error": ACCENT_RED,
            "warning": "#fbbf24"
        }
        symbol_map = {
            "info": "[i]",
            "error": "[!]",
            "warning": "[!]"
        }
        accent_color = color_map.get(dialog_type, ACCENT_BLUE)
        accent_symbol = symbol_map.get(dialog_type, "[i]")
        
        content_frame = tk.Frame(self, bg=BG_MAIN)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        lbl_icon = tk.Label(content_frame, text=accent_symbol, bg=BG_MAIN, fg=accent_color, font=("Courier", 18, "bold"))
        lbl_icon.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 15))
        
        msg_lbl = tk.Label(content_frame, text=message, bg=BG_MAIN, fg=TEXT_COLOR, justify=tk.LEFT, font=("Helvetica", 10), wraplength=300)
        msg_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.W)
        
        btn_frame = tk.Frame(self, bg=BG_MAIN, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_ok = ttk.Button(btn_frame, text="OK", style="Blue.TButton", command=self.destroy, width=10)
        btn_ok.pack(anchor=tk.CENTER)
        
        self.bind("<Return>", lambda e: self.destroy())
        self.bind("<Escape>", lambda e: self.destroy())

class CustomConfirmDialog(tk.Toplevel):
    def __init__(self, parent, title, message):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x180")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.transient(parent)
        self.grab_set()
        self.result = False
        
        # Border
        self.config(bd=1, relief=tk.SOLID, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_BLUE)
        self.overrideredirect(True)
        
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
        
        # Title bar
        title_bar = tk.Frame(self, bg=BG_CARD, height=30)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        
        lbl_title = tk.Label(title_bar, text=title, bg=BG_CARD, fg=TEXT_COLOR, font=("Helvetica", 9, "bold"))
        lbl_title.pack(side=tk.LEFT, padx=10)
        
        # Dragging logic
        def start_move(e):
            self.x = e.x
            self.y = e.y
        def drag(e):
            deltax = e.x - self.x
            deltay = e.y - self.y
            self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")
        title_bar.bind("<ButtonPress-1>", start_move)
        title_bar.bind("<B1-Motion>", drag)
        lbl_title.bind("<ButtonPress-1>", start_move)
        lbl_title.bind("<B1-Motion>", drag)
        
        content_frame = tk.Frame(self, bg=BG_MAIN)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        lbl_icon = tk.Label(content_frame, text="[?]", bg=BG_MAIN, fg=ACCENT_BLUE, font=("Courier", 18, "bold"))
        lbl_icon.pack(side=tk.LEFT, anchor=tk.N, padx=(0, 15))
        
        msg_lbl = tk.Label(content_frame, text=message, bg=BG_MAIN, fg=TEXT_COLOR, justify=tk.LEFT, font=("Helvetica", 10), wraplength=300)
        msg_lbl.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.W)
        
        btn_frame = tk.Frame(self, bg=BG_MAIN, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        btn_no = ttk.Button(btn_frame, text="No", style="Gray.TButton", command=self.on_no, width=10)
        btn_no.pack(side=tk.RIGHT, padx=(5, 20))
        
        btn_yes = ttk.Button(btn_frame, text="Yes", style="Blue.TButton", command=self.on_yes, width=10)
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
    def __init__(self, root):
        self.root = root
        
    def showinfo(self, title, message):
        CustomMessageDialog(self.root, title, message, "info")
        
    def showerror(self, title, message):
        CustomMessageDialog(self.root, title, message, "error")
        
    def showwarning(self, title, message):
        CustomMessageDialog(self.root, title, message, "warning")
        
    def askyesno(self, title, message):
        dialog = CustomConfirmDialog(self.root, title, message)
        self.root.wait_window(dialog)
        return dialog.result

class CustomAddAddressDialog(tk.Toplevel):
    def __init__(self, parent, addr_type, title="Add Tracked Address"):
        super().__init__(parent)
        self.title(title)
        self.geometry("450x245")
        self.resizable(False, False)
        self.configure(bg=BG_MAIN)
        self.transient(parent)
        self.grab_set()
        
        # Border and borderless
        self.config(bd=1, relief=tk.SOLID, highlightbackground=BORDER_COLOR, highlightcolor=ACCENT_BLUE)
        self.overrideredirect(True)
        
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
        
        # Custom Title Bar
        title_bar = tk.Frame(self, bg=BG_CARD, height=30)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        
        lbl_title_bar = tk.Label(title_bar, text=title, bg=BG_CARD, fg=TEXT_COLOR, font=("Helvetica", 9, "bold"))
        lbl_title_bar.pack(side=tk.LEFT, padx=10)
        
        btn_close = tk.Button(
            title_bar, 
            text="✕", 
            bg=BG_CARD, 
            fg=TEXT_MUTED, 
            activebackground=ACCENT_RED, 
            activeforeground="#ffffff", 
            bd=0, 
            font=("Helvetica", 9), 
            command=self.destroy,
            width=3,
            relief=tk.FLAT
        )
        btn_close.pack(side=tk.RIGHT, fill=tk.Y)
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg="#ffffff"))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg=BG_CARD, fg=TEXT_MUTED))
        
        # Dragging logic
        def start_move(e):
            self.x = e.x
            self.y = e.y
        def drag(e):
            deltax = e.x - self.x
            deltay = e.y - self.y
            self.geometry(f"+{self.winfo_x() + deltax}+{self.winfo_y() + deltay}")
        title_bar.bind("<ButtonPress-1>", start_move)
        title_bar.bind("<B1-Motion>", drag)
        lbl_title_bar.bind("<ButtonPress-1>", start_move)
        lbl_title_bar.bind("<B1-Motion>", drag)
        
        # Main form UI
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
