import time
import ctypes
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


print("程序啟動 — F1 停止，CAPS LOCK 暫停", flush=True)

while True:
    if is_key_pressed(F1_KEY):
        print("程序已停止", flush=True)
        break

    if is_key_on(CAPS_LOCK):
        time.sleep(0.1)
        continue

    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), flush=True)
    time.sleep(1)
