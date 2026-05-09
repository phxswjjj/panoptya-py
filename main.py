from datetime import datetime

from bot import Bot, MainBot
from win32 import get_focused_window_info


class GameBot(Bot):
    """Outputs time and focused window info only when the window title contains TARGET."""

    TARGET = "Panoptyca"

    def tick(self, main_bot: MainBot) -> None:
        name, pid, title = get_focused_window_info()
        if self.TARGET not in title:
            return
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), flush=True)
        print(f"[{name}] PID={pid} | {title}", flush=True)


if __name__ == "__main__":
    main_bot = MainBot(interval=1.0)
    main_bot.add(GameBot())
    main_bot.run()
