
import socket


class Protocol:
    def __init__(self, name: str):
        self._str = name

    def __repr__(self):
        return self._str


class Tcp(Protocol):
    def __init__(self):
        super(Tcp, self).__init__('TCP')


class Udp(Protocol):
    def __init__(self):
        super(Udp, self).__init__('UDP')


class Socket:
    def __init__(self, ip: str, port: str):
        self._ip = ip if ip else ''
        self._hostname = None
        self._port = str(port) if port else ''
        self._service = None

    @property
    def ip(self) -> str:
        return self._ip

    @ip.setter
    def ip(self, ip: str):
        self._ip = ip

    @property
    def hostname(self) -> str:
        return self._hostname

    @hostname.setter
    def hostname(self, hostname: str):
        self._hostname = hostname

    @property
    def port(self) -> str:
        return self._port

    @port.setter
    def port(self, port: str):
        self._port = port

    @property
    def service(self) -> str:
        return self._service

    @service.setter
    def service(self, service: str):
        self._service = service

    def resolve_dns(self) -> None:
        if self._hostname is None:
            try:
                self.hostname = socket.gethostbyaddr(self.ip)[0]
            except Exception:
                self.hostname = self.ip

    def resolve_service(self):
        if self._service is None:
            try:
                self.service = socket.getservbyport(int(self.port))
            except Exception:
                self.service = self.port

    def __repr__(self):
        return f'{self._ip} {self._port}'

    def __lt__(self, other: 'Socket'):
        return self.ip < other.ip

    def __eq__(self, other: 'Socket'):
        return self.ip == other.ip and self.port == other.port

    def __hash__(self):
        return hash((self.ip, self.port))


class SocketsFormatter:
    def __init__(self, sockets: [Socket], min_lengths: [int]):
        self._sockets = sockets
        self._min_lengths = min_lengths
        self._longest_ip = 0
        self._longest_hostname = 0
        self._longest_port = 0
        self._longest_service = 0

    @property
    def longest_ip(self):
        return self._longest_ip

    @property
    def longest_hostname(self):
        return self._longest_hostname

    @property
    def longest_service(self):
        return self._longest_service

    @property
    def longest_port(self):
        return self._longest_port

    def format(self):
        self._reset()
        self._longest_ip = max(len(max([s.ip for s in self._sockets], key=len)), self._min_lengths[0])
        self._longest_hostname = max(len(max([s.hostname for s in self._sockets], key=len)), self._min_lengths[0])
        self._longest_port = max(len(max([s.port for s in self._sockets], key=len)), self._min_lengths[1])
        self._longest_service = max(len(max([s.service for s in self._sockets], key=len)), self._min_lengths[1])
        for s in self._sockets:
            s.ip += self._pad(self._longest_ip, s.ip)
            s.hostname += self._pad(self._longest_hostname, s.hostname)
            s.port += self._pad(self._longest_port, s.port)
            s.service += self._pad(self._longest_service, s.service)
        return self

    @classmethod
    def _get_longer(cls, length, s):
        return length if len(s) < length else len(s)

    @classmethod
    def _pad(cls, longest, s):
        if len(s) < longest:
            return ' ' * (longest - len(s))
        return ''

    def _reset(self):
        self._longest_ip = 0
        self._longest_hostname = 0
        self._longest_port = 0
        self._longest_service = 0


class LocalSocket(Socket):
    def __init__(self, ip: str, port: str, protocol: str):
        """
        :param ip: ipaddress.IpAddress
        :param port: int
        :param protocol: Protocol
        """
        super().__init__(ip, port)
        self._protocol = protocol

    @property
    def protocol(self):
        return self._protocol

    @protocol.setter
    def protocol(self, protocol: str):
        self._protocol = protocol

    def __repr__(self):
        return f'{self._protocol} {super().__repr__()}'

    def __eq__(self, other: 'LocalSocket'):
        return super().__eq__(other) and self.protocol == other.protocol

    def __hash__(self):
        return hash((super().__hash__(), self.protocol))


class LocalSocketsFormatter(SocketsFormatter):
    def __init__(self, sockets: [LocalSocket], min_lengths: list):
        super().__init__(sockets, min_lengths[:4])
        self._longest_proto = 0

    @property
    def longest_protocol(self):
        return self._longest_proto

    def format(self):
        self._reset()
        super().format()
        for s in self._sockets:
            self._longest_proto = self._get_longer(self._longest_proto, s.protocol)
        self._longest_proto = max(self._longest_proto,  self._min_lengths[4])
        for s in self._sockets:
            s.protocol += self._pad(self._longest_proto, s.protocol)
        return self

    @classmethod
    def _get_longer(cls, length, s):
        return length if len(s) < length else len(s)

    @classmethod
    def _pad(cls, longest, s):
        if len(s) < longest:
            return ' ' * (longest - len(s))
        return ''

    def _reset(self):
        super()._reset()
        self._longest_proto = 0


class Connection:
    def __init__(self, remote_socket_tuple, local_ip, local_port, local_protocol):
        """
        :param: remote_socket: Socket
        :param: local_socket: LocalSocket
        """
        self._remote_socket = remote_socket_tuple
        self._local_socket = LocalSocket(local_ip, local_port, local_protocol)

    def __repr__(self):
        return f'remote:{self._remote_socket}, local:{self._local_socket}'

    @property
    def remote_socket(self):
        return self._remote_socket


def display_ip_or_host(ip, ip_to_host):
    """
    :param: ip: ipaddress.Ipaddress
    :param: ip_to_host: map<ipaddress.Ipaddress, str>
    :returns: str
    """
    if ip_to_host[ip]:
        return ip_to_host[ip]
    return str(ip)


def display_connection_string(connection, ip_to_host, iface_name):
    """
    :param: connection: &Connection
    :param: ip_to_host: map<ipaddress.IpAddress, str>
    :param: iface_name: str
    :returns: str
    """
    return (
        f'<{iface_name}>'
        f':{connection.local_socket.port}'
        f' => '
        f'{display_ip_or_host(connection.remote_socket.ip, ip_to_host)}'
        f':{connection.remote_socket.port} '
        f'({connection.local_socket.protocol})"'
    )
