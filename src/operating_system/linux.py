
import errno
import os
from proc import core as proclib_core
import psutil

from network import connection


def get_open_sockets():
    open_sockets = dict()
    inode_to_procname = dict()

    processes = proclib_core.find_processes()
    for process in processes:
        inode_to_procname[_get_proc_inodes(process.pid)] = process.comm
    tcps = psutil.net_connections('tcp')
    for tcp in tcps:
        procname = inode_to_procname[tcp.inode]
        open_sockets[connection.LocalSocket(tcp.laddr.ip, tcp.local_address.port, 'tcp')] = procname
    udps = psutil.net_connections('udp')
    for udp in udps:
        procname = inode_to_procname[udp.inode]
        open_sockets[connection.LocalSocket(udp.laddr.ip, udp.local_address.port, 'udp')] = procname
    return open_sockets


def _get_proc_inodes(pid):
    inodes = dict()
    for fd in os.listdir("%s/%s/fd" % ('/proc', pid)):
        try:
            inode = os.readlink("%s/%s/fd/%s" % ('/proc', pid, fd))
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
