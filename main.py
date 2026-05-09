from datetime import datetime

from bot import Bot, BotAction
from win32 import get_focused_window_info

TARGET_TITLE = "Panoptyca"


class LogStatusAction(BotAction):
    """Logs time and focused window info only when the window title contains TARGET_TITLE."""

    def run(self, bot: Bot) -> None:
        name, pid, title = get_focused_window_info()
        if TARGET_TITLE not in title:
            return
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), flush=True)
        print(f"[{name}] PID={pid} | {title}", flush=True)


if __name__ == "__main__":
    bot = Bot(interval=1.0)
    bot.add(LogStatusAction())
    bot.run()
