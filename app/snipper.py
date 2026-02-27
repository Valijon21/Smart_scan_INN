import tkinter as tk
from PIL import ImageGrab, ImageTk
from .utils import set_dpi_awareness
import ctypes

class Snipper:
    def __init__(self, root, on_capture):
        self.root = root
        self.on_capture = on_capture
        self.snip_surface = None
        self.start_x = None
        self.start_y = None
        self.current_rect = None
        self.screen_image = None
        self.tk_image = None

    def start_capture(self):
        """Captures screen immediately and opens a freeze-frame overlay."""
        # 0. Wait a tiny bit for the main window to hide
        self.root.update()
        
        # 1. Grab the screen immediately
        try:
            self.screen_image = ImageGrab.grab(all_screens=True)
            self.tk_image = ImageTk.PhotoImage(self.screen_image)
        except Exception as e:
            print(f"Screen grab failed: {e}")
            return

        # 2. Create Fullscreen Window (Virtual Screen)
        self.snip_surface = tk.Toplevel(self.root)
        
        # Get Virtual Screen Metrics for Multi-monitor support
        user32 = ctypes.windll.user32
        x = user32.GetSystemMetrics(76) # SM_XVIRTUALSCREEN
        y = user32.GetSystemMetrics(77) # SM_YVIRTUALSCREEN
        w = user32.GetSystemMetrics(78) # SM_CXVIRTUALSCREEN
        h = user32.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
        
        self.snip_surface.geometry(f"{w}x{h}+{x}+{y}")
        self.snip_surface.overrideredirect(True) # Remove title bar/borders
        self.snip_surface.attributes("-topmost", True)
        self.snip_surface.configure(cursor="cross")

        # 3. Canvas with the screenshot
        self.canvas = tk.Canvas(self.snip_surface, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Draw the image
        self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")

        # 4. Create a "Dim" layer (semi-transparent black rectangle covering everything)
        # Tkinter canvas doesn't support alpha on shapes well, so we simulate or check bounds.
        # Alternatively, we just draw the red rectangle on top. 
        # For a "Dim" effect in pure Tkinter without alpha bugs, we can use a stipple or just good UI feedback.
        # Let's keep it simple and performant: Just the image and a selection rectangle.
        
        self.snip_surface.bind("<ButtonPress-1>", self.on_button_press)
        self.snip_surface.bind("<B1-Motion>", self.on_move_press)
        self.snip_surface.bind("<ButtonRelease-1>", self.on_button_release)
        self.snip_surface.bind("<Escape>", lambda e: self.snip_surface.destroy())
        
        # 5. Bring to front
        self.snip_surface.lift()
        self.snip_surface.focus_force()

    def on_button_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="#ff0000", width=3)

    def on_move_press(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.current_rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        
        self.snip_surface.destroy()
        
        # Correct coordinates (handle negative drag)
        x1 = min(self.start_x, end_x)
        y1 = min(self.start_y, end_y)
        x2 = max(self.start_x, end_x)
        y2 = max(self.start_y, end_y)

        if abs(x2 - x1) < 5 or abs(y2 - y1) < 5:
            return

        # Crop from the original captured image
        # Note: We must consider if the Canvas loaded coordinates 1:1. 
        # If HighDPI awareness is ON, it should be fine.
        try:
            cropped_image = self.screen_image.crop((x1, y1, x2, y2))
            self.on_capture(cropped_image)
        except Exception as e:
            print(f"Crop failed: {e}")
