
import curses
import logging

from display.components.render_opts import RenderOpts

logger = logging.getLogger(__name__)


class WindowSize:
    def __init__(self, height, width, begin_y, begin_x):
        self._h = height
        self._w = width
        self._y = begin_y
        self._x = begin_x
        print(self)

    @property
    def h(self):
        return self._h

    @property
    def w(self):
        return self._w

    @property
    def y(self):
        return self._y

    @property
    def x(self):
        return self._x

    def __repr__(self):
        return f'h:{self._h} w{self._w} y:{self.y} x{self.x}'


class ScreenSize(WindowSize):
    def __init__(self):
        super(ScreenSize, self).__init__(curses.LINES, curses.COLS, 0, 0)
        # maxy ,maxx = stdscr.maxyx()

    @property
    def half_h(self):
        return int(self.h / 2)

    @property
    def half_w(self):
        return int(self.w / 2)


class Window:
    def __init__(self, curses_parent, win_size, skin, title=None, border=True):
        self._curses_window = curses_parent.subwin(win_size.h, win_size.w, win_size.y, win_size.x)
        self._skin = skin
        if border:
            self._curses_window.border(0, 0, 0, 0, 0, 0, 0, 0)
        if title:
            self.add_title(title)
        self._curses_window.refresh()

    def add_title(self, title):
        self._try_addstr(0, 1, title, self._skin.default_title_attr)

    def add_header(self, header):
        self._try_addstr(1, 1, header, self._skin.default_title_attr)

    def update(self, content_lines: [], attr=0):
        y, x = self.curses_win.getmaxyx()
        if content_lines:
            if y == 1 and len(content_lines) == 1:
                self._try_addstr(0, 1, f'{content_lines[0]}', attr)
            else:
                i = 2
                j = 0
                while i <= y - 2 and j < len(content_lines):
                    self._try_addstr(i, 1, str(content_lines[j]), attr)
                    i += 1
                    j += 1
            self.curses_win.refresh()

    def _try_addstr(self, y, x, content_line, attr):
        try:
            if content_line:
                self.curses_win.addstr(y, x, f' {content_line} ', attr)
        except curses.error as e:
            if 'addwstr() returned ERR' in str(e):
                curses.endwin()
                print('ERROR: Window size is too small to fit content. Try enlarging.', flush=True)
                exit(1)

    @property
    def curses_win(self):
        return self._curses_window


class BaseLayout:
    def __init__(self, stdscr, render_opts: RenderOpts):
        self._stdscr = stdscr
        self._opts = render_opts
        self._header = None
        self._footer = None

    def show_loading(self):
        self._header.update(('loading...',), attr=self._opts.skin.default_title_attr)

    def update_header(self, header_content: str):
        if header_content:
            self._header.update((header_content,), attr=self._opts.skin.default_title_attr)

    def update_list_window(self, title: str, list_with_headers: [], window):
        window.add_title(f'{title} ({self._list_len(list_with_headers)})')
        if list_with_headers:
            window.add_header(list_with_headers[0])
            window.update(sorted(list_with_headers[1:]))

    def update_footer(self, footer_content: str):
        if footer_content:
            self._footer.update((footer_content,), attr=self._opts.skin.default_title_attr)

    def _list_len(self, list_with_headers):
        return len(list_with_headers) - 1 if list_with_headers else 0


class UtilizationLayout(BaseLayout):
    BY_PROCESS = 'by Process'
    BY_REMOTE_ADDRESS = 'by Remote Address'
    BY_LOCAL_ADDRESS = 'by Local Address'

    def __init__(self, stdscr, render_opts: RenderOpts, header_content: str = None):
        super().__init__(stdscr, render_opts)
        self._stdscr.clear()
        scr_size = ScreenSize()

        self._header = Window(
            self._stdscr,
            WindowSize(1, scr_size.w, 0, 0),
            self._opts.skin,
            title=header_content,
            border=False
        )

        self._main = Window(
            self._stdscr, WindowSize(scr_size.h - 1, scr_size.w, 1, 0), self._opts.skin, border=False
        )
        self._by_proc_name = Window(
            self._stdscr,
            WindowSize(scr_size.half_h - 1, scr_size.half_w, 1, 0),
            self._opts.skin,
            title=self.BY_PROCESS
        )
        self._by_remote_addr = Window(
            self._main.curses_win,
            WindowSize(scr_size.half_h - 1, scr_size.half_w + 1, 1, scr_size.half_w),
            self._opts.skin,
            title=self.BY_REMOTE_ADDRESS
        )
        self._by_local_addr = Window(
            self._main.curses_win,
            WindowSize(scr_size.half_h - 1, scr_size.w, scr_size.half_h, 0),
            self._opts.skin,
            title=self.BY_LOCAL_ADDRESS
        )
        self._footer = Window(
            self._stdscr, WindowSize(1, scr_size.w, scr_size.h - 1, 0), self._opts.skin, border=False
        )
        self._stdscr.refresh()

    def update(
            self,
            header_content: str = None,
            by_process_with_headers: [] = None,
            by_remote_addr_with_headers: [] = None,
            by_local_addr_with_headers: [] = None,
            footer_content: str = None,
    ):
        self.update_header(header_content)
        self.update_list_window(self.BY_PROCESS, by_process_with_headers, self._by_proc_name)
        self.update_list_window(self.BY_REMOTE_ADDRESS, by_remote_addr_with_headers, self._by_remote_addr)
        self.update_list_window(self.BY_LOCAL_ADDRESS, by_local_addr_with_headers, self._by_local_addr)
        self.update_footer(footer_content)
        self._stdscr.refresh()


class ListLayout(BaseLayout):
    TOTAL = 'Connections'

    def __init__(self, stdscr, render_opts: RenderOpts, header_content: str = None, main_title: str = None):
        super().__init__(stdscr, render_opts)
        self._stdscr.clear()
        self._main_title = main_title
        scr_size = ScreenSize()

        self._header = Window(
            self._stdscr, WindowSize(1, scr_size.w, 0, 0), self._opts.skin, title=header_content, border=False
        )
        self._list_window = Window(
            self._stdscr, WindowSize(scr_size.h - 2, scr_size.w, 1, 0), self._opts.skin, title=f'{self._main_title}'
        )
        self._footer = Window(
            self._stdscr, WindowSize(1, scr_size.w, scr_size.h - 1, 0), self._opts.skin, border=False
        )
        self._stdscr.refresh()

    def update(self, header_content: str = None, list_lines_with_headers: [] = None, footer_content: str = None):
        self.update_header(header_content)
        self.update_list_window(self.TOTAL, list_lines_with_headers, self._list_window)
        self.update_footer(footer_content)
        self._stdscr.refresh()
