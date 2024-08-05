import meshtastic
import meshtastic.tcp_interface

# Define the Meshtastic device IP address and port
host = '192.168.1.87'
port = 4403  # Default port for Meshtastic TCP interface

# Connect to the Meshtastic device over TCP
interface = meshtastic.tcp_interface.TCPInterface(host, port)

def dump_info():
    try:
        # Retrieve the local node information
        node_info = interface.localNode
        
        # Print the entire node object to see its structure
        print("Node Information:")
        print(node_info)  # This will show the default string representation of the Node object
        
        # Alternatively, if you want to print the raw attributes:
        print("\nRaw Node Attributes:")
        for attr in dir(node_info):
            if not attr.startswith('__'):  # Skip private attributes
                print(f"{attr}: {getattr(node_info, attr)}")
        
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

