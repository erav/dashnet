
import curses
import locale

from common.utils import ToggleStates, FirstCharFilter, NoopFilter
from operating_system.linux import OpenSockets
from display.components.layout import UtilizationLayout, ListLayout
from display.components.skin import DefaultSkin


def main(stdscr):
    locale.setlocale(locale.LC_ALL, '')
    # code = locale.getpreferredencoding()
    stdscr.clear()

    open_sockets = OpenSockets().create_process_connection_lists()
    views = Views(stdscr, DefaultSkin())
    views.show_utilization_view(open_sockets.connected_processes_count_list)
    while True:
        key = stdscr.getkey().casefold()
        if views.handle_user_key(key, open_sockets):
            continue
        else:
            exit(0)


class Views:

    UTILIZATION_VIEW = 0
    LIST_VIEW = 1

    FOOTER = (
        '[T]oggle views  '
        '[U]tilization view  '
        '[L]ist view  '
        '[/<?>]filter list by first letter <?>  '
        '[//]undo filter'
    )

    def __init__(self, stdscr, ui_skin):
        self._stdscr = stdscr
        self._skin = ui_skin
        self._toggle = ToggleStates(len([self.UTILIZATION_VIEW, self.LIST_VIEW]))
        
    def handle_user_key(self, key, open_sockets):
        list_lines = open_sockets.process_with_local_sockets_list
        utilization_lines = open_sockets.connected_processes_count_list
        if key == 't' and self._toggle.is_active(self.UTILIZATION_VIEW):
            self.show_list_view(list_lines)
            self._toggle.toggle()
            return True
        elif key == 't' and self._toggle.is_active(self.LIST_VIEW):
            self.show_utilization_view(utilization_lines)
            self._toggle.toggle()
            return True
        elif key == 'u':
            self.show_utilization_view(utilization_lines)
            self._toggle.toggle_to(self.UTILIZATION_VIEW)
            return True
        elif key == 'l':
            self.show_list_view(list_lines)
            self._toggle.toggle_to(self.LIST_VIEW)
            return True
        elif key == '/':
            key = self._stdscr.getkey().casefold()
            list_filter = FirstCharFilter(key) if self._is_filter_key(key) else NoopFilter()
            if self._toggle.is_active(self.LIST_VIEW):
                self.show_list_view(list_lines, list_filter)
            if self._toggle.is_active(self.UTILIZATION_VIEW):
                self.show_utilization_view(utilization_lines, list_filter)
            return True
        return False

    def show_list_view(self, list_lines_with_headers, list_filter=NoopFilter()):
        layout = ListLayout(self._stdscr, self._skin, 'Process TCP & UDP connections')
        layout.update(
            list_filter=list_filter,
            list_lines_with_headers=list_lines_with_headers,
            footer_content=(self.FOOTER,)
        )

    def show_utilization_view(self, utilization_lines, list_filter=NoopFilter()):
        layout = UtilizationLayout(self._stdscr, self._skin)
        layout.update(
            list_filter=list_filter,
            proc_utilization_list_with_headers=utilization_lines,
            footer_content=(self.FOOTER,)
        )

    def _toggle(self):
        self._toggle.toggle()

    @staticmethod
    def _is_filter_key(key):
        return not key.casefold() < 'a' and not key.casefold() > 'z' or key == '<'


curses.wrapper(main)
