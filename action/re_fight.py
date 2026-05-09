from __future__ import annotations

import ctypes
import ctypes.wintypes
import time
from pathlib import Path

import cv2
import mss
import numpy as np
import pyautogui

_user32 = ctypes.WinDLL("User32.dll")

TEMPLATE_PATH = Path(__file__).parent.parent / "resource" / "re-fight.png"
CONFIDENCE    = 0.8


def _get_foreground_rect() -> tuple[int, int, int, int] | None:
    """Return (left, top, right, bottom) of the foreground window, or None."""
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return None
    rect = ctypes.wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


class ReFightAction:
    """
    Searches the foreground window for resource/re-fight.png using template matching.
    On match: left-clicks the centre of the found position, then enters a 60 s cooldown.
    execute() returns (x, y) on success, or None if not found / on cooldown.
    """

    COOLDOWN = 1.0  # seconds

    def __init__(self, confidence: float = CONFIDENCE) -> None:
        self.confidence = confidence
        self._template = cv2.imread(str(TEMPLATE_PATH), cv2.IMREAD_COLOR)
        if self._template is None:
            raise FileNotFoundError(f"Template image not found: {TEMPLATE_PATH}")
        self._th, self._tw = self._template.shape[:2]
        self._last_executed: float | None = None

    @property
    def cooldown_remaining(self) -> float:
        if self._last_executed is None:
            return 0.0
        return max(0.0, self.COOLDOWN - (time.monotonic() - self._last_executed))

    def execute(self) -> tuple[int, int] | None:
        if self._last_executed is not None and self.cooldown_remaining > 0:
            return None

        win_rect = _get_foreground_rect()
        if win_rect is None:
            print("[re-fight] no foreground window", flush=True)
            return None

        left, top, right, bottom = win_rect
        monitor = {"left": left, "top": top, "width": right - left, "height": bottom - top}

        with mss.mss() as sct:
            try:
                raw = sct.grab(monitor)
            except Exception:
                print("[re-fight] failed to capture screen", flush=True)
                return None

        screenshot = cv2.cvtColor(np.array(raw), cv2.COLOR_BGRA2BGR)
        result = cv2.matchTemplate(screenshot, self._template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val < self.confidence:
            return None

        cx = left + max_loc[0] + self._tw // 2
        cy = top  + max_loc[1] + self._th // 2

        pyautogui.click(cx, cy)
        self._last_executed = time.monotonic()

        print(f"[re-fight] clicked ({cx}, {cy})  confidence={max_val:.2f}", flush=True)
        return (cx, cy)
