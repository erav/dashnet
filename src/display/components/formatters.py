
from typing import Dict

from network.connection import Socket
from operating_system.linux import AllConnections
from operating_system.linux import LocalRemoteSockets
from operating_system.linux import TrafficByAddress
from operating_system.linux import TrafficByProcess


class TrafficByLocalAddressFormatter:
    def __init__(self, sockets: 'Dict[Socket]', resolve_dns=False, resolve_service=False):
        self._traffic = TrafficByAddress(sockets)
        self._header = TrafficByLocalAddressHeader()
        self._resolve_dns = resolve_dns
        self._resolve_service = resolve_service
        self._formatter = LocalAddressFormatter(sockets, self._header)

    @property
    def formatted_list(self) -> [str]:
        pad = 3
        formatted_list: [str] = [(self._create_header(pad))]
        for sock, count in self._traffic.as_list:
            ip = (
                self._formatter.get('hostname').padded(sock.hostname)
                if self._resolve_dns else
                self._formatter.get('ip').padded(sock.ip)
            )
            port = (
                self._formatter.get('service').padded(sock.service)
                if self._resolve_service else
                self._formatter.get('port').padded(sock.port)
            )
            protocol = self._formatter.get('protocol').padded(sock.protocol)
            formatted_list.append(
                f'{ip}{" " * pad}'
                f'{port}{" " * pad}'
                f'{protocol}{" " * pad}'
                f'{count}'
            )
        return formatted_list

    def _create_header(self, pad):
        header_line = self._header.create_header([
            self._formatter.get('hostname').longest if self._resolve_dns else self._formatter.get('ip').longest,
            self._formatter.get('service').longest if self._resolve_service else self._formatter.get('port').longest,
            self._formatter.get('protocol').longest,
            0
        ], pad)
        return header_line


class TrafficByRemoteAddressFormatter:
    def __init__(self, remotes: 'Dict[Socket]', resolve_dns=False, resolve_service=False):
        self._remotes = remotes
        self._resolve_dns = resolve_dns
        self._resolve_service = resolve_service
        self._traffic = TrafficByAddress(remotes)
        self._header = TrafficByRemoteAddressHeader()
        self._formatter = RemoteAddressFormatter(remotes, self._header)

    @property
    def formatted_list(self) -> [str]:
        pad = 3
        formatted_list: [str] = [self._create_header(pad)]
        for sock, count in self._traffic.as_list:
            pi = self._remotes[sock]
            ip = (
                self._formatter.get('hostname').padded(sock.hostname)
                if self._resolve_dns else
                self._formatter.get('ip').padded(sock.ip)
            )
            port = (
                self._formatter.get('service').padded(sock.service)
                if self._resolve_service else
                self._formatter.get('port').padded(sock.port)
            )
            protocol = self._formatter.get('protocol').padded(sock.protocol)
            formatted_list.append(
                f'{self._formatter.get("iface").padded(pi.iface)}{" " * pad}'
                f'{ip}{" " * pad}'
                f'{port}{" " * pad}'
                f'{protocol}{" " * pad}'
                f'{count}'
            )
        return formatted_list

    def _create_header(self, pad):
        return self._header.create_header([
            self._formatter.get('iface').longest,
            self._formatter.get('hostname').longest if self._resolve_dns else self._formatter.get('ip').longest,
            self._formatter.get('service').longest if self._resolve_service else self._formatter.get('port').longest,
            self._formatter.get('protocol').longest,
            0
        ], pad)


class AllConnectionsFormatter:
    def __init__(self, sockets: 'LocalRemoteSockets', resolve_dns=False, resolve_service=False):
        self._connections = AllConnections(sockets)
        self._resolve_dns = resolve_dns
        self._resolve_service = resolve_service
        self._header = AllConnectionsHeader()
        self._pformatter = TrafficByProcessFormatter(sockets, self._header)
        self._rformatter = RemoteAddressFormatter(sockets.remotes, TrafficByRemoteAddressHeader())
        self._lformatter = LocalAddressFormatter(sockets.locals, TrafficByLocalAddressHeader())

    @property
    def formatted_list(self):
        pad = 3
        header_line = self._create_header(pad)
        formatted_list: [str] = [header_line]
        for lsock, rsock, pi in self._connections.as_list:
            iface = pi.iface if pi.iface else ''
            formatted_list.append(
                f'{self._pformatter.get("process").padded(pi.process)}{" " * pad}'
                f'{self._get_ip(lsock, self._lformatter)}{" " * pad}'
                f'{self._get_port(lsock, self._lformatter)}{" " * pad}'
                f'{self._get_ip(rsock, self._rformatter)}{" " * pad}'
                f'{self._get_port(rsock, self._rformatter)}{" " * pad}'
                f'{self._get_protocol(lsock, self._lformatter)}{" " * pad}'
                f'{self._rformatter.get("iface").padded(iface)}'
            )
        return formatted_list

    def _create_header(self, pad):
        header_line = self._header.create_header([
            self._pformatter.get('process').longest,
            self._get_longest_ip(self._lformatter),
            self._get_longest_service(self._lformatter),
            self._get_longest_ip(self._rformatter),
            self._get_longest_service(self._rformatter),
            self._rformatter.get('protocol').longest,
            0
        ], pad)
        return header_line

    def _get_longest_service(self, formatter):
        return formatter.get('port').longest if not self._resolve_service else formatter.get('service').longest

    def _get_longest_ip(self, formatter):
        return formatter.get('ip').longest if not self._resolve_dns else formatter.get('hostname').longest

    @classmethod
    def _get_protocol(cls, sock, formatter):
        pf = formatter.get('protocol')
        return pf.padded(sock.protocol) if sock else pf.padded('')

    def _get_ip(self, sock, formatter):
        hf = formatter.get('hostname')
        ipf = formatter.get('ip')
        if self._resolve_dns:
            return hf.padded('') if not sock else hf.padded(sock.hostname)
        else:
            return ipf.padded('') if not sock else ipf.padded(sock.ip)

    def _get_port(self, sock, formatter):
        sf = formatter.get('service')
        pf = formatter.get('port')
        if self._resolve_service:
            return sf.padded('') if not sock else sf.padded(sock.service)
        else:
            return pf.padded('') if not sock else pf.padded(sock.port)


class TableHeaderFormatter:
    def __init__(self, column_names):
        self._col_names = column_names

    def create_header(self, col_widths: [], pad: int = 1) -> str:
        header = ''
        for col_name, width in zip(self._col_names, col_widths):
            diff = width - len(col_name) + pad
            header += col_name + ' ' * (diff if diff > 0 else pad)
        return header

    def col_len(self, column_name):
        return next(len(col_name) for col_name in self._col_names if col_name == column_name)


class AllConnectionsHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROCESS', 'LOCAL ADDRESS', 'PORT', 'REMOTE ADDRESS', 'PORT', 'PROTOCOL', 'INTERFACE'])


class TrafficByLocalAddressHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['LOCAL ADDRESS', 'PORT', 'PROTOCOL', 'CONNECTIONS'])


class TrafficByRemoteAddressHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['INTERFACE', 'REMOTE ADDRESS', 'PORT', 'PROTOCOL', 'CONNECTIONS'])


class TrafficByProcessHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROCESS', 'CONNECTIONS'])


class TrafficByProcessFormatter:
    """
    holds a dict of number of connections per process
    """
    def __init__(self, open_sockets: 'LocalRemoteSockets', header: TableHeaderFormatter):
        self._traffic = TrafficByProcess(open_sockets)
        self._header = header
        self._formatters = {}
        self.format()

    def get(self, formatter_name: str) -> 'AttrFormatter':
        return self._formatters[formatter_name]

    def format(self):
        if self._traffic.as_list and not self._formatters:
            self._formatters = {
                'process': AttrFormatter(
                    [line[0] for line in self._traffic.as_list], self._header.col_len('PROCESS')
                ).format(),
            }

    @property
    def formatted_list(self) -> [str]:
        pad = 9
        self.format()
        if self._traffic.as_list:
            header_line = TrafficByProcessHeader().create_header([self._formatters.get('process').longest, 0], pad)
            str_list: [str] = [header_line]
            for process_name, count in self._traffic.as_list:
                str_list.append(
                    f'{self._formatters.get("process").padded(process_name)}{" " * pad}'
                    f'{count}'
                )
            return str_list
        return []


class AttrFormatter:
    def __init__(self, attr_values: [str], min_len):
        self._attr_values = attr_values
        self._min_len = min_len
        self._longest = 0

    @property
    def longest(self):
        return self._longest

    def format(self):
        self._reset()
        longest_value = len(max(self._attr_values, key=len)) if self._attr_values else 0
        self._longest = max(longest_value, self._min_len)
        return self

    def padded(self, attr):
        return self._padded(self._longest, attr)

    @classmethod
    def _padded(cls, longest, s):
        if len(s) < longest:
            padding = ' ' * (longest - len(s))
            return s + padding
        return s

    def _reset(self):
        self._longest = 0


class LocalAddressFormatter:
    def __init__(self, sockets: 'Dict[Socket]', header: TableHeaderFormatter):
        self._formatters = {
            'ip': AttrFormatter([s.ip for s in sockets], header.col_len('LOCAL ADDRESS')).format(),
            'hostname': AttrFormatter([s.hostname for s in sockets], header.col_len('LOCAL ADDRESS')).format(),
            'port': AttrFormatter([s.port for s in sockets], header.col_len('PORT')).format(),
            'service': AttrFormatter([s.service for s in sockets], header.col_len('PORT')).format(),
            'protocol': AttrFormatter([s.protocol for s in sockets], header.col_len('PROTOCOL')).format(),
        }

    def get(self, formatter_name: str) -> AttrFormatter:
        return self._formatters[formatter_name]


class RemoteAddressFormatter:
    def __init__(self, sockets: 'Dict[Socket]', header: TableHeaderFormatter):
        self._formatters = {
            'iface': AttrFormatter(
                [pi.iface for pi in sockets.values() if pi.iface], header.col_len('INTERFACE')
            ).format(),
            'ip': AttrFormatter([s.ip for s in sockets], header.col_len('REMOTE ADDRESS')).format(),
            'hostname': AttrFormatter(
                [s.hostname for s in sockets], header.col_len('REMOTE ADDRESS')
            ).format(),
            'port': AttrFormatter([s.port for s in sockets], header.col_len('PORT')).format(),
            'service': AttrFormatter([s.service for s in sockets], header.col_len('PORT')).format(),
            'protocol': AttrFormatter([s.protocol for s in sockets], header.col_len('PROTOCOL')).format(),
        }

    def get(self, formatter_name: str) -> AttrFormatter:
        return self._formatters[formatter_name]
