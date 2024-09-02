import meshtastic
import meshtastic.serial_interface
from pubsub import pub
import time
import argparse

def on_receive(packet, interface):
    """Callback function for when a message is received"""
    print(f"Received: {packet}")
    # https://www.perplexity.ai/search/write-a-listen-and-reply-pytho-Yx3JIT0tTFC4n_lHCqir0g
    if 'decoded' in packet and 'text' in packet['decoded']:
        text = packet['decoded']['text']
        print(f"Message: {text}")
        
        # Generate a reply
        reply = f"Received your message: {text}"
        
        # Send the reply
        interface.sendText(reply)
        print(f"Sent reply: {reply}")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Meshtastic message listener and replier")
    parser.add_argument('--port', type=str, help='Serial port to use')
    args = parser.parse_args()

    # Connect to the Meshtastic device
    try:
        if args.port:
            interface = meshtastic.serial_interface.SerialInterface(devPath=args.port)
            print(f"Connected to Meshtastic device on port {args.port}")
        else:
            interface = meshtastic.serial_interface.SerialInterface()
            print("Connected to Meshtastic device on default port")
    except Exception as e:
        print(f"Error connecting to Meshtastic device: {e}")
        print("Make sure your device is connected and the correct port is being used.")
        return

    # Subscribe to the receive message event
    pub.subscribe(on_receive, "meshtastic.receive.text")
    
    print("Listening for messages. Press Ctrl+C to exit.")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        # Close the interface when done
        interface.close()

if __name__ == "__main__":
    main()