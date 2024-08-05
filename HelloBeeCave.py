import meshtastic
import meshtastic.tcp_interface
from pubsub import pub
import time
from datetime import datetime

# Define the Meshtastic device IP address and port
host = '192.168.1.87'
port = 4403  # Default port for Meshtastic TCP interface

# Function to connect to the Meshtastic device
def connect_to_device():
    return meshtastic.tcp_interface.TCPInterface(host, port)

# Define the message and the channel index
message = "Steve Here: Hello, this is a message to channel 1!"
channel_index = 1
broadcast_id = "^all"  # Special ID to broadcast to all nodes

# Function to get channel name
def get_channel_name(interface, index):
    try:
        channels = interface.localNode.channels
        if index < len(channels):
            return channels[index].settings.name
        else:
            return f"Channel {index}"
    except Exception as e:
        print(f"Error getting channel name for index {index}: {e}")
        return f"Channel {index}"

# Function to handle the response
def onReceive(packet, interface):
    from_id = packet.get('fromId', 'Unknown')
    to_id = packet.get('toId', 'Unknown')
    portnum = packet.get('decoded', {}).get('portnum', 'Unknown')
    channel_index = packet.get('channel', None)
    
    channel_name = get_channel_name(interface, channel_index) if channel_index is not None else "Default Channel"

    if portnum == 'POSITION_APP':
        print(f"Node {from_id} sent position update to {to_id} on {channel_name}")
    elif portnum == 'TELEMETRY_APP':
        print(f"Node {from_id} sent telemetry update to {to_id} on {channel_name}")
    elif portnum == 'TEXT_MESSAGE_APP':
        text = packet.get('decoded', {}).get('text', 'Unknown')
        print(f"Node {from_id} sent message to {to_id} on {channel_name}: {text}")
    else:
        print(f"Node {from_id} sent {portnum} data to {to_id} on {channel_name}")

# Subscribe to the receive event
pub.subscribe(onReceive, "meshtastic.receive")

# Function to send the message
def send_message(interface):
    try:
        interface.sendText(message, destinationId=broadcast_id, channelIndex=channel_index)
        channel_name = get_channel_name(interface, channel_index)
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Message sent to all on {channel_name}: {message}")
        print(f"Next message will be sent in 30 minutes.")
    except Exception as e:
        print(f"Error sending message: {e}")
        return False
    return True

# Main loop
interface = connect_to_device()
try:
    while True:
        if not send_message(interface):
            print("Reconnecting...")
            interface.close()
            interface = connect_to_device()  # Re-establish connection
        time.sleep(1800)  # Sleep for 30 minutes (1800 seconds)
except KeyboardInterrupt:
    print("\nScript terminated by user.")
finally:
    # Close the interface
    interface.close()
    print("Interface closed.")

