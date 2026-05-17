import ctypes
import ctypes.wintypes
import time
from pathlib import Path

import cv2
import keyboard
import numpy as np
import pyautogui

_user32           = ctypes.WinDLL("User32.dll")
CONFIRM_TEMPLATE  = Path(__file__).parent.parent / "resource" / "collect_confirm.png"
TITLE_TEMPLATE    = Path(__file__).parent.parent / "resource" / "collect_title.png"
CONFIDENCE        = 0.8


def _get_foreground_rect() -> tuple[int, int, int, int] | None:
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return None
    rect = ctypes.wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return (rect.left, rect.top, rect.right, rect.bottom)


def _grab_foreground() -> tuple[np.ndarray, tuple[int, int, int, int]] | None:
    """Screenshot the foreground window using pyautogui. Returns (bgr_image, rect) or None."""
    win_rect = _get_foreground_rect()
    if win_rect is None:
        return None
    left, top, right, bottom = win_rect
    pil_img = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
    bgr = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    return bgr, win_rect


class CollectAction:
    """
    Presses F4 → v → F4 to trigger an in-game collect action.
    Has a 60-second cooldown: execute() returns False if called again too soon.
    """

    COOLDOWN = 60.0  # seconds

    def __init__(self) -> None:
        self._last_executed: float | None = None
        self._confirm_template = cv2.imread(str(CONFIRM_TEMPLATE), cv2.IMREAD_COLOR)
        self._title_template   = cv2.imread(str(TITLE_TEMPLATE),   cv2.IMREAD_COLOR)

    def _click_confirm(self) -> bool:
        """Search the foreground window for collect_confirm.png and click it,
        but only when collect_title.png is also visible on screen.
        Returns True if clicked, False otherwise.
        """
        if self._confirm_template is None or self._title_template is None:
            return False

        cap = _grab_foreground()
        if cap is None:
            return False

        screenshot, (left, top, *_) = cap

        # guard: collect_title.png must be present
        _, title_val, _, _ = cv2.minMaxLoc(
            cv2.matchTemplate(screenshot, self._title_template, cv2.TM_CCOEFF_NORMED)
        )
        if title_val < CONFIDENCE:
            return False

        # find confirm button
        result = cv2.matchTemplate(screenshot, self._confirm_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < CONFIDENCE:
            return False

        th, tw = self._confirm_template.shape[:2]
        cx = left + max_loc[0] + tw // 2
        cy = top  + max_loc[1] + th // 2
        pyautogui.click(cx, cy, duration=0.2)
        return True

    def execute(self) -> bool:
        now = time.monotonic()
        if self._last_executed is not None and (now - self._last_executed) < self.COOLDOWN:
            return False

        # 切換至指揮視圖
        keyboard.press_and_release("F2")

        for _ in range(2):
            keyboard.press_and_release("F4")
            time.sleep(0.4)
            keyboard.press_and_release("v")
            time.sleep(0.4)

        for _ in range(10):
            time.sleep(0.4)
            if self._click_confirm():
                break
        
        self._last_executed = now
        return True

    @property
    def cooldown_remaining(self) -> float:
        """Seconds until the action can be executed again (0 if ready)."""
        if self._last_executed is None:
            return 0.0
        remaining = self.COOLDOWN - (time.monotonic() - self._last_executed)
        return max(0.0, remaining)
