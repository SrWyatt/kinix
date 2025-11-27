import customtkinter as ctk
import subprocess
import platform
import threading
import os
import datetime
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_HEADER_BG = "#121213"
COLOR_TARJETA = "#1F1F21"
COLOR_ACENTO = "#2596be"
COLOR_SAFE = "#4CAF50"
COLOR_RISK = "#FF5555"

class BiosLogic:
    def check(self):
        data = {"os": platform.system(), "sb": "unknown", "bios_ver": "N/A", "board": "N/A"}
        try:
            if data["os"] == "Windows":
                v = subprocess.check_output("wmic bios get smbiosbiosversion", shell=True).decode().split('\n')[1].strip()
                b = subprocess.check_output("wmic baseboard get product", shell=True).decode().split('\n')[1].strip()
                m = subprocess.check_output("wmic baseboard get manufacturer", shell=True).decode().split('\n')[1].strip()
                data["bios_ver"] = v
                data["board"] = f"{m} {b}"
                
                res = subprocess.run(["powershell", "-Command", "Confirm-SecureBootUEFI"], capture_output=True, text=True)
                if "True" in res.stdout: data["sb"] = "true"
                elif "False" in res.stdout: data["sb"] = "false"
                else: data["sb"] = "error"
            elif data["os"] == "Linux":
                if os.path.exists('/sys/class/dmi/id/bios_version'):
                    with open('/sys/class/dmi/id/bios_version') as f: data["bios_ver"] = f.read().strip()
                res = subprocess.run(['mokutil', '--sb-state'], capture_output=True, text=True)
                if "enabled" in res.stdout: data["sb"] = "true"
                else: data["sb"] = "false"
        except: data["sb"] = "error"
        return data

class SmartBiosWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("KINIX - SmartBios")
        self.geometry("800x600")
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

        try: self.iconphoto(False, ctk.tkinter.PhotoImage(file="resc/vn.png"))
        except: pass
        self.scanner = BiosLogic()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkFrame(self, height=80, fg_color=COLOR_HEADER_BG)
        self.header.grid(row=0, column=0, sticky="ew")
        tf = ctk.CTkFrame(self.header, fg_color="transparent")
        tf.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(tf, text="SmartBios", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        try:
            pil_img = ctk.CTkImage(light_image=Image.open("resc/logo h.png"), dark_image=Image.open("resc/logo h.png"), size=(150, 40))
            ctk.CTkLabel(self.header, text="", image=pil_img).pack(side="right", padx=20)
        except: pass

        self.status_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.status_frame.grid(row=1, column=0, sticky="ew", padx=40, pady=30)
        self.card = ctk.CTkFrame(self.status_frame, fg_color=COLOR_TARJETA, corner_radius=15, border_width=2)
        self.card.pack(fill="x", ipady=20)
        
        self.icon = ctk.CTkLabel(self.card, text="🛡️", font=("Segoe UI Emoji", 60))
        self.icon.pack(pady=10)
        self.lbl_main = ctk.CTkLabel(self.card, text="Esperando Análisis", font=("Roboto", 24, "bold"))
        self.lbl_main.pack()
        self.lbl_ver = ctk.CTkLabel(self.card, text="", text_color="gray")
        self.lbl_ver.pack(pady=5)
        self.lbl_board = ctk.CTkLabel(self.card, text="", text_color="gray")
        self.lbl_board.pack()

        self.btn = ctk.CTkButton(self, text="VERIFICAR FIRMWARE", fg_color=COLOR_ACENTO, width=200, command=self.run)
        self.btn.grid(row=2, column=0, pady=20)

    def run(self):
        self.btn.configure(state="disabled")
        threading.Thread(target=self.scan).start()

    def scan(self):
        res = self.scanner.check()
        self.after(0, lambda: self.show(res))

    def show(self, res):
        self.btn.configure(state="normal")
        c = COLOR_SAFE if res["sb"] == "true" else COLOR_RISK
        t = "SECURE BOOT ACTIVADO" if res["sb"] == "true" else "SECURE BOOT DESACTIVADO"
        self.card.configure(border_color=c)
        self.lbl_main.configure(text=t, text_color=c)
        self.lbl_ver.configure(text=f"Versión BIOS: {res['bios_ver']}")
        self.lbl_board.configure(text=f"Placa Base: {res['board']}")