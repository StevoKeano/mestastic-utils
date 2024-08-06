import socket
import subprocess
from scapy.all import ARP, Ether, srp

def get_hostname(ip):
    try:
        return socket.gethostbyaddr(ip)[0]
    except socket.herror:
        return None

def get_os_info(ip):
    try:
        output = subprocess.check_output(f"ping -n 1 -a {ip}", shell=True).decode('utf-8')
        if "TTL=128" in output:
            return "Likely Windows"
        elif "TTL=64" in output:
            return "Likely Linux/Unix"
        else:
            return "Unknown"
    except subprocess.CalledProcessError:
        return "Unable to determine"

def scan_network(ip_range):
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
        hostname = get_hostname(ip)
        os_info = get_os_info(ip)
        devices.append({'ip': ip, 'mac': mac, 'hostname': hostname, 'os': os_info})

    return devices

if __name__ == "__main__":
    # Define the IP range to scan
    ip_range = "192.168.1.1/24"  # Adjust this to match your network
    
    # Scan the network
    devices = scan_network(ip_range)
    
    # Print the results
    print("Available devices in the network:")
    print("IP" + " "*18+"MAC" + " "*20 + "Hostname" + " "*20 + "OS")
    for device in devices:
        print("{:16}    {:18}    {:20}    {}".format(device['ip'], device['mac'], device['hostname'] or 'N/A', device['os'] or 'N/A'))
