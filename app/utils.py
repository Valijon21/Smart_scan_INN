import ctypes
import os
import sys
import logging

def set_dpi_awareness():
    """Sets the DPI awareness to avoid blurry text on high-res screens."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def get_app_dir():
    """Returns the directory containing the executable or main.py"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_base_path():
    """Returns the base path for resources. Maintained for compatibility."""
    if getattr(sys, 'frozen', False):
        return getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_resource_path(relative_path):
    """
    Get absolute path to a resource.
    First checks next to the executable, then checks inside PyInstaller's _internal.
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        exe_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(exe_path):
            return exe_path
        return os.path.join(getattr(sys, '_MEIPASS', exe_dir), relative_path)
    
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), relative_path)

def get_save_folder():
    """Returns the path to the save folder, creating it if necessary."""
    app_dir = get_app_dir()
    save_folder = os.path.join(app_dir, "ekran_rasimlar")
    
    if not os.path.exists(save_folder):
        try:
            os.makedirs(save_folder)
        except OSError:
            pass
    return save_folder

def setup_logging():
    """Configures logging to write to debug.log in the project root."""
    app_dir = get_app_dir()
    log_file = os.path.join(app_dir, "debug.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("INN_TOp")
