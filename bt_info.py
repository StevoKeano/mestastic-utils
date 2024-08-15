import asyncio
from bleak import BleakScanner
import subprocess
import time

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

def run_meshtastic_info(address):
    for attempt in range(3):  # Retry up to 3 times
        try:
            print(f"Attempt {attempt + 1}: Running 'meshtastic --info --ble {address}'")
            result = subprocess.run(
                ["meshtastic", "--info", "--ble", address],
                text=True,
                check=True,
                stdout=subprocess.PIPE,  # Capture standard output
                stderr=subprocess.PIPE   # Capture standard error
            )
            print("Meshtastic Info:")
            print(result.stdout)
            return True
        except subprocess.CalledProcessError:
            # Suppress detailed error output during the first attempt
            print("Error retrieving Meshtastic info. The device might not be properly paired.")
            if attempt < 2:
                input("Please complete the pairing process on your computer if prompted, then press Enter to retry...")
        except FileNotFoundError:
            print("Meshtastic CLI not found. Make sure it's installed and in your PATH.")
            return False

        time.sleep(5)  # Wait a bit before retrying

    print("Failed to retrieve Meshtastic info after multiple attempts.")
    return False

async def main():
    devices = await scan_bluetooth_devices()
    display_devices(devices)
    
    if not devices:
        return  # Exit if no devices found
    
    selected_device = get_user_selection(devices)
    print(f"Selected device: Address: {selected_device.address}, Name: {selected_device.name or 'Unknown'}")
    
    input("Please ensure the device is paired on your computer. Press Enter to continue...")
    time.sleep(2)  # Pause briefly to allow pairing process to complete

    success = run_meshtastic_info(selected_device.address)
    
    if success:
        print("Successfully retrieved Meshtastic info.")
    else:
        print("Failed to retrieve Meshtastic info. Please try again later.")

if __name__ == "__main__":
    asyncio.run(main())