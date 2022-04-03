

class Protocol:
    def __init__(self, str):
        self._str = str

    def __repr__(self):
        return self._str


class Tcp(Protocol):
    def __init__(self):
        super(Tcp, self).__init__("TCP")


class Udp(Protocol):
    def __init__(self):
        super(Udp, self).__init__("UDP")


class Socket:
    def __init__(self, ip, port):
        self._ip = ip if ip else ''
        self._port = str(port) if port else ''

    @property
    def ip(self):
        return self._ip

    @ip.setter
    def ip(self, ip):
        self._ip = ip

    @property
    def port(self):
        return self._port

    @port.setter
    def port(self, port):
        self._port = port

    def __repr__(self):
        return f'{self._ip}     {self._port}'


class LocalSocket(Socket):
    def __init__(self, ip, port, protocol):
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
    def protocol(self, protocol):
        self._protocol = protocol

    def __repr__(self):
        return f'{self._protocol}       {super().__repr__()}'


class LocalSocketsFormatter:
    def __init__(self):
        self._longest_ip = 0
        self._longest_port = 0
        self._longest_proto = 0

    @property
    def longest_ip(self):
        return self._longest_ip

    @property
    def longest_port(self):
        return self._longest_port

    @property
    def longest_protocol(self):
        return self._longest_proto

    def format(self, sockets):
        for s in sockets:
            longest_ip = self._get_longer(self._longest_ip, s.ip)
            longest_port = self._get_longer(self._longest_port, s.port)
            longest_proto = self._get_longer(self._longest_proto, s.protocol)
        for s in sockets:
            s.ip += self._pad(self._longest_ip, s.ip)
            s.port += self._pad(self._longest_port, s.port)
            s.protocol += self._pad(self._longest_proto, s.protocol)

    @classmethod
    def _get_longer(cls, length, s):
        return length if len(s) < length else len(s)

    @classmethod
    def _pad(cls, longest, s):
        if len(s) < longest:
            return ' ' * (longest - len(s))
        return ''


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
