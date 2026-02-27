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

def get_base_path():
    """Returns the base path for resources, compatible with PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_save_folder():
    """Returns the path to the save folder, creating it if necessary."""
    base_path = get_base_path()
    project_root = os.path.dirname(base_path) 
    save_folder = os.path.join(project_root, "ekran_rasimlar")
    
    if not os.path.exists(save_folder):
        try:
            os.makedirs(save_folder)
        except OSError:
            pass
    return save_folder

def setup_logging():
    """Configures logging to write to debug.log in the project root."""
    base_path = get_base_path()
    project_root = os.path.dirname(base_path)
    log_file = os.path.join(project_root, "debug.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("INN_TOp")
