
import curses
import time
import threading

from display.ui import Ui
from display.components.render_opts import RenderOpts
from display.components.skin import CyanSkin, RedSkin
from operating_system.linux import LocalRemoteSockets


class App:
    def __init__(self):
        self._lock = threading.RLock()
        self._opts = None

    def start(self, _stdscr):
        self._opts = RenderOpts(_stdscr, [CyanSkin(), RedSkin()])
        ui = Ui(_stdscr, self._lock, self._opts)
        ui.show_view()
        threading.Thread(daemon=True, target=self._refresh_state, kwargs={'ui': ui}).start()
        ui.handle_user_input()
    
    def _refresh_state(self, ui):
        while True:
            if not self._opts.pause:
                open_sockets = LocalRemoteSockets()
                open_sockets.load()
                if self._lock.acquire(timeout=1):
                    ui.handle_refresh_state(open_sockets)
                    self._lock.release()
            time.sleep(1)


app = App()
curses.wrapper(app.start)
