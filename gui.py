import customtkinter as ctk
import subprocess
import threading
import os
import platform
import shutil
from PIL import Image
from tkinter import messagebox
from core.plugin_loader import cargar_plugins

# --- CONFIGURACIÓN DE COLORES ---
COLOR_BG = ("#F3F4F6", "#0B0910")          
COLOR_SIDEBAR = ("#E5E7EB", "#120E17")     
COLOR_CARD = ("#FFFFFF", "#1A1423")        
COLOR_BORDER = ("#D1D5DB", "#2D1F42")      
COLOR_PRIMARY = ("#7B2CBF", "#9D4EDD")     
COLOR_ACCENT = ("#9D4EDD", "#C77DFF")      
COLOR_RED = ("#DC2626", "#D90429")         
COLOR_GREEN = ("#059669", "#00F5D4")       
COLOR_TEXT = ("#1F2937", "#E0D4F5")        
COLOR_LOG_BG = ("#FFFFFF", "#0B0910")
COLOR_LOG_TEXT = ("#047857", "#00F5D4")

SISTEMA = platform.system()
ctk.set_appearance_mode("dark")
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))

TRADUCCIONES = {
    "es_latam": {"dashboard": "Dashboard", "quarantine": "Cuarentena", "plugins": "Plugins", "settings": "Ajustes", "status": "Estado del Sistema", "protection": "PROTECCIÓN", "threats": "AMENAZAS BLOQUEADAS", "dirs": "DIRECTORIOS", "monitored": "3 Monitoreados", "start": "▶ ACTIVAR ESCUDO", "stop": "⏹ DETENER", "console": "> Consola de Eventos en Tiempo Real", "active": "ACTIVA 🟢", "inactive": "DETENIDA 🔴", "error": "ERROR ⚠️", "settings_title": "⚙️ Ajustes de la Aplicación", "lang_lbl": "Idioma:", "theme_lbl": "Tema Visual:", "theme_dark": "Oscuro", "theme_light": "Claro", "close": "Cerrar", "info": "Información del Sistema", "quar_title": "🗄️ Cuarentena de Archivos", "restore": "Restaurar", "delete": "Eliminar", "empty_q": "No hay archivos bloqueados.", "confirm_del": "¿Eliminar permanentemente?", "restore_err": "No se pudo restaurar.", "plug_title": "🔌 Extensiones y Plugins", "plug_desc": "Plugins cargados desde la carpeta /plugins:", "open_folder": "Abrir Carpeta de Plugins"},
    "en_us": {"dashboard": "Dashboard", "quarantine": "Quarantine", "plugins": "Plugins", "settings": "Settings", "status": "System Status", "protection": "PROTECTION", "threats": "THREATS BLOCKED", "dirs": "DIRECTORIES", "monitored": "3 Monitored", "start": "▶ ACTIVATE SHIELD", "stop": "⏹ STOP", "console": "> Real-time Event Console", "active": "ACTIVE 🟢", "inactive": "STOPPED 🔴", "error": "ERROR ⚠️", "settings_title": "⚙️ App Settings", "lang_lbl": "Language:", "theme_lbl": "Visual Theme:", "theme_dark": "Dark", "theme_light": "Light", "close": "Close", "info": "System Information", "quar_title": "🗄️ File Quarantine", "restore": "Restore", "delete": "Delete", "empty_q": "No blocked files.", "confirm_del": "Permanently delete?", "restore_err": "Could not restore.", "plug_title": "🔌 Extensions & Plugins", "plug_desc": "Plugins loaded from /plugins folder:", "open_folder": "Open Plugins Folder"},
}

IDIOMAS_UI = {"Español (LatAm)": "es_latam", "English (US)": "en_us"}

def procesar_logo():
    ruta = os.path.join(DIRECTORIO_ACTUAL, "logo.png")
    if not os.path.exists(ruta): return None
    img = Image.open(ruta).convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        r, g, b, a = item
        if r > 180 and g > 180 and b > 180: newData.append((255, 255, 255, 0))
        elif r < 80 and g < 80 and b < 80: newData.append((199, 125, 255, 255))
        else: newData.append(item)
    img.putdata(newData)
    ancho, alto = img.size
    img = img.resize((180, int((alto / ancho) * 180)), Image.Resampling.LANCZOS)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(180, int((alto / ancho) * 180)))

class PrivacyGuardApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Privacy Guard - Endpoint Security")
        self.geometry("900x650")
        self.configure(fg_color=COLOR_BG)
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.idioma_actual = "es_latam"

        self.ventanas_hijas = []
        self._last_geom = (0, 0, 900, 650)
        self.bind("<Configure>", self.gestionar_ventanas_hijas)

        self.construir_sidebar()
        self.construir_main_panel()
        self.aplicar_idioma()
        self.check_status()
        self.update_logs()

    def gestionar_ventanas_hijas(self, event):
        if event.widget == self:
            x, y = self.winfo_x(), self.winfo_y()
            w, h = self.winfo_width(), self.winfo_height()
            if (x, y, w, h) == self._last_geom: return
            dw = w - self._last_geom[2]
            dh = h - self._last_geom[3]
            self._last_geom = (x, y, w, h)
            
            for item in list(self.ventanas_hijas):
                v = item["ventana"]
                if v.winfo_exists():
                    if dw != 0 or dh != 0:
                        item["offset_x"] = (w - item["ancho"]) // 2
                        item["offset_y"] = (h - item["alto"]) // 2
                    v.geometry(f"+{x + item['offset_x']}+{y + item['offset_y']}")
                else:
                    self.ventanas_hijas.remove(item)

    def crear_ventana_emergente(self, titulo, ancho, alto):
        v = ctk.CTkToplevel(self)
        v.title(titulo)
        v.overrideredirect(True)
        v.attributes("-topmost", True)
        px, py = self.winfo_x(), self.winfo_y()
        pw, ph = self.winfo_width(), self.winfo_height()
        x, y = px + (pw - ancho) // 2, py + (ph - alto) // 2
        v.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.ventanas_hijas.append({"ventana": v, "ancho": ancho, "alto": alto, "offset_x": x - px, "offset_y": y - py})
        marco = ctk.CTkFrame(v, fg_color=COLOR_BG, border_width=2, border_color=COLOR_BORDER, corner_radius=10)
        marco.pack(fill="both", expand=True)
        return v, marco

    def construir_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color=COLOR_SIDEBAR, border_width=1, border_color=COLOR_BORDER)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(6, weight=1)

        self.logo_img = procesar_logo()
        if self.logo_img:
            self.logo_label = ctk.CTkLabel(self.sidebar, image=self.logo_img, text="")
            self.logo_label.grid(row=0, column=0, pady=(30, 20), padx=20)

        self.btn_dash = ctk.CTkButton(self.sidebar, fg_color=COLOR_CARD, text_color=COLOR_PRIMARY, hover_color=COLOR_BORDER, anchor="w", font=("Segoe UI", 14, "bold"))
        self.btn_dash.grid(row=2, column=0, padx=15, pady=5, sticky="ew")
        
        self.btn_quarantine = ctk.CTkButton(self.sidebar, fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_CARD, anchor="w", font=("Segoe UI", 14), command=self.abrir_ventana_cuarentena)
        self.btn_quarantine.grid(row=3, column=0, padx=15, pady=5, sticky="ew")

        # NUEVO BOTÓN DE PLUGINS
        self.btn_plugins = ctk.CTkButton(self.sidebar, fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_CARD, anchor="w", font=("Segoe UI", 14), command=self.abrir_ventana_plugins)
        self.btn_plugins.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        self.btn_settings = ctk.CTkButton(self.sidebar, fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_CARD, anchor="w", font=("Segoe UI", 14), command=self.abrir_ajustes)
        self.btn_settings.grid(row=5, column=0, padx=15, pady=5, sticky="ew")

        self.label_version = ctk.CTkLabel(self.sidebar, text="v0.1.0 - Open Source", font=("Segoe UI", 10), text_color="#5A4A70")
        self.label_version.grid(row=7, column=0, pady=15)

    def construir_main_panel(self):
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=25, pady=25)

        self.header = ctk.CTkLabel(self.main, font=("Segoe UI", 26, "bold"), text_color=COLOR_TEXT)
        self.header.pack(anchor="w", pady=(0, 20))

        self.stats_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.stats_frame.pack(fill="x", pady=(0, 20))
        
        self.card_status = ctk.CTkFrame(self.stats_frame, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        self.card_status.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.lbl_prot = ctk.CTkLabel(self.card_status, font=("Segoe UI", 11), text_color=COLOR_TEXT)
        self.lbl_prot.pack(pady=(15,0))
        self.label_status = ctk.CTkLabel(self.card_status, text="...", font=("Segoe UI", 20, "bold"))
        self.label_status.pack(pady=(5,15))

        self.card_threats = ctk.CTkFrame(self.stats_frame, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        self.card_threats.pack(side="left", fill="both", expand=True, padx=10)
        self.lbl_threats = ctk.CTkLabel(self.card_threats, font=("Segoe UI", 11), text_color=COLOR_TEXT)
        self.lbl_threats.pack(pady=(15,0))
        self.label_threats = ctk.CTkLabel(self.card_threats, text="0", font=("Segoe UI", 20, "bold"), text_color=COLOR_ACCENT)
        self.label_threats.pack(pady=(5,15))

        self.card_paths = ctk.CTkFrame(self.stats_frame, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        self.card_paths.pack(side="left", fill="both", expand=True, padx=(10, 0))
        self.lbl_dirs = ctk.CTkLabel(self.card_paths, font=("Segoe UI", 11), text_color=COLOR_TEXT)
        self.lbl_dirs.pack(pady=(15,0))
        self.label_paths = ctk.CTkLabel(self.card_paths, font=("Segoe UI", 16, "bold"), text_color=COLOR_TEXT)
        self.label_paths.pack(pady=(7,15))

        self.actions_frame = ctk.CTkFrame(self.main, fg_color="transparent")
        self.actions_frame.pack(fill="x", pady=(0, 20))
        
        self.btn_start = ctk.CTkButton(self.actions_frame, command=self.start_service, fg_color=COLOR_PRIMARY, hover_color=COLOR_ACCENT, font=("Segoe UI", 14, "bold"), height=45, corner_radius=8)
        self.btn_start.pack(side="left", expand=True, padx=(0, 10))
        
        self.btn_stop = ctk.CTkButton(self.actions_frame, command=self.stop_service, fg_color=COLOR_RED, hover_color="#EF233C", font=("Segoe UI", 14, "bold"), height=45, corner_radius=8)
        self.btn_stop.pack(side="left", expand=True, padx=(10, 0))

        self.log_frame = ctk.CTkFrame(self.main, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        self.log_frame.pack(fill="both", expand=True)
        
        self.log_topbar = ctk.CTkFrame(self.log_frame, fg_color=COLOR_SIDEBAR, height=30, corner_radius=8)
        self.log_topbar.pack(fill="x", padx=10, pady=(10, 0))
        self.lbl_console = ctk.CTkLabel(self.log_topbar, font=("Consolas", 12, "bold"), text_color=COLOR_PRIMARY)
        self.lbl_console.pack(side="left", padx=10, pady=5)

        self.log_box = ctk.CTkTextbox(self.log_frame, fg_color=COLOR_LOG_BG, text_color=COLOR_LOG_TEXT, font=("Consolas", 12), corner_radius=8)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

    def aplicar_idioma(self):
        t = TRADUCCIONES[self.idioma_actual]
        self.btn_dash.configure(text=f"📊 {t['dashboard']}")
        self.btn_quarantine.configure(text=f"📁 {t['quarantine']}")
        self.btn_plugins.configure(text=f"🔌 {t['plugins']}")
        self.btn_settings.configure(text=f"⚙️ {t['settings']}")
        self.header.configure(text=t['status'])
        self.lbl_prot.configure(text=t['protection'])
        self.lbl_threats.configure(text=t['threats'])
        self.lbl_dirs.configure(text=t['dirs'])
        self.label_paths.configure(text=t['monitored'])
        self.btn_start.configure(text=t['start'])
        self.btn_stop.configure(text=t['stop'])
        self.lbl_console.configure(text=t['console'])
        self.check_status()

    def get_quarantine_path(self):
        path = os.path.expanduser("~/.local/share/privacy_guard/quarantine")
        if not os.path.exists(path): path = os.path.join(DIRECTORIO_ACTUAL, "quarantine")
        return path

    def abrir_ventana_plugins(self):
        t = TRADUCCIONES[self.idioma_actual]
        v, marco = self.crear_ventana_emergente(t['plugins'], 500, 400)
        
        top_bar = ctk.CTkFrame(marco, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(top_bar, text=t['plug_title'], font=("Segoe UI", 18, "bold"), text_color=COLOR_PRIMARY).pack(side="left", padx=10)
        ctk.CTkButton(top_bar, text="✖", width=30, height=30, fg_color="transparent", hover_color=COLOR_RED, text_color=COLOR_TEXT, command=v.destroy).pack(side="right")

        ctk.CTkLabel(marco, text=t['plug_desc'], font=("Segoe UI", 12), text_color=COLOR_TEXT).pack(pady=5)

        scroll_frame = ctk.CTkScrollableFrame(marco, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Cargar plugins en vivo
        plugins_dir = os.path.join(DIRECTORIO_ACTUAL, "plugins")
        plugins = cargar_plugins(plugins_dir)
        
        if not plugins:
            ctk.CTkLabel(scroll_frame, text="No hay plugins instalados.", text_color=COLOR_TEXT).pack(pady=20)
        else:
            for p in plugins:
                card = ctk.CTkFrame(scroll_frame, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
                card.pack(fill="x", pady=5, padx=5)
                ctk.CTkLabel(card, text=f"✅ {p.__name__}", font=("Segoe UI", 12, "bold"), text_color=COLOR_TEXT, anchor="w").pack(side="left", padx=15, pady=10)

        def abrir_carpeta():
            os.makedirs(plugins_dir, exist_ok=True)
            if SISTEMA == "Windows": os.startfile(plugins_dir)
            else: subprocess.Popen(["xdg-open", plugins_dir])
            
        ctk.CTkButton(marco, text=t['open_folder'], command=abrir_carpeta, fg_color=COLOR_PRIMARY).pack(pady=15)

    def abrir_ventana_cuarentena(self):
        t = TRADUCCIONES[self.idioma_actual]
        v, marco = self.crear_ventana_emergente(t['quarantine'], 600, 500)
        top_bar = ctk.CTkFrame(marco, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(top_bar, text=t['quar_title'], font=("Segoe UI", 18, "bold"), text_color=COLOR_PRIMARY).pack(side="left", padx=10)
        ctk.CTkButton(top_bar, text="✖", width=30, height=30, fg_color="transparent", hover_color=COLOR_RED, text_color=COLOR_TEXT, command=v.destroy).pack(side="right")

        scroll_frame = ctk.CTkScrollableFrame(marco, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        q_path = self.get_quarantine_path()
        try:
            archivos = [f for f in os.listdir(q_path) if not f.endswith('.meta')]
            if not archivos:
                ctk.CTkLabel(scroll_frame, text=t['empty_q'], font=("Segoe UI", 14), text_color=COLOR_TEXT).pack(pady=50)
            else:
                for arch in archivos:
                    filepath = os.path.join(q_path, arch)
                    meta_path = filepath + ".meta"
                    card = ctk.CTkFrame(scroll_frame, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
                    card.pack(fill="x", pady=5, padx=5)
                    txt = arch if len(arch) < 40 else arch[:37] + "..."
                    ctk.CTkLabel(card, text=f"📄 {txt}", font=("Segoe UI", 12, "bold"), text_color=COLOR_TEXT, anchor="w").pack(side="left", padx=15, pady=10)
                    ctk.CTkButton(card, text="🗑️", width=30, fg_color=COLOR_RED, hover_color="#EF233C", command=lambda f=filepath, m=meta_path, vv=v: self.eliminar_archivo(f, m, vv)).pack(side="right", padx=5)
                    ctk.CTkButton(card, text=t['restore'], width=80, fg_color=COLOR_GREEN, hover_color="#10B981", text_color="#000000", command=lambda f=filepath, m=meta_path, vv=v: self.restaurar_archivo(f, m, vv)).pack(side="right", padx=5)
        except FileNotFoundError:
            ctk.CTkLabel(scroll_frame, text=t['empty_q'], font=("Segoe UI", 14), text_color=COLOR_TEXT).pack(pady=50)

    def eliminar_archivo(self, filepath, meta_path, ventana):
        t = TRADUCCIONES[self.idioma_actual]
        if messagebox.askyesno(t['delete'], t['confirm_del']):
            try:
                if os.path.exists(filepath): os.remove(filepath)
                if os.path.exists(meta_path): os.remove(meta_path)
                ventana.destroy()
                self.abrir_ventana_cuarentena()
            except Exception as e: print(f"Error al eliminar: {e}")

    def restaurar_archivo(self, filepath, meta_path, ventana):
        t = TRADUCCIONES[self.idioma_actual]
        try:
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    for l in f.readlines():
                        if l.startswith("original_path="):
                            original_path = l.replace("original_path=", "").strip()
                            shutil.move(filepath, original_path)
                            os.remove(meta_path)
                            ventana.destroy()
                            self.abrir_ventana_cuarentena()
                            return
            shutil.move(filepath, os.path.expanduser(f"~/{os.path.basename(filepath)}"))
            if os.path.exists(meta_path): os.remove(meta_path)
            ventana.destroy()
            self.abrir_ventana_cuarentena()
        except Exception as e:
            messagebox.showerror("Error", f"{t['restore_err']}\n{e}")

    def abrir_ajustes(self):
        t = TRADUCCIONES[self.idioma_actual]
        v, marco = self.crear_ventana_emergente(t['settings'], 450, 550)
        top_bar = ctk.CTkFrame(marco, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(top_bar, text=t['settings_title'], font=("Segoe UI", 18, "bold"), text_color=COLOR_PRIMARY).pack(side="left", padx=10)
        ctk.CTkButton(top_bar, text="✖", width=30, height=30, fg_color="transparent", hover_color=COLOR_RED, text_color=COLOR_TEXT, command=v.destroy).pack(side="right")

        content = ctk.CTkFrame(marco, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20)

        frame_lang = ctk.CTkFrame(content, fg_color="transparent")
        frame_lang.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_lang, text=t['lang_lbl'], font=("Segoe UI", 14), text_color=COLOR_TEXT).pack(anchor="w")
        combo_lang = ctk.CTkOptionMenu(frame_lang, values=list(IDIOMAS_UI.keys()), fg_color=COLOR_PRIMARY, command=self.cambiar_idioma)
        combo_lang.set([k for k, v_ in IDIOMAS_UI.items() if v_ == self.idioma_actual][0])
        combo_lang.pack(fill="x", pady=5)

        frame_theme = ctk.CTkFrame(content, fg_color="transparent")
        frame_theme.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_theme, text=t['theme_lbl'], font=("Segoe UI", 14), text_color=COLOR_TEXT).pack(anchor="w")
        combo_theme = ctk.CTkOptionMenu(frame_theme, values=[t['theme_dark'], t['theme_light']], fg_color=COLOR_PRIMARY, command=self.cambiar_tema)
        combo_theme.set(t['theme_dark'] if ctk.get_appearance_mode() == "Dark" else t['theme_light'])
        combo_theme.pack(fill="x", pady=5)
        
        info_frame = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        info_frame.pack(pady=10, fill="both", expand=True)
        ctk.CTkLabel(info_frame, text=f"{t['info']}:\nS.O: {SISTEMA}\nPython: {platform.python_version()}\nDir: {DIRECTORIO_ACTUAL}", justify="left", font=("Consolas", 11), text_color=COLOR_TEXT).pack(padx=20, pady=20, anchor="w")

    def cambiar_idioma(self, seleccion):
        self.idioma_actual = IDIOMAS_UI[seleccion]
        self.aplicar_idioma()

    def cambiar_tema(self, seleccion):
        ctk.set_appearance_mode("dark" if seleccion in ["Oscuro", "Dark"] else "light")

    def start_service(self):
        t = TRADUCCIONES[self.idioma_actual]
        self.log_box.insert("end", f"\n[*] {t['start']}...\n")
        try:
            if SISTEMA == "Windows": subprocess.run(["schtasks", "/run", "/tn", "PrivacyGuard_Engine"], check=False, timeout=5)
            else: subprocess.run(["systemctl", "--user", "restart", "privacy-guard"], check=False, timeout=5)
        except: pass
        self.check_status()

    def stop_service(self):
        t = TRADUCCIONES[self.idioma_actual]
        self.log_box.insert("end", f"\n[!] {t['stop']}...\n")
        try:
            if SISTEMA == "Windows": subprocess.run(["schtasks", "/end", "/tn", "PrivacyGuard_Engine"], check=False, timeout=5)
            else: subprocess.run(["systemctl", "--user", "stop", "privacy-guard"], check=False, timeout=5)
        except: pass
        self.check_status()

    def check_status(self):
        t = TRADUCCIONES[self.idioma_actual]
        try:
            if SISTEMA == "Windows": self.label_status.configure(text=t['active'], text_color=COLOR_GREEN)
            else:
                result = subprocess.run(["systemctl", "--user", "is-active", "privacy-guard"], capture_output=True, text=True, timeout=3)
                if result.stdout.strip() == "active": self.label_status.configure(text=t['active'], text_color=COLOR_GREEN)
                else: self.label_status.configure(text=t['inactive'], text_color=COLOR_RED)
        except Exception: self.label_status.configure(text=t['error'], text_color="#FFD166")

    def update_logs(self):
        def fetch():
            try:
                if SISTEMA == "Windows": return "[*] Motor activo.\n"
                result = subprocess.run(["journalctl", "--user", "-u", "privacy-guard", "-n", "20", "--no-pager"], capture_output=True, text=True, timeout=3)
                return result.stdout
            except Exception as e: return f"[!] Error: {e}"

        def update_ui():
            self._apply_logs(fetch())
            self.after(5000, self.update_logs)

        threading.Thread(target=lambda: self.after(0, update_ui), daemon=True).start()

    def _apply_logs(self, logs):
        self.log_box.delete("1.0", "end")
        self.log_box.insert("1.0", logs)
        self.log_box.see("end")

if __name__ == "__main__":
    app = PrivacyGuardApp()
    app.mainloop()
