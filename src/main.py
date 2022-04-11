
import curses
import locale

from operating_system.linux import LocalRemoteSockets, AllConnections, TrafficByRemoteAddress
from operating_system.linux import TrafficByProcessFormatter, TrafficByRemoteAddressFormatter
from display.components.layout import UtilizationLayout, ListLayout
from display.components.render_opts import RenderOpts
from display.components.skin import DefaultSkin


def main(stdscr):
    curses.use_default_colors()
    locale.setlocale(locale.LC_ALL, '')
    # code = locale.getpreferredencoding()
    stdscr.clear()
    open_sockets = LocalRemoteSockets().load()
    views = Views(stdscr, DefaultSkin())
    views.show_utilization_view(open_sockets)
    while True:
        key = stdscr.getkey().casefold()
        if views.handle_user_key(key, open_sockets):
            continue
        else:
            exit(0)


class Views:

    FOOTER = (
        '[V]iews cycle  '
        '[U]tilization view  '
        '[L]ist view  '
        '[S]ervice resolution toggle  '
        '[H]ost DNS resolution toggle  '
        '[/<?>]filter list by first letter <?>  '
        '[//]undo filter'
    )
    
    def __init__(self, stdscr, ui_skin):
        self._stdscr = stdscr
        self._skin = ui_skin
        self._render_opts = RenderOpts(stdscr)

    def handle_user_key(self, key: str, open_sockets: 'LocalRemoteSockets'):
        if self._render_opts.handle_user_key(key):
            if self._render_opts.views.show_list:
                self.show_list_view(open_sockets)
                return True
            elif self._render_opts.views.show_utilization:
                self.show_utilization_view(open_sockets)
                return True
        return False

    def show_list_view(self, open_sockets: 'LocalRemoteSockets'):
        layout = ListLayout(self._stdscr, self._skin, 'Process TCP & UDP connections')
        all_connections = [''.join(str(i)) for i in AllConnections(open_sockets).as_list]
        all_connections.insert(0, 'PROCESS NAME   PROTOCOL LOCAL ADDRESS PORT    REMOTE ADDRESS')
        layout.update(
            render_opts=self._render_opts,
            list_lines_with_headers=all_connections,
            footer_content=(self.FOOTER,)
        )

    def show_utilization_view(self, open_sockets: 'LocalRemoteSockets'):
        layout = UtilizationLayout(self._stdscr, self._skin)
        traffic_by_process = TrafficByProcessFormatter(open_sockets).formatted_list
        traffic_by_remote_addr = TrafficByRemoteAddressFormatter(
            open_sockets, self._render_opts.dns.resolve, self._render_opts.service.resolve
        ).formatted_list
        layout.update(
            render_opts=self._render_opts,
            process_utilization_with_headers=traffic_by_process,
            remote_addr_utilization_with_headers=traffic_by_remote_addr,
            footer_content=(self.FOOTER,)
        )


curses.wrapper(main)
