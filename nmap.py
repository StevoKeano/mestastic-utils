import socket
import subprocess
import argparse
from scapy.all import ARP, Ether, srp
import networkx as nx
import matplotlib.pyplot as plt

def get_hostname(ip, verbose=False):
    try:
        if verbose:
            print(f"[DEBUG] Resolving hostname for IP: {ip}")
        hostname = socket.gethostbyaddr(ip)[0]
        if verbose:
            print(f"[DEBUG] Hostname resolved: {hostname}")
        return hostname
    except socket.herror:
        if verbose:
            print(f"[DEBUG] Unable to resolve hostname for IP: {ip}")
        return None

def get_os_info(ip, verbose=False):
    try:
        command = f"ping -n 1 -t 500 -a {ip}"
        if verbose:
            print(f"[DEBUG] Executing command: {command}")
        output = subprocess.check_output(command, shell=True).decode('utf-8')
        if verbose:
            print(f"[DEBUG] Ping output: {output}")
        if "TTL=128" in output:
            return "Likely Windows"
        elif "TTL=64" in output:
            return "Likely Linux/Unix"
        else:
            return "Unknown"
    except subprocess.CalledProcessError:
        if verbose:
            print(f"[DEBUG] Error executing ping command for IP: {ip}")
        return "Unable to determine"

def scan_network(ip_range, verbose=False):
    if verbose:
        print(f"[DEBUG] Scanning network range: {ip_range}")
    
    # Create an ARP request packet
    arp_request = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp_request

    if verbose:
        print(f"[DEBUG] Sending ARP request: {packet.summary()}")

    # Send the packet and receive the response
    result = srp(packet, timeout=2, verbose=0)[0]

    if verbose:
        print(f"[DEBUG] Received {len(result)} responses")

    # Parse the response
    devices = []
    for sent, received in result:
        ip = received.psrc
        mac = received.hwsrc
        if verbose:
            print(f"[DEBUG] Processing device: IP={ip}, MAC={mac}")
        hostname = get_hostname(ip, verbose)
        os_info = get_os_info(ip, verbose)
        devices.append({'ip': ip, 'mac': mac, 'hostname': hostname, 'os': os_info})

    return devices

def create_network_map(devices):
    if verbose:
        print("[DEBUG] Creating network map")
    G = nx.Graph()

    for device in devices:
        node_label = f"{device['hostname'] or 'N/A'}\n{device['ip']}\n{device['os']}"
        G.add_node(device['ip'], label=node_label)
        if verbose:
            print(f"[DEBUG] Added node: {device['ip']}")

    # For simplicity, connect all devices to a central hub (e.g., router)
    central_hub = "Router"
    G.add_node(central_hub, label=central_hub)
    if verbose:
        print(f"[DEBUG] Added central hub: {central_hub}")
    for device in devices:
        G.add_edge(central_hub, device['ip'])
        if verbose:
            print(f"[DEBUG] Added edge: {central_hub} - {device['ip']}")

    if verbose:
        print("[DEBUG] Drawing network map")
    pos = nx.spring_layout(G)
    labels = nx.get_node_attributes(G, 'label')
    nx.draw(G, pos, with_labels=True, labels=labels, node_size=3000, node_color='skyblue', font_size=10, font_weight='bold')
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Network Scanner and Mapper")
    parser.add_argument("--v", action="store_true", help="Enable verbose output")
    args = parser.parse_args()

    verbose = args.v

    if verbose:
        print("[DEBUG] Verbose mode enabled")

    # Define the IP range to scan
    ip_range = "192.168.1.1/24"  # Adjust this to match your network
    if verbose:
        print(f"[DEBUG] IP range set to: {ip_range}")
    
    # Scan the network
    devices = scan_network(ip_range, verbose)
    
    # Print the results
    print("Available devices in the network:")
    print("IP" + " "*18+"MAC" + " "*20 + "Hostname" + " "*20 + "OS")
    for device in devices:
        print("{:16}    {:18}    {:20}    {}".format(device['ip'], device['mac'], device['hostname'] or 'N/A', device['os'] or 'N/A'))
    
    # Create network map
    create_network_map(devices)


