import socket
import subprocess
import argparse
from scapy.all import ARP, Ether, srp
import networkx as nx
import matplotlib.pyplot as plt

def get_hostname(ip, verbose=False):
    try:
        if verbose:
            print(f"Resolving hostname for IP: {ip}")
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return None

def get_os_info(ip, verbose=False):
    try:
        command = f"ping -n 1 -a {ip}"
        if verbose:
            print(f"Executing command: {command}")
        output = subprocess.check_output(command, shell=True).decode('utf-8')
        if "TTL=128" in output:
            return "Likely Windows"
        elif "TTL=64" in output:
            return "Likely Linux/Unix"
        else:
            return "Unknown"
    except subprocess.CalledProcessError:
        return "Unable to determine"

def scan_network(ip_range, verbose=False):
    if verbose:
        print(f"Scanning network range: {ip_range}")
    
    # Create an ARP request packet
    arp_request = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp_request

    # Send the packet and receive the response
    result = srp(packet, timeout=2, verbose=0)[0]

    # Parse the response
    devices = []
    for sent, received in result:
        ip = received.psrc
        mac = received.hwsrc
        hostname = get_hostname(ip, verbose)
        os_info = get_os_info(ip, verbose)
        devices.append({'ip': ip, 'mac': mac, 'hostname': hostname, 'os': os_info})

    return devices

def create_network_map(devices):
    G = nx.Graph()

    for device in devices:
        node_label = f"{device['hostname'] or 'N/A'}\n{device['ip']}\n{device['os']}"
        G.add_node(device['ip'], label=node_label)

    # For simplicity, connect all devices to a central hub (e.g., router)
    central_hub = "Router"
    G.add_node(central_hub, label=central_hub)
    for device in devices:
        G.add_edge(central_hub, device['ip'])

    pos = nx.spring_layout(G)
    labels = nx.get_node_attributes(G, 'label')
    nx.draw(G, pos, with_labels=True, labels=labels, node_size=3000, node_color='skyblue', font_size=10, font_weight='bold')
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network Scanner and Mapper")
    parser.add_argument("--v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    verbose = args.v

    # Define the IP range to scan
    ip_range = "192.168.1.1/24"  # Adjust this to match your network
    
    # Scan the network
    devices = scan_network(ip_range, verbose)
    
    # Print the results
    print("Available devices in the network:")
    print("IP" + " "*18+"MAC" + " "*20 + "Hostname" + " "*20 + "OS")
    for device in devices:
        print("{:16}    {:18}    {:20}    {}".format(device['ip'], device['mac'], device['hostname'] or 'N/A', device['os'] or 'N/A'))
    
    # Create network map
    create_network_map(devices)
