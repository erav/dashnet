
import socket


class ProcessIface:
    def __init__(self, process_name, iface_name=None):
        self._process = process_name
        self._iface = iface_name

    @property
    def process(self):
        return self._process

    @property
    def iface(self):
        return self._iface

    @iface.setter
    def iface(self, iface_name):
        self._iface = iface_name


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
