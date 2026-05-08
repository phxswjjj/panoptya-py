from __future__ import annotations

import time
from abc import ABC, abstractmethod

from win32 import CAPS_LOCK, F1_KEY, is_key_on, is_key_pressed


class BotAction(ABC):
    """Base class for all bot actions."""

    def __init__(self, name: str = ""):
        self.name = name or self.__class__.__name__
        self.enabled: bool = True

    @abstractmethod
    def run(self, bot: Bot) -> None:
        """Called once per bot tick when the bot is active."""
        ...

    def __repr__(self) -> str:
        status = "on" if self.enabled else "off"
        return f"<{self.name} [{status}]>"


class Bot:
    """
    Manages a collection of BotActions and drives the main loop.

    Loop behaviour:
      - Pauses (busy-waits at 0.1 s) while `pause_key` toggle is active.
      - Stops cleanly when `stop_key` is held down.
      - Calls each enabled action once per `interval` seconds.
    """

    def __init__(
        self,
        interval: float = 1.0,
        stop_key: int = F1_KEY,
        pause_key: int = CAPS_LOCK,
    ) -> None:
        self.interval  = interval
        self.stop_key  = stop_key
        self.pause_key = pause_key
        self._actions: list[BotAction] = []
        self._running  = False

    # ── action management ───────────────────────────────────────────────────

    def add(self, *actions: BotAction) -> Bot:
        """Add one or more actions. Returns self for chaining."""
        self._actions.extend(actions)
        return self

    def remove(self, action: BotAction) -> Bot:
        """Remove an action. Returns self for chaining."""
        self._actions.remove(action)
        return self

    def clear(self) -> Bot:
        """Remove all actions."""
        self._actions.clear()
        return self

    @property
    def actions(self) -> list[BotAction]:
        return list(self._actions)

    # ── lifecycle ────────────────────────────────────────────────────────────

    def stop(self) -> None:
        """Request the bot to stop after the current tick."""
        self._running = False

    def run(self) -> None:
        """Start the main loop (blocking)."""
        self._running = True
        print(
            f"Bot 啟動 ({len(self._actions)} actions) — "
            f"F1 停止，CAPS LOCK 暫停",
            flush=True,
        )
        try:
            while self._running:
                if is_key_pressed(self.stop_key):
                    print("Bot 已停止", flush=True)
                    break

                if is_key_on(self.pause_key):
                    time.sleep(0.1)
                    continue

                for action in list(self._actions):   # copy: safe to mutate during iteration
                    if action.enabled:
                        action.run(self)

                time.sleep(self.interval)
        finally:
            self._running = False
