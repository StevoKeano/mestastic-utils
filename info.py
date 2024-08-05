import meshtastic
import meshtastic.tcp_interface

# Define the Meshtastic device IP address and port
host = '192.168.1.87'
port = 4403  # Default port for Meshtastic TCP interface

# Connect to the Meshtastic device over TCP
interface = meshtastic.tcp_interface.TCPInterface(host, port)

def dump_info():
    try:
        # Retrieve the list of nodes
        nodes = interface.nodes
        
        # Print node information
        print(f"Node Information:{nodes.items()}")
        for node_id, node in nodes.items():
            print(f"Node ID: {node_id}")
            print(f"  Long Name: {node.get('user', {}).get('longName', 'N/A')}")
            print(f"  Short Name: {node.get('user', {}).get('shortName', 'N/A')}")
            print(f"  Last Heard: {node.get('lastHeard', 'N/A')}")
            print(f"  Channels: {node.get('channels', 'N/A')}")
            print(f"  Firmware Version: {node.get('firmwareVersion', 'N/A')}")
            print(f"  Power Level: {node.get('powerLevel', 'N/A')}")
            print()  # Blank line for readability
        
    except Exception as e:
        print(f"An error occurred: {e}")

# Query the radio for information and print it out
try:
    print("Querying Meshtastic device for information...")
    dump_info()
except Exception as e:
    print(f"An error occurred while querying: {e}")
finally:
    # Close the interface
    interface.close()
    print("Interface closed.")


