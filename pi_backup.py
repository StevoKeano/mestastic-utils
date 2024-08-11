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

# List of services to stop before backup
services_to_stop = [
    "avahi-daemon.service",
    "bluetooth.service",
    "cron.service",
    "ModemManager.service",
    "ssh.service",
    "triggerhappy.service",
    "mesh-bbs.service"
    # Add any other services you deem unnecessary during backup
]

def stop_services():
    """Stop necessary services before running fsck."""
    for service in services_to_stop:
        try:
            subprocess.run(["sudo", "systemctl", "stop", service], check=True)
            print(f"Stopped {service}.")
        except subprocess.CalledProcessError as e:
            if e.returncode == 5:  # Service not loaded
                print(f"{service} is not loaded. No need to stop.")
            else:
                print(f"Error stopping service {service}: {e}")

def start_services():
    """Start services after the backup is complete."""
    for service in services_to_stop:
        try:
            subprocess.run(["sudo", "systemctl", "start", service], check=True)
            print(f"Started {service}.")
        except subprocess.CalledProcessError as e:
            print(f"Error starting service {service}: {e}")

def remount_drive():
    """Remount the external drive if it is already mounted."""
    if is_mounted(mount_point):
        print(f"{mount_point} is already mounted.")
    else:
        print(f"Remounting {mount_point}...")
        try:
            subprocess.run(["sudo", "mount", external_device, mount_point], check=True)
            print(f"Remounted {external_device} at {mount_point}")
        except subprocess.CalledProcessError as e:
            print(f"Error remounting drive: {e}")
            sys.exit(1)

def get_used_space():
    """Calculate the used space in the root filesystem, excluding virtual filesystems."""
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
    """Check if the specified mount point is already mounted."""
    return mount_point in subprocess.check_output(["mount"]).decode()

def mount_drive():
    """Mount the external drive at the specified mount point."""
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

def clean_filesystem():
    """Check and clean the filesystem before creating a new backup."""
    print("Freezing the filesystem...")
    try:
        subprocess.run(["sudo", "fsfreeze", "-f", "/"], check=True)
        print("Checking the filesystem for errors...")
        subprocess.run(["sudo", "fsck", "-y", "-v", pi_device], check=True)
        print("Filesystem checked and cleaned successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error cleaning filesystem: {e}")
        sys.exit(1)
    finally:
        print("Unfreezing the filesystem...")
        subprocess.run(["sudo", "fsfreeze", "-u", "/"], check=True)

def create_backup():
    """Create a backup of the Raspberry Pi's SD card."""
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    backup_file = f"{mount_point}/pi_backup_{timestamp}.img"

    used_space = get_used_space()
    backup_size = int(used_space * 1.1)  # Add 10% to the used space
    block_count = backup_size // block_size

    dd_command = f"sudo dd if={pi_device} of={backup_file} bs={block_size} count={block_count} status=progress"

    try:
        subprocess.run(dd_command, shell=True, check=True)
        print(f"Backup created successfully: {backup_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error creating backup: {e}")

if __name__ == "__main__":
    # Stop unnecessary services before cleaning the filesystem
    stop_services()

    # Ensure the drive is mounted
    if not is_mounted(mount_point):
        print(f"{mount_point} is not mounted. Attempting to mount...")
        mount_drive()

    # Clean the filesystem before creating a backup
    clean_filesystem()

    # Check if there's enough space on the external drive for the backup
    used_space = get_used_space()
    backup_size = int(used_space * 1.1)
    if shutil.disk_usage(mount_point).free < backup_size:
        print("Not enough space on the external drive for the backup.")
        sys.exit(1)

    create_backup()

    # Start services after the backup is complete
    start_services()
