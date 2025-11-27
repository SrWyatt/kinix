import customtkinter as ctk
import threading
import requests
import os
import datetime
# Usamos la librería estándar para evitar errores de importación
from importlib.metadata import distributions 
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_HEADER_BG = "#121213"
COLOR_ACENTO = "#2596be"
COLOR_TARJETA = "#1F1F21"

class PatchScanner:
    def check_pypi(self, pkg):
        try:
            r = requests.get(f"https://pypi.org/pypi/{pkg}/json", timeout=2)
            if r.status_code == 200:
                return r.json()['info']['version']
        except: pass
        return None

class PatchTrackWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("KINIX - PatchTrack")
        self.geometry("900x600")
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

        try: self.iconphoto(False, ctk.tkinter.PhotoImage(file="resc/vn.png"))
        except: pass
        self.scanner = PatchScanner()
        self.last_scan_data = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkFrame(self, height=80, fg_color=COLOR_HEADER_BG, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        tf = ctk.CTkFrame(self.header, fg_color="transparent")
        tf.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(tf, text="PatchTrack", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        
        try:
            pil_img = ctk.CTkImage(light_image=Image.open("resc/logo h.png"), dark_image=Image.open("resc/logo h.png"), size=(150, 40))
            ctk.CTkLabel(self.header, text="", image=pil_img).pack(side="right", padx=20)
        except: pass

        self.input_f = ctk.CTkFrame(self, fg_color="transparent")
        self.input_f.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        
        self.btn_list = ctk.CTkButton(self.input_f, text="ESCANEAR LIBRERÍAS", width=200, fg_color=COLOR_ACENTO, command=self.start_scan)
        self.btn_list.pack(side="left", padx=5)
        self.btn_save = ctk.CTkButton(self.input_f, text="GUARDAR REPORTE", width=150, fg_color="#2B2B2B", hover_color="#3A3A3A", command=self.save_log)
        self.btn_save.pack(side="left", padx=5)
        self.lbl_s = ctk.CTkLabel(self.input_f, text="", text_color="gray")
        self.lbl_s.pack(side="left", padx=10)

        self.res_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.res_area.grid(row=2, column=0, sticky="nsew", padx=40, pady=20)

    def start_scan(self):
        for w in self.res_area.winfo_children(): w.destroy()
        self.btn_list.configure(state="disabled")
        self.lbl_s.configure(text="Analizando paquetes instalados (esto puede tardar)...", text_color=COLOR_ACENTO)
        threading.Thread(target=self.run).start()

    def run(self):
        try:
            dists = list(distributions())
            pkgs = []
            total = len(dists)
            
            # Limitar a los primeros 30 para no saturar la API en demo, 
            # o quitar el slice [:30] para escanear todo (tardará más).
            # Para este ejemplo escaneamos todos pero con timeout corto.
            for i, d in enumerate(dists):
                name = d.metadata['Name']
                ver = d.version
                latest = self.scanner.check_pypi(name)
                
                status = "unknown"
                if latest:
                    status = "outdated" if latest != ver else "ok"
                
                pkgs.append({"name": name, "ver": ver, "latest": latest, "status": status})
                
                # Actualizar progreso visual cada 5 paquetes (opcional, requiere invocar al main thread)
                
            pkgs.sort(key=lambda x: x['name'])
            self.after(0, lambda: self.show(pkgs))
        except Exception as e: 
            self.after(0, lambda: self.lbl_s.configure(text=f"Error: {str(e)}"))

    def show(self, pkgs):
        self.btn_list.configure(state="normal")
        self.last_scan_data = pkgs
        outdated_count = sum(1 for p in pkgs if p["status"] == "outdated")
        
        self.lbl_s.configure(text=f"Escaneo completado: {outdated_count} desactualizados de {len(pkgs)}.", text_color="white")
        
        headers = ctk.CTkFrame(self.res_area, fg_color="#2B2B2B")
        headers.pack(fill="x")
        ctk.CTkLabel(headers, text="PAQUETE", width=200, anchor="w", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(headers, text="ESTADO", width=120, anchor="w", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(headers, text="VERSIÓN LOCAL", width=120, anchor="w", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(headers, text="ÚLTIMA VERSIÓN", width=120, anchor="w", font=("Roboto", 12, "bold")).pack(side="left", padx=10)

        for p in pkgs:
            # Color e icono según estado
            bg_color = COLOR_TARJETA
            status_text = "VERIFICADO"
            status_color = "#4CAF50" # Verde
            
            if p['status'] == 'outdated':
                status_text = "DESACTUALIZADO"
                status_color = "#FF5555" # Rojo
                bg_color = "#2a1a1c" # Fondo rojizo sutil para destacar
            elif p['status'] == 'unknown':
                status_text = "DESCONOCIDO"
                status_color = "gray"

            r = ctk.CTkFrame(self.res_area, fg_color=bg_color)
            r.pack(fill="x", pady=2)
            
            ctk.CTkLabel(r, text=p['name'], width=200, anchor="w", text_color="white", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
            ctk.CTkLabel(r, text=status_text, width=120, anchor="w", text_color=status_color, font=("Roboto", 11, "bold")).pack(side="left", padx=10)
            ctk.CTkLabel(r, text=p['ver'], width=120, anchor="w", text_color="gray").pack(side="left", padx=10)
            
            latest_txt = p['latest'] if p['latest'] else "-"
            ctk.CTkLabel(r, text=latest_txt, width=120, anchor="w", text_color=COLOR_ACENTO if p['status'] == 'outdated' else "gray").pack(side="left", padx=10)

    def save_log(self):
        if not self.last_scan_data: return
        log_dir = os.path.join("logs", "patchtrack")
        os.makedirs(log_dir, exist_ok=True)
        ts = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
        path = os.path.join(log_dir, f"patchtrack_scan_{ts}.txt")
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"REPORTE DE VERSIONES - {datetime.datetime.now()}\n")
                f.write("-" * 60 + "\n")
                f.write(f"{'PAQUETE':<30} {'LOCAL':<15} {'LATEST':<15} {'ESTADO'}\n")
                f.write("-" * 60 + "\n")
                for p in self.last_scan_data:
                    state = "OUTDATED" if p['status'] == 'outdated' else "OK"
                    lat = p['latest'] if p['latest'] else "N/A"
                    f.write(f"{p['name']:<30} {p['ver']:<15} {lat:<15} {state}\n")
            self.lbl_s.configure(text="REPORTE GUARDADO", text_color="#00E676")
        except:
            self.lbl_s.configure(text="ERROR AL GUARDAR", text_color="#FF3D00")