import customtkinter as ctk
from tkinter import filedialog
import os
import json
import datetime
import math
from mimetypes import guess_type
from PIL import Image

COLOR_FONDO = "#171718"
COLOR_HEADER_BG = "#121213"
COLOR_ACENTO = "#2596be"
COLOR_TARJETA = "#1F1F21"
COLOR_SAFE = "#00E676"
COLOR_WARN = "#FFEA00"
COLOR_DANGER = "#FF3D00"

try:
    import yara
    ENG_OK = True
except ImportError:
    ENG_OK = False

try:
    import exifread
    from pypdf import PdfReader
    import docx
    import openpyxl
except ImportError: pass

RULES = """
rule Suspicious {
    strings:
        $a = "CreateObject" nocase
        $b = "Shell" nocase
        $c = "eval(" nocase
        $d = "base64_decode" nocase
    condition: any of them
}
"""

class DocScanner:
    def scan(self, p):
        r = {
            "path": p, "safe": True, "hit": [], 
            "summary": {"Size": "0 KB", "Author": "N/A", "Date": "N/A", "Software": "N/A", "Location": "N/A", "Device": "N/A"},
            "raw_meta": {}, 
            "ent": 0.0, "magic_check": True
        }
        
        try:
            # 1. Análisis de Bytes (Entropía y Magic)
            with open(p, 'rb') as f:
                d = f.read()
                if d:
                    e = 0
                    for x in range(256):
                        px = float(d.count(bytes([x]))) / len(d)
                        if px > 0: e += - px * math.log(px, 2)
                    r["ent"] = round(e, 2)
                
                header = d[:4].hex().upper()
                ext = os.path.splitext(p)[1].lower()
                r["magic_check"] = self.check_magic(header, ext)
        except: pass

        # 2. Análisis YARA
        if ENG_OK:
            try:
                c = yara.compile(source=RULES)
                m = c.match(p)
                if m:
                    r["safe"] = False
                    r["hit"] = [x.rule for x in m]
            except: pass
        
        # 3. Extracción Profunda de Metadatos
        self.extract_metadata(p, r)
        return r

    def check_magic(self, header, ext):
        sigs = {".jpg": "FFD8", ".jpeg": "FFD8", ".png": "89504E47", ".gif": "47494638", ".pdf": "25504446", ".exe": "4D5A", ".zip": "504B0304"}
        if ext in sigs:
            if not header.startswith(sigs[ext]): return False
        return True

    def extract_metadata(self, p, r):
        # Datos básicos del sistema
        try:
            s = os.stat(p)
            sz = s.st_size
            if sz < 1024: r["summary"]["Size"] = f"{sz} B"
            elif sz < 1024**2: r["summary"]["Size"] = f"{sz/1024:.2f} KB"
            else: r["summary"]["Size"] = f"{sz/(1024**2):.2f} MB"
            
            # Fecha de modificación como fallback
            dt = datetime.datetime.fromtimestamp(s.st_mtime)
            r["summary"]["Date"] = dt.strftime("%Y-%m-%d %H:%M")
            r["raw_meta"]["System Modified"] = str(dt)
            r["raw_meta"]["System Created"] = str(datetime.datetime.fromtimestamp(s.st_ctime))
        except: pass

        mt, _ = guess_type(p)
        if mt:
            if "image" in mt: self._img(p, r)
            elif "pdf" in mt: self._pdf(p, r)
            elif "word" in mt or "sheet" in mt: self._office(p, r)

    def _img(self, p, r):
        try:
            with open(p, 'rb') as f:
                tags = exifread.process_file(f, details=True)
                for k, v in tags.items():
                    if k == "JPEGThumbnail": continue # Ignorar binario
                    r["raw_meta"][k] = str(v)
                    
                    # Mapeo al Dashboard
                    k_lo = k.lower()
                    val = str(v)
                    if "image artist" in k_lo or "xpauthor" in k_lo: r["summary"]["Author"] = val
                    if "software" in k_lo: r["summary"]["Software"] = val
                    if "model" in k_lo: r["summary"]["Device"] = val
                    if "datetime" in k_lo and "original" in k_lo: r["summary"]["Date"] = val
                    
                    # Detección simple de GPS
                    if "gps latitude" in k_lo:
                        r["summary"]["Location"] = "Datos GPS Detectados"
        except: pass

    def _pdf(self, p, r):
        try:
            pdf = PdfReader(p)
            meta = pdf.metadata
            if meta:
                for k, v in meta.items():
                    key_clean = k.replace("/", "")
                    r["raw_meta"][key_clean] = str(v)
                    
                    if "Author" in key_clean: r["summary"]["Author"] = str(v)
                    if "Creator" in key_clean or "Producer" in key_clean: r["summary"]["Software"] = str(v)
                    if "CreationDate" in key_clean: r["summary"]["Date"] = str(v).replace("D:", "").split('+')[0]
        except: pass

    def _office(self, p, r):
        try:
            if p.endswith(".docx"):
                doc = docx.Document(p)
                cp = doc.core_properties
                r["summary"]["Author"] = cp.author or "N/A"
                r["summary"]["Date"] = str(cp.modified) or str(cp.created)
                r["summary"]["Software"] = "Microsoft Word / OpenXML"
                # Dump de todo lo que haya
                attrs = ["author", "category", "comments", "content_status", "created", "identifier", "keywords", "language", "last_modified_by", "modified", "revision", "subject", "title", "version"]
                for a in attrs:
                    val = getattr(cp, a, None)
                    if val: r["raw_meta"][a.capitalize()] = str(val)

            elif p.endswith(".xlsx"):
                wb = openpyxl.load_workbook(p)
                cp = wb.properties
                r["summary"]["Author"] = cp.creator or "N/A"
                r["summary"]["Date"] = str(cp.modified) or str(cp.created)
                r["summary"]["Software"] = "Microsoft Excel / OpenXML"
                attrs = ["creator", "title", "description", "subject", "identifier", "language", "created", "modified", "lastModifiedBy", "category", "contentStatus", "version", "revision"]
                for a in attrs:
                    val = getattr(cp, a, None)
                    if val: r["raw_meta"][a.capitalize()] = str(val)
        except: pass

class MetaCard(ctk.CTkFrame):
    def __init__(self, parent, icon, title, value, color=COLOR_ACENTO):
        super().__init__(parent, fg_color=COLOR_TARJETA, corner_radius=10, border_width=1, border_color="#2B2B2B")
        self.icon_lbl = ctk.CTkLabel(self, text=icon, font=("Segoe UI Emoji", 20))
        self.icon_lbl.pack(side="left", padx=(15, 10), pady=15)
        
        self.data_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.data_frame.pack(side="left", fill="both", expand=True, pady=5)
        
        self.lbl_title = ctk.CTkLabel(self.data_frame, text=title, font=("Roboto", 10, "bold"), text_color="gray", anchor="w")
        self.lbl_title.pack(fill="x")
        
        # Ajuste de tamaño de fuente si el texto es muy largo
        f_size = 13 if len(str(value)) < 18 else 10
        self.lbl_val = ctk.CTkLabel(self.data_frame, text=str(value), font=("Roboto", f_size, "bold"), text_color=color, anchor="w")
        self.lbl_val.pack(fill="x")

class SecureDocsWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("KINIX - SecureDocs Forensic")
        self.geometry("1000x800")
        self.configure(fg_color=COLOR_FONDO)
        self.attributes("-topmost", True)
        self.after(200, lambda: self.attributes("-topmost", False))
        self.focus_force()

        try: self.iconphoto(False, ctk.tkinter.PhotoImage(file="resc/vn.png"))
        except: pass
        self.eng = DocScanner()
        self.cache = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        self.head = ctk.CTkFrame(self, height=80, fg_color=COLOR_HEADER_BG)
        self.head.grid(row=0, column=0, sticky="ew")
        tf = ctk.CTkFrame(self.head, fg_color="transparent")
        tf.pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(tf, text="SecureDocs", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(tf, text="| Análisis de Metadatos", font=("Roboto", 14), text_color=COLOR_ACENTO).pack(side="left", padx=10)
        
        try:
            img = ctk.CTkImage(light_image=Image.open("resc/logo h.png"), dark_image=Image.open("resc/logo h.png"), size=(150, 40))
            ctk.CTkLabel(self.head, text="", image=img).pack(side="right", padx=20)
        except: pass
        
        # Main Scroll
        self.scr = ctk.CTkScrollableFrame(self, fg_color="#121213")
        self.scr.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        
        # Estado inicial
        self.empty_state()

        # Footer Actions
        self.ft = ctk.CTkFrame(self, height=80, fg_color="#1F1F21")
        self.ft.grid(row=2, column=0, sticky="ew")
        self.btn = ctk.CTkButton(self.ft, text="SELECCIONAR ARCHIVO", fg_color=COLOR_ACENTO, width=200, command=self.sel)
        self.btn.pack(side="left", padx=30, pady=20)
        self.btn_s = ctk.CTkButton(self.ft, text="EXPORTAR JSON", fg_color="#2B2B2B", width=150, command=self.save)
        self.btn_s.pack(side="right", padx=30, pady=20)

    def empty_state(self):
        self.lbl_empty = ctk.CTkLabel(self.scr, text="📂\nArrastre un archivo o haga clic en Seleccionar\npara extraer metadatos forenses.", font=("Roboto", 16), text_color="gray")
        self.lbl_empty.pack(pady=150)

    def sel(self):
        p = filedialog.askopenfilename()
        self.lift()
        if p: self.run(p)

    def run(self, p):
        for w in self.scr.winfo_children(): w.destroy()
        r = self.eng.scan(p)
        self.cache = r
        
        # 1. STATUS HEADER
        self.draw_status_header(r, p)

        # 2. MINI DASHBOARD (Key Insights)
        ctk.CTkLabel(self.scr, text="RESUMEN CLAVE", font=("Roboto", 12, "bold"), text_color="gray").pack(anchor="w", pady=(20, 10))
        self.draw_dashboard(r["summary"])

        # 3. RAW DATA LIST
        ctk.CTkLabel(self.scr, text=f"METADATOS RAW ({len(r['raw_meta'])})", font=("Roboto", 12, "bold"), text_color="gray").pack(anchor="w", pady=(30, 10))
        self.draw_raw_list(r["raw_meta"])

    def draw_status_header(self, r, path):
        # Color logic
        is_safe = r["safe"] and r["magic_check"]
        c = COLOR_SAFE if is_safe else COLOR_DANGER
        t = "INTEGRIDAD VERIFICADA" if is_safe else "POSIBLE ANOMALÍA"
        
        status_fr = ctk.CTkFrame(self.scr, fg_color=c, corner_radius=8)
        status_fr.pack(fill="x", pady=(0, 10))
        
        top = ctk.CTkFrame(status_fr, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(top, text=t, font=("Roboto", 18, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(top, text=f"Entropía: {r['ent']}", font=("Consolas", 12, "bold"), text_color="white").pack(side="right")
        
        ctk.CTkLabel(status_fr, text=os.path.basename(path), text_color="white", font=("Roboto", 12)).pack(padx=15, pady=(0, 10), anchor="w")

        if not r["magic_check"]:
            err_fr = ctk.CTkFrame(self.scr, fg_color="#2B2B2B", border_color=COLOR_WARN, border_width=1)
            err_fr.pack(fill="x", pady=5)
            ctk.CTkLabel(err_fr, text="⚠️ ALERTA DE MAGIC BYTES: La extensión del archivo no coincide con su firma hexadecimal real.", text_color=COLOR_WARN).pack(pady=5)

    def draw_dashboard(self, s):
        grid = ctk.CTkFrame(self.scr, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure((0, 1, 2), weight=1)
        
        # Fila 1
        MetaCard(grid, "👤", "AUTOR", s["Author"]).grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        MetaCard(grid, "📅", "FECHA / HORA", s["Date"]).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        MetaCard(grid, "💾", "TAMAÑO", s["Size"]).grid(row=0, column=2, sticky="ew", padx=5, pady=5)
        
        # Fila 2
        MetaCard(grid, "📍", "LOCACIÓN", s["Location"], color=COLOR_WARN if s["Location"] != "N/A" else "gray").grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        MetaCard(grid, "💻", "SOFTWARE", s["Software"]).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        MetaCard(grid, "📷", "DISPOSITIVO", s["Device"]).grid(row=1, column=2, sticky="ew", padx=5, pady=5)

    def draw_raw_list(self, raw):
        list_fr = ctk.CTkFrame(self.scr, fg_color=COLOR_TARJETA)
        list_fr.pack(fill="x")
        
        if not raw:
            ctk.CTkLabel(list_fr, text="No se encontraron metadatos adicionales.", text_color="gray").pack(pady=20)
            return

        i = 0
        for k, v in raw.items():
            bg = "#252526" if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(list_fr, fg_color=bg, corner_radius=0)
            row.pack(fill="x")
            
            # Key (Truncada)
            k_txt = (k[:30] + '..') if len(k) > 30 else k
            ctk.CTkLabel(row, text=k_txt, width=200, anchor="w", font=("Consolas", 11), text_color=COLOR_ACENTO).pack(side="left", padx=10, pady=2)
            
            # Value (Truncado)
            v_txt = (v[:80] + '...') if len(v) > 80 else v
            ctk.CTkLabel(row, text=v_txt, anchor="w", font=("Roboto", 11), text_color="#DDD").pack(side="left", padx=10, pady=2)
            i += 1

    def save(self):
        if not self.cache: return
        d = "logs/securedocs"
        if not os.path.exists(d): os.makedirs(d)
        n = f"forensic_report_{datetime.datetime.now().strftime('%d%m%Y_%H%M%S')}.json"
        with open(os.path.join(d, n), "w") as f: json.dump(self.cache, f, indent=4, default=str)
        self.btn_s.configure(text="EXPORTADO ✅", fg_color="#00E676")
        self.after(2000, lambda: self.btn_s.configure(text="EXPORTAR JSON", fg_color="#2B2B2B"))