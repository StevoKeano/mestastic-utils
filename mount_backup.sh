#!/bin/bash

# Define variables
IMAGE_DIR="/media/stevo/sga3"
MOUNT_POINT="/mnt/pi_backup"

# List all matching image files and store them in an array
mapfile -t IMAGE_FILES < <(ls "$IMAGE_DIR"/pi_backup_*.img 2>/dev/null)

# Check if any image files were found
if [ ${#IMAGE_FILES[@]} -eq 0 ]; then
    echo "No backup image files found in $IMAGE_DIR."
    exit 1
fi

# Display the list of image files with indices
echo "Available backup image files:"
for i in "${!IMAGE_FILES[@]}"; do
    echo "[$i] ${IMAGE_FILES[$i]}"
done

# Prompt the user to select an image file by index
read -p "Enter the index of the image file to use: " INDEX

# Validate the user's input
if [[ ! "$INDEX" =~ ^[0-9]+$ ]] || [ "$INDEX" -ge ${#IMAGE_FILES[@]} ]; then
    echo "Invalid selection. Exiting."
    exit 1
fi

# Set the selected image path
IMAGE_PATH="${IMAGE_FILES[$INDEX]}"

# Check partitions in the backup image
echo "Checking partitions in the backup image..."
fdisk -l "$IMAGE_PATH"

# Set up a loop device for the image
echo "Setting up loop device..."
LOOP_DEVICE=$(sudo losetup -fP --show "$IMAGE_PATH")

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
