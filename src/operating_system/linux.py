
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
        self.socket_formatter = connection.LocalSocketsFormatter()
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
        self._socket_formatter.format(self._local_open_sockets)
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
        for socket, process_name in self._local_open_sockets.items():
            self._process_with_local_sockets_list.append(f'{process_name}   {socket}')

    def _create_local_socket_count_by_process_list(self):
        for socket, process_name in self._local_open_sockets.items():
            try:
                count = self._local_socket_count_by_process[process_name]
                self._local_socket_count_by_process[process_name] = count + 1
            except KeyError:
                self._local_socket_count_by_process[process_name] = 0
        for item in self._local_socket_count_by_process.items():
            if item[1] > 0:
                self._local_socket_count_by_process_list.append(f'{item[0]} {item[1]}')


class ConnectionLoader:
    TCP = 'tcp'
    UDP = 'udp'

    def __init__(self):
        self._tcps = self._load(self.TCP, None)
        self._udps = self._load(self.UDP, None)

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
        self._longest_name_len = 0
        self._align_name_lengths()

    @property
    def pids(self):
        return [p.pid for p in self._processes]

    @property
    def longest_name_len(self):
        return self._longest_name_len

    def get_name_for_pid(self, pid):
        return self._pid_to_procname[pid] if pid else '<UNKNOWN>'

    @staticmethod
    def _load():
        return proclib_core.find_processes()

    def _map_pid_to_proc_name(self):
        for p in self._processes:
            self._pid_to_procname[p.pid] = p.comm if p.comm != 'java' else f'{p.comm}:{p.command_line[-1]}'

    def _align_name_lengths(self):
        self._longest_name_len = 0
        for process_name in self._pid_to_procname.values():
            if len(process_name) > self._longest_name_len:
                self._longest_name_len = len(process_name)
        self._longest_name_len += 2
        for process_name in self._pid_to_procname.values():
            if len(process_name) < self._longest_name_len:
                process_name += ' ' * (self._longest_name_len - len(process_name))


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
