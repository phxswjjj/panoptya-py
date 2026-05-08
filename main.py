import time
import ctypes
import ctypes.wintypes
import psutil
from datetime import datetime

user32 = ctypes.WinDLL("User32.dll")

CAPS_LOCK = 0x14
F1_KEY = 0x70


def is_key_on(vk: int) -> bool:
    """Return True if a toggle key (e.g. CAPS LOCK) is currently active."""
    return bool(user32.GetKeyState(vk) & 0x0001)


def is_key_pressed(vk: int) -> bool:
    """Return True if a key is currently held down (high-order bit set)."""
    return bool(user32.GetAsyncKeyState(vk) & 0x8000)


def get_focused_window_info() -> str:
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "(no focused window)"

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

    return f"[{name}] PID={pid} | {title}"


print("程序啟動 — F1 停止，CAPS LOCK 暫停", flush=True)

while True:
    if is_key_pressed(F1_KEY):
        print("程序已停止", flush=True)
        break

    if is_key_on(CAPS_LOCK):
        time.sleep(0.1)
        continue

    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), get_focused_window_info(), flush=True)
    time.sleep(1)
