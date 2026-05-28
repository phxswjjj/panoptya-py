from __future__ import annotations

import ctypes
import ctypes.wintypes
import os
import time
from datetime import datetime
from pathlib import Path

import cv2
import mss
import numpy as np
import psutil
import pyautogui

PROCESS_NAME       = "Panoptyca.exe"
STEAM_URL          = "steam://rungameid/3882730"
CONTINUE_TEMPLATE  = Path(__file__).parent.parent / "resource" / "re-boot-continue.png"
COMMANDER_TEMPLATE = Path(__file__).parent.parent / "resource" / "commander.png"
CONFIDENCE         = 0.8

_user32     = ctypes.WinDLL("User32.dll")
SW_MAXIMIZE = 3


def _get_foreground_rect() -> tuple[int, int, int, int] | None:
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return None
    rect = ctypes.wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


def _maximize_pid(pid: int) -> bool:
    """Find the main window of the given PID and maximize it. Returns True on success."""
    result = ctypes.c_bool(False)

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_long)
    def _enum_cb(hwnd, _):
        win_pid = ctypes.c_ulong()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(win_pid))
        if win_pid.value == pid and _user32.IsWindowVisible(hwnd):
            _user32.ShowWindow(hwnd, SW_MAXIMIZE)
            _user32.SetForegroundWindow(hwnd)
            result.value = True
            return False
        return True

    _user32.EnumWindows(_enum_cb, 0)
    return result.value


def _wait_and_maximize(timeout: float = 60.0, poll: float = 2.0) -> bool:
    """Wait for PROCESS_NAME to appear, then maximize its window."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        proc = next(
            (p for p in psutil.process_iter(["name", "pid"])
             if p.info["name"] == PROCESS_NAME),
            None,
        )

        if proc:
            # 等待載入完成，否則可能找不到視窗或最大化失敗
            time.sleep(1)
            if _maximize_pid(proc.pid):
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"{ts} [reboot] {PROCESS_NAME} launched (PID={proc.pid}) — maximized", flush=True)
                return True
            
        time.sleep(poll)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} [reboot] timed out waiting for {PROCESS_NAME}", flush=True)
    return False


def _wait_menu_and_continue(timeout: float = 60.0, poll: float = 2.0) -> bool:
    """Poll the foreground window until re-boot-continue.png appears, then click it."""
    template = cv2.imread(str(CONTINUE_TEMPLATE), cv2.IMREAD_COLOR)
    if template is None:
        print(f"[reboot] template not found: {CONTINUE_TEMPLATE}", flush=True)
        return False

    th, tw = template.shape[:2]
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        win_rect = _get_foreground_rect()
        if win_rect is None:
            time.sleep(poll)
            continue

        left, top, right, bottom = win_rect
        monitor = {"left": left, "top": top, "width": right - left, "height": bottom - top}

        with mss.mss() as sct:
            raw = sct.grab(monitor)

        screenshot = cv2.cvtColor(np.array(raw), cv2.COLOR_BGRA2BGR)
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= CONFIDENCE:
            cx = left + max_loc[0] + tw // 2
            cy = top  + max_loc[1] + th // 2
            pyautogui.click(cx, cy)
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{ts} [reboot] continue clicked at ({cx}, {cy})  confidence={max_val:.2f}", flush=True)
            return True

        time.sleep(poll)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} [reboot] timed out waiting for continue button", flush=True)
    return False


def _wait_commander(timeout: float = 60.0, poll: float = 2.0) -> bool:
    """Poll the foreground window until commander.png appears, then press ESC × 2 + F2."""
    import keyboard

    template = cv2.imread(str(COMMANDER_TEMPLATE), cv2.IMREAD_COLOR)
    if template is None:
        print(f"[reboot] template not found: {COMMANDER_TEMPLATE}", flush=True)
        return False

    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        win_rect = _get_foreground_rect()
        if win_rect is None:
            time.sleep(poll)
            continue

        left, top, right, bottom = win_rect
        monitor = {"left": left, "top": top, "width": right - left, "height": bottom - top}

        with mss.mss() as sct:
            raw = sct.grab(monitor)

        screenshot = cv2.cvtColor(np.array(raw), cv2.COLOR_BGRA2BGR)
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _ , _ = cv2.minMaxLoc(result)

        if max_val >= CONFIDENCE:
            keyboard.press_and_release("esc")
            time.sleep(0.2)
            keyboard.press_and_release("esc")
            time.sleep(0.2)
            keyboard.press_and_release("F2")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{ts} [reboot] commander found (confidence={max_val:.2f}) — esc esc F2", flush=True)
            return True

        time.sleep(poll)

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{ts} [reboot] timed out waiting for commander", flush=True)
    return False


class ReBootAction:
    """
    Every 5 minutes, checks whether Panoptyca.exe is running.
    - Found    → no action.
    - Not found → launches via Steam, maximizes the window, then clicks the continue button.
    """

    INTERVAL = 300.0  # seconds

    def __init__(self) -> None:
        self._last_executed: float | None = None

    def execute(self) -> None:
        now = time.monotonic()
        if self._last_executed is not None and (now - self._last_executed) < self.INTERVAL:
            return

        self._last_executed = now

        proc = next(
            (p for p in psutil.process_iter(["name", "pid"])
             if p.info["name"] == PROCESS_NAME),
            None,
        )

        if proc:
            return

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"{ts} [reboot] {PROCESS_NAME} not found — launching via Steam", flush=True)
        os.startfile(STEAM_URL)
        if not _wait_and_maximize():
            return
        
        if not _wait_menu_and_continue():
            return
        if not _wait_commander():
            return
