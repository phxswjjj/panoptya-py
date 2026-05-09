from __future__ import annotations

import time
from abc import ABC, abstractmethod

from win32 import CAPS_LOCK, F1_KEY, is_key_on, is_key_pressed


class Bot(ABC):
    """Abstract base class for all worker bots driven by MainBot."""

    def __init__(self, name: str = "") -> None:
        self.name = name or self.__class__.__name__
        self.enabled: bool = True

    @abstractmethod
    def tick(self, main_bot: MainBot) -> None:
        """Called once per MainBot tick when this bot is enabled."""
        ...

    def __repr__(self) -> str:
        status = "on" if self.enabled else "off"
        return f"<{self.name} [{status}]>"


class MainBot:
    """
    Orchestrates multiple Bots and drives the main loop.

    Responsibilities:
      - Run all registered Bots on every tick.
      - Pause (busy-wait at 0.1 s) while `pause_key` toggle is active.
      - Stop cleanly when `stop_key` is held down.
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
        self._bots: list[Bot] = []
        self._running = False

    # ── bot management ───────────────────────────────────────────────────────

    def add(self, *bots: Bot) -> MainBot:
        """Add one or more bots. Returns self for chaining."""
        self._bots.extend(bots)
        return self

    def remove(self, bot: Bot) -> MainBot:
        self._bots.remove(bot)
        return self

    def clear(self) -> MainBot:
        self._bots.clear()
        return self

    @property
    def bots(self) -> list[Bot]:
        return list(self._bots)

    # ── lifecycle ────────────────────────────────────────────────────────────

    def stop(self) -> None:
        """Request the loop to stop after the current tick."""
        self._running = False

    def run(self) -> None:
        """Start the main loop (blocking)."""
        self._running = True
        print(
            f"MainBot 啟動 ({len(self._bots)} bots) — "
            f"F1 停止，CAPS LOCK 暫停",
            flush=True,
        )
        try:
            while self._running:
                if is_key_pressed(self.stop_key):
                    print("MainBot 已停止", flush=True)
                    break

                if is_key_on(self.pause_key):
                    time.sleep(0.1)
                    continue

                for bot in list(self._bots):   # copy: safe to mutate during tick
                    if bot.enabled:
                        bot.tick(self)

                time.sleep(self.interval)
        finally:
            self._running = False
