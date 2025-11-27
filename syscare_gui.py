import customtkinter as ctk
import psutil
import datetime
import platform
import threading
import time
import os
import gc
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_HEADER_BG = "#121213"
COLOR_TARJETA = "#1F1F21"
COLOR_ACENTO = "#2596be"
COLOR_SAFE = "#00E676"
COLOR_WARN = "#FFEA00"
COLOR_CRIT = "#FF3D00"

class SysCareScanner:
    def get_metrics(self):
        m = {}
        try:
            m['cpu_percent'] = psutil.cpu_percent(interval=None)
            m['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else 0
            m['cpu_cores'] = psutil.cpu_count(logical=False)
            m['cpu_threads'] = psutil.cpu_count(logical=True)
            
            ram = psutil.virtual_memory()
            m['ram_percent'] = ram.percent
            m['ram_used'] = round(ram.used / (1024**3), 2)
            m['ram_total'] = round(ram.total / (1024**3), 2)
            
            disk = psutil.disk_usage('/')
            m['disk_percent'] = disk.percent
            m['disk_free'] = round(disk.free / (1024**3), 2)
            m['disk_total'] = round(disk.total / (1024**3), 2)
            
            m['boot_time'] = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")
            m['os'] = f"{platform.system()} {platform.release()}"
            m['process_count'] = len(psutil.pids())
            
            battery = psutil.sensors_battery()
            if battery:
                m['battery_percent'] = battery.percent
                m['battery_plugged'] = battery.power_plugged
            else:
                m['battery_percent'] = None
        except:
            pass
        return m

class MetricCard(ctk.CTkFrame):
    def __init__(self, parent, title, icon, unit="%", **kwargs):
        super().__init__(parent, fg_color=COLOR_TARJETA, corner_radius=12, border_width=1, border_color="#2B2B2B", **kwargs)
        self.unit = unit
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))
        ctk.CTkLabel(header, text=icon, font=("Segoe UI Emoji", 24)).pack(side="left")
        ctk.CTkLabel(header, text=title, font=("Roboto", 14, "bold"), text_color="white").pack(side="left", padx=10)
        self.lbl_value = ctk.CTkLabel(self, text="--", font=("Roboto", 32, "bold"), text_color=COLOR_ACENTO)
        self.lbl_value.pack(padx=15, pady=(5, 0), anchor="w")
        self.progress = ctk.CTkProgressBar(self, height=8)
        self.progress.set(0)
        self.progress.pack(fill="x", padx=15, pady=(10, 5))
        self.lbl_sub = ctk.CTkLabel(self, text="...", font=("Roboto", 11), text_color="gray")
        self.lbl_sub.pack(padx=15, pady=(0, 15), anchor="w")

    def update_data(self, value, max_val, subtext):
        if value is None: value = 0
        percent = value / max_val if max_val > 0 else 0
        color = COLOR_SAFE
        if percent > 0.60: color = COLOR_WARN
        if percent > 0.85: color = COLOR_CRIT
        self.progress.configure(progress_color=color)
        self.progress.set(percent)
        self.lbl_value.configure(text=f"{value}{self.unit}", text_color=color)
        self.lbl_sub.configure(text=subtext)

class SysCareWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("KINIX - SysCare Monitor")
        self.geometry("1000x700")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

        try: self.iconphoto(False, ctk.tkinter.PhotoImage(file="resc/vn.png"))
        except: pass
        self.scanner = SysCareScanner()
        self.monitoring = False
        self.last_data = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkFrame(self, height=80, fg_color=COLOR_HEADER_BG, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        title_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(title_frame, text="SysCare", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        
        try:
            pil_img = ctk.CTkImage(light_image=Image.open("resc/logo h.png"), dark_image=Image.open("resc/logo h.png"), size=(150, 40))
            ctk.CTkLabel(self.header, text="", image=pil_img).pack(side="right", padx=20)
        except: pass

        self.control_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.control_bar.grid(row=1, column=0, sticky="ew", padx=30, pady=(20, 10))
        self.lbl_status = ctk.CTkLabel(self.control_bar, text="ESTADO: EN ESPERA", font=("Roboto", 12, "bold"), text_color="gray")
        self.lbl_status.pack(side="left")

        self.switch_var = ctk.StringVar(value="off")
        self.switch_monitor = ctk.CTkSwitch(self.control_bar, text="EN VIVO", command=self.toggle_monitoring,
                                            variable=self.switch_var, onvalue="on", offvalue="off", progress_color=COLOR_ACENTO)
        self.switch_monitor.pack(side="right")
        
        self.btn_clean = ctk.CTkButton(self.control_bar, text="OPTIMIZAR RAM", width=120, fg_color="#2B2B2B", hover_color="#4CAF50", command=self.clean_ram)
        self.btn_clean.pack(side="right", padx=15)

        self.btn_log = ctk.CTkButton(self.control_bar, text="GUARDAR LOG", width=120, fg_color="#2B2B2B", hover_color="#3A3A3A", command=self.save_log)
        self.btn_log.pack(side="right", padx=5)

        self.dash_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.dash_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=10)
        self.dash_frame.grid_columnconfigure((0, 1), weight=1)
        self.dash_frame.grid_rowconfigure((0, 1), weight=0)

        self.card_cpu = MetricCard(self.dash_frame, "CPU", "💾", unit="%")
        self.card_cpu.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.card_ram = MetricCard(self.dash_frame, "Memoria", "🧠", unit="%")
        self.card_ram.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.card_disk = MetricCard(self.dash_frame, "Disco", "💿", unit="%")
        self.card_disk.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        self.card_sys = ctk.CTkFrame(self.dash_frame, fg_color=COLOR_TARJETA, corner_radius=12, border_width=1, border_color="#2B2B2B")
        self.card_sys.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.card_sys, text="Información del Sistema", font=("Roboto", 14, "bold"), text_color="white").pack(pady=15)
        
        self.lbl_os = ctk.CTkLabel(self.card_sys, text="...", text_color="gray", font=("Consolas", 12))
        self.lbl_os.pack(pady=2)
        
        self.lbl_boot = ctk.CTkLabel(self.card_sys, text="...", text_color="gray", font=("Consolas", 12))
        self.lbl_boot.pack(pady=2)
        
        self.lbl_procs = ctk.CTkLabel(self.card_sys, text="...", text_color="gray", font=("Consolas", 12))
        self.lbl_procs.pack(pady=2)

        self.run_once()

    def toggle_monitoring(self):
        if self.switch_var.get() == "on":
            self.monitoring = True
            self.lbl_status.configure(text="MONITOREANDO", text_color=COLOR_ACENTO)
            threading.Thread(target=self.loop_monitor, daemon=True).start()
        else:
            self.monitoring = False
            self.lbl_status.configure(text="PAUSADO", text_color="gray")

    def loop_monitor(self):
        while self.monitoring:
            try:
                data = self.scanner.get_metrics()
                self.after(0, lambda: self.update_ui(data))
                time.sleep(1)
            except:
                self.monitoring = False
                break

    def run_once(self):
        data = self.scanner.get_metrics()
        self.update_ui(data)

    def update_ui(self, m):
        if not m: return
        self.last_data = m
        self.card_cpu.update_data(m.get('cpu_percent', 0), 100, f"{m.get('cpu_freq', 0):.0f} Mhz")
        self.card_ram.update_data(m.get('ram_percent', 0), 100, f"{m.get('ram_used', 0)}GB / {m.get('ram_total', 0)}GB")
        self.card_disk.update_data(m.get('disk_percent', 0), 100, f"Libre: {m.get('disk_free', 0)} GB")
        
        self.lbl_os.configure(text=f"SO: {m.get('os', 'N/A')}")
        self.lbl_boot.configure(text=f"Inicio: {m.get('boot_time', 'N/A')}")
        self.lbl_procs.configure(text=f"Procesos: {m.get('process_count', 0)}")

    def clean_ram(self):
        gc.collect()
        self.lbl_status.configure(text="RAM OPTIMIZADA (GC)", text_color="#00E676")
        self.run_once()

    def save_log(self):
        if not self.last_data: return
        log_dir = os.path.join("logs", "syscare")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
        filename = f"syscare_log{timestamp}.txt"
        path = os.path.join(log_dir, filename)
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("=== REPORTE SYSCARE ===\n")
                f.write(f"Fecha: {datetime.datetime.now()}\n\n")
                for k, v in self.last_data.items():
                    f.write(f"{k}: {v}\n")
            self.lbl_status.configure(text="LOG GUARDADO", text_color="#00E676")
        except:
            self.lbl_status.configure(text="ERROR AL GUARDAR", text_color="#FF3D00")

    def destroy(self):
        self.monitoring = False
        super().destroy()