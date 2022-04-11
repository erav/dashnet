
import curses
import locale
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
    def __init__(self, curses_parent, win_size, skin, title=None, border=True, content=None):
        self._parent = curses_parent
        self._size = win_size
        self._skin = skin
        self._title = title
        self._border = border
        self._content = content
        self._curses_window = self._parent.subwin(self._size.h, self._size.w, self._size.y, self._size.x)
        if border:
            self._curses_window.border(0, 0, 0, 0, 0, 0, 0, 0)
        if title:
            self._curses_window.addstr(0, 1, self._title, skin.default_title_attr)
        if content:
            y = 0 if self._size.h == 1 else 1
            x = 1
            self._curses_window.addstr(y, x, content)
        self._curses_window.refresh()

    def add_header(self, header):
        self.curses_win.addstr(1, 2, header, self._skin.default_title_attr)

    def update(self, content_lines, attr=0):
        y, x = self.curses_win.getmaxyx()
        if content_lines:
            if y == 1 and len(content_lines) == 1:
                self.curses_win.addstr(0, 1, f' {content_lines[0]} ', attr)
            else:
                i = 2
                j = 0
                while i <= y - 2 and j < len(content_lines):
                    self.curses_win.addstr(i, 2, str(content_lines[j]), attr)
                    i += 1
                    j += 1
            self.curses_win.refresh()

    @property
    def curses_win(self):
        return self._curses_window


class BaseLayout:
    def __init__(self, stdscr, skin):
        self._stdscr = stdscr
        # self._stdscr.bkgd(skin.bg_color)
        self._header = None
        self._footer = None


class UtilizationLayout(BaseLayout):
    def __init__(self, stdscr, skin):
        super().__init__(stdscr, skin)
        self._skin = skin
        self._stdscr.clear()
        scr_size = ScreenSize()

        self._header = Window(self._stdscr, WindowSize(1, scr_size.w, 0, 0), skin, border=False)

        self._main = Window(self._stdscr, WindowSize(scr_size.h - 1, scr_size.w, 1, 0), skin, border=False)
        self._by_proc_name = Window(
            self._stdscr,
            WindowSize(scr_size.half_h - 1, scr_size.half_w, 1, 0),
            skin,
            title=' Utilization by process: '
        )
        self._by_remote_addr = Window(
            self._main.curses_win,
            WindowSize(scr_size.half_h - 1, scr_size.half_w, 1, scr_size.half_w),
            skin,
            title=' Utilization by remote address '
        )
        self._by_conn = Window(
            self._main.curses_win,
            WindowSize(scr_size.half_h - 1, scr_size.w - 1, scr_size.half_h, 0),
            skin,
            title=' Utilization by connection '
        )
        self._footer = Window(self._stdscr, WindowSize(1, scr_size.w, scr_size.h - 1, 0), skin, border=False)
        self._stdscr.refresh()

    def update(
            self,
            render_opts: 'RenderOpts',
            process_utilization_with_headers=None,
            remote_addr_utilization_with_headers=None,
            connections_utilization=None,
            footer_content=None,
    ):
        header_content = (f'Total processes: {len(process_utilization_with_headers) - 1}',)
        self._header.update(header_content, attr=self._skin.default_title_attr)
        self._update_by_process_name(process_utilization_with_headers, render_opts)
        self._update_by_remote_addr(remote_addr_utilization_with_headers, render_opts)
        self._by_conn.update(connections_utilization)
        self._footer.update(footer_content, attr=self._skin.default_title_attr)

    def _update_by_process_name(self, utilization_with_headers, render_opts):
        self._by_proc_name.curses_win.addstr(
            1, 2, utilization_with_headers[0], self._skin.default_title_attr
        )
        utilization = utilization_with_headers[1:]
        for f in render_opts.filters:
            utilization = f.filter(utilization)
        self._by_proc_name.update(sorted(utilization))

    def _update_by_remote_addr(self, utilization_with_headers, render_opts):
        self._by_remote_addr.curses_win.addstr(
            1, 2, utilization_with_headers[0], self._skin.default_title_attr
        )
        utilization = utilization_with_headers[1:]
        for f in render_opts.filters:
            utilization = f.filter(utilization)
        self._by_remote_addr.update(sorted(utilization))


class ListLayout(BaseLayout):
    def __init__(self, stdscr, skin, title):
        super().__init__(stdscr, skin)
        self._stdscr.clear()
        self._title = title
        self._skin = skin
        scr_size = ScreenSize()

        self._header = Window(self._stdscr, WindowSize(1, scr_size.w, 0, 0), skin, border=False)
        self._list_window = Window(
            self._stdscr,
            WindowSize(scr_size.h - 3, scr_size.w, 2, 0),
            skin,
            title=f' {self._title} '
        )
        self._footer = Window(self._stdscr, WindowSize(1, scr_size.w, scr_size.h - 1, 0), skin, border=False)
        self._stdscr.refresh()

    def update(self, render_opts, list_lines_with_headers=None, footer_content=None):
        header_content = (f'Total: {len(list_lines_with_headers) - 1}',)
        self._header.update(header_content, attr=self._skin.default_title_attr)
        self._list_window.add_header(list_lines_with_headers[0])
        list_lines = list_lines_with_headers[1:]
        for f in render_opts.filters:
            list_lines = f.filter(list_lines)
        self._list_window.update(sorted(list_lines))
        self._footer.update(footer_content, attr=self._skin.default_title_attr)
