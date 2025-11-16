import subprocess
import platform
import os

def check_bios_features():
    """
    Verificar características de seguridad de la BIOS/UEFI.
    """
    system = platform.system()
    print(f"[INFO] Sistema operativo detectado: {system}")
    print("--- SmartBios: Verificación de Características ---")

    if system == "Linux":
        print("Verificando SecureBoot (Linux)...")
        
        try:
          
            result = subprocess.run(['cat', '/sys/firmware/efi/fw_platform_size'], capture_output=True, text=True, check=True)
            print(f"  - Modo UEFI detectado (Plataforma de {result.stdout.strip()} bits).")
            
            
            sb_result = subprocess.run(['mokutil', '--sb-state'], capture_output=True, text=True)
            if sb_result.returncode == 0:
                print(f"  - Estado de SecureBoot: {sb_result.stdout.strip()}")
            else:
                print("  - No se pudo determinar el estado de SecureBoot (¿mokutil no instalado?)")
        except FileNotFoundError:
            print("  - Sistema no parece estar en modo UEFI (o no es Linux).")
        except Exception as e:
            print(f"  - Error al verificar (es posible que se necesiten permisos de root): {e}")

    elif system == "Windows":
        print("Verificando SecureBoot (Windows con PowerShell)...")
    
        try:
     
            result = subprocess.run(
                ["powershell", "Confirm-SecureBootUEFI"], 
                capture_output=True, text=True, shell=True
            )
            if "True" in result.stdout:
                print("  - Estado de SecureBoot: Habilitado")
            elif "False" in result.stdout:
                print("  - Estado de SecureBoot: Deshabilitado")
            else:
                print("  - No se pudo determinar el estado (o el comando falló).")
                print(f"    {result.stderr}")
                
        except FileNotFoundError:
            print("  - PowerShell no encontrado.")
        except Exception as e:
            print(f"  - Error al ejecutar PowerShell: {e}")
    else:
        print(f"  - Verificación no implementada para {system}.")

    print("-------------------------------------------------")

if __name__ == "__main__":
    # Requiere permisos de administrador en muchos casos
    if platform.system() == "Windows" and not os.access("C:\\Windows\\System32\\config", os.R_OK):
        print("[ADVERTENCIA] Este script puede requerir permisos de Administrador para funcionar.")
    elif platform.system() == "Linux" and os.geteuid() != 0:
         print("[ADVERTENCIA] Este script puede requerir permisos de 'root' para funcionar.")
         
    check_bios_features()
