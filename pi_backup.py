#!/usr/bin/env python3

import os
import subprocess
import datetime
import shutil
import sys

# Configuration
pi_device = "/dev/mmcblk0"  # Typical device for Raspberry Pi's SD card
mount_point = "/media/stevo/sga3"  # Mount point for the external drive
external_device = "/dev/sda3"  # Device identifier for the external drive
block_size = 512  # 512 bytes block size (standard block size for dd)
bbsIP = "192.168.1.95"

def remount_drive():
    # Check if the drive is already mounted
    if is_mounted(mount_point):
        print(f"{mount_point} is already mounted.")
        send_meshtastic_message("The backup is complete. The BBS is back online.")
    else:
        print(f"Remounting {mount_point}...")
        try:
            subprocess.run(["sudo", "mount", external_device, mount_point], check=True)
            print(f"Remounted {external_device} at {mount_point}")
            send_meshtastic_message("The backup is complete. The BBS is back online.")
        except subprocess.CalledProcessError as e:
            print(f"Error remounting drive: {e}")
            sys.exit(1)


def get_used_space():
    # Use du to calculate the used space in the root filesystem, excluding /proc and other virtual filesystems
    try:
        du_output = subprocess.check_output(
            ["sudo", "du", "-sx", "--exclude=/proc", "--exclude=/dev", "--exclude=/sys", "--block-size=1", "/"]
        ).decode().split("\t")[0]
        used_bytes = int(du_output)
        return used_bytes
    except subprocess.CalledProcessError as e:
        print(f"Error calculating used space: {e}")
        sys.exit(1)

def is_mounted(mount_point):
    return mount_point in subprocess.check_output(["mount"]).decode()

def mount_drive():
    # Create the mount point if it doesn't exist
    if not os.path.exists(mount_point):
        try:
            subprocess.run(["sudo", "mkdir", "-p", mount_point], check=True)
            print(f"Created mount point {mount_point}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating mount point: {e}")
            sys.exit(1)
    
    try:
        subprocess.run(["sudo", "mount", external_device, mount_point], check=True)
        print(f"Mounted {external_device} at {mount_point}")
    except subprocess.CalledProcessError as e:
        print(f"Error mounting drive: {e}")
        sys.exit(1)

def send_meshtastic_message(message):
    try:
        # Specify the host and port if using TCP
        subprocess.run(["/home/stevo/TC2-BBS-mesh/venv/bin/meshtastic", "--host", bbsIP, "--sendtext", message], check=True)
        #subprocess.run(["meshtastic", "--host", bbsIP, "--sendtext", message], check=True)
        print("Meshtastic message sent: ", message)
    except subprocess.CalledProcessError as e:
        print(f"Error sending Meshtastic message: {e}")


def create_backup():
    # Send a message before starting the backup
    send_meshtastic_message("The BBS is currently offline for backup. Please check back later.")
    # Get current date and time
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # Calculate backup size
    used_space = get_used_space()
    backup_size = int(used_space * 1.1)  # Add 10% to the used space
    block_count = backup_size // block_size
    
    # Create backup filename
    backup_file = f"{mount_point}/pi_backup_{timestamp}.img"
    
    # Create the backup using dd
    dd_command = f"sudo dd if={pi_device} of={backup_file} bs={block_size} count={block_count} status=progress"
    
    try:
        subprocess.run(dd_command, shell=True, check=True)
        print(f"Backup created successfully: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating backup: {e}")

if __name__ == "__main__":
    # Ensure the drive is mounted
    if not is_mounted(mount_point):
        print(f"{mount_point} is not mounted. Attempting to mount...")
        mount_drive()
    
    # Check if there's enough space on the external drive
    used_space = get_used_space()
    backup_size = int(used_space * 1.1)
    if shutil.disk_usage(mount_point).free < backup_size:
        print("Not enough space on the external drive for the backup.")
        sys.exit(1)
    
    create_backup()
    remount_drive()
   
