
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
        # self._parser = argparse.ArgumentParser(prefix_chars='-+')
        # self._parser.add_argument('v', 'cycle between available views')
        # self._add_bool_arg('d', 'toggle resolve dns: IPs \\ hostnames')
        # self._add_bool_arg('s', 'toggle resolve service: numbered port \\ service name')
        # self._ns = argparse.Namespace()
        self._stdscr = stdscr
        self._views = ToggleViews('v')
        self._resolve_dns = ResolveDns('d')
        self._resolve_service = ResolveService('s')
        self._filters = [NoopFilter()]

    def handle_user_key(self, key) -> bool:
        key = key.casefold()
        handled = True
        if self.views.is_key(key):
            self.views.toggle()
        elif self.dns.is_key(key):
            self.dns.toggle()
        elif self.service.is_key(key):
            self.service.toggle()
        elif self.filter_list(key):
            key = self._stdscr.getkey().casefold()
            if self.is_filter_key(key):
                self._filters.append(FirstCharFilter(key))
            elif self.filter_list(key):
                self._filters = [NoopFilter()]
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
    def filter_list(user_key: str) -> bool:
        return user_key == '/'

    @staticmethod
    def is_filter_key(key: str):
        return not key.casefold() < 'a' and not key.casefold() > 'z' or key == '<'

    # def _add_bool_arg(self, name: str, description: str):
    #     self._parser.add_argument(
    #         name_or_flags=f'-{name}',
    #         dest=f'{name}',
    #         type=bool,
    #         default=False,
    #         required=False,
    #         description=description
    #     )

    # @property
    # def get_help(self) -> str:
    #     return self._parser.format_help()

    # @property
    # def get_toggle_views(self) -> bool:
    #     return self._ns.toggle_views

    # @property
    # def get_filter_list(self) -> str:
    #     return self._ns.filter_list
    #
    # @property
    # def get_toggle_resolve_service(self) -> bool:
    #     return self._ns.toggle_resolve_service
    #
    # @property
    # def get_toggle_resolve_dns(self) -> bool:
    #     return self._ns.toggle_resolve_dns

    # def toggle_resolve_dns(self):
    #     self.set(f'-s {not self.get_toggle_resolve_dns}')
    #
    # def toggle_resolve_service(self):
    #     self.set(f'-s {not self.get_toggle_resolve_service}')
    #
    # def set(self, args: str):
    #     args = args.split()
    #     for arg in args:
    #         if arg in ['d', 's']:
    #             curr = getattr(self._ns, arg)
    #             self._parser.parse_args(f'-{arg} {not curr}', self._ns)
    #         if arg in ['v']:
    #             self._toggle_views.toggle()