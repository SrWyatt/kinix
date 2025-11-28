import customtkinter as ctk
from tkinter import filedialog
import os
import threading
import time
import re
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_SIDE = "#121213"
COLOR_BUBBLE_BOT = "#1F1F21"
COLOR_BUBBLE_USER = "#2596be"

COLOR_SAFE = "#00E676"
COLOR_WARN = "#FFEA00"
COLOR_DANGER = "#FF3D00"

class SecurityEngine:
    def __init__(self):
        self.PORT_KNOWLEDGE = {
            21: "FTP (Transferencia de Archivos). Inseguro, el tráfico viaja sin cifrar.",
            22: "SSH (Secure Shell). Acceso remoto seguro. Es vital tener una contraseña fuerte.",
            23: "Telnet. MUY INSEGURO. Permite acceso remoto sin cifrado. Deshabilítalo.",
            25: "SMTP (Correo). Usado para enviar emails.",
            53: "DNS (Nombres de Dominio). Traduce nombres a IPs.",
            80: "HTTP (Web). Servidor web estándar sin candado de seguridad.",
            443: "HTTPS (Web Segura). Servidor web con cifrado SSL/TLS.",
            445: "SMB (Samba/Windows). Crítico. Frecuente vector de ransomware (WannaCry).",
            3306: "MySQL. Base de datos. No debería estar expuesta a internet.",
            3389: "RDP (Escritorio Remoto). Muy atacado por fuerza bruta.",
            8080: "HTTP-Alt. Frecuentemente usado para paneles de administración o pruebas."
        }

        self.signatures = {
            "SQL Injection": [r"union select", r"OR 1=1", r"DROP TABLE", r"xp_cmdshell"],
            "XSS Attack": [r"<script>", r"javascript:", r"onerror="],
            "Path Traversal": [r"\.\./", r"/etc/passwd", r"c:\\windows\\system32"],
            "Brute Force": [r"failed password", r"authentication failure", r"too many attempts"],
            "Critical Errors": [r"fatal error", r"kernel panic", r"segmentation fault"]
        }

    def analyze(self, text):
        if "TARGET:" in text and "|" in text:
            return self.analyze_autopentest(text)
        elif "REPORTE DE VERSIONES" in text:
            return self.analyze_patchtrack(text)
        elif "IP,MAC,VENDOR" in text:
            return self.analyze_golem(text)
        elif "=== REPORTE SYSCARE ===" in text:
            return self.analyze_syscare(text)
        else:
            return self.analyze_generic(text)

    def analyze_autopentest(self, text):
        ports_found = re.findall(r'\|\s+(\d+)\s+\|', text)
        risks = re.findall(r'\|\s+(CRITICO|ALERTA)\s+', text)
        
        explanations = []
        for p in ports_found:
            port_num = int(p)
            desc = self.PORT_KNOWLEDGE.get(port_num, "Puerto TCP/UDP genérico.")
            explanations.append(f"• Puerto {p}: {desc}")
        
        summary = " TIPO: LOG DE PUERTOS (AutoPentest)\n"
        summary += f" [PORTS]: {', '.join(ports_found)}\n"
        summary += f" [RISKS]: {len(risks)} alertas detectadas."

        if "CRITICO" in risks:
            color = COLOR_DANGER
            desc = "He detectado puertos de ALTO RIESGO abiertos (posiblemente FTP, Telnet o SMB). \n\n" + "\n".join(explanations)
        elif ports_found:
            color = COLOR_WARN
            desc = "Se detectaron servicios expuestos. Verifica que sean estrictamente necesarios.\n\n" + "\n".join(explanations)
        else:
            color = COLOR_SAFE
            desc = "El escaneo no reporta puertos abiertos accesibles. El objetivo parece blindado."
            
        return summary, color, desc

    def analyze_patchtrack(self, text):
        outdated = re.findall(r'(\S+)\s+\S+\s+\S+\s+(OUTDATED|DESACTUALIZADO)', text)
        
        summary = " TIPO: CONTROL DE VERSIONES (PatchTrack)\n"
        summary += f" [MODULES]: {len(outdated)} desactualizados."

        if outdated:
            pkgs = [x[0] for x in outdated]
            color = COLOR_WARN
            desc = f"Encontré {len(outdated)} librerías obsoletas: {', '.join(pkgs)}. \n\nLas versiones antiguas pueden contener vulnerabilidades (CVEs) ya parcheadas en versiones nuevas. Recomiendo actualizar con 'pip install --upgrade'."
        else:
            color = COLOR_SAFE
            desc = "Todas las librerías analizadas están actualizadas a su última versión estable. Buen mantenimiento."
            
        return summary, color, desc

    def analyze_golem(self, text):
        devices = re.findall(r'(\d+\.\d+\.\d+\.\d+),', text)
        vendors = re.findall(r',([^,\n]+)$', text, re.MULTILINE)
        
        summary = " TIPO: ESCANEO DE RED (Golem)\n"
        summary += f" [HOSTS]: {len(devices)} dispositivos encontrados."

        color = COLOR_SAFE
        desc = f"He mapeado {len(devices)} dispositivos conectados a la red local. \n\nFabricantes detectados: {', '.join(list(set(vendors))[:5])}."
        
        return summary, color, desc

    def analyze_syscare(self, text):
        summary = " TIPO: MONITOR DE SISTEMA (SysCare)\n"
        cpu = re.search(r'cpu_percent: (\d+\.?\d*)', text)
        ram = re.search(r'ram_percent: (\d+\.?\d*)', text)
        
        cpu_val = float(cpu.group(1)) if cpu else 0
        ram_val = float(ram.group(1)) if ram else 0
        
        summary += f" [CPU]: {cpu_val}% | [RAM]: {ram_val}%"
        
        if cpu_val > 90 or ram_val > 90:
            color = COLOR_DANGER
            desc = "El sistema estaba bajo carga extrema al momento del log. Posible cuello de botella o proceso fuera de control."
        elif cpu_val > 70 or ram_val > 80:
            color = COLOR_WARN
            desc = "Carga del sistema elevada. Verifica procesos en segundo plano."
        else:
            color = COLOR_SAFE
            desc = "Los recursos del sistema operaban dentro de parámetros normales y saludables."
            
        return summary, color, desc

    def analyze_generic(self, text):
        text_lower = text.lower()
        risk_score = 0
        detected_threats = []
        
        for threat, patterns in self.signatures.items():
            for p in patterns:
                if re.search(p, text_lower):
                    detected_threats.append(threat)
                    risk_score += 20
                    break
        
        ips = list(set(re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', text)))
        
        summary = " TIPO: LOG GENÉRICO / SISTEMA\n"
        if detected_threats: summary += f" [THREATS]: {', '.join(detected_threats)}\n"
        if ips: summary += f" [IPS]: {len(ips)} detectadas."
        if not detected_threats and not ips: summary += " [DATA]: Sin patrones de ataque."

        if risk_score >= 40:
            color = COLOR_DANGER
            desc = f"PELIGRO CRÍTICO. Se detectaron firmas de ataque tipo: {', '.join(detected_threats)}. Investiga la fuente de inmediato."
        elif risk_score > 0:
            color = COLOR_WARN
            desc = "Actividad sospechosa detectada en los registros. Posibles intentos de acceso o errores."
        else:
            color = COLOR_SAFE
            desc = "Análisis heurístico limpio. No se encontraron patrones de ataque conocidos en este archivo."

        return summary, color, desc


class MayaWindow(ctk.CTkToplevel):
    def __init__(self, parent, archivo_pre_cargado=None):
        super().__init__(parent)
        self.title("MAYA - Security Core")
        self.geometry("550x700")
        self.resizable(True, True)
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        
        self.engine = SecurityEngine()
        self.is_typing = False
        
        self.avatar_img = None
        try:
            path = os.path.join("resc", "MAiA.png")
            if os.path.exists(path):
                pil = Image.open(path)
                self.avatar_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(30, 30))
        except: pass

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self, height=60, fg_color=COLOR_SIDE, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        
        title_box = ctk.CTkFrame(self.header, fg_color="transparent")
        title_box.pack(side="left", padx=15, pady=8)
        
        try:
            logo_path = os.path.join("resc", "maya11.png")
            if os.path.exists(logo_path):
                logo_pil = Image.open(logo_path)
                self.logo_img = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(90, 25))
                ctk.CTkLabel(title_box, text="", image=self.logo_img).pack(anchor="w")
            else:
                ctk.CTkLabel(title_box, text="MAYA", font=("Arial Black", 18), text_color="#2596be").pack(anchor="w")
        except: pass
        
        ctk.CTkLabel(title_box, text="Security Audit & Pattern Recognition", font=("Roboto", 9), text_color="gray").pack(anchor="w")
        ctk.CTkLabel(self.header, text="ACTIVE", font=("Roboto", 9, "bold"), text_color="#00E676").pack(side="right", padx=15)

        self.chat_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self.footer = ctk.CTkFrame(self, height=100, fg_color=COLOR_SIDE, corner_radius=0)
        self.footer.grid(row=2, column=0, sticky="ew")
        
        self.fake_entry = ctk.CTkEntry(self.footer, placeholder_text="Esperando log...", height=40, 
                                       border_width=1, border_color="#333", fg_color="#1a1a1c", text_color="gray")
        self.fake_entry.pack(fill="x", padx=15, pady=(15, 10))
        self.fake_entry.configure(state="disabled")

        self.actions_frame = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=5, pady=(0, 15))

        self.btn_file = ctk.CTkButton(self.actions_frame, text="ANALIZAR LOG", fg_color="#2596be", hover_color="#1c7aa0", height=35, command=self.ask_file)
        self.btn_file.pack(side="left", fill="x", expand=True, padx=4)
        
        self.btn_help = ctk.CTkButton(self.actions_frame, text="AYUDA", fg_color="#2B2B2B", hover_color="#3A3A3A", height=35, border_width=1, border_color="#444", command=self.open_help)
        self.btn_help.pack(side="left", fill="x", expand=True, padx=4)

        self.welcome()
        
        if archivo_pre_cargado:
            self.auto_analyze(archivo_pre_cargado)

    def add_msg(self, text, is_user=False):
        bubble_color = COLOR_BUBBLE_USER if is_user else COLOR_BUBBLE_BOT
        align = "right" if is_user else "left"
        
        frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        frame.pack(fill="x", pady=4)

        if not is_user and self.avatar_img:
            ctk.CTkLabel(frame, text="", image=self.avatar_img).pack(side="left", anchor="n", padx=(0,8))

        msg = ctk.CTkLabel(frame, text=text, fg_color=bubble_color, corner_radius=12, 
                           text_color="white", font=("Roboto", 12), wraplength=350, justify="left")
        msg.pack(side=align, ipadx=12, ipady=8)
        self.scroll_to_bottom()

    def add_report(self, summary_text, status_color, desc_text):
        frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        frame.pack(fill="x", pady=10)

        bubble = ctk.CTkFrame(frame, fg_color=COLOR_BUBBLE_BOT, corner_radius=12)
        bubble.pack(side="left", padx=(40, 10), fill="x", expand=True)

        lbl_summary = ctk.CTkLabel(bubble, text=summary_text, font=("Consolas", 11), text_color="#AAAAAA", justify="left", anchor="w")
        lbl_summary.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkFrame(bubble, height=1, fg_color="#333").pack(fill="x", padx=10, pady=5)

        status_row = ctk.CTkFrame(bubble, fg_color="transparent")
        status_row.pack(fill="x", padx=15, pady=(5, 15))
        
        dot = ctk.CTkFrame(status_row, width=14, height=14, corner_radius=7, fg_color=status_color)
        dot.pack(side="left", pady=2)
        
        lbl_desc = ctk.CTkLabel(status_row, text=desc_text, font=("Roboto", 12), text_color="white", wraplength=320, justify="left")
        lbl_desc.pack(side="left", padx=(10, 0))

        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        self.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def welcome(self):
        self.add_msg("MAYA Security Core iniciada.\nPuedo analizar logs de AutoPentest, PatchTrack, Golem o archivos genéricos.")

    def ask_file(self):
        path = filedialog.askopenfilename(filetypes=[("Logs", "*.txt *.log *.csv *.json")])
        if path:
            self.auto_analyze(path)

    def auto_analyze(self, path):
        self.add_msg(f"Analizando: {os.path.basename(path)}", is_user=True)
        self.fake_entry.configure(placeholder_text="Identificando formato...")
        self.is_typing = True
        threading.Thread(target=self.typing_animation).start()
        threading.Thread(target=self.process_file_thread, args=(path,)).start()

    def typing_animation(self):
        dots = 0
        while self.is_typing:
            dots = (dots + 1) % 4
            try: self.fake_entry.configure(placeholder_text="Procesando" + "." * dots)
            except: break
            time.sleep(0.4)
        try: self.fake_entry.configure(placeholder_text="Análisis finalizado.")
        except: pass

    def process_file_thread(self, path):
        time.sleep(1.0)
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            content = ""
        
        summary, color, desc = self.engine.analyze(content)
        
        self.is_typing = False
        self.after(0, lambda: self.add_report(summary, color, desc))

    def open_help(self):
        self.add_msg("Ayuda", True)
        self.add_msg("Este módulo reconoce automáticamente los logs generados por las herramientas de KINIX y explica su contenido.")

if __name__ == "__main__":
    app = MayaWindow(None)
    app.mainloop()