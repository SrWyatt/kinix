import customtkinter as ctk
import os
import datetime
import platform
import subprocess
from PIL import Image

try:
    from maya import MayaWindow
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

try:
    from securedocs_gui import SecureDocsWindow
    SECUREDOCS_AVAILABLE = True
except ImportError:
    SECUREDOCS_AVAILABLE = False

try:
    from autopentest_gui import AutoPentestWindow
    AUTOPENTEST_AVAILABLE = True
except ImportError:
    AUTOPENTEST_AVAILABLE = False

try:
    from golem_gui import GolemWindow
    GOLEM_AVAILABLE = True
except ImportError:
    GOLEM_AVAILABLE = False

try:
    from patchtrack_gui import PatchTrackWindow
    PATCHTRACK_AVAILABLE = True
except ImportError:
    PATCHTRACK_AVAILABLE = False

try:
    from sentra_gui import SentraWindow
    SENTRA_AVAILABLE = True
except ImportError:
    SENTRA_AVAILABLE = False

try:
    from smartbios_gui import SmartBiosWindow
    SMARTBIOS_AVAILABLE = True
except ImportError:
    SMARTBIOS_AVAILABLE = False

try:
    from syscare_gui import SysCareWindow
    SYSCARE_AVAILABLE = True
except ImportError:
    SYSCARE_AVAILABLE = False

try:
    from guardex_gui import GuardexWindow
    GUARDEX_AVAILABLE = True
except ImportError:
    GUARDEX_AVAILABLE = False

COLOR_FONDO_MAIN = "#0f0f10"      
COLOR_SIDEBAR = "#121213"         
COLOR_TARJETA = "#1a1a1c"         
COLOR_ACENTO_1 = "#2596be"        
COLOR_ACENTO_HOVER = "#1c7aa0"
COLOR_TEXTO = "#FFFFFF"           
COLOR_GOLD = "#ffe2a8"
COLOR_WINE = "#4c2a2c"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

class GenericModuleWindow(ctk.CTkToplevel):
    def __init__(self, parent, module_name, module_desc):
        super().__init__(parent)
        self.title(f"KINIX - {module_name}")
        self.geometry("600x400")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO_MAIN)
        self.after(200, lambda: self.lift())
        self.after(200, lambda: self.focus())
        
        ctk.CTkLabel(self, text=module_name, font=("Roboto", 24, "bold"), text_color="white").pack(pady=(40,10))
        ctk.CTkLabel(self, text=module_desc, text_color="gray").pack()
        ctk.CTkLabel(self, text="Modulo no cargado o en desarrollo", text_color="#e056fd").pack(pady=40)

class KinixDashboard(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("KINIX Security Suite")
        self.geometry("1280x800")
        self.minsize(1100, 750)
        
        try:
            icon_path = os.path.join("resc", "vn.png")
            if os.path.exists(icon_path):
                self.iconphoto(False, ctk.tkinter.PhotoImage(file=icon_path))
        except Exception: pass

        self.grid_columnconfigure(0, weight=0) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=COLOR_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.logo_frame.pack(pady=(40, 30), padx=20)
        try:
            logo_path = os.path.join("resc", "logo h.png")
            pil_img = Image.open(logo_path)
            w_base = 180
            w_percent = (w_base / float(pil_img.size[0]))
            h_size = int((float(pil_img.size[1]) * float(w_percent)))
            self.logo_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w_base, h_size))
            ctk.CTkLabel(self.logo_frame, text="", image=self.logo_img).pack()
        except:
            ctk.CTkLabel(self.logo_frame, text="KINIX", font=("Arial Black", 30), text_color=COLOR_ACENTO_1).pack()

        self.nav_label = ctk.CTkLabel(self.sidebar, text="NAVEGACION", font=("Roboto", 11, "bold"), text_color="#555555", anchor="w")
        self.nav_label.pack(padx=30, pady=(10, 10), fill="x")

        self.botones_menu = {}

        self.crear_boton_menu("Dashboard", command=self.show_dashboard, activo=True)
        self.crear_boton_menu("Archivos", command=self.show_files, activo=False)
        self.crear_boton_menu("Mi Cuenta", command=self.show_account, activo=False)
        self.crear_boton_menu("Configuracion", command=lambda: self.marcar_activo("Configuracion"), activo=False)
        self.crear_boton_menu("Ayuda", command=self.show_help, activo=False)

        self.lbl_ver = ctk.CTkLabel(self.sidebar, text="v0.9.4 Stable", font=("Roboto", 9), text_color="gray")
        self.lbl_ver.pack(side="bottom", pady=(5, 30))

        self.btn_pro = ctk.CTkButton(self.sidebar, text="PRO", 
                                     font=("Roboto", 12, "bold"), 
                                     text_color=COLOR_GOLD,
                                     fg_color=COLOR_WINE, 
                                     border_width=1, 
                                     border_color=COLOR_GOLD,
                                     hover_color=COLOR_WINE,
                                     corner_radius=20, 
                                     height=32,
                                     width=100)
        self.btn_pro.pack(side="bottom", pady=(0, 5))

        self.main_area = ctk.CTkFrame(self, fg_color=COLOR_FONDO_MAIN, corner_radius=0)
        self.main_area.grid(row=0, column=1, sticky="nsew")
        
        self.show_dashboard()

    def crear_boton_menu(self, texto, command=None, activo=False):
        color_fg = "transparent"
        color_text = "#888888"
        border_c = COLOR_SIDEBAR
        
        if activo:
            color_fg = "#1F1F21"
            color_text = "white"
            border_c = COLOR_ACENTO_1 

        btn = ctk.CTkButton(self.sidebar, text=texto, fg_color=color_fg, 
                            text_color=color_text, hover_color="#1F1F21",
                            border_width=1 if activo else 0,
                            border_color=border_c,
                            anchor="w", height=45, corner_radius=8, 
                            font=("Roboto", 13, "bold"),
                            command=lambda: self.manejar_click_menu(texto, command))
        btn.pack(fill="x", padx=20, pady=6)
        
        self.botones_menu[texto] = btn

    def manejar_click_menu(self, texto, command):
        self.marcar_activo(texto)
        if command:
            command()

    def marcar_activo(self, texto_activo):
        for txt, btn in self.botones_menu.items():
            if txt == texto_activo:
                btn.configure(fg_color="#1F1F21", text_color="white", border_width=1, border_color=COLOR_ACENTO_1)
            else:
                btn.configure(fg_color="transparent", text_color="#888888", border_width=0, border_color=COLOR_SIDEBAR)

    def clear_main_area(self):
        for widget in self.main_area.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_main_area()
        
        header = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header.pack(fill="x", padx=50, pady=(40, 10)) 
        ctk.CTkLabel(header, text="Panel de Control", font=("Roboto", 32, "bold"), text_color="white").pack(side="left")
        
        container = ctk.CTkFrame(self.main_area, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=20) 
        container.grid_columnconfigure((0, 1, 2), weight=1)
        container.grid_rowconfigure((0, 1, 2), weight=1)

        modulos = [
            {"name": "MAYA", "desc": "IA Neural Core", "status": "active", "icon": "🧠", "img": "MAiA.png"},
            {"name": "SecureDocs", "desc": "Analisis Forense", "status": "active", "icon": "📄"},
            {"name": "Golem", "desc": "Escaner de Red", "status": "active", "icon": "📡"},
            {"name": "AutoPentest", "desc": "Auditoria de Puertos", "status": "active", "icon": "🛡️"},
            {"name": "PatchTrack", "desc": "Control de Versiones", "status": "warning", "icon": "📥"},
            {"name": "SysCare", "desc": "Monitor de Hardware", "status": "active", "icon": "🌡️"},
            {"name": "Sentra", "desc": "Brechas de Seguridad", "status": "danger", "icon": "👁️"},
            {"name": "SmartBios", "desc": "Integridad UEFI", "status": "active", "icon": "💻"},
            {"name": "Guardex", "desc": "Proteccion Hash", "status": "dev", "icon": "🔒"}
        ]

        for i, mod in enumerate(modulos):
            self.crear_tarjeta_modulo(container, mod, i // 3, i % 3)

    def show_files(self):
        self.clear_main_area()

        header = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header.pack(fill="x", padx=50, pady=(40, 20))
        ctk.CTkLabel(header, text="Historial de Logs", font=("Roboto", 32, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(header, text="| Archivos Generados", font=("Roboto", 20), text_color="gray").pack(side="left", padx=15, pady=(10,0))

        scroll = ctk.CTkScrollableFrame(self.main_area, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=40, pady=(0, 20))

        log_root = "logs"
        found_files = []
        
        if os.path.exists(log_root):
            for root, dirs, files in os.walk(log_root):
                for file in files:
                    if file.endswith(".txt") or file.endswith(".json") or file.endswith(".csv"):
                        full_path = os.path.join(root, file)
                        try:
                            ts = os.path.getmtime(full_path)
                            dt = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
                            found_files.append({"path": full_path, "name": file, "date": dt, "ts": ts})
                        except: pass
        
        found_files.sort(key=lambda x: x["ts"], reverse=True)

        if not found_files:
            ctk.CTkLabel(scroll, text="No se encontraron registros de actividad.", font=("Roboto", 16), text_color="gray").pack(pady=50)
            return

        for f in found_files:
            self.crear_tarjeta_archivo(scroll, f)

    def show_help(self):
        self.clear_main_area()

        header = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header.pack(fill="x", padx=50, pady=(40, 20))
        ctk.CTkLabel(header, text="Centro de Ayuda", font=("Roboto", 32, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(header, text="| Soporte y Recursos", font=("Roboto", 20), text_color="gray").pack(side="left", padx=15, pady=(10,0))

        container = ctk.CTkFrame(self.main_area, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=40, pady=20)
        container.grid_columnconfigure((0, 1), weight=1)
        container.grid_rowconfigure((0, 1), weight=1)

        self.crear_tarjeta_ayuda(container, 0, 0, "Soporte Tecnico", "Contacta con nuestros expertos 24/7", "🎧")
        self.crear_tarjeta_ayuda(container, 0, 1, "Reportar un Problema", "Envia logs de errores o bugs", "⚠️")
        self.crear_tarjeta_ayuda(container, 1, 0, "FAQs", "Respuestas a dudas comunes", "❓")
        self.crear_tarjeta_ayuda(container, 1, 1, "Guias y Tutoriales", "Aprende a usar KINIX al maximo", "📚")

    def show_account(self):
        self.clear_main_area()

        header = ctk.CTkFrame(self.main_area, fg_color="transparent")
        header.pack(fill="x", padx=50, pady=(40, 20))
        ctk.CTkLabel(header, text="Mi Cuenta", font=("Roboto", 32, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(header, text="| Perfil de Usuario", font=("Roboto", 20), text_color="gray").pack(side="left", padx=15, pady=(10,0))

        content = ctk.CTkFrame(self.main_area, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=10)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=2)

        card_profile = ctk.CTkFrame(content, fg_color=COLOR_TARJETA, corner_radius=16)
        card_profile.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        ctk.CTkLabel(card_profile, text="👤", font=("Arial", 80), text_color="#B0B0B0", fg_color="#2B2B2B", width=120, height=120, corner_radius=60).pack(pady=(50, 20))
        
        ctk.CTkLabel(card_profile, text="Aleksei Svarog", font=("Roboto", 24, "bold"), text_color="white").pack()
        ctk.CTkLabel(card_profile, text="@SrWyatt_", font=("Roboto", 14), text_color="gray").pack(pady=(5, 25))

        plan_badge = ctk.CTkFrame(card_profile, fg_color=COLOR_WINE, border_color=COLOR_GOLD, border_width=1, corner_radius=20, height=36)
        plan_badge.pack(pady=10, padx=50, fill="x")
        plan_badge.pack_propagate(False) 
        
        badge_content = ctk.CTkFrame(plan_badge, fg_color="transparent")
        badge_content.place(relx=0.5, rely=0.5, anchor="center")
        ctk.CTkLabel(badge_content, text="PLAN PREMIUM", font=("Roboto", 12, "bold"), text_color=COLOR_GOLD).pack()

        card_details = ctk.CTkFrame(content, fg_color="transparent")
        card_details.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.crear_detalle_cuenta(card_details, "ID de Usuario", "UID-8829-XJ22")
        self.crear_detalle_cuenta(card_details, "Correo Electronico", "aleksei.svarog@kinix.io")
        self.crear_detalle_cuenta(card_details, "Fecha de Registro", "14 de Octubre, 2023")
        self.crear_detalle_cuenta(card_details, "Ultimo Acceso", datetime.datetime.now().strftime("%d-%m-%Y %H:%M"))
        self.crear_detalle_cuenta(card_details, "Nivel de Seguridad", "Alto (2FA Activado)")

    def crear_detalle_cuenta(self, parent, label, value):
        frame = ctk.CTkFrame(parent, fg_color=COLOR_TARJETA, corner_radius=10)
        frame.pack(fill="x", pady=5)
        ctk.CTkLabel(frame, text=label, font=("Roboto", 12), text_color="gray").pack(side="left", padx=20, pady=15)
        ctk.CTkLabel(frame, text=value, font=("Roboto", 14, "bold"), text_color="white").pack(side="right", padx=20, pady=15)

    def crear_tarjeta_modulo(self, parent, mod, r, c):
        card = ctk.CTkFrame(parent, fg_color=COLOR_TARJETA, corner_radius=16, border_width=0)
        card.grid(row=r, column=c, padx=15, pady=15, sticky="nsew") 
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1) 

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 5))
        
        icon_loaded = False
        if "img" in mod:
            try:
                img_path = os.path.join("resc", mod["img"])
                if os.path.exists(img_path):
                    pil_icon = Image.open(img_path)
                    ctk_icon = ctk.CTkImage(light_image=pil_icon, dark_image=pil_icon, size=(40, 40))
                    ctk.CTkLabel(head, text="", image=ctk_icon).pack(side="left")
                    icon_loaded = True
            except: pass 
        if not icon_loaded:
            ctk.CTkLabel(head, text=mod['icon'], font=("Arial", 28)).pack(side="left")

        status_colors = {"active": "#00E676", "warning": "#FFEA00", "danger": "#FF3D00", "dev": "#636e72"}
        dot_color = status_colors.get(mod["status"], "gray")
        status_dot = ctk.CTkFrame(head, width=8, height=8, corner_radius=4, fg_color=dot_color)
        status_dot.pack(side="right", anchor="n", pady=5)

        text_frame = ctk.CTkFrame(card, fg_color="transparent")
        text_frame.grid(row=1, column=0, sticky="ew", padx=20)
        ctk.CTkLabel(text_frame, text=mod["name"], font=("Roboto", 20, "bold"), text_color="white", anchor="w").pack(fill="x")
        ctk.CTkLabel(text_frame, text=mod["desc"], font=("Roboto", 13), text_color="#888888", anchor="w").pack(fill="x", pady=(2, 0))

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        btn_launch = ctk.CTkButton(btn_frame, text="ABRIR", height=35, 
                                 fg_color=COLOR_ACENTO_1, hover_color=COLOR_ACENTO_HOVER, 
                                 font=("Roboto", 12, "bold"), corner_radius=8,
                                 command=lambda m=mod: self.abrir_modulo(m))
        btn_launch.pack(fill="x")

    def crear_tarjeta_archivo(self, parent, file_data):
        card = ctk.CTkFrame(parent, fg_color=COLOR_TARJETA, corner_radius=10)
        card.pack(fill="x", pady=5)
        
        ctk.CTkLabel(card, text="📄", font=("Arial", 24)).pack(side="left", padx=15, pady=15)
        
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(info_frame, text=file_data["name"], font=("Roboto", 14, "bold"), text_color="white", anchor="w").pack(fill="x", pady=(5,0))
        ctk.CTkLabel(info_frame, text=f"Modificado: {file_data['date']}", font=("Roboto", 11), text_color="gray", anchor="w").pack(fill="x")

        btn_analyze = ctk.CTkButton(card, text="ANALIZAR", width=100, fg_color="#2B2B2B", hover_color="#3A3A3A", font=("Roboto", 11, "bold"))
        btn_analyze.pack(side="right", padx=(5, 15), pady=15)
        
        btn_open = ctk.CTkButton(card, text="ABRIR", width=100, fg_color=COLOR_ACENTO_1, hover_color=COLOR_ACENTO_HOVER, font=("Roboto", 11, "bold"),
                                 command=lambda p=file_data["path"]: self.abrir_archivo_sistema(p))
        btn_open.pack(side="right", padx=5, pady=15)

    def crear_tarjeta_ayuda(self, parent, r, c, title, desc, icon):
        card = ctk.CTkFrame(parent, fg_color=COLOR_TARJETA, corner_radius=16)
        card.grid(row=r, column=c, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(card, text=icon, font=("Arial", 40)).pack(pady=(40, 15))
        
        ctk.CTkLabel(card, text=title, font=("Roboto", 22, "bold"), text_color="white").pack(pady=5)
        
        ctk.CTkLabel(card, text=desc, font=("Roboto", 14), text_color="gray").pack(pady=(0, 30))
        
        ctk.CTkButton(card, text="ACCEDER", fg_color="transparent", border_width=1, border_color=COLOR_ACENTO_1, 
                      text_color=COLOR_ACENTO_1, hover_color="#2B2B2B", height=35).pack(pady=20)

    def abrir_archivo_sistema(self, path):
        try:
            if platform.system() == 'Darwin':       
                subprocess.call(('open', path))
            elif platform.system() == 'Windows':    
                os.startfile(path)
            else:                                   
                subprocess.call(('xdg-open', path))
        except Exception as e:
            print(f"Error al abrir archivo: {e}")

    def abrir_modulo(self, modulo_data):
        name = modulo_data["name"]
        
        if name == "MAYA" and MAYA_AVAILABLE: MayaWindow(self)
        elif name == "SecureDocs" and SECUREDOCS_AVAILABLE: SecureDocsWindow(self)
        elif name == "AutoPentest" and AUTOPENTEST_AVAILABLE: AutoPentestWindow(self)
        elif name == "Golem" and GOLEM_AVAILABLE: GolemWindow(self)
        elif name == "PatchTrack" and PATCHTRACK_AVAILABLE: PatchTrackWindow(self)
        elif name == "Sentra" and SENTRA_AVAILABLE: SentraWindow(self)
        elif name == "SmartBios" and SMARTBIOS_AVAILABLE: SmartBiosWindow(self)
        elif name == "SysCare" and SYSCARE_AVAILABLE: SysCareWindow(self)
        elif name == "Guardex" and GUARDEX_AVAILABLE: GuardexWindow(self)
        else:
            GenericModuleWindow(self, name, modulo_data["desc"])

if __name__ == "__main__":
    app = KinixDashboard()
    app.mainloop()