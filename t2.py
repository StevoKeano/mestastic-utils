import subprocess

def get_active_window_name():
    try:
        output = subprocess.check_output(['wmctrl', '-l']).decode('utf-8')
        active_window = subprocess.check_output(['xdotool', 'getactivewindow']).decode('utf-8').strip()
        for line in output.splitlines():
            if line.split()[0] == active_window:
                return ' '.join(line.split()[3:])
    except subprocess.CalledProcessError:
        return None

print(get_active_window_name())
