
import curses
import locale
import threading

from display.components.formatters import TrafficByAddressFormatter, TrafficByProcessFormatter, AllConnectionsFormatter
from display.components.layout import UtilizationLayout, ListLayout
from display.components.render_opts import RenderOpts
from operating_system.linux import LocalRemoteSockets, AllConnections


class Ui:

    def __init__(self, _stdscr, lock: threading.RLock, render_opts: RenderOpts):
        self._stdscr = _stdscr
        self._lock = lock
        self._opts = render_opts
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
            if self._lock.acquire():
                if self._opts.handle_user_key(key.casefold()):
                    self._apply_filter()
                    self.show_view()
                    self._lock.release()
                    continue
                else:
                    self._lock.release()
                    return

    def handle_refresh_state(self, open_sockets):
        self._update(open_sockets)
        self._apply_filter()
        self.show_view()

    def _update(self, open_sockets: 'LocalRemoteSockets'):
        self._open_sockets = open_sockets

    def _apply_filter(self):
        if self._open_sockets:
            if self._opts.process_filter.apply():
                self._open_sockets.filter_by_regex(self._opts.process_filter.pattern)
            elif self._opts.process_filter.unapply():
                self._open_sockets.load()
                self._opts.process_filter.reset()

    def show_view(self):
        if self._opts.views.show_list:
            self.show_list_view()
        elif self._opts.views.show_utilization:
            self.show_utilization_view()

    def show_list_view(self):
        self._list_layout = ListLayout(self._stdscr, self._opts)
        self._list_layout.update(footer_content=self._footer_title())
        if not self._open_sockets:
            self._list_layout.show_loading()
        else:
            all_connections = AllConnectionsFormatter(
                self._open_sockets, self._opts.dns.resolve, self._opts.service.resolve
            )
            self._list_layout.update(
                header_content=self._header_title(),
                list_lines_with_headers=all_connections.formatted_list,
                footer_content=self._footer_title()
            )

    def show_utilization_view(self):
        self._utilization_layout = UtilizationLayout(self._stdscr, self._opts)
        self._utilization_layout.update(footer_content=self._footer_title())
        if not self._open_sockets:
            self._utilization_layout.show_loading()
        else:
            process_traffic = TrafficByProcessFormatter(self._open_sockets)
            remote_traffic = TrafficByAddressFormatter(
                self._open_sockets.remote_sockets, self._opts.dns.resolve, self._opts.service.resolve
            )
            local_traffic = TrafficByAddressFormatter(
                self._open_sockets.local_sockets, self._opts.dns.resolve, self._opts.service.resolve
            )
            self._utilization_layout.update(
                header_content=self._header_title(),
                by_process_with_headers=process_traffic.formatted_list,
                by_remote_addr_with_headers=remote_traffic.formatted_list,
                by_local_addr_with_headers=local_traffic.formatted_list,
                footer_content=self._footer_title()
            )

    def _header_title(self):
        p = '(Paused)' if self._opts.pause else ''
        return f'TCP\\UDP Connections {p}'

    def _footer_title(self):
        p = '<SPACE> Resume' if self._opts.pause else '<SPACE> Pause'
        return (
            '[V]iews  '
            f'{p}  '
            '[D]NS Resolution  '
            '[S]ervice Resolution  '
            '[/]Filter  '
        )
