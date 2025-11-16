import yara
import argparse
import sys
import os
import datetime
from mimetypes import guess_type


try:
    # Para .jpg, .tif (EXIF)
    import exifread
    # Para .pdf
    from pypdf import PdfReader
    # Para .docx
    import docx
    # Para .xlsx
    import openpyxl
except ImportError:
    print("[ERROR] Faltan bibliotecas. Ejecuta: pip install exifread pypdf python-docx openpyxl")
    sys.exit(1)

YARA_RULE_EXAMPLE = """
rule MaliciousMacroExample
{
    meta:
        description = "Detecta strings comunes de macros sospechosas"
    strings:
        $a = "CreateObject" nocase
        $b = "Shell" nocase
        $c = "WScript" nocase
    condition:
        ($a and $b) or ($a and $c)
}
"""


def scan_file_yara(file_path):
    """
    Escanea un archivo.
    """
    print(f"--- Análisis de Seguridad ---")
    is_safe = True
    try:
        rules = yara.compile(source=YARA_RULE_EXAMPLE)
        matches = rules.match(file_path)
        
        if matches:
            is_safe = False
            print(f"[ALERTA] ¡AMENAZA DETECTADA!")
            for match in matches:
                print(f"  - Regla: {match.rule}")
                print(f"  - Descripción: {match.meta.get('description', 'N/A')}")
        else:
            print(f"[INFO] Archivo parece seguro.")
            
    except yara.Error as e:
        print(f"[ERROR] Error: {e}")
    except Exception as e:
        print(f"[ERROR] Ocurrió un error en el escaneo: {e}")
    print("------------------------------------")
    return is_safe


def _print_meta(key, value):
    """Ayudante para imprimir metadatos de forma limpia."""
    if value:
        print(f"    - {key:<22}: {value}")

def _format_gps(gps_tag):
    """Convierte coordenadas GPS de EXIF a un formato legible."""
    try:
        d = gps_tag.values[0].num / gps_tag.values[0].den
        m = gps_tag.values[1].num / gps_tag.values[1].den
        s = gps_tag.values[2].num / gps_tag.values[2].den
        return f"{d:.0f}° {m:.0f}' {s:.2f}\""
    except Exception:
        return str(gps_tag.values)

def get_system_metadata(file_path):
    """Metadatos básicos del sistema de archivos (para CUALQUIER archivo)."""
    print("\n  [Metadatos del Sistema]")
    try:
        stat = os.stat(file_path)
        _print_meta("Tamaño", f"{stat.st_size} bytes")
        _print_meta("Última Modificación", datetime.datetime.fromtimestamp(stat.st_mtime))
        _print_meta("Último Acceso", datetime.datetime.fromtimestamp(stat.st_atime))
        _print_meta("Fecha de Creación", datetime.datetime.fromtimestamp(stat.st_ctime))
    except Exception as e:
        print(f"[ERROR] No se pudo leer metadatos del sistema: {e}")

def get_exif_metadata(file_path):
    """Metadatos detallados de EXIF (para .jpg, .tif)."""
    print("\n  [Metadatos EXIF (Imagen)]")
    try:
        with open(file_path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
            if not tags:
                print("    - No se encontraron datos EXIF.")
                return

            print("    --- DATOS IMPORTANTES ---")
            # Locación
            lat = tags.get('GPS GPSLatitude')
            lon = tags.get('GPS GPSLongitude')
            if lat and lon:
                lat_ref = tags.get('GPS GPSLatitudeRef', 'N').values
                lon_ref = tags.get('GPS GPSLongitudeRef', 'E').values
                _print_meta("LOCACIÓN (Lat)", f"{_format_gps(lat)} {lat_ref}")
                _print_meta("LOCACIÓN (Lon)", f"{_format_gps(lon)} {lon_ref}")
                _print_meta("Google Maps (aprox)", f"https://www.google.com/maps?q={lat.values[0].num/lat.values[0].den},{lon.values[0].num/lon.values[0].den}")

            # Fecha/Hora
            _print_meta("Fecha de Creación", tags.get('Image DateTimeOriginal'))
            
            # Software y Dispositivo
            _print_meta("Autor/Artista", tags.get('Image Artist'))
            _print_meta("Software", tags.get('Image Software'))
            _print_meta("Dispositivo (Marca)", tags.get('Image Make'))
            _print_meta("Dispositivo (Modelo)", tags.get('Image Model'))
            
            print("\n    --- Todos los Datos EXIF ---")
            for tag, value in tags.items():
                if tag not in ('JPEGThumbnail', 'TIFFThumbnail'): # Ignorar miniaturas
                    print(f"    - {tag:<22}: {value}")

    except Exception as e:
        print(f"[ERROR] No se pudo leer metadatos EXIF: {e}")

def get_pdf_metadata(file_path):
    """Metadatos detallados de PDF."""
    print("\n  [Metadatos de PDF]")
    try:
        reader = PdfReader(file_path)
        meta = reader.metadata
        if not meta:
            print("    - No se encontraron metadatos.")
            return

        print("    --- DATOS IMPORTANTES ---")
        _print_meta("Autor", meta.author)
        _print_meta("Software (Creador)", meta.creator)
        _print_meta("Software (Productor)", meta.producer)
        _print_meta("Fecha de Creación", meta.creation_date)
        _print_meta("Fecha de Modificación", meta.modification_date)
        
        print("\n    --- Todos los Datos PDF ---")
        _print_meta("Título", meta.title)
        _print_meta("Asunto", meta.subject)
        # Bucle por si hay más metadatos no estándar
        for key, value in meta.items():
            if key not in ('/Author', '/Creator', '/Producer', '/CreationDate', '/ModDate', '/Title', '/Subject'):
                 _print_meta(key, value)
                 
    except Exception as e:
        print(f"[ERROR] No se pudo leer metadatos del PDF: {e}")

def get_office_metadata(file_path, file_type):
    """Metadatos de DOCX y XLSX."""
    print(f"\n  [Metadatos de Office ({file_type})]")
    try:
        if file_type == 'docx':
            doc = docx.Document(file_path)
            meta = doc.core_properties
        elif file_type == 'xlsx':
            doc = openpyxl.load_workbook(file_path)
            meta = doc.properties
        else:
            return

        print("    --- DATOS IMPORTANTES ---")
        _print_meta("Autor", meta.author)
        _print_meta("Última Modificación por", meta.last_modified_by)
        _print_meta("Fecha de Creación", meta.created)
        _print_meta("Fecha de Modificación", meta.modified)
        _print_meta("Versión", meta.version)

        print("\n    --- Todos los Datos Office ---")
        _print_meta("Título", meta.title)
        _print_meta("Asunto", meta.subject)
        _print_meta("Comentarios", meta.comments)
        _print_meta("Categoría", meta.category)
        
    except Exception as e:
        print(f"[ERROR] No se pudo leer metadatos de Office: {e}")


def get_file_metadata(file_path):
    """
    Controlador principal que decide qué función de metadatos llamar.
    """
    print(f"\n--- Análisis de Metadatos ---")
    # Siempre obtenemos los metadatos del sistema
    get_system_metadata(file_path)
    
    # Adivinamos el tipo de archivo
    mime_type, _ = guess_type(file_path)
    if mime_type is None:
        print("[INFO] No se pudo determinar el tipo de archivo (MIME).")
        return

    # Llamamos al analizador especializado
    if mime_type in ('image/jpeg', 'image/tiff'):
        get_exif_metadata(file_path)
    elif mime_type == 'application/pdf':
        get_pdf_metadata(file_path)
    elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        get_office_metadata(file_path, 'docx')
    elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        get_office_metadata(file_path, 'xlsx')
    else:
        print(f"\n[INFO] No hay un analizador de metadatos interno para el tipo '{mime_type}'.")
    
    print("-----------------------------")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SecureDocs: Analizador de Archivos (Seguridad y Metadatos).")
    parser.add_argument("file", help="La ruta al archivo a escanear (ej: foto.jpg, reporte.pdf, etc.)")
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"[ERROR] El archivo no existe: {args.file}")
        sys.exit(1)

    print(f"Analizando archivo: {os.path.abspath(args.file)}")
    
    # 1. Ejecuta el escaneo de seguridad
    is_safe = scan_file_yara(args.file)
    
    # 2. Ejecuta la extracción de metadatos
    get_file_metadata(args.file)
    
    print("\n--- RESUMEN FINAL ---")
    if is_safe:
        print("Estado de Seguridad: ESTE ARCHIVO PARECE SEGURO")
    else:
        print("Estado de Seguridad: (!) AMENAZA DETECTADA")
    print("---------------------")
