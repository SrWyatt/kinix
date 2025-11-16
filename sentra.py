# sentra.py
import requests
import hashlib
import sys
import argparse
import getpass
import os
import platform

# Importar y Inicializar Colorama
try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    print("Por favor instala 'colorama': pip install colorama")
    # Definir colores 'dummy' si colorama no está
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()

# --- Definición de Colores ---
C_RED = Fore.RED + Style.BRIGHT
C_GREEN = Fore.GREEN + Style.BRIGHT
C_YELLOW = Fore.YELLOW + Style.BRIGHT
C_CYAN = Fore.CYAN + Style.BRIGHT
C_WHITE = Fore.WHITE + Style.BRIGHT
C_RESET = Style.RESET_ALL

# --- Funciones de Gráficos ---

def create_risk_bar(count):
    """
    Crea una barra de riesgo y un nivel basado en el conteo de brechas.
    """
    if count == 0:
        color = C_GREEN
        bar = "■" * 10
        level = "NULO"
        message = "¡Contraseña segura! No se encontró en brechas conocidas."
    elif count < 100:
        color = C_YELLOW
        bar = "■" * 5 + "—" * 5
        level = "MEDIO"
        message = f"Ha sido vista {C_WHITE}{count}{color} veces. Es riesgosa."
    else: # count >= 100
        color = C_RED
        bar = "■" * 10
        level = "CRÍTICO"
        message = f"Ha sido vista {C_WHITE}{count}{color} veces. ¡NO USAR!"

    print(f"  Nivel de Riesgo: {color}[{bar}]{C_RESET}")
    print(f"  Evaluación:      {color}{message}{C_RESET}")

# --- Función Principal de Verificación ---

def check_pwned_password(password):
    """
    Verifica una contraseña.
    """
    count = 0
    try:
        # 1. Hashear la contraseña con SHA-1
        sha1_password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
        prefix, suffix = sha1_password[:5], sha1_password[5:]
        
        # 2. Enviar solo el prefijo a la API
        print(f"\n{C_CYAN}[INFO] Consultando base de datos de brechas (K-Anonymity)...{C_RESET}")
        response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
        response.raise_for_status()
        
        # 3. Comprobar el sufijo en la respuesta
        hashes = (line.split(':') for line in response.text.splitlines())
        for h, c in hashes:
            if h == suffix:
                count = int(c)
                break # Encontrado, salimos del bucle
        
        # 4. Mostrar resultados (fuera del bucle)
        print(f"{C_GREEN}==================================================={C_RESET}")
        print(f"{C_WHITE}--- Evaluación de la Contraseña (Sentra) ---{C_RESET}")
        
        if count > 0:
            print(f"\n{C_RED}[ALERTA] ¡Contraseña expuesta en brechas de datos!{C_RESET}")
            create_risk_bar(count)
        else:
            print(f"\n{C_GREEN}[INFO] ¡Contraseña segura!{C_RESET}")
            create_risk_bar(0)
            
        print(f"{C_GREEN}==================================================={C_RESET}")


    except requests.exceptions.RequestException as e:
        print(f"\n{C_RED}[ERROR] Error de red. No se pudo contactar el servicio de verificación.{C_RESET}")
    except Exception as e:
        print(f"\n{C_RED}[ERROR] Ocurrió un error inesperado: {e}{C_RESET}")

# --- Bloque de Ejecución ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sentra: Verifica si una contraseña ha sido comprometida.")
    args = parser.parse_args()
    
    # Limpiar pantalla
    os.system('cls' if platform.system() == "Windows" else 'clear')
    
    print(f"{C_CYAN}==================================================={C_RESET}")
    print(f"{C_WHITE}--- KINIX Security: Sentra ---{C_RESET}")
    print(f"{C_CYAN}==================================================={C_RESET}\n")
    
    print("Por favor, introduce la contraseña que deseas verificar.")
    print(f"{C_YELLOW}(No se mostrará en pantalla por seguridad){C_RESET}")
    
    try:
        password = getpass.getpass("Contraseña: ")
    except KeyboardInterrupt:
        print("\n\nOperación cancelada.")
        sys.exit(0)
        
    if not password:
        print(f"\n{C_RED}[ERROR] No se introdujo ninguna contraseña.{C_RESET}")
        sys.exit(1)
        
    check_pwned_password(password)
