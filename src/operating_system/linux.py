
import errno
import os
from proc import core as proclib_core
import psutil

from network.connection import LocalSocket
from network.connection import Socket, SocketsFormatter

LOCALHOST_ADDRESSES = [
    '127.0.0.1',
    '::1',
    '::ffff:127.0.0.1'
]

PADDING = 5


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


class TrafficByProcessFormatter:
    """
    holds a dict of number of connections by process
    """
    def __init__(self, open_sockets: 'LocalRemoteSockets'):
        self._traffic = TrafficByProcess(open_sockets)
        self._longest_process_name = 0

    @property
    def formatted_list(self) -> [str]:
        self._longest_process_name = len(max([line[0] for line in self._traffic.as_list], key=len)) + PADDING
        self._align_process_names()
        header_line = TrafficByProcessHeader().create_header([self._longest_process_name, 0])
        str_list: [str] = [header_line]
        for line in self._traffic.as_list:
            str_list.append(f'{line[0]} {line[1]}')
        return str_list

    def _align_process_names(self) -> None:
        for line in self._traffic.as_list:
            line[0] = line[0] + ' ' * (self._longest_process_name - len(line[0]))


class TrafficByRemoteAddress:
    """
    holds a dict of which remote address is contacted by which process
    """
    def __init__(self, open_sockets: 'LocalRemoteSockets'):
        self._remote_sockets = open_sockets.remote_sockets
        self._connections_count = {}
        self._count()

    def _count(self) -> None:
        """
        assumed below there will always only be count = 1,
        i.e. only one process engaging with a remote address
        :return:
        """
        for remote, proc_name in self._remote_sockets.items():
            try:
                process_name, count = self._connections_count[remote]
                self._connections_count[remote] = (process_name, count + 1)
            except KeyError:
                self._connections_count[remote] = (proc_name, 1)

    @property
    def as_list(self) -> [['Socket', str]]:
        as_list = []
        for remote, (process_name, count) in self._connections_count.items():
            as_list.append([remote, count])
        return as_list

    @property
    def remotes(self):
        return self._remote_sockets


class TrafficByRemoteAddressFormatter:
    def __init__(self, open_sockets: 'LocalRemoteSockets', resolve_dns=False, resolve_service=False):
        self._traffic = TrafficByRemoteAddress(open_sockets)
        self._resolve_dns = resolve_dns
        self._resolve_service = resolve_service
        self._longest_remote = 0

    @property
    def formatted_list(self) -> [str]:
        header = TrafficByRemoteAddressHeader()
        formatter = SocketsFormatter(self._traffic.remotes, header.col_name_lengths()).format()
        longest_ip = formatter.longest_ip if not self._resolve_dns else formatter.longest_hostname
        longest_port = formatter.longest_port if not self._resolve_service else formatter.longest_service
        header_line = header.create_header([longest_ip + 3, longest_port + 3, 0])
        formatted_list: [str] = [header_line]
        for line in self._traffic.as_list:
            ip = line[0].ip if not self._resolve_dns else line[0].hostname
            port = line[0].port if not self._resolve_service else line[0].service
            formatted_list.append(f'{ip}    {port}    {line[1]}')
        return formatted_list


class AllConnections:
    def __init__(self, open_sockets: 'LocalRemoteSockets'):
        self._connections = open_sockets.connections

    @property
    def as_list(self) -> [[str, 'LocalSocket', 'Socket']]:
        as_list = []
        for (local, remote), proc_name in self._connections.items():
            as_list.append([local, '<=>', remote, proc_name])
        return as_list


class AllConnectionsFormatter:
    def __init__(self, open_sockets: 'LocalRemoteSockets', resolve_dns=False, resolve_service=False):
        self._connections = AllConnections(open_sockets)
        self._resolve_dns = resolve_dns
        self._resolve_service = resolve_service

    @property
    def formatted_list(self):
        header = AllConnectionsHeader()
        formatter = SocketsFormatter(self._connections.keys(), header.col_name_lengths()).format()
        longest_ip = formatter.longest_ip if not self._resolve_dns else formatter.longest_hostname
        longest_port = formatter.longest_port if not self._resolve_service else formatter.longest_service
        header_line = header.create_header([longest_ip, longest_port, 0])
        formatted_list: [str] = [header_line]
        for line in self._connections.as_list:
            lip = line[0].ip if not self._resolve_dns else line[0].hostname
            lport = line[0].port if not self._resolve_service else line[0].service
            rip = line[2].ip if not self._resolve_dns else line[2].hostname
            rport = line[2].port if not self._resolve_service else line[2].service
            formatted_list.append(f'{lip}    {lport}    {rip}    {rport}   {line[3]}')
        return formatted_list


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
        # self._filter_local_sockets(self._localhost_filter)
        return self

    def _add_connections(self, connections, protocol) -> None:
        for conn in connections:
            local_socket = remote_socket = None
            process_name = self._process_loader.get_name_for_pid(conn.pid)
            if conn.laddr:
                local_socket = LocalSocket(conn.laddr.ip, conn.laddr.port, protocol)
                self._resolve(local_socket)
                self._local_sockets[local_socket] = process_name
            if conn.raddr:
                remote_socket = Socket(conn.raddr[0], conn.raddr[1])
                self._resolve(remote_socket)
                self._remote_sockets[remote_socket] = process_name
            if local_socket and remote_socket:
                self._connections[(local_socket, remote_socket)] = process_name

    def _filter_local_sockets(self, socket_filter) -> None:
        for key in list(filter(socket_filter, self._local_sockets.keys())):
            del self._local_sockets[key]

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
            # self._pid_to_procname[p.pid] = p.comm if p.comm != 'java' else f'{p.comm}:{p.command_line[-1]}'


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


class ProcessByLocalAddressListFormatter(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROCESS', 'PROTOCOL', 'LOCAL ADDRESS', 'PORT', 'REMOTE ADDRESS'])


class TrafficByProcessHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROCESS', 'CONNECTIONS'])


class TrafficByRemoteAddressHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['REMOTE ADDRESS', 'PORT', 'CONNECTIONS'])


class AllConnectionsHeader(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROTOCOL', 'LOCAL ADDRESS', 'PORT', '    ', 'REMOTE ADDRESS', 'PORT', 'PROCESS'])
