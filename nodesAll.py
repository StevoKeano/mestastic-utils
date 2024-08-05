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
            latitude = node.get('position', {}).get('latitude', 'N/A')
            longitude = node.get('position', {}).get('longitude', 'N/A')
            altitude = node.get('position', {}).get('altitude', 'N/A')
            last_heard = node.get('lastHeard', 'N/A')
            battery_level = node.get('deviceMetrics', {}).get('batteryLevel', 'N/A')
            voltage = node.get('deviceMetrics', {}).get('voltage', 'N/A')
            uptime_seconds = node.get('deviceMetrics', {}).get('uptimeSeconds', 'N/A')

            # Append the row to the table data
            table_data.append([
                node_id,
                long_name,
                short_name,
                latitude,
                longitude,
                altitude,
                last_heard,
                battery_level,
                voltage,
                uptime_seconds
            ])
        
        # Print the table
        headers = [
            "Node ID", "Long Name", "Short Name", 
            "Latitude", "Longitude", "Altitude", 
            "Last Heard", "Battery Level", "Voltage", "Uptime (s)"
        ]
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

