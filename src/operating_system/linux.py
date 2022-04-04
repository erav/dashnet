
import errno
import os
from proc import core as proclib_core
import psutil

from network import connection

LOCALHOST_ADDRESSES = [
    '127.0.0.1',
    '::1',
    '::ffff:127.0.0.1'
]


class OpenSockets:
    def __init__(self):
        self._processes = ProcessLoader()
        self._procfs = InodeLoader()
        self._connections = ConnectionLoader()
        self._local_open_sockets = {}
        self._remote_open_sockets = {}
        self._inodes_to_pid = {}
        self._pid_to_procname = {}
        self._local_socket_count_by_process = {}
        self._local_socket_count_by_process_list = []
        self._process_with_local_sockets_list = []

    @property
    def connected_processes_count_list(self):
        return self._local_socket_count_by_process_list

    @property
    def process_with_local_sockets_list(self):
        return self._process_with_local_sockets_list

    def create_process_connection_lists(self):
        self._load_open_sockets()
        self._add_connections_to_open_sockets(self._connections.tcps, ConnectionLoader.TCP)
        self._add_connections_to_open_sockets(self._connections.udps, ConnectionLoader.UDP)
        self._filter_localhost()
        if not self._local_open_sockets:
            self._process_with_local_sockets_list.append('<NO TRAFFIC DETECTED>')
            self._local_socket_count_by_process_list.append('<NO TRAFFIC DETECTED>')
        else:
            self._create_process_with_local_sockets_list()
            self._create_local_socket_count_by_process_list()
        return self

    def _load_open_sockets(self):
        for pid in self._processes.pids:
            inodes = self._procfs.get_all_inodes(pid)
            for item in inodes.items():
                inode = item[0]
                self._inodes_to_pid[inode] = pid

    def _add_connections_to_open_sockets(self, connections, protocol):
        for conn in connections:
            process_name = self._processes.get_name_for_pid(conn.pid)
            self._local_open_sockets[connection.LocalSocket(conn.laddr.ip, conn.laddr.port, protocol)] = process_name

    def _filter_localhost(self):
        items_to_delete = lambda s: s.ip in LOCALHOST_ADDRESSES
        for key in list(filter(items_to_delete, self._local_open_sockets.keys())):
            del self._local_open_sockets[key]

    def _create_process_with_local_sockets_list(self):
        name_formatter = ProcessNameFormatter()
        socket_formatter = connection.LocalSocketsFormatter()
        header_formatter = ProcessByLocalAddressListFormatter()
        socket_formatter.format(self._local_open_sockets.keys(), header_formatter.col_name_lengths())
        name_formatter.find_longest(self._local_open_sockets.values())
        header = header_formatter.create_header(
            [name_formatter.longest, socket_formatter.longest_protocol, socket_formatter.longest_ip, 0]
        )
        name_formatter.align_names(self._local_open_sockets)
        self._process_with_local_sockets_list.append(header)
        for socket, process_name in self._local_open_sockets.items():
            self._process_with_local_sockets_list.append(f'{process_name} {socket}')

    def _create_local_socket_count_by_process_list(self):
        name_formatter = ProcessNameFormatter()
        header_formatter = ProcessByConnectionCountFormatter()
        name_formatter.find_longest(self._local_open_sockets.values())
        header = header_formatter.create_header([name_formatter.longest, 0])
        self._local_socket_count_by_process_list.append(header)
        for socket, process_name in self._local_open_sockets.items():
            try:
                count = self._local_socket_count_by_process[process_name]
                self._local_socket_count_by_process[process_name] = count + 1
            except KeyError:
                self._local_socket_count_by_process[process_name] = 0
        name_formatter.align_names(self._local_open_sockets)
        for item in self._local_socket_count_by_process.items():
            if item[1] > 0:
                self._local_socket_count_by_process_list.append(f'{item[0]} {item[1]}')


class ConnectionLoader:
    TCP = 'tcp'
    UDP = 'udp'
    CLOSING_CONNECTION_STATES = ['FIN_WAIT1', 'FIN_WAIT2', 'TIME_WAIT']

    def __init__(self):
        conn_filter = lambda sconn: sconn.status not in self.CLOSING_CONNECTION_STATES
        self._tcps = self._load(self.TCP, conn_filter)
        self._udps = self._load(self.UDP, conn_filter)

    @property
    def tcps(self):
        return self._tcps

    @property
    def udps(self):
        return self._udps

    @staticmethod
    def _load(protocol, connection_filter):
        net_conns = psutil.net_connections(protocol)
        return net_conns if not connection_filter else list(filter(connection_filter, net_conns))


class ProcessLoader:
    def __init__(self):
        self._processes = self._load()
        self._pid_to_procname = {}
        self._map_pid_to_proc_name()

    @property
    def pids(self):
        return [p.pid for p in self._processes]

    def get_name_for_pid(self, pid):
        return self._pid_to_procname[pid] if pid else '<UNKNOWN>'

    @staticmethod
    def _load():
        return proclib_core.find_processes()

    def _map_pid_to_proc_name(self):
        for p in self._processes:
            self._pid_to_procname[p.pid] = p.comm if p.comm != 'java' else f'{p.comm}:{p.command_line[-1]}'


class InodeLoader:
    @staticmethod    
    def get_all_inodes(pid):
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


class ProcessNameFormatter:
    def __init__(self):
        self._longest = 0

    @property
    def longest(self):
        return self._longest

    def find_longest(self, process_names):
        self._longest = 0
        for process_name in process_names:
            if len(process_name) > self._longest:
                self._longest = len(process_name)
        return self._longest

    def align_names(self, pid_to_process_names):
        for pid, process_name in pid_to_process_names.items():
            if len(process_name) < self._longest:
                pid_to_process_names[pid] = process_name + ' ' * (self._longest - len(process_name))


class TableHeaderFormatter:
    def __init__(self, column_names):
        self._col_names = column_names

    def create_header(self, col_widths):
        header = ''
        for col_name, width in zip(self._col_names, col_widths):
            header += col_name + ' ' * (width - len(col_name) + 1)
        return header

    def col_name_lengths(self):
        return [len(col_name) for col_name in self._col_names]


class ProcessByLocalAddressListFormatter(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROCESS NAME', 'PROTOCOL', 'LOCAL ADDRESS', 'PORT'])


class ProcessByConnectionCountFormatter(TableHeaderFormatter):
    def __init__(self):
        super().__init__(['PROCESS NAME', 'CONNECTIONS'])
