# patchtrack.py
import requests
import argparse
import sys

def check_package_version(package_name, current_version):
    """
    Comprueba la última versión de un paquete en PyPI.
    """
    try:
        print(f"[INFO] Verificando {package_name} (Versión actual: {current_version})...")
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        response.raise_for_status() # Lanza un error si la solicitud falla
        
        latest_version = response.json()['info']['version']
        
        if latest_version != current_version:
            print(f"[ALERTA] ¡Actualización disponible para {package_name}!")
            print(f"  - Versión actual: {current_version}")
            print(f"  - Última versión: {latest_version}")
        else:
            print(f"[INFO] {package_name} está actualizado.")
            
    except requests.exceptions.HTTPError:
        print(f"[ERROR] No se pudo encontrar el paquete: {package_name}")
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error de red: {e}")
    except KeyError:
        print("[ERROR] No se pudo parsear la respuesta de la API.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PatchTrack: Verifica la versión de un paquete de PyPI.")
    parser.add_argument("package", help="Nombre del paquete (ej: requests)")
    parser.add_argument("version", help="Versión instalada actualmente (ej: 2.28.0)")
    args = parser.parse_args()
    
    check_package_version(args.package, args.version)
