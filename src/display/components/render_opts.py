
from common.utils import ToggleStates
from common.utils import FirstCharFilter, NoopFilter


class ResolveDns(ToggleStates):
    DNS = 0
    IP = 1

    def __init__(self, key: str):
        super().__init__(len([self.DNS, self.IP]))
        self._key = key

    @property
    def active(self) -> int:
        return self.DNS if self.is_active(self.DNS) else self.IP

    @property
    def resolve(self) -> bool:
        return self.active == self.DNS

    def is_key(self, key) -> bool:
        return self._key == key


class ResolveService(ToggleStates):
    SERVICE = 0
    PORT = 1

    def __init__(self, key):
        super().__init__(len([self.SERVICE, self.PORT]))
        self._key = key

    @property
    def active(self) -> int:
        return self.SERVICE if self.is_active(self.SERVICE) else self.PORT

    @property
    def resolve(self) -> bool:
        return self.active == self.SERVICE

    def is_key(self, key: str):
        return self._key == key


class ToggleViews(ToggleStates):
    UTILIZATION = 0
    LIST = 1

    def __init__(self, key: str):
        super().__init__(len([self.UTILIZATION, self.LIST]))
        self._key = key

    @property
    def show_utilization(self) -> bool:
        return self.is_active(self.UTILIZATION)

    @property
    def show_list(self) -> bool:
        return self.is_active(self.LIST)

    def is_key(self, key: str) -> bool:
        return self._key == key


class RenderOpts:
    def __init__(self, stdscr):
        self._stdscr = stdscr
        self._views = ToggleViews('v')
        self._resolve_dns = ResolveDns('d')
        self._resolve_service = ResolveService('s')
        self._filters = []

    def handle_user_key(self, key) -> bool:
        key = key.casefold()
        handled = True
        if self.views.is_key(key):
            self.views.toggle()
        elif self.dns.is_key(key):
            self.dns.toggle()
        elif self.service.is_key(key):
            self.service.toggle()
        elif self.add_filter(key):
            key = self._stdscr.getkey().casefold()
            if self.is_filter_key(key):
                self._filters.append(FirstCharFilter(key))
            elif self.remove_filter(key):
                self._filters = []
        else:
            handled = False
        return handled

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
    def filters(self) -> []:
        return self._filters

    @staticmethod
    def add_filter(user_key: str) -> bool:
        return user_key == '/'

    @staticmethod
    def remove_filter(user_key: str) -> bool:
        return RenderOpts.add_filter(user_key)

    @staticmethod
    def is_filter_key(key: str):
        return not key.casefold() < 'a' and not key.casefold() > 'z' or key == '<'
