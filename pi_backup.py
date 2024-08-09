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
block_size = 4 * 1024 * 1024  # 4MB block size

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

def create_backup():
    # Get current date and time
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    # Create backup filename
    backup_file = f"{mount_point}/pi_backup_{timestamp}.img"
    
    # Create the backup using dd
    dd_command = f"sudo dd if={pi_device} of={backup_file} bs={block_size} status=progress"
    
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
    total_sd_size = shutil.disk_usage(pi_device).total
    if shutil.disk_usage(mount_point).free < total_sd_size:
        print("Not enough space on the external drive for the backup.")
        sys.exit(1)
    
    create_backup()
