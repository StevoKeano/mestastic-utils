import meshtastic
import meshtastic.tcp_interface
from pubsub import pub
import time
from datetime import datetime
from tabulate import tabulate

# Define the Meshtastic device IP address and port
host = '192.168.1.87'
port = 4403  # Default port for Meshtastic TCP interface

# Connect to the Meshtastic device over TCP
interface = meshtastic.tcp_interface.TCPInterface(host, port)

# Dictionary to store node information
nodes = {}

def snr_to_hopcount(snr):
    if snr is None:
        return 'N/A'
    elif snr > 6:
        return 1
    elif snr > 4:
        return 2
    elif snr > 2:
        return 3
    else:
        return 4

def initialize_nodes():
    for node_id, node in interface.nodes.items():
        snr = node.get('snr')
        nodes[node_id] = {
            'name': node.get('user', {}).get('longName', node_id),
            'hop_count': snr_to_hopcount(snr),
            'last_seen': datetime.fromtimestamp(node.get('lastHeard', 0))
        }

def update_node_info(packet):
    from_id = packet.get('fromId', 'Unknown')
    snr = packet.get('rxSnr')
    
    if from_id != 'Unknown':
        if from_id not in nodes:
            nodes[from_id] = {'name': from_id, 'hop_count': snr_to_hopcount(snr), 'last_seen': datetime.now()}
        else:
            nodes[from_id]['hop_count'] = snr_to_hopcount(snr)
            nodes[from_id]['last_seen'] = datetime.now()

def onReceive(packet, interface):
    update_node_info(packet)

# Subscribe to the receive event
pub.subscribe(onReceive, "meshtastic.receive")

def display_node_table():
    current_time = datetime.now()
    table_data = []
    
    for node_id, info in nodes.items():
        minutes_since_last_seen = (current_time - info['last_seen']).total_seconds()
        hours, remainder = divmod(minutes_since_last_seen, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_since_last_seen = f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        
        table_data.append([
            info['name'],
            info['hop_count'],
            time_since_last_seen
        ])
    
    # Sort the table data by time since last seen (in seconds)
    table_data.sort(key=lambda x: (current_time - info['last_seen']).total_seconds())

    headers = ["Node Name", "Hop Count", "Time Since Last Seen (hh:mm:ss)"]
    print(f"\nNumber of nodes: {len(nodes)}")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    print(f"Last updated: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")

# Main loop
try:
    print("Initializing node list...")
    initialize_nodes()
    print("Monitoring Meshtastic network. Press Ctrl+C to exit.")
    while True:
        display_node_table()
        time.sleep(60)  # Update every minute
except KeyboardInterrupt:
    print("\nScript terminated by user.")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    # Close the interface
    interface.close()
    print("Interface closed.")

