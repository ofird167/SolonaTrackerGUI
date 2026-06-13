import tkinter as tk
from tkinter import ttk

# Colors
BG_MAIN = "#121214"
BG_CARD = "#1a1a1e"
TEXT_COLOR = "#e1e1e6"
TEXT_MUTED = "#8d8d99"
ACCENT_GREEN = "#10b981"
ACCENT_BLUE = "#3b82f6"
ACCENT_RED = "#ef4444"
BORDER_COLOR = "#29292e"

# Application Base64 GIF Icon (16x16 blue circle)
APP_ICON_BASE64 = (
    "R0lGODlhEAAQAPMAAAAAAP///wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
    "ACH5BAEAAAEALAAAAAAQABAAQAM4CLrc/jDKKau9OAuyNu/gGBhCgG3MYKaGia5rurbtGMR0LNf2fed2"
    "D+R8OBwuh8TksIhMDovEYBEIADs="
)

def setup_styles():
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

    # Notebook Tab Styling
    style.configure("TNotebook", background=BG_MAIN, borderwidth=0)
    style.configure("TNotebook.Tab", background=BG_CARD, foreground=TEXT_MUTED, borderwidth=1, bordercolor=BORDER_COLOR, padding=[12, 6], font=("Helvetica", 9, "bold"))
    style.map("TNotebook.Tab", 
              background=[("selected", BG_MAIN), ("active", "#222226")], 
              foreground=[("selected", TEXT_COLOR), ("active", TEXT_COLOR)],
              bordercolor=[("selected", BORDER_COLOR)])
