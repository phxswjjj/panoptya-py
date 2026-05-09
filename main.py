import time
from datetime import datetime

import keyboard

from bot import Bot, MainBot
from win32 import get_focused_window_info


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

        keyboard.press_and_release("F4")
        time.sleep(0.2)
        keyboard.press_and_release("v")
        time.sleep(0.2)
        keyboard.press_and_release("F4")
        time.sleep(0.2)
        keyboard.press_and_release("v")

        self._last_executed = now
        return True

    @property
    def cooldown_remaining(self) -> float:
        """Seconds until the action can be executed again (0 if ready)."""
        if self._last_executed is None:
            return 0.0
        remaining = self.COOLDOWN - (time.monotonic() - self._last_executed)
        return max(0.0, remaining)


class GameBot(Bot):
    """Runs CollectAction when the focused window title contains TARGET."""

    TARGET = "Panoptyca"

    def __init__(self) -> None:
        super().__init__()
        self._collect = CollectAction()

    def tick(self, main_bot: MainBot) -> None:
        _, _, title = get_focused_window_info()
        if self.TARGET not in title:
            return

        result = self._collect.execute()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if result:
            print(f"{ts} [collect] ok", flush=True)
        else:
            remaining = self._collect.cooldown_remaining
            # print(f"{ts} [collect] cooldown {remaining:.0f}s", flush=True)


if __name__ == "__main__":
    main_bot = MainBot(interval=0.2)
    main_bot.add(GameBot())
    main_bot.run()
