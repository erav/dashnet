
import errno
import os
from typing import Pattern

from proc import core as proclib_core
import psutil

from network.connection import Socket

LOCALHOST_ADDRESSES = [
    '127.0.0.1',
    '::1',
    '::ffff:127.0.0.1'
]


class TrafficByProcess:
    """
    holds a dict of number of connections by process
    """
    def __init__(self, open_sockets: 'LocalRemoteSockets'):
        self._local_sockets = open_sockets.local_sockets
        self._connections_count = {}
        self._count()
        self._as_list = []

    @property
    def as_list(self) -> [[str, int]]:
        if not self._as_list:
            for process_name, count in self._connections_count.items():
                self._as_list.append([process_name, count])
        return self._as_list

    def _count(self) -> None:
        for local_socket, process_name in self._local_sockets.items():
            try:
                count = self._connections_count[process_name]
                self._connections_count[process_name] = count + 1
            except KeyError:
                self._connections_count[process_name] = 1


class TrafficByAddress:
    def __init__(self, sockets: 'dict[Socket]'):
        self._sockets = sockets
        self._connections_count = {}
        self._count()

    def _count(self) -> None:
        """
        assumed below there will always only be count = 1,
        i.e. only one process engaging with an address
        """
        for sock, proc_name in self._sockets.items():
            try:
                process_name, count = self._connections_count[sock]
                self._connections_count[sock] = (process_name, count + 1)
            except KeyError:
                self._connections_count[sock] = (proc_name, 1)

    @property
    def as_list(self) -> [['Socket', str]]:
        as_list = []
        for local, (process_name, count) in self._connections_count.items():
            as_list.append([local, count])
        return as_list

    @property
    def sockets(self):
        return self._sockets


class AllConnections:
    def __init__(self, open_sockets: 'LocalRemoteSockets'):
        self._open_sockets = open_sockets

    @property
    def locals(self):
        return self._open_sockets.local_sockets

    @property
    def remotes(self):
        return self._open_sockets.remote_sockets

    @property
    def as_list(self) -> [[str, 'Socket', 'Socket']]:
        as_list = []
        for (local, remote), proc_name in self._open_sockets.connections.items():
            as_list.append([local, remote, proc_name])
        return as_list


class LocalRemoteSockets:
    def __init__(self):
        self._process_loader = ProcessLoader()
        self._connection_loader = ConnectionLoader()
        self._local_sockets = {}
        self._remote_sockets = {}
        self._connections = {}
        self._ip_to_dns = {}
        self._port_to_service = {}

    @property
    def local_sockets(self):
        return self._local_sockets

    @property
    def remote_sockets(self):
        return self._remote_sockets

    @property
    def connections(self):
        return self._connections

    def load(self) -> 'LocalRemoteSockets':
        self._process_loader.load()
        self._connection_loader.load()
        self._add_connections(self._connection_loader.tcps, ConnectionLoader.TCP)
        self._add_connections(self._connection_loader.udps, ConnectionLoader.UDP)
        return self

    def _add_connections(self, connections, protocol) -> None:
        for conn in connections:
            local_socket = None
            remote_socket = None
            process_name = self._process_loader.get_name_for_pid(conn.pid)
            if conn.laddr:
                local_socket = Socket(conn.laddr.ip, str(conn.laddr.port), protocol)
                self._resolve(local_socket)
                self._local_sockets[local_socket] = process_name
            if conn.raddr:
                remote_socket = Socket(conn.raddr.ip, str(conn.raddr.port), protocol)
                self._resolve(remote_socket)
                self._remote_sockets[remote_socket] = process_name
            self._connections[(local_socket, remote_socket)] = process_name

    def filter_lsockets(self, socket_filter) -> None:
        for sock in list(filter(socket_filter, self._local_sockets)):
            del self._local_sockets[sock]

    def filter_rsockets(self, socket_filter) -> None:
        for sock in list(filter(socket_filter, self._remote_sockets)):
            del self._remote_sockets[sock]

    def filter_by_regex(self, re_pattern: Pattern[str]):
        for (lsock, rsock), process_name in list(self._connections.items()):
            # if self._match(re_pattern, lsock, process_name) or self._match(re_pattern, rsock, process_name):
            if self._match_line(re_pattern, lsock, rsock, process_name):
                continue
            try:
                del self._local_sockets[lsock]
            except KeyError:
                pass
            try:
                del self._remote_sockets[rsock]
            except KeyError:
                pass
            del self._connections[(lsock, rsock)]

    @staticmethod
    def _match_line(re_pattern: Pattern, lsock: Socket, rsock: Socket, process_name: str) -> bool:
        line = (
            f'{process_name} '
            f'{str(lsock)if lsock else ""} '
            f'{str(rsock)if rsock else ""}'
        )
        return bool(re_pattern.search(line))

    @staticmethod
    def _match(re_pattern: Pattern, sock: Socket, process_name: str) -> bool:
        return (
            bool(re_pattern.search(process_name)) or (
                sock and (
                    bool(re_pattern.search(sock.protocol)) or
                    bool(re_pattern.search(sock.ip)) or
                    bool(re_pattern.search(sock.hostname)) or
                    bool(re_pattern.search(sock.port)) or
                    bool(re_pattern.search(sock.service))
                )
            )
        )

    @staticmethod
    def _localhost_filter(_socket) -> bool:
        return _socket.ip in LOCALHOST_ADDRESSES

    def resolve(self):
        for local in self._local_sockets:
            self._resolve(local)
        for remote in self._remote_sockets:
            self._resolve(remote)

    def _resolve(self, _socket) -> None:
        try:
            _socket.hostname = self._ip_to_dns[_socket.ip]
        except KeyError:
            _socket.resolve_dns()
            self._ip_to_dns[_socket.ip] = _socket.hostname
        try:
            _socket.service = self._port_to_service[_socket.port]
        except KeyError:
            _socket.resolve_service()
            self._port_to_service[_socket.port] = _socket.service


class ConnectionLoader:
    TCP = 'tcp'
    UDP = 'udp'
    CLOSING_CONNECTION_STATES = ['FIN_WAIT1', 'FIN_WAIT2', 'TIME_WAIT']

    def __init__(self):
        self._connection_filter = lambda sconn: sconn.status.upper() not in self.CLOSING_CONNECTION_STATES
        self._tcps = {}
        self._udps = {}

    def load(self):
        self._tcps = {}
        self._udps = {}
        self._tcps = self._load(self.TCP)
        self._udps = self._load(self.UDP)
        return self

    @property
    def tcps(self):
        return self._tcps

    @property
    def udps(self):
        return self._udps

    def _load(self, protocol):
        net_conns = psutil.net_connections(protocol)
        return net_conns if not self._connection_filter else list(filter(self._connection_filter, net_conns))


class ProcessLoader:

    UNKNOWN = '<UNKNOWN>'

    def __init__(self):
        self._processes = []
        self._pid_to_procname = {}

    def load(self):
        self._processes = []
        self._pid_to_procname = {}
        self._find()
        self._map_pid_to_proc_name()
        return self

    @property
    def pids(self) -> list:
        return [p.pid for p in self._processes]

    def get_name_for_pid(self, pid) -> str:
        try:
            return self._pid_to_procname[pid] if pid else self.UNKNOWN
        except KeyError:
            return '_NOT_FOUND_'

    def _find(self):
        self._processes = list(proclib_core.find_processes())

    def _map_pid_to_proc_name(self):
        for p in self._processes:
            if p.comm == 'java':
                self._pid_to_procname[p.pid] = f'{p.comm}:{p.command_line[-1]}'
            elif p.comm == 'python3.9':
                self._pid_to_procname[p.pid] = f'{p.comm}:{p.command_line[1][:12]}'
            else:
                self._pid_to_procname[p.pid] = p.comm


class InodeLoader:
    @staticmethod
    def get_inodes_by_pid(self, process_pids):
        inodes_by_pid = {}
        for pid in process_pids:
            inodes = self._get_all_inodes(pid)
            for item in inodes.items():
                inode = item[0]
                inodes_by_pid[inode] = pid
        return inodes_by_pid

    @staticmethod
    def _get_all_inodes(pid):
        inodes = dict()
        folder = f'/proc/{pid}/fd'
        for fd in os.listdir(folder):
            try:
                inode = os.readlink(f'{folder}/{fd}')
                if inode.startswith('socket:['):
                    # the process is using a socket
                    inode = inode[8:][:-1]
                    pid_list = inodes.setdefault(inode, [])
                    pid_list.append((pid, int(fd)))
            except OSError as err:
                if err.errno in (errno.ENOENT, errno.ESRCH):
                    # ENOENT: file which is gone in the meantime;
                    continue
                elif err.errno == errno.EINVAL:
                    # not a link
                    continue
                else:
                    raise
        return inodes


class DeviceUsedForIp:
    def __init__(self, ip):
        self._script = f"ip route get {ip} | head -n1 | awk '{{print $5}}'"


class DeviceStats:
    def __init__(self):
        self._script = "ip -s address"
        self._inactive_device = 'NO CARRIER'
