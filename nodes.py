import meshtastic
import meshtastic.tcp_interface
from tabulate import tabulate

# Define the Meshtastic device IP address and port
host = '192.168.1.87'
port = 4403  # Default port for Meshtastic TCP interface

# Connect to the Meshtastic device over TCP
interface = meshtastic.tcp_interface.TCPInterface(host, port)

def dump_info():
    try:
        # Retrieve the list of nodes
        nodes = interface.nodes
        
        # Prepare data for tabulation
        table_data = []
        
        for node_id, node in nodes.items():
            # Extract relevant attributes
            long_name = node.get('user', {}).get('longName', 'N/A')
            short_name = node.get('user', {}).get('shortName', 'N/A')
            altitude = node.get('position', {}).get('altitude', 'N/A')
            last_heard = node.get('lastHeard', 'N/A')  # Keep for sorting
            battery_level = node.get('deviceMetrics', {}).get('batteryLevel', 'N/A')
            voltage = node.get('deviceMetrics', {}).get('voltage', 'N/A')
            uptime_seconds = node.get('deviceMetrics', {}).get('uptimeSeconds', 'N/A')

            # Append the row to the table data
            table_data.append([
                node_id,
                long_name,
                short_name,
                altitude,
                battery_level,
                voltage,
                uptime_seconds,
                last_heard  # Keep last_heard for sorting
            ])
        
        # Sort the table data by last_heard (the last column)
        # Convert last_heard to int for sorting, handle non-integer values
        table_data.sort(key=lambda x: int(x[-1]) if isinstance(x[-1], (int, float)) else float('inf'))  # Sort by last_heard
        
        # Print the table without last_heard
        headers = [
            "Node ID", "Long Name", "Short Name", 
            "Altitude", "Battery Level", 
            "Voltage", "Uptime (s)"
        ]
        # Remove last_heard from the table data for printing
        table_data = [row[:-1] for row in table_data]  # Exclude last_heard
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
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

