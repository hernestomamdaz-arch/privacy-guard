import customtkinter as ctk
import subprocess
import threading
import os
import platform
import shutil
import send2trash
import json
import psutil
from tkinter import filedialog
from PIL import Image
from core.plugin_loader import cargar_plugins
from core.database import obtener_eventos

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
COLOR_GRAY = ("#9CA3AF", "#4B5563")

SISTEMA = platform.system()
ctk.set_appearance_mode("dark")
DIRECTORIO_ACTUAL = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(DIRECTORIO_ACTUAL, "config.json")

TRADUCCIONES = {
    "es_latam": {"dashboard": "Dashboard", "quarantine": "Cuarentena", "plugins": "Plugins", "settings": "Ajustes", "status": "Estado del Sistema", "protection": "PROTECCIÓN", "threats": "AMENAZAS BLOQUEADAS", "dirs": "DIRECTORIOS", "monitored": "Protegidos", "start": "▶ ACTIVAR ESCUDO", "stop": "⏹ DETENER", "console": "🛡️ Historial de Protección", "active": "ACTIVA 🟢", "inactive": "DETENIDA 🔴", "error": "ERROR ⚠️", "settings_title": "⚙️ Ajustes de la Aplicación", "lang_lbl": "Idioma:", "theme_lbl": "Tema Visual:", "theme_dark": "Oscuro", "theme_light": "Claro", "show_quar": "Mostrar pestaña de Cuarentena", "show_plug": "Mostrar pestaña de Plugins", "add_dir": "➕ Añadir Carpeta a Proteger", "info": "Información del Sistema", "quar_title": "🗄️ Cuarentena de Archivos", "restore": "Restaurar", "delete": "Papelera", "empty_q": "No hay archivos bloqueados.", "plug_title": "🔌 Extensiones y Plugins", "plug_desc": "Plugins cargados desde la carpeta /plugins:", "open_folder": "Abrir Carpeta de Plugins", "confirm_trash": "¿Mover este archivo a la papelera?", "yes": "Sí, mover", "no": "Cancelar", "empty_logs": "Aún no hay actividad. El sistema está seguro.", "kill_btn": "🔪 Neutralizar", "killed_btn": "Neutralizado"},
    "en_us": {"dashboard": "Dashboard", "quarantine": "Quarantine", "plugins": "Plugins", "settings": "Settings", "status": "System Status", "protection": "PROTECTION", "threats": "THREATS BLOCKED", "dirs": "DIRECTORIES", "monitored": "Protected", "start": "▶ ACTIVATE SHIELD", "stop": "⏹ STOP", "console": "🛡️ Protection History", "active": "ACTIVE 🟢", "inactive": "STOPPED 🔴", "error": "ERROR ⚠️", "settings_title": "⚙️ App Settings", "lang_lbl": "Language:", "theme_lbl": "Visual Theme:", "theme_dark": "Dark", "theme_light": "Light", "show_quar": "Show Quarantine tab", "show_plug": "Show Plugins tab", "add_dir": "➕ Add Folder to Protect", "info": "System Information", "quar_title": "🗄️ File Quarantine", "restore": "Restore", "delete": "Trash", "empty_q": "No blocked files.", "plug_title": "🔌 Extensions & Plugins", "plug_desc": "Plugins loaded from /plugins folder:", "open_folder": "Open Plugins Folder", "confirm_trash": "Move this file to trash?", "yes": "Yes, move", "no": "Cancel", "empty_logs": "No activity yet. System is safe.", "kill_btn": "🔪 Neutralize", "killed_btn": "Neutralized"},
}

IDIOMAS_UI = {"Español (LatAm)": "es_latam", "English (US)": "en_us"}

def cargar_config():
    default_config = {"mostrar_cuarentena": True, "mostrar_plugins": True, "idioma": "es_latam", "rutas_extra": []}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f: return {**default_config, **json.load(f)}
        except: return default_config
    return default_config

def guardar_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f: json.dump(config, f, indent=4)

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
        
        self.config_data = cargar_config()
        self.idioma_actual = self.config_data.get("idioma", "es_latam")
        self.pids_neutralizados = set()

        self.ventanas_hijas = []
        self._last_geom = (0, 0, 900, 650)
        
        self.bind("<Configure>", self.gestionar_ventanas_hijas)
        self.bind("<Unmap>", self.ocultar_hijas)
        self.bind("<Map>", self.mostrar_hijas)

        self.construir_sidebar()
        self.construir_main_panel()
        self.aplicar_idioma()
        self.check_status()
        self.update_logs()

    def ocultar_hijas(self, event):
        if event.widget == self:
            for item in self.ventanas_hijas:
                v = item["ventana"]
                if v.winfo_exists(): v.withdraw()

    def mostrar_hijas(self, event):
        if event.widget == self:
            for item in self.ventanas_hijas:
                v = item["ventana"]
                if v.winfo_exists(): v.deiconify()

    def gestionar_ventanas_hijas(self, event):
        if event.widget == self:
            if self.state() == 'iconic': return
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
        v.transient(self)
        v.overrideredirect(True)
        v.attributes("-topmost", True)
        
        px, py = self.winfo_x(), self.winfo_y()
        pw, ph = self.winfo_width(), self.winfo_height()
        x, y = px + (pw - ancho) // 2, py + (ph - alto) // 2
        v.geometry(f"{ancho}x{alto}+{x}+{y}")
        
        self.ventanas_hijas.append({"ventana": v, "ancho": ancho, "alto": alto, "offset_x": x - px, "offset_y": y - py})
        
        marco = ctk.CTkFrame(v, fg_color=COLOR_BG, border_width=2, border_color=COLOR_BORDER, corner_radius=10)
        marco.pack(fill="both", expand=True)
        
        top_bar = ctk.CTkFrame(marco, fg_color="transparent", height=30)
        top_bar.pack(fill="x", padx=10, pady=(5, 0))
        ctk.CTkLabel(top_bar, text=titulo, font=("Segoe UI", 14, "bold"), text_color=COLOR_PRIMARY).pack(side="left", padx=5)
        
        btn_min = ctk.CTkButton(top_bar, text="—", width=30, height=25, fg_color="transparent", hover_color=COLOR_BORDER, text_color=COLOR_TEXT, command=lambda: v.withdraw())
        btn_min.pack(side="right", padx=2)
        btn_close = ctk.CTkButton(top_bar, text="✖", width=30, height=25, fg_color="transparent", hover_color=COLOR_RED, text_color=COLOR_TEXT, command=v.destroy)
        btn_close.pack(side="right", padx=2)
        
        return v, marco

    def cerrar_ventanas_secundarias(self):
        for item in list(self.ventanas_hijas):
            v = item["ventana"]
            if v.winfo_exists(): v.destroy()
        self.ventanas_hijas.clear()

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
        self.btn_plugins = ctk.CTkButton(self.sidebar, fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_CARD, anchor="w", font=("Segoe UI", 14), command=self.abrir_ventana_plugins)
        self.btn_settings = ctk.CTkButton(self.sidebar, fg_color="transparent", text_color=COLOR_TEXT, hover_color=COLOR_CARD, anchor="w", font=("Segoe UI", 14), command=self.abrir_ajustes)

        self.label_version = ctk.CTkLabel(self.sidebar, text="v0.3.0 - Open Source", font=("Segoe UI", 10), text_color="#5A4A70")
        self.label_version.grid(row=7, column=0, pady=15)
        
        self.actualizar_visibilidad_sidebar()

    def actualizar_visibilidad_sidebar(self):
        self.btn_quarantine.grid_remove()
        self.btn_plugins.grid_remove()
        self.btn_settings.grid_remove()
        
        row_idx = 3
        if self.config_data.get("mostrar_cuarentena", True):
            self.btn_quarantine.grid(row=row_idx, column=0, padx=15, pady=5, sticky="ew")
            row_idx += 1
        if self.config_data.get("mostrar_plugins", True):
            self.btn_plugins.grid(row=row_idx, column=0, padx=15, pady=5, sticky="ew")
            row_idx += 1
        self.btn_settings.grid(row=row_idx, column=0, padx=15, pady=5, sticky="ew")

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
        self.lbl_console = ctk.CTkLabel(self.log_topbar, font=("Segoe UI", 12, "bold"), text_color=COLOR_PRIMARY)
        self.lbl_console.pack(side="left", padx=10, pady=5)

        self.log_scroll = ctk.CTkScrollableFrame(self.log_frame, fg_color=COLOR_LOG_BG, corner_radius=8)
        self.log_scroll.pack(fill="both", expand=True, padx=10, pady=10)

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

    def abrir_ventana_cuarentena(self):
        self.cerrar_ventanas_secundarias()
        t = TRADUCCIONES[self.idioma_actual]
        v, marco = self.crear_ventana_emergente(t['quar_title'], 600, 500)
        
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
                    
                    btn_del = ctk.CTkButton(card, text="🗑️", width=30, fg_color=COLOR_RED, hover_color="#EF233C", command=lambda f=filepath, m=meta_path, vq=v: self.confirmar_papelera(f, m, vq))
                    btn_del.pack(side="right", padx=5)
                    
                    btn_rest = ctk.CTkButton(card, text=t['restore'], width=80, fg_color=COLOR_GREEN, hover_color="#10B981", text_color="#000000", command=lambda f=filepath, m=meta_path, vq=v: self.restaurar_archivo(f, m, vq))
                    btn_rest.pack(side="right", padx=5)
        except FileNotFoundError:
            ctk.CTkLabel(scroll_frame, text=t['empty_q'], font=("Segoe UI", 14), text_color=COLOR_TEXT).pack(pady=50)

    def confirmar_papelera(self, filepath, meta_path, ventana_q):
        t = TRADUCCIONES[self.idioma_actual]
        v, marco = self.crear_ventana_emergente(t['delete'], 350, 150)
        
        ctk.CTkLabel(marco, text=t['confirm_trash'], font=("Segoe UI", 14, "bold"), text_color=COLOR_TEXT).pack(pady=20)
        
        btn_frame = ctk.CTkFrame(marco, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def hacer_borrado():
            try:
                send2trash.send2trash(filepath)
                if os.path.exists(meta_path): os.remove(meta_path)
            except Exception as e:
                print(f"Error al mover a papelera: {e}")
            
            v.destroy()
            ventana_q.destroy()
            self.abrir_ventana_cuarentena() 
            
        ctk.CTkButton(btn_frame, text=t['yes'], fg_color=COLOR_RED, hover_color="#EF233C", command=hacer_borrado).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text=t['no'], fg_color=COLOR_PRIMARY, hover_color=COLOR_ACCENT, command=v.destroy).pack(side="left", padx=10)

    def restaurar_archivo(self, filepath, meta_path, ventana):
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
            print(f"Error al restaurar: {e}")

    def abrir_ventana_plugins(self):
        self.cerrar_ventanas_secundarias()
        t = TRADUCCIONES[self.idioma_actual]
        v, marco = self.crear_ventana_emergente(t['plug_title'], 500, 400)
        
        ctk.CTkLabel(marco, text=t['plug_desc'], font=("Segoe UI", 12), text_color=COLOR_TEXT).pack(pady=5)

        scroll_frame = ctk.CTkScrollableFrame(marco, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

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

    def abrir_ajustes(self):
        self.cerrar_ventanas_secundarias()
        t = TRADUCCIONES[self.idioma_actual]
        v, marco = self.crear_ventana_emergente(t['settings_title'], 450, 650)
        
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
        
        frame_visual = ctk.CTkFrame(content, fg_color="transparent")
        frame_visual.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_visual, text="Personalización", font=("Segoe UI", 14, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0,5))
        
        self.chk_cuarentena = ctk.CTkCheckBox(frame_visual, text=t['show_quar'], font=("Segoe UI", 12), text_color=COLOR_TEXT, 
                                              command=lambda: self.guardar_config("mostrar_cuarentena", self.chk_cuarentena.get()))
        self.chk_cuarentena.pack(anchor="w", pady=5)
        if self.config_data.get("mostrar_cuarentena", True): self.chk_cuarentena.select()
        
        self.chk_plugins = ctk.CTkCheckBox(frame_visual, text=t['show_plug'], font=("Segoe UI", 12), text_color=COLOR_TEXT, 
                                           command=lambda: self.guardar_config("mostrar_plugins", self.chk_plugins.get()))
        self.chk_plugins.pack(anchor="w", pady=5)
        if self.config_data.get("mostrar_plugins", True): self.chk_plugins.select()

        frame_rutas = ctk.CTkFrame(content, fg_color="transparent")
        frame_rutas.pack(fill="x", pady=10)
        ctk.CTkLabel(frame_rutas, text="Carpetas Protegidas", font=("Segoe UI", 14, "bold"), text_color=COLOR_TEXT).pack(anchor="w", pady=(0,5))
        
        btn_add_dir = ctk.CTkButton(frame_rutas, text=t['add_dir'], fg_color=COLOR_PRIMARY, hover_color=COLOR_ACCENT, command=self.agregar_carpeta)
        btn_add_dir.pack(fill="x", pady=5)
        
        lista_rutas = self.config_data.get("rutas_extra", [])
        if lista_rutas:
            for r in lista_rutas:
                ctk.CTkLabel(frame_rutas, text=f"📁 {r}", font=("Segoe UI", 11), text_color=COLOR_GREEN, anchor="w").pack(fill="x", padx=10)

        info_frame = ctk.CTkFrame(content, fg_color=COLOR_CARD, corner_radius=10, border_width=1, border_color=COLOR_BORDER)
        info_frame.pack(pady=10, fill="both", expand=True)
        ctk.CTkLabel(info_frame, text=f"{t['info']}:\nS.O: {SISTEMA}\nPython: {platform.python_version()}\nMotor: C / C++ integrado", justify="left", font=("Consolas", 11), text_color=COLOR_TEXT).pack(padx=20, pady=20, anchor="w")

    def agregar_carpeta(self):
        carpeta = None
        self.withdraw()

        if SISTEMA == "Linux":
            try:
                resultado = subprocess.run(
                    ["zenity", "--file-selection", "--directory", "--title=Selecciona una carpeta para proteger"],
                    capture_output=True, text=True, timeout=60
                )
                if resultado.returncode == 0:
                    carpeta = resultado.stdout.strip()
            except FileNotFoundError:
                self.deiconify()
                carpeta = filedialog.askdirectory(title="Selecciona una carpeta", parent=self)
        else:
            self.deiconify()
            carpeta = filedialog.askdirectory(title="Selecciona una carpeta para proteger", parent=self)

        self.deiconify()
        self.lift()
        
        if carpeta:
            rutas = self.config_data.get("rutas_extra", [])
            if carpeta not in rutas:
                rutas.append(carpeta)
                self.config_data["rutas_extra"] = rutas
                guardar_config(self.config_data)
                self.start_service()
                
        self.after(100, self.abrir_ajustes)

    def guardar_config(self, llave, valor):
        self.config_data[llave] = bool(valor)
        guardar_config(self.config_data)
        self.actualizar_visibilidad_sidebar()

    def cambiar_idioma(self, seleccion):
        self.idioma_actual = IDIOMAS_UI[seleccion]
        self.config_data["idioma"] = self.idioma_actual
        guardar_config(self.config_data)
        self.aplicar_idioma()

    def cambiar_tema(self, seleccion):
        ctk.set_appearance_mode("dark" if seleccion in ["Oscuro", "Dark"] else "light")

    def start_service(self):
        try:
            if SISTEMA == "Windows": subprocess.run(["schtasks", "/run", "/tn", "PrivacyGuard_Engine"], check=False, timeout=5)
            else: subprocess.run(["systemctl", "--user", "restart", "privacy-guard"], check=False, timeout=5)
        except: pass
        self.check_status()

    def stop_service(self):
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

    def matar_proceso(self, pid):
        try:
            pid_int = int(pid)
            proceso = psutil.Process(pid_int)
            proceso.kill()
            print(f"[*] Proceso {pid_int} neutralizado directamente.")
            self.pids_neutralizados.add(pid)
        except psutil.AccessDenied:
            try:
                if SISTEMA == "Linux": subprocess.run(["pkexec", "/usr/bin/kill", "-9", str(pid)])
                elif SISTEMA == "Windows": subprocess.run(["taskkill", "/F", "/PID", str(pid)])
                self.pids_neutralizados.add(pid)
            except Exception as e: pass
        except psutil.NoSuchProcess:
            self.pids_neutralizados.add(pid)
        except Exception as e: pass
            
        self.actualizar_tarjetas_logs()

    def update_logs(self):
        def update_ui():
            # AHORA LEEMOS DE LA BASE DE DATOS SQLITE
            eventos = obtener_eventos(50)
            
            for widget in self.log_scroll.winfo_children():
                widget.destroy()
                
            if not eventos:
                ctk.CTkLabel(self.log_scroll, text=TRADUCCIONES[self.idioma_actual]["empty_logs"], font=("Segoe UI", 14), text_color="#6B7280").pack(pady=50)
            else:
                for ev in eventos:
                    tarjeta = ctk.CTkFrame(self.log_scroll, fg_color=COLOR_CARD, corner_radius=8, border_width=1, border_color=COLOR_BORDER)
                    tarjeta.pack(fill="x", pady=5, padx=5)
                    
                    frame_top = ctk.CTkFrame(tarjeta, fg_color="transparent")
                    frame_top.pack(fill="x", padx=15, pady=(10, 0))
                    
                    icono = "🛡️"
                    if ev["tipo"] == "Amenaza": icono = "🚨"
                    elif ev["tipo"] == "Ransomware": icono = "🔪"
                    elif ev["tipo"] == "FIM": icono = "🛡️"
                    elif ev["tipo"] == "Binario": icono = "⚠️"
                    elif ev["tipo"] == "Nativo": icono = "⚙️"
                    
                    ctk.CTkLabel(frame_top, text=f"{icono} {ev['titulo']}", font=("Segoe UI", 13, "bold"), text_color=ev["color"]).pack(side="left")
                    
                    # Mostrar la fecha al lado derecho del título
                    ctk.CTkLabel(frame_top, text=ev["fecha"], font=("Segoe UI", 10), text_color="#6B7280").pack(side="right")
                    
                    if ev["pid"] != "0":
                        pid = ev["pid"]
                        esta_muerto = (pid in self.pids_neutralizados) or (not psutil.pid_exists(int(pid)))
                        
                        if esta_muerto:
                            btn_kill = ctk.CTkButton(frame_top, text=TRADUCCIONES[self.idioma_actual]["killed_btn"], width=100, height=25, 
                                                     fg_color=COLOR_GRAY, hover_color=COLOR_GRAY, font=("Segoe UI", 11, "bold"), 
                                                     state="disabled")
                            btn_kill.pack(side="right", padx=10)
                        else:
                            btn_kill = ctk.CTkButton(frame_top, text=TRADUCCIONES[self.idioma_actual]["kill_btn"], width=100, height=25, 
                                                     fg_color=COLOR_RED, hover_color="#EF233C", font=("Segoe UI", 11, "bold"),
                                                     command=lambda p=pid: self.matar_proceso(p))
                            btn_kill.pack(side="right", padx=10)
                    
                    ctk.CTkLabel(tarjeta, text=ev['detalle'], font=("Segoe UI", 12), text_color=COLOR_TEXT, anchor="w", justify="left").pack(fill="x", padx=15, pady=(2, 10))
            
            amenazas = sum(1 for e in eventos if e["tipo"] in ("Amenaza", "Ransomware"))
            self.label_threats.configure(text=str(amenazas))
            
            self.after(5000, self.update_logs)

        threading.Thread(target=lambda: self.after(0, update_ui), daemon=True).start()

if __name__ == "__main__":
    app = PrivacyGuardApp()
    app.mainloop()
