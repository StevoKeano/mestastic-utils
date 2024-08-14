import asyncio
import subprocess
from bleak import BleakScanner, BleakClient

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

async def connect_device(address):
    print(f"Attempting to connect to device: {address}")
    async with BleakClient(address) as client:
        if client.is_connected:
            print("Successfully connected to the BLE device.")
            return True
        else:
            print("Failed to connect to the BLE device.")
            return False

def run_meshtastic_info(address):
    try:
        print(f"Running 'meshtastic --info --ble {address}'...")
        result = subprocess.run(
            ["meshtastic", "--info", "--ble", address],
            capture_output=True,
            text=True
        )
        print("Meshtastic Info:\n", result.stdout)
        if result.stderr:
            print("Meshtastic Errors:\n", result.stderr)
    except Exception as e:
        print(f"Failed to run Meshtastic command: {e}")

async def main():
    devices = await scan_bluetooth_devices()
    display_devices(devices)
    
    if not devices:
        return  # Exit if no devices found
    
    selected_device = get_user_selection(devices)
    print(f"Selected device: Address: {selected_device.address}, Name: {selected_device.name or 'Unknown'}")
    
    connected = await connect_device(selected_device.address)
    
    if connected:
        print("Successfully connected to the BLE device.")
        run_meshtastic_info(selected_device.address)
    else:
        print("Failed to connect to the BLE device. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())
