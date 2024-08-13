import asyncio
from bleak import BleakScanner
import subprocess
import sys

async def scan_bluetooth_devices():
    print("Scanning for Bluetooth devices...")
    devices = await BleakScanner.discover()
    return devices

def display_devices(devices):
    if not devices:
        print("No Bluetooth devices found.")
        return

    print(f"Found {len(devices)} devices:")
    for i, device in enumerate(devices, 1):
        print(f"{i}. Address: {device.address}, Name: {device.name or 'Unknown'}")

def get_user_selection(devices):
    while True:
        try:
            selection = int(input("Enter the number of the device to connect to: "))
            if 1 <= selection <= len(devices):
                return devices[selection - 1]
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")

def run_meshtastic_info(device_address):
    try:
        result = subprocess.run(["meshtastic", "--info", "--host", device_address], 
                                capture_output=True, text=True, check=True)
        print("Meshtastic Info:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running Meshtastic command: {e}")
        print(f"Error output: {e.stderr}")
    except FileNotFoundError:
        print("Meshtastic CLI not found. Make sure it's installed and in your PATH.")

async def main():
    devices = await scan_bluetooth_devices()
    display_devices(devices)
    
    if not devices:
        sys.exit(1)
    
    selected_device = get_user_selection(devices)
    print(f"Selected device: Address: {selected_device.address}, Name: {selected_device.name or 'Unknown'}")
    
    run_meshtastic_info(selected_device.address)

if __name__ == "__main__":
    asyncio.run(main())