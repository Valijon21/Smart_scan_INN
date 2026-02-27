import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from PIL import ImageTk, ImageDraw
import os
import subprocess
import io
from datetime import datetime
from .ui import ModernButton, BG_COLOR, FG_COLOR

class Editor:
    def __init__(self, root, image, on_close):
        self.root = root
        self.image = image  # PIL Image
        self.on_close = on_close
        self.draw_color = "red"
        self.is_drawing = False
        self.last_x, self.last_y = None, None

        # Window Setup
        self.editor_window = tk.Toplevel(root)
        self.editor_window.title("Tahrirlash - INN TOp")
        self.editor_window.geometry("1200x9000")
        self.editor_window.state('zoomed')
        self.editor_window.configure(bg=BG_COLOR)
        
        # Toolbar
        self.toolbar = tk.Frame(self.editor_window, bg=BG_COLOR, height=60)
        self.toolbar.pack(fill="x", pady=5)
        
        # Canvas Container (Scrollable)
        self.canvas_frame = tk.Frame(self.editor_window, bg="black")
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="black", highlightthickness=0)
        self.scroll_x = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        
        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)
        
        self.scroll_x.pack(side="bottom", fill="x")
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Image Setup
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # Draw Object (for saving)
        # We draw on the PIL image simultaneously to save it later
        self.draw = ImageDraw.Draw(self.image)

        self._init_buttons()
        self._bind_events()

    def _init_buttons(self):
        # Tools
        btn_frame = tk.Frame(self.toolbar, bg=BG_COLOR)
        btn_frame.pack(side="top")


        
        # Actions
        ModernButton(btn_frame, "💾 Saqlash", self.save_image, bg="#00b894").pack(side="left", padx=20)
        ModernButton(btn_frame, "📋 Nusxalash", self.copy_to_clipboard, bg="#6c5ce7").pack(side="left", padx=5)
        ModernButton(btn_frame, "❌ Yopish", self.close, bg="#d63031").pack(side="left", padx=5)

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

    def activate_pen(self):
        self.is_drawing = True
        self.canvas.config(cursor="pencil")

    def activate_text(self):
        self.is_drawing = False
        self.canvas.config(cursor="xterm")

    def on_press(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        if self.is_drawing:
            self.last_x, self.last_y = x, y
        else:
            # Add text
            text = simpledialog.askstring("Matn", "Matn kiriting:", parent=self.editor_window)
            if text:
                self.canvas.create_text(x, y, text=text, fill="red", font=("Arial", 16, "bold"), anchor="nw")
                self.draw.text((x, y), text, fill="red") # Basic implementation, font might mismatch

    def on_drag(self, event):
        if self.is_drawing and self.last_x:
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            # Draw on Canvas
            self.canvas.create_line(self.last_x, self.last_y, x, y, fill=self.draw_color, width=3, capstyle=tk.ROUND, smooth=True)
            # Draw on PIL Image
            self.draw.line([self.last_x, self.last_y, x, y], fill=self.draw_color, width=3)
            
            self.last_x, self.last_y = x, y

    def on_release(self, event):
        self.last_x, self.last_y = None, None

    def save_image(self):
        filename = f"Screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path = filedialog.asksaveasfilename(defaultextension=".png", 
                                                 initialfile=filename,
                                                 filetypes=[("PNG files", "*.png"), ("All Files", "*.*")])
        if file_path:
            self.image.save(file_path)
            messagebox.showinfo("Saqlandi", f"Rasm saqlandi:\n{file_path}")

    def copy_to_clipboard(self):
        # Save to temp file first to use the PowerShell script method (reliable for files)
        # For bitmap copy without win32clipboard, it's hard in pure python environment without dependencies
        # So we will mimic the user's previous 'silent copy' but for a temp file, 
        # OR we try to use a specific powershell command to set clipboard to image content.
        
        # Method 1: Save to temp and set file drop list (User's preferred way likely)
        import tempfile
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                self.image.save(tmp.name)
                tmp_path = tmp.name
            
            # Use PowerShell to set clipboard to this file path (File Copy)
            path = os.path.abspath(tmp_path).replace("/", "\\")
            ps_script = f"Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Collections.Specialized.StringCollection; $f.Add('{path}'); [System.Windows.Forms.Clipboard]::SetFileDropList($f)"
            
            subprocess.run(["powershell", "-Command", ps_script], creationflags=subprocess.CREATE_NO_WINDOW)
            messagebox.showinfo("Nusxalandi", "Rasm fayl sifatida buferga olindi!")
        except Exception as e:
            messagebox.showerror("Xato", f"Nusxalashda xato: {e}")

    def close(self):
        self.editor_window.destroy()
        if self.on_close:
            self.on_close()
