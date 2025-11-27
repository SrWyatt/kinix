import customtkinter as ctk
import hashlib
import requests
import threading
import os
import datetime
import random
import string
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_HEADER_BG = "#121213"
COLOR_ACENTO = "#2596be"
COLOR_TARJETA = "#1F1F21"

class SentraLogic:
    def check(self, pwd):
        h = hashlib.sha1(pwd.encode()).hexdigest().upper()
        pre, suf = h[:5], h[5:]
        try:
            r = requests.get(f"https://api.pwnedpasswords.com/range/{pre}", timeout=5)
            for line in r.text.splitlines():
                hh, c = line.split(':')
                if hh == suf: return int(c)
        except: pass
        return 0

    def complexity(self, pwd):
        score = 0
        if len(pwd) > 8: score += 1
        if len(pwd) > 12: score += 1
        if any(c.isdigit() for c in pwd): score += 1
        if any(c.isupper() for c in pwd): score += 1
        if any(not c.isalnum() for c in pwd): score += 1
        return score 

class SentraWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("KINIX - Sentra")
        self.geometry("900x700")
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

        try: self.iconphoto(False, ctk.tkinter.PhotoImage(file="resc/vn.png"))
        except: pass
        self.logic = SentraLogic()
        self.last_res = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header = ctk.CTkFrame(self, height=80, fg_color=COLOR_HEADER_BG)
        self.header.grid(row=0, column=0, sticky="ew")
        tf = ctk.CTkFrame(self.header, fg_color="transparent")
        tf.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(tf, text="Sentra", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        
        try:
            pil_img = ctk.CTkImage(light_image=Image.open("resc/logo h.png"), dark_image=Image.open("resc/logo h.png"), size=(150, 40))
            ctk.CTkLabel(self.header, text="", image=pil_img).pack(side="right", padx=20)
        except: pass

        self.tabs = ctk.CTkTabview(self, fg_color="transparent")
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=20)
        self.tab_audit = self.tabs.add("Auditoría")
        self.tab_gen = self.tabs.add("Generador")

        self.e = ctk.CTkEntry(self.tab_audit, width=300, show="*", placeholder_text="Contraseña a verificar")
        self.e.pack(pady=20)
        self.btn = ctk.CTkButton(self.tab_audit, text="VERIFICAR", fg_color=COLOR_ACENTO, command=self.start)
        self.btn.pack(pady=5)
        self.lbl_comp = ctk.CTkLabel(self.tab_audit, text="Análisis Local: -", text_color="gray")
        self.lbl_comp.pack(pady=10)

        self.res = ctk.CTkFrame(self.tab_audit, fg_color="transparent")
        self.res.pack(fill="x", padx=40, pady=20)

        self.lbl_gen = ctk.CTkEntry(self.tab_gen, width=300, font=("Consolas", 16))
        self.lbl_gen.pack(pady=30)
        self.slider_len = ctk.CTkSlider(self.tab_gen, from_=8, to=32, number_of_steps=24)
        self.slider_len.set(16)
        self.slider_len.pack(pady=10)
        self.btn_gen = ctk.CTkButton(self.tab_gen, text="GENERAR NUEVA", fg_color=COLOR_ACENTO, command=self.generate)
        self.btn_gen.pack(pady=10)

    def start(self):
        p = self.e.get()
        if not p: return
        score = self.logic.complexity(p)
        lvl = ["Muy Débil", "Débil", "Regular", "Buena", "Fuerte", "Muy Fuerte"][score]
        self.lbl_comp.configure(text=f"Fuerza: {lvl} ({score}/5)")
        self.btn.configure(state="disabled")
        threading.Thread(target=self.run, args=(p,)).start()

    def run(self, p):
        c = self.logic.check(p)
        self.after(0, lambda: self.show(c))

    def show(self, c):
        self.btn.configure(state="normal")
        self.e.delete(0, "end")
        self.last_res = c
        for w in self.res.winfo_children(): w.destroy()
        
        color = "#4CAF50" if c == 0 else "#FF5555"
        card = ctk.CTkFrame(self.res, fg_color=color, corner_radius=10)
        card.pack(fill="x", ipady=20)
        
        if c == 0:
            ctk.CTkLabel(card, text="NO FILTRADA", font=("Roboto", 24, "bold"), text_color="white").pack()
            ctk.CTkLabel(card, text="Esta contraseña no aparece en bases de datos públicas.", text_color="white").pack()
        else:
            ctk.CTkLabel(card, text="COMPROMETIDA", font=("Roboto", 24, "bold"), text_color="white").pack()
            ctk.CTkLabel(card, text=f"Aparece {c} veces en filtraciones conocidas.", text_color="white").pack()

    def generate(self):
        l = int(self.slider_len.get())
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = ''.join(random.choice(chars) for _ in range(l))
        self.lbl_gen.delete(0, "end")
        self.lbl_gen.insert(0, pwd)