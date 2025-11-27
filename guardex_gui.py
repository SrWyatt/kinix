import customtkinter as ctk
import hashlib
import os
import threading
import datetime
from tkinter import filedialog
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_HEADER_BG = "#121213"
COLOR_ACENTO = "#2596be"
COLOR_TARJETA = "#1F1F21"

class GuardexLogic:
    def calc_hash(self, path):
        if not os.path.exists(path): return None
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for b in iter(lambda: f.read(4096), b""): h.update(b)
        return h.hexdigest()

    def search_recursive(self, folder, key):
        matches = []
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith((".log", ".txt", ".xml", ".json")):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding='utf-8', errors='ignore') as f:
                            for i, line in enumerate(f):
                                if key in line:
                                    matches.append(f"[{file}:{i+1}] {line.strip()[:100]}")
                    except: pass
        return matches

class GuardexWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("KINIX - Guardex")
        self.geometry("900x700")
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

        try: self.iconphoto(False, ctk.tkinter.PhotoImage(file="resc/vn.png"))
        except: pass
        self.logic = GuardexLogic()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header = ctk.CTkFrame(self, height=80, fg_color=COLOR_HEADER_BG)
        self.header.grid(row=0, column=0, sticky="ew")
        tf = ctk.CTkFrame(self.header, fg_color="transparent")
        tf.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(tf, text="Guardex", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        try:
            pil_img = ctk.CTkImage(light_image=Image.open("resc/logo h.png"), dark_image=Image.open("resc/logo h.png"), size=(150, 40))
            ctk.CTkLabel(self.header, text="", image=pil_img).pack(side="right", padx=20)
        except: pass

        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=20)
        self.tab_h = self.tabs.add("Integridad de Archivos")
        self.tab_l = self.tabs.add("Búsqueda en Logs")

        self.btn_f = ctk.CTkButton(self.tab_h, text="SELECCIONAR ARCHIVO", fg_color=COLOR_ACENTO, command=self.do_hash)
        self.btn_f.pack(pady=20)
        self.e_hash = ctk.CTkEntry(self.tab_h, width=600, placeholder_text="SHA-256 Calculado")
        self.e_hash.pack(pady=5)
        self.e_cmp = ctk.CTkEntry(self.tab_h, width=600, placeholder_text="Hash original para comparar")
        self.e_cmp.pack(pady=5)
        self.btn_cmp = ctk.CTkButton(self.tab_h, text="VERIFICAR", fg_color="#333", command=self.compare)
        self.btn_cmp.pack(pady=10)
        self.lbl_res = ctk.CTkLabel(self.tab_h, text="")
        self.lbl_res.pack()

        fr = ctk.CTkFrame(self.tab_l, fg_color="transparent")
        fr.pack(fill="x")
        self.e_k = ctk.CTkEntry(fr, placeholder_text="Palabra clave (Error, Fail, Admin)", width=200)
        self.e_k.pack(side="left", padx=5)
        self.btn_l = ctk.CTkButton(fr, text="BUSCAR EN CARPETA", fg_color=COLOR_ACENTO, command=self.do_log)
        self.btn_l.pack(side="left", padx=5)
        self.scr_l = ctk.CTkScrollableFrame(self.tab_l)
        self.scr_l.pack(fill="both", expand=True, pady=10)

    def do_hash(self):
        p = filedialog.askopenfilename()
        self.lift()
        if p:
            h = self.logic.calc_hash(p)
            self.e_hash.delete(0, "end")
            self.e_hash.insert(0, h)

    def compare(self):
        h1 = self.e_hash.get().strip()
        h2 = self.e_cmp.get().strip()
        if h1 == h2:
            self.lbl_res.configure(text="✅ INTEGRIDAD VERIFICADA", text_color="#4CAF50")
        else:
            self.lbl_res.configure(text="❌ HASH NO COINCIDE", text_color="#FF5555")

    def do_log(self):
        k = self.e_k.get()
        if not k: return
        d = filedialog.askdirectory()
        self.lift()
        if d:
            threading.Thread(target=self.run_search, args=(d, k)).start()

    def run_search(self, d, k):
        matches = self.logic.search_recursive(d, k)
        self.after(0, lambda: self.show_matches(matches))

    def show_matches(self, matches):
        for w in self.scr_l.winfo_children(): w.destroy()
        if not matches:
            ctk.CTkLabel(self.scr_l, text="No se encontraron coincidencias.").pack()
            return
        for m in matches:
            ctk.CTkLabel(self.scr_l, text=m, anchor="w", text_color="gray").pack(fill="x")