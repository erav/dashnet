
import curses
import re
import time
from typing import Pattern

from common.utils import ToggleStates
from .skin import DefaultSkin, RedSkin


class ResolveDns(ToggleStates):
    _DNS = 0
    _IP = 1

    def __init__(self, key: str):
        super().__init__(len([self._DNS, self._IP]))
        self._key = key

    @property
    def active(self) -> int:
        return self._DNS if self.is_active(self._DNS) else self._IP

    @property
    def resolve(self) -> bool:
        return self.active == self._DNS

    def is_key(self, key: str) -> bool:
        return self._key == key


class ResolveService(ToggleStates):
    _SERVICE = 0
    _PORT = 1

    def __init__(self, key: str):
        super().__init__(len([self._SERVICE, self._PORT]))
        self._key = key

    @property
    def active(self) -> int:
        return self._SERVICE if self.is_active(self._SERVICE) else self._PORT

    @property
    def resolve(self) -> bool:
        return self.active == self._SERVICE

    def is_key(self, key: str):
        return self._key == key


class ToggleViews(ToggleStates):
    _UTILIZATION = 0
    _LIST = 1

    def __init__(self, key: str):
        super().__init__(len([self._UTILIZATION, self._LIST]))
        self._key = key

    @property
    def show_utilization(self) -> bool:
        return self.is_active(self._UTILIZATION)

    @property
    def show_list(self) -> bool:
        return self.is_active(self._LIST)

    def is_key(self, key: str) -> bool:
        return self._key == key


class ToggleSkin(ToggleStates):
    def __init__(self, skins: [DefaultSkin]):
        super().__init__(len(skins))
        self._skins = skins

    def active(self) -> DefaultSkin:
        return self._skins[super().active]


class ToggleRegexFilter(ToggleStates):
    """
    If a string of the form '?[^?]+?' is specified toggle to 'apply' state
    If '??' is specified toggle to undo state
    """
    _NOOP = 0
    _UNAPPLY = 1
    _APPLY = 2

    def __init__(self, key: chr):
        super().__init__(len([self._NOOP, self._UNAPPLY, self._APPLY]))
        self._key = key
        self._regex = ''
        self._pattern = None

    @property
    def pattern(self) -> Pattern:
        return self._pattern

    def apply(self) -> bool:
        return self.is_active(self._APPLY)

    def unapply(self) -> bool:
        return self.is_active(self._UNAPPLY)

    def noop(self) -> bool:
        return self.is_active(self._NOOP)

    def is_key(self, key: chr) -> bool:
        return key == self._key

    def handle_regex(self, regex: str) -> None:
        if self._regex == regex:
            self.toggle_to(self._NOOP)
        elif regex == '':
            self._regex = ''
            self.toggle_to(self._UNAPPLY)
        else:
            self._regex = regex
            self._pattern = re.compile(self._regex)
            self.toggle_to(self._APPLY)

    def reset(self) -> None:
        self._regex = ''
        self._pattern = None
        self.toggle_to(self._NOOP)


class RenderOpts:

    PAUSE = ' '

    def __init__(self, stdscr, skins: [DefaultSkin]):
        self._stdscr = stdscr
        self._skin = ToggleSkin(skins)
        self._views = ToggleViews('v')
        self._resolve_dns = ResolveDns('d')
        self._resolve_service = ResolveService('s')
        self._pause = ToggleStates(2)
        self._process_filter = ToggleRegexFilter('/')

    def handle_user_key(self, key: str) -> bool:
        key = key.casefold()
        if self.views.is_key(key):
            self.views.toggle()
        elif self.dns.is_key(key):
            self.dns.toggle()
        elif self.service.is_key(key):
            self.service.toggle()
        elif key == self.PAUSE:
            self._pause.toggle()
            self._skin.toggle()
        elif self._process_filter.is_key(key):
            self._process_filter.reset()
            regex = self.get_user_string('filter regex (<ENTER> to clear):')
            try:
                self._process_filter.handle_regex(regex)
            except Exception as e:
                self._post_regex_error(e)
                time.sleep(4)
        else:
            return False
        return True

    def get_user_string(self, msg: str) -> str:
        _, max_x = self._stdscr.getmaxyx()
        pos = int(max_x / 3)
        self._stdscr.addstr(0, pos - len(msg) - 1, msg)
        self._stdscr.refresh()
        curses.echo()
        regex = self._stdscr.getstr(0, pos, 99)
        curses.noecho()
        return regex.decode('utf-8')

    def _post_regex_error(self, e: Exception) -> None:
        _, max_x = self._stdscr.getmaxyx()
        pos = int(max_x / 2)
        self._stdscr.addstr(0, pos, f'bad regex: {e.args[0]}', RedSkin().red)
        self._stdscr.refresh()

    @property
    def skin(self) -> DefaultSkin:
        return self._skin.active()

    @property
    def views(self) -> ToggleViews:
        return self._views

    @property
    def dns(self) -> ResolveDns:
        return self._resolve_dns

    @property
    def service(self) -> ResolveService:
        return self._resolve_service

    @property
    def pause(self) -> bool:
        return self._pause.is_active(1)

    @property
    def process_filter(self):
        return self._process_filter
