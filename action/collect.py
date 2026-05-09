import time

import keyboard


class CollectAction:
    """
    Presses F4 → v → F4 to trigger an in-game collect action.
    Has a 60-second cooldown: execute() returns False if called again too soon.
    """

    COOLDOWN = 60.0  # seconds

    def __init__(self) -> None:
        self._last_executed: float | None = None

    def execute(self) -> bool:
        now = time.monotonic()
        if self._last_executed is not None and (now - self._last_executed) < self.COOLDOWN:
            return False

        for _ in range(8):
            keyboard.press_and_release("F4")
            time.sleep(0.2)
            keyboard.press_and_release("v")
            time.sleep(0.2)

        time.sleep(1)
        keyboard.press_and_release("esc")

        self._last_executed = now
        return True

    @property
    def cooldown_remaining(self) -> float:
        """Seconds until the action can be executed again (0 if ready)."""
        if self._last_executed is None:
            return 0.0
        remaining = self.COOLDOWN - (time.monotonic() - self._last_executed)
        return max(0.0, remaining)
