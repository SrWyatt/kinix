import psutil
import datetime
import platform
import subprocess
import re
import os


try:
    import colorama
    from colorama import Fore, Style
    colorama.init(autoreset=True)
except ImportError:
    print("Por favor instala 'colorama': pip install colorama")
   
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()


C_RED = Fore.RED + Style.BRIGHT
C_GREEN = Fore.GREEN + Style.BRIGHT
C_YELLOW = Fore.YELLOW + Style.BRIGHT
C_CYAN = Fore.CYAN + Style.BRIGHT
C_WHITE = Fore.WHITE + Style.BRIGHT
C_RESET = Style.RESET_ALL


def get_color_by_percent(percent):
    """Devuelve un color basado en el porcentaje."""
    if percent > 85:
        return C_RED
    if percent > 65:
        return C_YELLOW
    return C_GREEN

def create_bar(percent, length=20):
    """Crea una barra de progreso gráfica en texto."""
    color = get_color_by_percent(percent)
    filled_len = int(length * percent / 100)
    bar = '■' * filled_len + '—' * (length - filled_len)
    return f"{color}[{bar}]{C_RESET} {percent:.1f}%"

def get_wifi_info():
    """Obtiene el SSID y la fuerza de la señal de la red Wi-Fi."""
    system = platform.system()
    ssid = "No detectado"
    signal_percent = 0

    try:
        if system == "Windows":
            cmd = "netsh wlan show interfaces"
            output = subprocess.check_output(cmd, shell=True, text=True, encoding='utf-8', errors='ignore')
            
            ssid_match = re.search(r"SSID\s+:\s(.*)", output)
            signal_match = re.search(r"Señal\s+:\s(\d+)%", output)
            
            if ssid_match and ssid_match.group(1).strip():
                ssid = ssid_match.group(1).strip()
            if signal_match:
                signal_percent = int(signal_match.group(1))

        elif system == "Linux":
            cmd = "iwconfig"
            output = subprocess.check_output(cmd, shell=True, text=True, encoding='utf-8', errors='ignore')
            
            ssid_match = re.search(r'ESSID:"(.*)"', output)
            signal_match = re.search(r"Signal level=(-?\d+)", output) # En dBm
            
            if ssid_match and ssid_match.group(1).strip():
                ssid = ssid_match.group(1).strip()
            if signal_match:
                dbm = int(signal_match.group(1))
              
                if dbm > -50: signal_percent = 100
                elif dbm > -60: signal_percent = 80
                elif dbm > -70: signal_percent = 60
                elif dbm > -80: signal_percent = 40
                else: signal_percent = 20
        else:
            ssid = "SO no compatible para Wi-Fi"

    except Exception:
        ssid = "N/A (¿Wi-Fi?)" 
        
    return ssid, signal_percent


def analyze_risks(metrics):
    """Analiza las métricas y devuelve una lista de riesgos."""
    risks = []
    
    # CPU
    if metrics['cpu'] > 95:
        risks.append(f"{C_RED}RIESGO CRÍTICO: Uso de CPU ({metrics['cpu']}%) al máximo. El sistema puede colapsar.")
    elif metrics['cpu'] > 80:
        risks.append(f"{C_YELLOW}ADVERTENCIA: Uso de CPU ({metrics['cpu']}%) muy alto. Rendimiento degradado.")
    
    # RAM
    if metrics['ram'] > 90:
        risks.append(f"{C_RED}RIESGO CRÍTICO: Memoria RAM ({metrics['ram']}%) casi agotada. Posibles fallos de aplicaciones.")
    elif metrics['ram'] > 80:
        risks.append(f"{C_YELLOW}ADVERTENCIA: Memoria RAM ({metrics['ram']}%) alta. Cierre aplicaciones innecesarias.")

    # DISCO
    if metrics['disk'] > 95:
        risks.append(f"{C_RED}RIESGO CRÍTICO: Espacio en disco ({metrics['disk']}%) casi lleno. Riesgo de corrupción de datos.")
    elif metrics['disk'] > 85:
        risks.append(f"{C_YELLOW}ADVERTENCIA: Espacio en disco ({metrics['disk']}%) bajo. Libere espacio pronto.")
        
    # SEÑAL
    if 0 < metrics['signal'] < 30:
        risks.append(f"{C_RED}RIESGO DE RED: Señal Wi-F ({metrics['signal']}%) críticamente baja. Conexión inestable.")
    elif 0 < metrics['signal'] < 50:
        risks.append(f"{C_YELLOW}ADVERTENCIA: Señal Wi-Fi ({metrics['signal']}%) débil. Considere acercarse al router.")

    if not risks:
        risks.append(f"{C_GREEN}INFO: No se detectaron riesgos inmediatos. El sistema opera dentro de los parámetros normales.")
        
    return risks

def main():
 
    os.system('cls' if platform.system() == "Windows" else 'clear')
    
    print(f"{C_CYAN}==========================================={C_RESET}")
    print(f"{C_WHITE}--- SysCare: Diagnóstico del Sistema (KINIX) ---{C_RESET}")
    print(f"{C_CYAN}==========================================={C_RESET}\n")
    metrics = {}
    print(f"{C_WHITE}Hardware y Almacenamiento:{C_RESET}")
    cpu_percent = psutil.cpu_percent(interval=1)
    metrics['cpu'] = cpu_percent
    print(f"  Uso de CPU: \t{create_bar(cpu_percent)}")
    memory = psutil.virtual_memory()
    metrics['ram'] = memory.percent
    print(f"  Uso de RAM: \t{create_bar(memory.percent)} (Total: {memory.total / (1024**3):.2f} GB)")

    disk = psutil.disk_usage('/')
    metrics['disk'] = disk.percent
    print(f"  Uso de Disco (/): {create_bar(disk.percent)} (Total: {disk.total / (1024**3):.2f} GB)")

    print(f"\n{C_WHITE}Conectividad de Red:{C_RESET}")
    
    ssid, signal = get_wifi_info()
    metrics['signal'] = signal
    print(f"  Red Wi-Fi: \t{C_CYAN}{ssid}{C_RESET}")
    print(f"  Señal Wi-Fi: \t{create_bar(signal)}")
    
    print(f"\n{C_WHITE}Información General:{C_RESET}")
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    print(f"  Sistema iniciado: {C_GREEN}{boot_time}{C_RESET}")

    print(f"\n{C_RED}===================================={C_RESET}")
    print(f"{C_WHITE}--- Riesgos Encontrados ---{C_RESET}")
    print(f"{C_RED}===================================={C_RESET}\n")
    
    risks = analyze_risks(metrics)
    for risk in risks:
        print(f"  » {risk}")
    
    print("\n")

if __name__ == "__main__":
    main()
