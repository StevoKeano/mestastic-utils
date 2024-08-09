#!/bin/bash

# Define variables
IMAGE_PATH="/media/stevo/sga3/pi_backup_20240809_002357.img"
MOUNT_POINT="/mnt/pi_backup"

# Check partitions in the backup image
echo "Checking partitions in the backup image..."
fdisk -l "$IMAGE_PATH"

# Set up a loop device for the image
echo "Setting up loop device..."
LOOP_DEVICE=$(sudo losetup -fP "$IMAGE_PATH")

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    echo "Creating mount point at $MOUNT_POINT..."
    sudo mkdir -p "$MOUNT_POINT"
fi

# Mount the root filesystem partition (usually p2)
echo "Mounting the root filesystem partition..."
sudo mount "${LOOP_DEVICE}p2" "$MOUNT_POINT"

# Check if the mount was successful
if mountpoint -q "$MOUNT_POINT"; then
    echo "Exploring the mounted filesystem at $MOUNT_POINT..."
    cd "$MOUNT_POINT" || exit
    ls -l

    # List contents of the /home directory
    if [ -d "home" ]; then
        echo "Contents of /home directory:"
        ls home
    else
        echo "/home directory does not exist."
    fi
else
    echo "Failed to mount the root filesystem partition."
    exit 1
fi

# Unmount when done
echo "Unmounting the filesystem..."
sudo umount "$MOUNT_POINT"

# Detach the loop device
echo "Detaching the loop device..."
sudo losetup -d "$LOOP_DEVICE"

echo "Done."
