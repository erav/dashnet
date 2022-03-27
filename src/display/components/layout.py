
import curses
import locale
import logging

import ipdb

FIRST_HEIGHT_BREAKPOINT = 30
FIRST_WIDTH_BREAKPOINT = 120

logger = logging.getLogger(__name__)


class ScreenSize:
    @property
    def width(self):
        return curses.COLS

    @property
    def height(self):
        return curses.LINES

    @property
    def half_width(self):
        return int(curses.COLS / 2)

    @property
    def half_height(self):
        return int(curses.LINES / 2)


class Layout:
    """
    self._header: HeaderDetails<'a>,
    self._children: Vec<Table<'a>>,
    self._footer: HelpText,
    """
    def __init__(self, header, children, footer):
        self._header = header
        self._children = children
        self._footer = footer

    def render(self, stdscr):
        locale.setlocale(locale.LC_ALL, '')
        # code = locale.getpreferredencoding()
        stdscr.clear()
        scr_size = ScreenSize()
        self._create_win(stdscr, 0, 0, 1, scr_size.width, border=False, content=self._header.details())
        main = stdscr.subwin(scr_size.height - 2, scr_size.width, 1, 0)
        title1 = 'Util by process name'
        self._create_win(main, 0, 1, scr_size.half_height - 1, scr_size.half_width, title1)
        title2 = 'Util by remote address'
        self._create_win(main, scr_size.half_width + 1, 1, scr_size.half_height - 1, scr_size.half_width, title2)
        title3 = 'Util by process connection'
        self._create_win(main, 0, scr_size.half_height, scr_size.half_height - 1, scr_size.width, title3)
        self._create_win(stdscr, 0, scr_size.height - 1, 1, scr_size.width, border=False, content=self._footer.render())
        stdscr.refresh()
        stdscr.getkey()

    @staticmethod
    def _create_win(parent, begin_x, begin_y, height, width, title=None, border=True, content=None):
        win = parent.subwin(height, width, begin_y, begin_x)
        if border:
            win.border(0, 0, 0, 0, 0, 0, 0, 0)
        if title:
            win.addstr(0, 1, title)
        if content:
            x = 1
            y = 0 if height == 1 else 1
            win.addstr(y, x, content)
        win.refresh()
        return win
