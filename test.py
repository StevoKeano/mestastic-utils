import platform

# Try to import Xlib for Linux
try:
    from Xlib import X, display, Xatom, error
    import Xlib.protocol.event
    XLIB_AVAILABLE = True
except ImportError:
    XLIB_AVAILABLE = False

def get_active_window():
    system = platform.system()
    if system == "Windows":
        import pygetwindow as gw
        return gw.getActiveWindow()
    elif system == "Linux":
        if XLIB_AVAILABLE:
            d = display.Display()
            root = d.screen().root
            active_window = root.get_full_property(d.intern_atom('_NET_ACTIVE_WINDOW'), X.AnyPropertyType)
            if active_window:
                window = d.create_resource_object('window', active_window.value[0])
                return d, window
        return None
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")

def set_window_name(display_window, new_name):
    system = platform.system()
    if system == "Windows":
        display_window.title = new_name
    elif system == "Linux":
        if XLIB_AVAILABLE:
            try:
                d, window = display_window
                # For GNOME Terminal, we need to set the _NET_WM_VISIBLE_NAME property
                window.change_property(
                    d.intern_atom('_NET_WM_VISIBLE_NAME'),
                    d.intern_atom('UTF8_STRING'),
                    8,
                    new_name.encode('utf-8')
                )
                window.change_property(
                    d.intern_atom('_NET_WM_NAME'),
                    d.intern_atom('UTF8_STRING'),
                    8,
                    new_name.encode('utf-8')
                )
                window.change_property(
                    d.intern_atom('WM_NAME'),
                    Xatom.STRING,
                    8,
                    new_name.encode('utf-8')
                )
                d.flush()
            except error.BadWindow:
                print("Error: Invalid window")
            except Exception as e:
                print(f"Error setting window name: {e}")
        else:
            print("Xlib is not available. Unable to set window name.")
    else:
        raise NotImplementedError(f"Unsupported platform: {system}")

# Example usage
new_name = "New Window Name"
active_window = get_active_window()
if active_window:
    set_window_name(active_window, new_name)
    print(f"Attempted to set window name to: {new_name}")
else:
    print("Could not get active window")

# For Linux, print additional debug information
if platform.system() == "Linux" and XLIB_AVAILABLE:
    d, window = active_window
    wm_class = window.get_wm_class()
    wm_name = window.get_wm_name()
    visible_name = window.get_full_property(d.intern_atom('_NET_WM_VISIBLE_NAME'), 0)
    print(f"Active Window Class: {wm_class}")
    print(f"Active Window Name: {wm_name}")
    print(f"Active Window Visible Name: {visible_name.value.decode('utf-8') if visible_name else 'Not set'}")

