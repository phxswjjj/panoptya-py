import ctypes
import ctypes.wintypes
import psutil

user32 = ctypes.WinDLL("User32.dll")

CAPS_LOCK = 0x14
F1_KEY    = 0x70


def is_key_on(vk: int) -> bool:
    """Return True if a toggle key (e.g. CAPS LOCK) is currently active."""
    return bool(user32.GetKeyState(vk) & 0x0001)


def is_key_pressed(vk: int) -> bool:
    """Return True if a key is currently held down (high-order bit set)."""
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def get_focused_window_info() -> tuple[str, int, str]:
    """Return (process_name, pid, window_title) of the current foreground window."""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ("", 0, "")

    length = user32.GetWindowTextLengthW(hwnd) + 1
    buf = ctypes.create_unicode_buffer(length)
    user32.GetWindowTextW(hwnd, buf, length)
    title = buf.value or "(no title)"

    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    pid = pid.value

    try:
        name = psutil.Process(pid).name()
    except psutil.NoSuchProcess:
        name = "(unknown)"

    return (name, pid, title)
