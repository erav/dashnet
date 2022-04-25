
from network.connection import SocketsFormatter, Socket
from operating_system.linux import TrafficByAddress, AllConnections, TrafficByProcess, LocalRemoteSockets

PAD = 5


class TrafficByAddressFormatter:
    def __init__(self, sockets: 'dict[Socket]', resolve_dns=False, resolve_service=False):
        self._traffic = TrafficByAddress(sockets)
        self._resolve_dns = resolve_dns
        self._resolve_service = resolve_service

    @property
    def formatted_list(self) -> [str]:
        header = TrafficByAddressHeader()
        formatter = SocketsFormatter(self._traffic.sockets, header.col_name_lengths()).format()
        longest_ip = formatter.longest_ip if not self._resolve_dns else formatter.longest_hostname
        longest_port = formatter.longest_port if not self._resolve_service else formatter.longest_service
        header_line = header.create_header(
            [longest_ip + PAD, longest_port + PAD, formatter.longest_protocol + PAD, 0]
        )
        formatted_list: [str] = [header_line]
        for sock, count in self._traffic.as_list:
            ip = formatter.padded_ip(sock.ip) if not self._resolve_dns else formatter.padded_hostname(sock.hostname)
            port = (
                formatter.padded_port(sock.port) 
                if not self._resolve_service 
                else formatter.padded_service(sock.service)
            )
            pad = ' ' * (PAD + 1)
            formatted_list.append(f'{ip}{pad}{port}{pad}{formatter.padded_protocol(sock.protocol)}{pad}{count}')
        return formatted_list


class AllConnectionsFormatter:
    def __init__(self, open_sockets: 'LocalRemoteSockets', resolve_dns=False, resolve_service=False):
        self._connections = AllConnections(open_sockets)
        self._resolve_dns = resolve_dns
        self._resolve_service = resolve_service
        self._pformatter = TrafficByProcessFormatter(open_sockets)
        self._lformatter = SocketsFormatter(open_sockets.local_sockets, TrafficByAddressHeader().col_name_lengths())
        self._rformatter = SocketsFormatter(open_sockets.remote_sockets, TrafficByAddressHeader().col_name_lengths())

    @property
    def formatted_list(self):
        self._lformatter.format()
        self._rformatter.format()
        header = AllConnectionsHeader()
        header_line = header.create_header([
            self._pformatter.longest_name + PAD,
            (self._lformatter.longest_ip if not self._resolve_dns else self._lformatter.longest_hostname) + PAD,
            (self._lformatter.longest_port if not self._resolve_service else self._lformatter.longest_service) + PAD,
            (self._rformatter.longest_ip if not self._resolve_dns else self._rformatter.longest_hostname) + PAD,
            (self._rformatter.longest_port if not self._resolve_service else self._rformatter.longest_service) + PAD,
            0
        ])
        formatted_list: [str] = [header_line]
        pad = ' ' * (PAD + 1)
        for lsock, rsock, process_name in self._connections.as_list:
            formatted_list.append(
                f'{self._pformatter.padded_name(process_name)}{pad}'
                f'{self._get_ip(lsock, self._lformatter)}{pad}'
                f'{self._get_port(lsock, self._lformatter)}{pad}'
                f'{self._get_ip(rsock, self._rformatter)}{pad}'
                f'{self._get_port(rsock, self._rformatter)}{pad}'
                f'{self._get_protocol(lsock, self._lformatter)}'
            )
        return formatted_list

    @classmethod
    def _get_protocol(cls, sock, formatter):
        return formatter.padded_protocol(sock.protocol) if sock else formatter.padded_protocol('')

    def _get_ip(self, sock, formatter):
        if self._resolve_dns:
            return formatter.padded_hostname('') if not sock else formatter.padded_hostname(sock.hostname)
        else:
            return formatter.padded_ip('') if not sock else formatter.padded_ip(sock.ip)

    def _get_port(self, sock, formatter):
        if self._resolve_service:
            return formatter.padded_service('') if not sock else formatter.padded_service(sock.service)
        else:
            return formatter.padded_port('') if not sock else formatter.padded_port(sock.port)


class TableHeaderFormatter:
    def __init__(self, column_names):
        self._col_names = column_names

    def create_header(self, col_widths: []) -> str:
        header = ''
        for col_name, width in zip(self._col_names, col_widths):
            header += col_name + ' ' * (width - len(col_name) + 1)
        return header

    def col_name_lengths(self) -> []:
        return [len(col_name) for col_name in self._col_names]


class AllConnectionsHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROCESS', 'LOCAL ADDRESS', 'PORT', 'REMOTE ADDRESS', 'PORT', 'PROTOCOL'])


class TrafficByAddressHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['ADDRESS', 'PORT', 'PROTOCOL', 'CONNECTIONS'])


class TrafficByProcessHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROCESS', 'CONNECTIONS'])


class TrafficByProcessFormatter:
    """
    holds a dict of number of connections per process
    """
    def __init__(self, open_sockets: 'LocalRemoteSockets'):
        self._traffic = TrafficByProcess(open_sockets)
        self._longest_process_name = 0
        self.format()

    def format(self):
        if self._traffic.as_list:
            self._longest_process_name = len(max([line[0] for line in self._traffic.as_list], key=len)) + PAD

    @property
    def longest_name(self):
        return self._longest_process_name

    @property
    def formatted_list(self) -> [str]:
        if self._traffic.as_list:
            header_line = TrafficByProcessHeader().create_header([self._longest_process_name, 0])
            str_list: [str] = [header_line]
            for process_name, count in self._traffic.as_list:
                str_list.append(f'{self.padded_name(process_name)} {count}')
            return str_list
        return []

    def padded_name(self, process_name) -> None:
        return process_name + ' ' * (self._longest_process_name - len(process_name))
