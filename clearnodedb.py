import meshtastic
import meshtastic.tcp_interface
import meshtastic.serial_interface
import serial.tools.list_ports
import ipaddress
import time
import subprocess

def get_highest_com_port():
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        return None
    return sorted(ports, key=lambda x: int(x.device[3:]))[-1].device

def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def connect_and_clear_nodedb():
    while True:
        choice = input("Enter 'C' for COM port or 'I' for IP address: ").upper()
        
        if choice == 'C':
            com_port = get_highest_com_port()
            if not com_port:
                print("No COM ports found.")
                continue
            print(f"Connecting to highest COM port: {com_port}")
            try:
                interface = meshtastic.serial_interface.SerialInterface(com_port)
            except Exception as e:
                print(f"Failed to connect to {com_port}: {str(e)}")
                continue
        elif choice == 'I':
            ip_address = input("Enter the IP address of the radio: ")
            if not is_valid_ip(ip_address):
                print("Invalid IP address.")
                continue
            try:
                interface = meshtastic.tcp_interface.TCPInterface(ip_address)
            except Exception as e:
                print(f"Failed to connect to {ip_address}: {str(e)}")
                continue
        else:
            print("Invalid choice. Please enter 'C' or 'I'.")
            continue

        print(f"Connecting to IP: {ip_address}")

        try:
            # Connect to the radio
            interface = meshtastic.tcp_interface.TCPInterface(ip_address)
            
            # Get initial node count
            initial_nodes = interface.nodes
            print(f"NodeDB initially contains {len(initial_nodes)} nodes.")

            # Send clearNodeDB command
            print("Sending clearNodeDB command...")
            subprocess.run(["meshtastic", "--host", ip_address, "--reset-nodedb"], check=True)
            print("NodeDB reset command sent successfully. Sleep 25 seconds")

            # Wait for changes to take effect
            print("Waiting for changes to take effect...")
            time.sleep(25)

            # Get REMAINING node count
            initial_nodes = interface.nodes
            print(f"NodeDB now contains {len(initial_nodes)} nodes.")

        except subprocess.CalledProcessError as e:
            print(f"An error occurred: {e.stderr}")
        finally:
            try:
                interface.close()
            except Exception as e:
                print(f"Error closing interface: {str(e)}")

        break

if __name__ == "__main__":
    connect_and_clear_nodedb()
