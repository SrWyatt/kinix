# golem.py
import argparse
import sys
try:
    from scapy.all import ARP, Ether, srp
except ImportError:
    print("[ERROR] Scapy no está instalado. Ejecuta 'pip install scapy'.")
    sys.exit(1)

def discover_hosts(network_range):
    """
    Descubre hosts en la red local usando un escaneo ARP.
    Ejemplo de network_range: "192.168.1.0/24"
    """
    print(f"[INFO] Escaneando la red {network_range} con ARP...")
    
    # Crear el paquete ARP request
    arp_request = ARP(pdst=network_range)
    # Crear el frame de Ethernet (broadcast)
    broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
    
    packet = broadcast / arp_request
    
    try:
        # Enviar el paquete y recibir respuestas
        # srp = Send and Receive Packet
        result = srp(packet, timeout=3, verbose=0)[0]
        
        clients = []
        for sent, received in result:
            clients.append({'ip': received.psrc, 'mac': received.hwsrc})
            
        print("--- Golem: Hosts Detectados ---")
        print("IP" + " "*18 + "MAC")
        print("-----------------------------------")
        if not clients:
            print("No se encontraron hosts activos.")
        
        for client in clients:
            print(f"{client['ip']:<20} {client['mac']}")
        print("-----------------------------------")
        
    except Exception as e:
        print(f"[ERROR] Ocurrió un error (¿ejecutaste como administrador/root?): {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Golem: Descubridor de hosts en la red local (ARP Scan).")
    parser.add_argument("network", help="El rango de red a escanear (ej: 192.168.1.0/24)")
    args = parser.parse_args()
    
    # Scapy a menudo requiere privilegios de administrador para enviar paquetes
    import os
    if os.name == 'posix' and os.geteuid() != 0:
        print("[ADVERTENCIA] Este script funciona mejor si se ejecuta como 'root' (sudo).")
    elif os.name == 'nt':
        # En Windows, es más difícil verificar si es admin desde CLI
        print("[ADVERTENCIA] Asegúrate de ejecutar este script en un terminal 'Como Administrador'.")

    discover_hosts(args.network)
