from datetime import datetime

from bot import Bot, BotAction
from win32 import get_focused_window_info


class LogTimeAction(BotAction):
    def run(self, bot: Bot) -> None:
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), flush=True)


class LogFocusedWindowAction(BotAction):
    def run(self, bot: Bot) -> None:
        name, pid, title = get_focused_window_info()
        print(f"[{name}] PID={pid} | {title}", flush=True)


if __name__ == "__main__":
    bot = Bot(interval=1.0)
    bot.add(LogTimeAction(), LogFocusedWindowAction())
    bot.run()
