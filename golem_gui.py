import customtkinter as ctk
import threading
import datetime
import os
import sys
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_HEADER_BG = "#121213"
COLOR_ACENTO = "#2596be"
COLOR_TARJETA = "#1F1F21"

try:
    from scapy.all import ARP, Ether, srp
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

class GolemScanner:
    def scan(self, network_range):
        results = {"range": network_range, "timestamp": str(datetime.datetime.now()), "status": "error", "data": [], "error_msg": ""}
        if not SCAPY_AVAILABLE:
            results["error_msg"] = "Motor Scapy no instalado."
            return results
        try:
            arp = ARP(pdst=network_range)
            ether = Ether(dst="ff:ff:ff:ff:ff:ff")
            packet = ether / arp
            answered, _ = srp(packet, timeout=2, verbose=0)
            clients = []
            for sent, received in answered:
                mac = received.hwsrc
                vendor = self.get_vendor(mac)
                clients.append({'ip': received.psrc, 'mac': mac, 'vendor': vendor})
            results["data"] = clients
            results["status"] = "success"
        except PermissionError:
            results["error_msg"] = "Faltan permisos de Admin/Root."
        except Exception as e:
            results["error_msg"] = str(e)
        return results

    def get_vendor(self, mac):
        mac_prefix = mac[:8].upper()
        vendors = {
            "00:50:56": "VMware", "00:0C:29": "VMware", "00:1C:14": "VMware",
            "00:15:5D": "Microsoft Hyper-V",
            "B8:27:EB": "Raspberry Pi", "DC:A6:32": "Raspberry Pi",
            "00:1A:11": "Google",
            "AC:87:A3": "Apple", "00:17:F2": "Apple",
            "F0:9F:C2": "Ubiquiti",
            "00:E0:4C": "Realtek"
        }
        return vendors.get(mac_prefix, "Desconocido")

class GolemWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("KINIX - Golem")
        self.geometry("950x700")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()
        
        try: self.iconphoto(False, ctk.tkinter.PhotoImage(file="resc/vn.png"))
        except: pass
        self.scanner = GolemScanner()
        self.current_results = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkFrame(self, height=80, fg_color=COLOR_HEADER_BG, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        title_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(title_frame, text="Golem", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        
        try:
            logo_path = os.path.join("resc", "logo h.png")
            if os.path.exists(logo_path):
                pil_img = ctk.CTkImage(light_image=Image.open(logo_path), dark_image=Image.open(logo_path), size=(150, 40))
                ctk.CTkLabel(self.header, text="", image=pil_img).pack(side="right", padx=20)
        except: pass

        self.input_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.input_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=20)
        self.entry_target = ctk.CTkEntry(self.input_frame, placeholder_text="192.168.1.0/24", width=250)
        self.entry_target.insert(0, "192.168.1.0/24")
        self.entry_target.pack(side="left", padx=(0, 10))
        self.btn_scan = ctk.CTkButton(self.input_frame, text="ESCANEAR RED", fg_color=COLOR_ACENTO, width=120, command=self.start_scan)
        self.btn_scan.pack(side="left")
        self.btn_csv = ctk.CTkButton(self.input_frame, text="EXPORTAR CSV", width=120, fg_color="#2B2B2B", hover_color="#3A3A3A", command=self.save_csv)
        self.btn_csv.pack(side="left", padx=10)
        self.lbl_status = ctk.CTkLabel(self.input_frame, text="", text_color=COLOR_ACENTO)
        self.lbl_status.pack(side="left", padx=10)

        self.scroll_results = ctk.CTkScrollableFrame(self, fg_color="#121213", corner_radius=0)
        self.scroll_results.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 20))

    def start_scan(self):
        target = self.entry_target.get().strip()
        if not target: return
        for widget in self.scroll_results.winfo_children(): widget.destroy()
        self.btn_scan.configure(state="disabled")
        self.lbl_status.configure(text="ESCANEANDO...", text_color=COLOR_ACENTO)
        threading.Thread(target=self.run_scan, args=(target,)).start()

    def run_scan(self, target):
        results = self.scanner.scan(target)
        self.after(0, lambda: self.display_results(results))

    def display_results(self, results):
        self.btn_scan.configure(state="normal")
        self.current_results = results.get("data", [])
        
        if results["status"] == "error":
            self.lbl_status.configure(text="ERROR", text_color="#FF5555")
            ctk.CTkLabel(self.scroll_results, text=results["error_msg"], text_color="#FF5555").pack(pady=20)
            return

        self.lbl_status.configure(text=f"DISPOSITIVOS: {len(self.current_results)}", text_color="#00E676")
        
        headers = ctk.CTkFrame(self.scroll_results, fg_color="#2B2B2B", height=35)
        headers.pack(fill="x", pady=5)
        ctk.CTkLabel(headers, text="IP", width=150, anchor="w", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(headers, text="MAC", width=180, anchor="w", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
        ctk.CTkLabel(headers, text="FABRICANTE", width=200, anchor="w", font=("Roboto", 12, "bold")).pack(side="left", padx=10)

        for dev in self.current_results:
            row = ctk.CTkFrame(self.scroll_results, fg_color=COLOR_TARJETA)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=dev['ip'], width=150, anchor="w", text_color="#00E676").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=dev['mac'], width=180, anchor="w", text_color="gray").pack(side="left", padx=10)
            ctk.CTkLabel(row, text=dev['vendor'], width=200, anchor="w", text_color="white").pack(side="left", padx=10)

    def save_csv(self):
        if not self.current_results: return
        log_dir = os.path.join("logs", "golem")
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
        path = os.path.join(log_dir, f"golem_scan_{timestamp}.csv")
        with open(path, "w") as f:
            f.write("IP,MAC,VENDOR\n")
            for d in self.current_results:
                f.write(f"{d['ip']},{d['mac']},{d['vendor']}\n")
        self.lbl_status.configure(text="CSV GUARDADO")