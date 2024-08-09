import subprocess

def check_service_status():
    try:
        # Run the systemctl status command and capture the output
        result = subprocess.run(
            ['sudo', 'systemctl', 'status', 'mesh-bbs.service'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Check if "BrokenPipeError" is in the output
        if "BrokenPipeError: [Errno 32] Broken pipe" in result.stdout or "BrokenPipeError: [Errno 32] Broken pipe" in result.stderr:
            print("BrokenPipeError detected. Restarting the service...")
            restart_service()
        else:
            print("Service is running normally.")

    except Exception as e:
        print(f"An error occurred: {e}")

def restart_service():
    try:
        # Restart the service
        subprocess.run(['sudo', 'systemctl', 'restart', 'mesh-bbs.service'], check=True)
        print("Service restarted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to restart the service: {e}")

if __name__ == "__main__":
    check_service_status()
