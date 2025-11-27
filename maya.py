import customtkinter as ctk
from tkinter import filedialog
import os
import datetime
import time
import threading
import re
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_SIDE = "#121213"
COLOR_BUBBLE_BOT = "#1F1F21"
COLOR_BUBBLE_USER = "#2596be"
COLOR_TEXT = "#FFFFFF"
COLOR_GOLD = "#ffe2a8"
COLOR_WINE = "#4c2a2c"

class ForensicEngine:
    def __init__(self):
        self.risk_score = 0
        self.findings = []
    
    def analyze(self, path):
        self.risk_score = 0
        self.findings = []
        stats = {"lines": 0, "size": os.path.getsize(path), "ips": 0, "emails": 0, "errors": 0}
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                stats["lines"] = content.count('\n') + 1
                
                ips = re.findall(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', content)
                stats["ips"] = len(ips)
                if ips: self.findings.append(f"Detectadas {len(ips)} direcciones IP únicas.")

                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                stats["emails"] = len(emails)
                
                keywords = {
                    "CRITICAL": 10, "FATAL": 10, "PANIC": 10,
                    "ERROR": 5, "FAIL": 5, "DENIED": 5,
                    "WARNING": 2, "TIMEOUT": 2
                }
                
                content_upper = content.upper()
                for k, weight in keywords.items():
                    count = content_upper.count(k)
                    if count > 0:
                        self.risk_score += count * weight
                        stats["errors"] += count
                        self.findings.append(f"Patrón '{k}' encontrado {count} veces.")

            return self.generate_conclusion(stats, os.path.basename(path))
            
        except Exception as e:
            return f"Error crítico al leer el archivo: {str(e)}"

    def generate_conclusion(self, s, filename):
        report = f"ANÁLISIS COMPLETADO: {filename}\n"
        report += f"─" * 30 + "\n"
        
        if self.risk_score == 0:
            report += "El archivo parece estar limpio. No se detectaron indicadores de compromiso o errores críticos en la estructura analizada."
        elif self.risk_score < 50:
            report += f"Se han detectado anomalías leves (Nivel de Riesgo: {self.risk_score}).\n"
            report += "Resumen de hallazgos:\n• " + "\n• ".join(self.findings[:3])
            if len(self.findings) > 3: report += "\n...y otros indicadores menores."
        else:
            report += f"⚠️ ALERTA DE SEGURIDAD (Riesgo: {self.risk_score})\n"
            report += "El archivo contiene múltiples indicadores críticos que sugieren un fallo del sistema o un intento de intrusión.\n"
            report += "Hallazgos principales:\n• " + "\n• ".join(self.findings[:5])
        
        report += f"\n\nMetadatos: {s['size']} bytes | {s['lines']} líneas procesadas."
        return report

class MayaWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("MAYA - Neural Core")
        self.geometry("550x800")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

        self.engine = ForensicEngine()
        self.current_report = ""
        self.is_typing = False

        self.avatar_img = None
        try:
            path = os.path.join("resc", "MAiA.png")
            if os.path.exists(path):
                pil = Image.open(path)
                self.avatar_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(35, 35))
        except: pass

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- HEADER ESTILIZADO ---
        self.header = ctk.CTkFrame(self, height=80, fg_color=COLOR_SIDE, corner_radius=0)
        self.header.grid(row=0, column=0, sticky="ew")
        
        title_box = ctk.CTkFrame(self.header, fg_color="transparent")
        title_box.pack(side="left", padx=20, pady=10)

        try:
            logo_path = os.path.join("resc", "maya11.png")
            if os.path.exists(logo_path):
                logo_pil = Image.open(logo_path)
                self.logo_img = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(100, 30))
                ctk.CTkLabel(title_box, text="", image=self.logo_img).pack(anchor="w")
            else:
                ctk.CTkLabel(title_box, text="MAYA", font=("Arial Black", 20), text_color="#2596be").pack(anchor="w")
        except: pass
        
        ctk.CTkLabel(title_box, text="Módulo de Automatización Y Análisis.", font=("Roboto", 10), text_color="gray").pack(anchor="w")
        
        ctk.CTkLabel(self.header, text="● EN LÍNEA", font=("Roboto", 10, "bold"), text_color="#00E676").pack(side="right", padx=20)

        # --- CHAT AREA ---
        self.chat_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.chat_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # --- FOOTER ---
        self.footer = ctk.CTkFrame(self, height=150, fg_color=COLOR_SIDE, corner_radius=0)
        self.footer.grid(row=2, column=0, sticky="ew")
        
        # Fake Entry con estilo cristalino
        self.fake_entry = ctk.CTkEntry(self.footer, placeholder_text="Esperando comando...", height=45, 
                                       border_width=1, border_color="#333", fg_color="#1a1a1c", text_color="gray")
        self.fake_entry.pack(fill="x", padx=20, pady=(20, 15))
        self.fake_entry.configure(state="disabled")

        self.actions_frame = ctk.CTkFrame(self.footer, fg_color="transparent")
        self.actions_frame.pack(fill="x", padx=10, pady=(0, 20))

        self.confirm_frame = ctk.CTkFrame(self.footer, fg_color="transparent")

        # Botones Modernos
        self.btn_file = ctk.CTkButton(self.actions_frame, text="Analizar Archivo", fg_color="#2596be", hover_color="#1c7aa0", height=40, corner_radius=8, command=self.ask_file)
        self.btn_file.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_help = ctk.CTkButton(self.actions_frame, text="Ayuda", fg_color="#2B2B2B", hover_color="#3A3A3A", height=40, corner_radius=8, border_width=1, border_color="#444", command=self.open_help)
        self.btn_help.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_acc = ctk.CTkButton(self.actions_frame, text="Membresía", fg_color="#2B2B2B", hover_color="#3A3A3A", height=40, corner_radius=8, border_width=1, border_color="#444", command=self.open_account)
        self.btn_acc.pack(side="left", fill="x", expand=True, padx=5)

        self.btn_yes = ctk.CTkButton(self.confirm_frame, text="SÍ, GUARDAR", fg_color="#4CAF50", hover_color="#43a047", height=40, command=self.save_log)
        self.btn_yes.pack(side="left", fill="x", expand=True, padx=10)
        
        self.btn_no = ctk.CTkButton(self.confirm_frame, text="NO, DESCARTAR", fg_color="#FF5555", hover_color="#e53935", height=40, command=self.reset_chat)
        self.btn_no.pack(side="left", fill="x", expand=True, padx=10)

        self.welcome()

    def add_msg(self, text, is_user=False):
        bubble_color = COLOR_BUBBLE_USER if is_user else COLOR_BUBBLE_BOT
        align = "e" if is_user else "w"
        
        frame = ctk.CTkFrame(self.chat_frame, fg_color="transparent")
        frame.pack(fill="x", pady=5)

        if not is_user and self.avatar_img:
            ctk.CTkLabel(frame, text="", image=self.avatar_img).pack(side="left", anchor="n", padx=(0,10))

        # Burbuja con borde sutil para efecto moderno
        msg = ctk.CTkLabel(frame, text=text, fg_color=bubble_color, corner_radius=16, 
                           text_color="white", font=("Roboto", 13), wraplength=380, justify="left")
        msg.pack(side="right" if is_user else "left", ipadx=15, ipady=10)
        
        self.update_idletasks()
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def welcome(self):
        self.add_msg("¡Buenos días! Soy MAYA, tu analista forense inteligente.\nSelecciona una opción para comenzar.")

    # --- POPUPS COMPACTOS ---

    def open_account(self):
        self.add_msg("Consultar Membresía", True)
        self.add_msg("Aquí tienes tu tarjeta de identificación.")
        
        win = ctk.CTkToplevel(self)
        win.title("Perfil")
        win.geometry("300x320")
        win.resizable(False, False) # Bloquear tamaño
        win.configure(fg_color=COLOR_FONDO)
        win.transient(self) # Hacerla hija de la ventana principal
        win.grab_set() # Bloquear interacción con ventana padre
        
        ctk.CTkLabel(win, text="👤", font=("Arial", 60), text_color="#AAAAAA").pack(pady=(30, 10))
        ctk.CTkLabel(win, text="Aleksei Svarog", font=("Roboto", 18, "bold"), text_color="white").pack()
        ctk.CTkLabel(win, text="@SrWyatt_", text_color="gray").pack()
        
        badge = ctk.CTkFrame(win, fg_color=COLOR_WINE, border_color=COLOR_GOLD, border_width=1)
        badge.pack(pady=25, padx=40, fill="x")
        ctk.CTkLabel(badge, text="PLAN PREMIUM", font=("Roboto", 11, "bold"), text_color=COLOR_GOLD).pack(pady=8)
        
        ctk.CTkButton(win, text="Cerrar", fg_color="transparent", border_width=1, border_color="#333", text_color="gray", 
                      command=win.destroy).pack(side="bottom", pady=15)
        
        # Esperar a que se cierre para reiniciar
        self.wait_window(win)
        self.clear_and_restart()

    def open_help(self):
        self.add_msg("Ayuda y Soporte", True)
        self.add_msg("Abriendo panel de recursos...")
        
        win = ctk.CTkToplevel(self)
        win.title("Ayuda")
        win.geometry("380x300")
        win.resizable(False, False)
        win.configure(fg_color=COLOR_FONDO)
        win.transient(self)
        win.grab_set()
        
        ctk.CTkLabel(win, text="Soporte Técnico", font=("Roboto", 16, "bold"), text_color="white").pack(pady=20)
        grid = ctk.CTkFrame(win, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=20)
        grid.grid_columnconfigure((0,1), weight=1)
        
        opts = [("🎧 Soporte", 0, 0), ("⚠️ Reportar", 0, 1), ("❓ FAQs", 1, 0), ("📚 Guías", 1, 1)]
        for t, r, c in opts:
            btn = ctk.CTkButton(grid, text=t, fg_color="#1F1F21", height=50, border_width=1, border_color="#333", 
                                hover_color="#2B2B2B", command=win.destroy)
            btn.grid(row=r, column=c, padx=5, pady=5, sticky="nsew")
            
        # Esperar a que se cierre para reiniciar
        self.wait_window(win)
        self.clear_and_restart()

    # --- LÓGICA DE ANÁLISIS ---

    def ask_file(self):
        self.add_msg("Analizar Archivo", True)
        path = filedialog.askopenfilename(filetypes=[("Archivos de Log", "*.txt *.log *.csv *.json")])
        if path:
            self.add_msg(f"Procesando: {os.path.basename(path)}")
            self.fake_entry.configure(placeholder_text="MAYA está analizando...")
            self.actions_frame.pack_forget()
            
            # Iniciar animación y proceso
            self.is_typing = True
            threading.Thread(target=self.typing_animation).start()
            threading.Thread(target=self.process_file_thread, args=(path,)).start()
        else:
            self.add_msg("Operación cancelada.")
            # Reiniciar si cancela selección
            self.after(1000, self.clear_and_restart)

    def typing_animation(self):
        # Efecto visual en la barra de entrada
        dots = 0
        while self.is_typing:
            dots = (dots + 1) % 4
            txt = "Escribiendo" + "." * dots
            try:
                self.fake_entry.configure(placeholder_text=txt)
            except: break
            time.sleep(0.5)
        
        try:
            self.fake_entry.configure(placeholder_text="Análisis finalizado.")
        except: pass

    def process_file_thread(self, path):
        time.sleep(2.5) # Tiempo para apreciar la animación
        result = self.engine.analyze(path)
        self.current_report = result
        self.is_typing = False # Detener animación
        
        self.after(0, lambda: self.show_result(result))

    def show_result(self, result):
        self.add_msg(result)
        self.after(800, self.ask_save)

    def ask_save(self):
        self.add_msg("¿Desea guardar este informe en la base de datos?")
        self.confirm_frame.pack(fill="x", padx=10, pady=(0, 15))

    def save_log(self):
        self.add_msg("Sí, guardar registro.", True)
        if self.current_report:
            log_dir = os.path.join("logs", "maya")
            os.makedirs(log_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime("%d%m%Y_%H%M%S")
            path = os.path.join(log_dir, f"maya_report_{ts}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.current_report)
            self.add_msg(f"✅ Informe guardado correctamente.")
        
        # Esperar un momento antes de limpiar
        self.after(2000, self.clear_and_restart)

    def reset_chat(self):
        if not self.confirm_frame.winfo_ismapped():
             self.add_msg("No, gracias.", True)
        
        self.add_msg("Entendido. Descartando resultados...")
        self.after(1500, self.clear_and_restart)

    def clear_and_restart(self):
        # Limpiar Chat
        for widget in self.chat_frame.winfo_children():
            widget.destroy()
            
        # Restaurar Botones
        self.confirm_frame.pack_forget()
        self.actions_frame.pack(fill="x", padx=10, pady=(0, 20))
        self.fake_entry.configure(placeholder_text="Esperando comando...")
        
        # Mensaje de bienvenida limpio
        self.welcome()

if __name__ == "__main__":
    app = MayaWindow(None)
    app.mainloop()