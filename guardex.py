# guardex.py
import argparse
import hashlib
import sys
import os

def calculate_hash(file_path):
    """
    Calcula el hash SHA-256 de un archivo.
    """
    if not os.path.exists(file_path):
        print(f"[ERROR] El archivo no existe: {file_path}")
        sys.exit(1)
        
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Leer el archivo en bloques para no consumir mucha RAM
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
            print(f"SHA-256 de {file_path}:")
            print(sha256_hash.hexdigest())
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo: {e}")

def search_log(log_file, keyword):
    """
    Busca una palabra clave (sensible a mayúsculas) en un archivo de log.
    """
    if not os.path.exists(log_file):
        print(f"[ERROR] El archivo de log no existe: {log_file}")
        sys.exit(1)
        
    print(f"\n[INFO] Buscando '{keyword}' en {log_file}...")
    found = False
    try:
        with open(log_file, "r", encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f):
                if keyword in line:
                    print(f"  - Línea {i+1}: {line.strip()}")
                    found = True
        if not found:
            print(f"No se encontraron coincidencias para '{keyword}'.")
    except Exception as e:
        print(f"[ERROR] No se pudo leer el archivo de log: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Guardex: Herramientas forenses básicas.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Sub-comando para 'hash'
    hash_parser = subparsers.add_parser("hash", help="Calcula el hash SHA-256 de un archivo.")
    hash_parser.add_argument("file", help="Ruta al archivo.")
    
    # Sub-comando para 'search'
    search_parser = subparsers.add_parser("search", help="Busca una palabra clave en un archivo de log.")
    search_parser.add_argument("logfile", help="Ruta al archivo de log.")
    search_parser.add_argument("keyword", help="Palabra clave a buscar.")
    
    args = parser.parse_args()
    
    if args.command == "hash":
        calculate_hash(args.file)
    elif args.command == "search":
        search_log(args.logfile, args.keyword)
