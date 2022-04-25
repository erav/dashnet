
import socket


class Socket:
    def __init__(
            self,
            ip: str = '<UNKNOWN>',
            port: str = '<UNKNOWN>',
            protocol: str = '<UNKNOWN>',
            hostname=None,
            service=None
    ):
        self._ip = ip
        self._port = port
        self._protocol = protocol
        self._hostname = hostname
        self._service = service

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

    @property
    def protocol(self) -> str:
        return self._protocol

    @protocol.setter
    def protocol(self, protocol: str):
        self._protocol = protocol

    def resolve_dns(self) -> None:
        if self._hostname is None:
            try:
                self.hostname = socket.gethostbyaddr(self.ip)[0]
            except OSError:
                self.hostname = self.ip

    def resolve_service(self):
        if self._service is None:
            try:
                self.service = socket.getservbyport(int(self.port))
            except OSError:
                self.service = self.port

    def __repr__(self):
        return f'{self._ip} {self._port} {self._protocol}'

    def __str__(self):
        return f'{self._ip} {self._hostname} {self._port} {self._service} {self._protocol}'

    def __lt__(self, other: 'Socket'):
        return self.ip < other.ip

    def __eq__(self, other: 'Socket'):
        return self.ip == other.ip and self.port == other.port and self.protocol == other.protocol

    def __hash__(self):
        return hash((self.ip, self.port, self.protocol))


class SocketsFormatter:
    def __init__(self, sockets: [Socket], min_lengths: [int]):
        self._sockets = sockets
        self._min_lengths = min_lengths
        self._longest_ip = 0
        self._longest_hostname = 0
        self._longest_port = 0
        self._longest_service = 0
        self._longest_protocol = 0
        self._formatted_sockets = {}

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

    @property
    def longest_protocol(self):
        return self._longest_protocol

    def format(self):
        if not self._sockets:
            return self
        self._reset()
        self._longest_ip = max(len(max([s.ip for s in self._sockets], key=len)), self._min_lengths[0])
        self._longest_hostname = max(len(max([s.hostname for s in self._sockets], key=len)), self._min_lengths[0])
        self._longest_port = max(len(max([s.port for s in self._sockets], key=len)), self._min_lengths[1])
        self._longest_service = max(len(max([s.service for s in self._sockets], key=len)), self._min_lengths[1])
        self._longest_protocol = max(len(max([s.protocol for s in self._sockets], key=len)), self._min_lengths[2])
        # for s, v in list(self._sockets.items()):
        #     new_sock = Socket(
        #         ip=s.ip + self._pad(self._longest_ip, s.ip),
        #         hostname=s.hostname + self._pad(self._longest_hostname, s.hostname),
        #         port=s.port + self._pad(self._longest_port, s.port),
        #         service=s.service + self._pad(self._longest_service, s.service),
        #         protocol=s.protocol + self._pad(self._longest_protocol, s.protocol)
        #     )
        #     self._formatted_sockets[new_sock] = v
        return self

    def padded_ip(self, ip):
        return self._padded(self._longest_ip, ip)

    def padded_hostname(self, hostname):
        return self._padded(self._longest_hostname, hostname)

    def padded_port(self, port):
        return self._padded(self._longest_port, port)

    def padded_service(self, service):
        return self._padded(self._longest_service, service)

    def padded_protocol(self, protocol):
        return self._padded(self._longest_protocol, protocol)

    @classmethod
    def _padded(cls, longest, s):
        if len(s) < longest:
            padding = ' ' * (longest - len(s))
            return s + padding
        return s

    @classmethod
    def _get_longer(cls, length, s):
        return length if len(s) < length else len(s)

    def _reset(self):
        self._longest_ip = 0
        self._longest_hostname = 0
        self._longest_port = 0
        self._longest_service = 0
        self._longest_protocol = 0
