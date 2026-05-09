import time
from datetime import datetime

from action.collect import CollectAction
from bot import Bot, MainBot
from win32 import get_focused_window_info


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
