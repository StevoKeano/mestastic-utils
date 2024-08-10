#!/bin/bash

# Unmount all loop devices
for mount_point in $(mount | grep loop | awk '{print $3}'); do
    echo "Unmounting $mount_point"
    sudo umount "$mount_point"
done

# Detach all loop devices
for loop_device in $(losetup -l | grep loop | awk '{print $1}'); do
    echo "Detaching $loop_device"
    sudo losetup -d "$loop_device"
done

echo "Cleanup complete."

