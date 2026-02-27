import tkinter as tk
from tkinter import ttk

# --- THEME COLORS ---
BG_COLOR = "#2d3436"       # Dark Grey
FG_COLOR = "#dfe6e9"       # Light Grey
ACCENT_COLOR = "#0984e3"   # Bright Blue
HOVER_COLOR = "#74b9ff"    # Lighter Blue
BUTTON_BG = "#636e72"      # Medium Grey
DANGER_COLOR = "#d63031"   # Red
SUCCESS_COLOR = "#00b894"  # Green

class ModernButton(tk.Button):
    """A customizable modern button with hover effects"""
    def __init__(self, master, text, command, bg=ACCENT_COLOR, fg="white", font=("Segoe UI", 10, "bold"), **kwargs):
        super().__init__(master, text=text, command=command, bg=bg, fg=fg, font=font, 
                         relief="flat", activebackground=HOVER_COLOR, activeforeground="white", curs="hand2", **kwargs)
        self.default_bg = bg
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self.config(bg=HOVER_COLOR)

    def on_leave(self, e):
        self.config(bg=self.default_bg)

def apply_theme(root):
    """Applies the dark theme to the root window and basic widgets."""
    root.configure(bg=BG_COLOR)
    
    style = ttk.Style()
    style.theme_use('clam')
    
    style.configure("TFrame", background=BG_COLOR)
    style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR, font=("Segoe UI", 10))
    style.configure("TButton", background=BUTTON_BG, foreground="white", borderwidth=0, focuscolor="none")
    style.map("TButton", background=[("active", HOVER_COLOR)])
