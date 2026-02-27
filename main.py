import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab
import sys
import os
import ctypes # Added for global hotkeys

# Ensure we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.ui import apply_theme, ModernButton, BG_COLOR, FG_COLOR
from app.utils import set_dpi_awareness, get_base_path, get_save_folder, setup_logging
from app.snipper import Snipper
from app.editor import Editor

# Setup Logging
logger = setup_logging()
logger.info("Application starting...")
from datetime import datetime

class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("INN TOp - Screenshot Tool")
        self.root.geometry("1200x900")
        self.root.resizable(False, False)
        
        set_dpi_awareness()
        apply_theme(self.root)
        
        self.snipper = Snipper(root, self.on_capture)
        
        self._init_ui()
        
        # Global Hotkey State
        self._f8_pressed = False
        self._f9_pressed = False
        self._start_global_hotkeys()

    def _start_global_hotkeys(self):
        """Starts a polling loop to check for global key presses."""
        self._check_hotkeys()

    def _check_hotkeys(self):
        # F8 key code = 0x77
        if ctypes.windll.user32.GetAsyncKeyState(0x77) & 0x8000:
            if not self._f8_pressed:
                self._f8_pressed = True
                self.root.after(0, self.capture_full)
        else:
            self._f8_pressed = False

        # F9 key code = 0x78
        if ctypes.windll.user32.GetAsyncKeyState(0x78) & 0x8000:
            if not self._f9_pressed:
                self._f9_pressed = True
                self.root.after(0, self.capture_region)
        else:
            self._f9_pressed = False
            
        # Poll every 50ms
        self.root.after(50, self._check_hotkeys)

    def _init_ui(self):
        # Header
        header = tk.Label(self.root, text="INN TOp Capture", font=("Segoe UI", 24, "bold"), bg=BG_COLOR, fg=FG_COLOR)
        header.pack(pady=40)
        
        # Buttons
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=10)
        
        ModernButton(btn_frame, "To'liq Ekran (F8)", self.capture_full, width=40,height=3).pack(side="left", padx=20, pady=10)
        ModernButton(btn_frame, "Kesish (Region) (F9)", self.capture_region, width=40,height=3, bg="#6c5ce7").pack(side="left", padx=20, pady=10)
        ModernButton(btn_frame, "Tarix (History)", self.show_history, width=30,height=3, bg="#f39c12").pack(side="left", padx=20, pady=10)
        
        # Options
        self.autosave_var = tk.BooleanVar(value=True)
        chk = tk.Checkbutton(self.root, text="Avtomatik INN Qidirish", variable=self.autosave_var, 
                             bg=BG_COLOR, fg=FG_COLOR, selectcolor=BG_COLOR, activebackground=BG_COLOR, activeforeground=FG_COLOR)
        chk.pack(pady=5)

        # --- MANUAL INN SEARCH ---
        search_frame = tk.Frame(self.root, bg=BG_COLOR)
        search_frame.pack(pady=10)

        tk.Label(search_frame, text="Tashkilot nomi yoki raqami yozing:", font=("Segoe UI", 12, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(side="left", padx=5)
        
        # Adjusted width to fit window
        self.manual_inn_entry = tk.Entry(search_frame, font=("Segoe UI", 16), width=28) 
        self.manual_inn_entry.pack(side="left", padx=10)
        self.manual_inn_entry.bind("<Return>", lambda event: self.manual_search())
        
        ModernButton(search_frame, "Qidirish", self.manual_search, width=15, height=1, bg="#00b894").pack(side="left", padx=10)

        # Footer
        tk.Label(self.root, text="INN Top  v1.1  Dasturchi : Valijon Ergashev  Tel:773423321", font=("Segoe UI", 18), bg=BG_COLOR, fg="#636e72").pack(side="bottom", pady=20)

    def manual_search(self):
        query = self.manual_inn_entry.get().strip()
        if not query:
            messagebox.showwarning("Diqqat", "Iltimos, INN yoki Tashkilot nomini kiriting!")
            return
        
        try:
            # Import logic
            from app.ocr_service import search_organizations
            
            results = search_organizations(query)
            
            if not results:
                messagebox.showwarning("Topilmadi", f"Soruv: '{query}' bo'yicha hech qanday tashkilot topilmadi.")
                return

            if len(results) == 1:
                res = results[0]
                # Display with larger font in a custom message box if possible, but standard messagebox font is fixed.
                # However, the user asked for "shriftlanri kattalashtir" for the result dialog specifically.
                person = res.get('person', '')
                phone = res.get('phone', '')
                phone_str = f"Tel: {phone}" if phone else "Tel: Nomer yo'q"
                msg = f"Topildi:\n\nINN: {res['inn']}\nTashkilot: {res['name']}\nRahbar: {person}\n{phone_str}"
                messagebox.showinfo("Natija", msg)
            else:
                # Multiple results
                msg = f"'{query}' bo'yicha {len(results)} ta tashkilot topildi:\n\n"
                for res in results[:10]: # Show top 10 max
                    person = res.get('person', '')
                    phone = res.get('phone', '')
                    phone_str = f"Tel: {phone}" if phone else "Tel: Nomer yo'q"
                    msg += f"🔹 {res['name']}\n   Rahbar: {person}\n   {phone_str}\n   INN: {res['inn']}\n\n"
                
                if len(results) > 10:
                    msg += f"\n... va yana {len(results)-10} ta."
                    
                messagebox.showinfo("Qidiruv Natijasi", msg)
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            messagebox.showerror("Xato", f"Qidirishda xatolik: {e}")

    def capture_full(self):
        self.root.withdraw()
        try:
            # Small delay to ensure window is gone
            self.root.after(200, self._perform_full_capture)
        except Exception as e:
            self.show_error(e)
            self.root.deiconify()

    def _perform_full_capture(self):
        try:
            img = ImageGrab.grab(all_screens=True)
            self.on_capture(img)
        except Exception as e:
            self.show_error(e)
            self.root.deiconify()

    def capture_region(self):
        self.root.withdraw()
        # Give time for withdraw
        self.root.after(200, self.snipper.start_capture)

    def on_capture(self, image):
        """Callback when an image is captured."""
        self.root.deiconify() # Restore main window
        # 1. Autosave
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            filename = f"Screen_{timestamp}.png"
            folder = get_save_folder()
            save_path = os.path.join(folder, filename)
            # Save image
            self.last_capture_path = save_path
            image.save(save_path)
            logger.info(f"Captured image saved to: {save_path}")

            # Open Editor
            # self.open_editor(image) # Editor expects PIL Image object, not path
            
            # --- AUTOSAVE & RENAME LOGIC ---
            if self.autosave_var.get():
                logger.info("Autosave/Rename Triggered")
                
                # --- OCR CHECK ---
                from app.ocr_service import extract_text_from_image, find_inn_in_text, lookup_company_by_inn
                
                # Run OCR in background
                result_text = extract_text_from_image(save_path)
                
                # --- SAVE TXT ---
                try:
                    txt_path = os.path.splitext(save_path)[0] + ".txt"
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(result_text)
                    logger.debug(f"Saved text to: {txt_path}")
                except Exception as e:
                    logger.error(f"Failed to save txt: {e}")
                # ----------------

                inn = find_inn_in_text(result_text)
                company_name_found = None
                company_person_found = None
                company_phone_found = None
                
                # Strategy 1: Find by INN
                if inn:
                    logger.info(f"INN Found: {inn}")
                    lookup_result = lookup_company_by_inn(inn)
                    if lookup_result:
                        company_name_found = lookup_result.get('name')
                        company_person_found = lookup_result.get('person')
                        company_phone_found = lookup_result.get('phone')
                
                # Strategy 2: Find by Name (if INN failed or Name not found for INN)
                if not company_name_found:
                     from app.ocr_service import find_organization_in_text
                     # Updated to receive 4 values
                     potential_name, matched_inn, potential_person, potential_phone = find_organization_in_text(result_text)
                     
                     if potential_name:
                         logger.info(f"Organization Found by Text Match: {potential_name}")
                         company = potential_name
                         # Update INN if we found it in DB match but OCR missed it
                         if not inn and matched_inn:
                             inn = matched_inn
                             logger.info(f"INN Auto-filled from DB match: {inn}")
                         
                         # Use dummy INN or empty for filename if still missing
                         inn = inn if inn else "INN_TOPILMADI" 
                         company_name_found = potential_name
                         company_person_found = potential_person
                         company_phone_found = potential_phone

                # Rename Logic
                if inn or company_name_found:
                    safe_inn = str(inn).strip() if (inn and inn != "INN_TOPILMADI") else "INN-yuq"
                    
                    safe_company = "Tashkilot-yuq"
                    if company_name_found:
                        safe_company = "".join([c for c in company_name_found if c.isalnum() or c in (' ', '_', '-')]).strip()
                        if not safe_company: 
                            safe_company = "Tashkilot-yuq"
                            
                    safe_person = "FISH-yuq"
                    if company_person_found:
                        safe_person = "".join([c for c in company_person_found if c.isalnum() or c in (' ', '_', '-')]).strip()
                        if not safe_person: 
                            safe_person = "FISH-yuq"
                            
                    safe_phone = "Tel-yuq"
                    if company_phone_found:
                        cleaned_phone = "".join([c for c in company_phone_found if c.isalnum() or c == '+']).strip()
                        if cleaned_phone:
                            safe_phone = f"Tel-{cleaned_phone}"
                            
                    # Fayl nomiga barchasini qo'shish (INN_Tashkilot_FISH_Tel.png)
                    new_filename = f"{safe_inn}_{safe_company}_{safe_person}_{safe_phone}.png"
                    
                    # Fayl nomidagi ortiqcha chiziqlarni go'zallashtirish
                    new_filename = new_filename.replace("  ", " ").strip()

                    
                    new_path = os.path.join(folder, new_filename)
                    
                    # Handle Duplicate Names
                    counter = 1
                    base_name, ext = os.path.splitext(new_filename)
                    while os.path.exists(new_path):
                        new_path = os.path.join(folder, f"{base_name}_{counter}{ext}")
                        counter += 1
                    
                    try:
                        os.rename(save_path, new_path)
                        save_path = new_path # Update path for Editor
                        
                        # Update TXT filename too if it exists
                        try:
                            old_txt = os.path.splitext(self.last_capture_path)[0] + ".txt"
                            new_txt = os.path.splitext(new_path)[0] + ".txt"
                            if os.path.exists(old_txt):
                                os.rename(old_txt, new_txt)
                        except: pass
                        
                        self.last_capture_path = new_path # Update reference
                        logger.info(f"Renamed file to: {new_path}")
                    except Exception as ren_err:
                        logger.error(f"Rename failed: {ren_err}")
                else:
                    logger.info("No INN or Organization found. File kept as original.")
                    new_path = save_path
                
                # Show Result Dialog
                self.root.after(100, lambda: self.show_result_dialog(inn, company_name_found, company_person_found, company_phone_found, new_path))
        except Exception as e:
            logger.error(f"Error in on_capture: {e}")
            self.show_error(e)

    def show_result_dialog(self, inn, org_name, person_name, phone, file_path):
        """Displays a custom dialog with OCR results. Refactored for larger fonts."""
        try:
            dialog = tk.Toplevel(self.root)
            dialog.title("Natija")
            dialog.geometry("1000x950") # Increased size
            dialog.configure(bg=BG_COLOR)
            dialog.lift()
            dialog.attributes('-topmost', True)
            
            # Larger Font Settings
            LABEL_FONT = ("Segoe UI", 22, "bold") # Was 12 bold
            VALUE_FONT = ("Segoe UI", 22)         # Was 10
            HEADER_FONT = ("Segoe UI", 24, "bold")
            
            tk.Label(dialog, text="✅ Rasm tahlil qilindi!", font=HEADER_FONT, bg=BG_COLOR, fg="#00b894").pack(pady=15)
            
            # --- IMAGE PREVIEW ---
            try:
                from PIL import Image, ImageTk
                img = Image.open(file_path)
                # Resize for preview
                img.thumbnail((500, 350)) 
                photo = ImageTk.PhotoImage(img)
                
                img_label = tk.Label(dialog, image=photo, bg=BG_COLOR)
                img_label.image = photo # Keep reference
                img_label.pack(pady=10)
            except Exception as img_err:
                logger.error(f"Failed to load preview: {img_err}")
                tk.Label(dialog, text="(Rasm yuklanmadi)", bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)
            # ---------------------

            # Details Frame
            frame = tk.Frame(dialog, bg=BG_COLOR)
            frame.pack(pady=10, padx=20, fill="x")
            
            # Helper for grid rows
            current_row = 0
            
            def add_row(label_text, value_text, color=FG_COLOR):
                nonlocal current_row
                tk.Label(frame, text=label_text, font=LABEL_FONT, bg=BG_COLOR, fg=FG_COLOR).grid(row=current_row, column=0, sticky="w", pady=5)
                tk.Label(frame, text=value_text, font=VALUE_FONT, bg=BG_COLOR, fg=color, wraplength=500, justify="left").grid(row=current_row, column=1, sticky="w", padx=15)
                current_row += 1

            # INN
            add_row("INN:", str(inn) if inn else "⚠️ Topilmadi")

            # Tashkilot
            add_row("Tashkilot:", str(org_name) if org_name else "⚠️ Topilmadi")
            
            # NEW: Rahbar (Person)
            if person_name:
                add_row("Rahbar:", str(person_name), color="#fdcb6e") # Orange-ish for person

            # NEW: Phone
            phone_text = f"Tel: {phone}" if phone else "Tel: Nomer yo'q"
            phone_color = "#55efc4" if phone else "#ff7675" # Green if exists, Red if not
            add_row("", phone_text, color=phone_color)

            # File
            add_row("Fayl:", os.path.basename(file_path), color="#74b9ff")

            # Buttons
            btn_frame = tk.Frame(dialog, bg=BG_COLOR)
            btn_frame.pack(pady=20)
            
            def open_folder():
                folder = os.path.dirname(file_path)
                os.startfile(folder)
                dialog.destroy()
                
            def on_edit():
                from PIL import Image
                try:
                    img = Image.open(file_path)
                    self.open_editor(img)
                    dialog.destroy()
                except Exception as ex:
                    logger.error(f"Failed to open editor: {ex}")
            
            # Button sizes also increased? Maybe keep them standard but larger text
            ModernButton(btn_frame, "✏️ Tahrirlash", on_edit, width=20, height=2, bg="#6c5ce7").pack(side="left", padx=10)
            ModernButton(btn_frame, "📂 Papkani Ochish", open_folder, width=20, height=2, bg="#0984e3").pack(side="left", padx=10)
            ModernButton(btn_frame, "Yopish", dialog.destroy, width=15, height=2, bg="#636e72").pack(side="left", padx=10)

        except Exception as e:
            logger.error(f"Error showing dialog: {e}")
                # But currently Editor is initialized with just Image.
                # If we want Editor to know the filename, we should have passed it or updated it.
                # For now, it's fine. editor 'save' asks for path usually or we can improve it later.
            pass
        except KeyboardInterrupt:
            raise
        except Exception as e:
            print(f"Autosave/OCR failed: {e}")
            logger.error(f"Autosave/OCR failed: {e}")

        # 2. Open Editor (This was moved to the top of the try block)

    def open_editor(self, image):
        Editor(self.root, image, self.on_editor_close)

    def on_editor_close(self):
        self.root.deiconify()

    def show_error(self, message):
        messagebox.showerror("Xato", str(message))

    def show_history(self):
        """Displays a history window of previously saved images and their parse results."""
        history_dialog = tk.Toplevel(self.root)
        history_dialog.title("Tarix (History)")
        history_dialog.geometry("1100x800")
        history_dialog.configure(bg=BG_COLOR)
        history_dialog.lift()
        
        tk.Label(history_dialog, text="📜 Saqlangan Rasmlar Tarixi", font=("Segoe UI", 24, "bold"), bg=BG_COLOR, fg="#f39c12").pack(pady=10)
        
        # Main Layout: Listbox on left, Details on right
        paned = tk.PanedWindow(history_dialog, orient=tk.HORIZONTAL, bg=BG_COLOR, sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # --- LEFT PANEL (List of images) ---
        left_frame = tk.Frame(paned, bg=BG_COLOR)
        paned.add(left_frame, minsize=350)
        
        tk.Label(left_frame, text="Ro'yxat", font=("Segoe UI", 14, "bold"), bg=BG_COLOR, fg=FG_COLOR).pack(pady=5)
        
        listbox_frame = tk.Frame(left_frame, bg=BG_COLOR)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_listbox = tk.Listbox(listbox_frame, font=("Segoe UI", 12), bg="#2d3436", fg=FG_COLOR, 
                                          selectbackground="#0984e3", yscrollcommand=scrollbar.set)
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_listbox.yview)
        
        # --- RIGHT PANEL (Details View) ---
        right_frame = tk.Frame(paned, bg=BG_COLOR)
        paned.add(right_frame, minsize=650)
        
        # Image Preview
        self.preview_label = tk.Label(right_frame, bg=BG_COLOR, text="Rasm ustiga bosing", fg="#636e72", font=("Segoe UI", 14))
        self.preview_label.pack(pady=10)
        
        # Details Text
        details_frame = tk.Frame(right_frame, bg=BG_COLOR)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.details_text = tk.Text(details_frame, font=("Segoe UI", 14), bg="#2d3436", fg=FG_COLOR, wrap="word", state="disabled", height=10)
        self.details_text.pack(fill=tk.BOTH, expand=True)
        
        # Action Buttons
        btn_frame = tk.Frame(right_frame, bg=BG_COLOR)
        btn_frame.pack(pady=10)
        
        ModernButton(btn_frame, "Ochish (Folder)", lambda: self._open_history_folder(self.history_files), width=20, height=1, bg="#0984e3").pack(side="left", padx=5)
        ModernButton(btn_frame, "Matn (TXT)", lambda: self._open_history_txt(self.history_files), width=20, height=1, bg="#00b894").pack(side="left", padx=5)
        
        # Load Files
        self.history_files = [] # Store full paths
        self._load_history()
        
        # Bind selection event
        self.history_listbox.bind('<<ListboxSelect>>', self._on_history_select)

    def _load_history(self):
        folder = get_save_folder()
        self.history_listbox.delete(0, tk.END)
        self.history_files.clear()
        
        # Get png files, sort by modify time descending
        try:
            files = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".png")]
            files.sort(key=os.path.getmtime, reverse=True)
            
            for file_path in files:
                self.history_files.append(file_path)
                filename = os.path.basename(file_path)
                # Show simpler name in list
                display_name = filename
                if display_name.startswith("Screen_"):
                    display_name = "Kiritilmagan rasm (" + display_name[7:23] + ")"
                self.history_listbox.insert(tk.END, display_name)
                
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self.history_listbox.insert(tk.END, "Xatolik yuz berdi")

    def _on_history_select(self, event):
        selection = event.widget.curselection()
        if not selection: return
        index = selection[0]
        file_path = self.history_files[index]
        
        # 1. Update Image Preview
        try:
            from PIL import Image, ImageTk
            img = Image.open(file_path)
            img.thumbnail((450, 450)) 
            photo = ImageTk.PhotoImage(img)
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo
        except Exception as e:
            self.preview_label.config(image='', text="(Rasm yuklanmadi)")
            
        # 2. Update Details
        filename = os.path.basename(file_path)
        details = f"Fayl nomi:\n{filename}\n\n"
        
        try:
            mtime = os.path.getmtime(file_path)
            dt = datetime.fromtimestamp(mtime)
            details += f"Sana va Vaqt: {dt.strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        except Exception:
            pass
        
        # Try to parse properties from filename
        # Expected format: INN_Tashkilot_FISH_Tel.png
        parts = os.path.splitext(filename)[0].split("_", 3)
        if len(parts) >= 2 and not filename.startswith("Screen_"):
            details += f"INN: {parts[0]}\n"
            details += f"Tashkilot: {parts[1]}\n"
            if len(parts) >= 3: details += f"FISH: {parts[2]}\n"
            if len(parts) >= 4: details += f"Telefon: {parts[3].replace('Tel-', '')}\n"
        else:
             details += "Holat: Aniqlanmagan (Yoki eski format)\n"
             
        # Add OCR Text if available
        txt_path = os.path.splitext(file_path)[0] + ".txt"
        details += "\n\nO'qilgan Matnlar:\n" + ("-"*30) + "\n"
        if os.path.exists(txt_path):
            try:
                with open(txt_path, "r", encoding="utf-8") as f:
                    txt = f.read().strip()
                    details += txt if txt else "(Matn bo'sh)"
            except:
                details += "(Matn o'qishda xato)"
        else:
            details += "(TXT fayl topilmadi)"
            
        self.details_text.config(state="normal")
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(tk.END, details)
        self.details_text.config(state="disabled")

    def _open_history_folder(self, files_list):
        selection = self.history_listbox.curselection()
        # If specific file selected, open folder and highlight, else normal
        if selection:
            filepath = files_list[selection[0]]
            subprocess.Popen(f'explorer /select,"{filepath}"')
        else:
            os.startfile(get_save_folder())

    def _open_history_txt(self, files_list):
        selection = self.history_listbox.curselection()
        if selection:
            filepath = files_list[selection[0]]
            txt_path = os.path.splitext(filepath)[0] + ".txt"
            if os.path.exists(txt_path):
                os.startfile(txt_path)
            else:
                messagebox.showinfo("Malumot", "Ushbu rasm uchun TXT matni saqlanmagan.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()