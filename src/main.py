
import curses
import locale
import time
import threading

from operating_system.linux import LocalRemoteSockets, AllConnections
from operating_system.linux import TrafficByProcessFormatter, TrafficByRemoteAddressFormatter
from display.components.layout import UtilizationLayout, ListLayout
from display.components.render_opts import RenderOpts
from display.components.skin import DefaultSkin


class App:
    def __init__(self):
        self._lock = threading.RLock()

    def start(self, _stdscr):
        ui = Ui(_stdscr, self._lock, DefaultSkin())
        ui.show_view()
        threading.Thread(daemon=True, target=self._refresh_state, kwargs={'ui': ui}).start()
        ui.handle_user_input()
    
    def _refresh_state(self, ui):
        while True:
            open_sockets = LocalRemoteSockets()
            open_sockets.load()
            self._lock.acquire(blocking=False)
            ui.update(open_sockets)
            ui.show_view()
            self._lock.release()
            time.sleep(3)


class Ui:

    FOOTER = (
        '[V]iews toogle  '
        '[S]ervice resolution toggle  '
        '[H]ost DNS resolution toggle  '
        '[/<?>]filter list by first letter <?>  '
        '[//]undo filter'
    )

    def __init__(self, _stdscr, lock: threading.RLock, ui_skin: 'DefaultSkin'):
        self._stdscr = _stdscr
        self._lock = lock
        self._skin = ui_skin
        self._render_opts = RenderOpts(self._stdscr)
        self._open_sockets = None
        self._list_layout = None
        self._utilization_layout = None
        self._setup_curses()

    def _setup_curses(self):
        self._stdscr.clear()
        curses.use_default_colors()
        locale.setlocale(locale.LC_ALL, '')
        # code = locale.getpreferredencoding()

    def handle_user_input(self):
        while True:
            key = self._stdscr.getkey()
            if self._render_opts.handle_user_key(key.casefold()):
                self.show_view()
                continue
            else:
                return

    def update(self, open_sockets: 'LocalRemoteSockets'):
        self._open_sockets = open_sockets

    def show_view(self):
        self._lock.acquire(blocking=False)
        if self._render_opts.views.show_list:
            self.show_list_view()
        elif self._render_opts.views.show_utilization:
            self.show_utilization_view()
        self._lock.release()

    def show_list_view(self):
        if not self._list_layout:
            self._list_layout = ListLayout(self._stdscr, self._skin, 'Process TCP & UDP connections')
        self._list_layout.update(render_opts=self._render_opts, footer_content=(self.FOOTER,))
        if not self._open_sockets:
            self._list_layout.show_loading()
        else:
            all_connections = [''.join(str(i)) for i in AllConnections(self._open_sockets).as_list]
            self._list_layout.update(
                render_opts=self._render_opts,
                list_lines_with_headers=all_connections,
                footer_content=(self.FOOTER,)
            )

    def show_utilization_view(self):
        if not self._utilization_layout:
            self._utilization_layout = UtilizationLayout(self._stdscr, self._skin)
        self._utilization_layout.update(render_opts=self._render_opts, footer_content=(self.FOOTER,))
        if not self._open_sockets:
            self._utilization_layout.show_loading()
        else:
            traffic_by_process = TrafficByProcessFormatter(self._open_sockets).formatted_list
            traffic_by_remote_addr = TrafficByRemoteAddressFormatter(
                self._open_sockets, self._render_opts.dns.resolve, self._render_opts.service.resolve
            ).formatted_list
            self._utilization_layout.update(
                render_opts=self._render_opts,
                process_utilization_with_headers=traffic_by_process,
                remote_addr_utilization_with_headers=traffic_by_remote_addr,
                footer_content=(self.FOOTER,)
            )


app = App()
curses.wrapper(app.start)
