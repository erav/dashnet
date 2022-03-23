import ipaddress
import socket

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
        self._ip = ip
        self._port = port


class LocalSocket(Socket):
    def __init__(self, ip, port, protocol):
        """
        :param ip: ipaddress.IpAddress
        :param port: int
        :param protocol: Protocol
        """
        super(LocalSocket, self).__init__(ip, port)
        self. protocol = protocol


class Connection:
    def __init__(self, remote_socket, local_ip, local_port, local_protocol):
        """
        :param: remote_socket: Socket
        :param: local_socket: LocalSocket
        """
        self._remote_socket = remote_socket
        self._local_socket = LocalSocket(local_ip, local_port, local_protocol)

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
