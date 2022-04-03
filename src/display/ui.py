
import time

import curses

from . import ui_state
from .components import header_details
from .components.help_text import HelpText
from .components.layout import Layout
from network import connection


class Ui:
    """
    terminal: Terminal<B>,
    state: UIState,
    ip_to_host: HashMap<IpAddr, String>,
    opts: RenderOpts,
    """
    def __init__(self, stdscr, render_opts):
        self._stdscr = stdscr
        self._stdscr.bkgdset(curses.COLOR_BLUE, curses.A_COLOR)
        self._ui_state = ui_state.UIState(render_opts.total_utilization)
        self._opts = render_opts
        self._ip_to_host = None

    def output_text(self):
        self._stdscr.clear()
        timestamp = time.time()
        no_traffic = True
        # header
        self._stdscr.addstr("Refreshing:")
        # body1
        if self._opts.processes:
            self.output_process_data(timestamp)
            no_traffic = False
        if self._opts.connections:
            self.output_connections_data(timestamp)
            no_traffic = False
        if self._opts.addresses:
            self.output_adressess_data(timestamp)
            no_traffic = False
        if not (self._opts.processes or self._opts.connections or self._opts.addresses):
            self.output_process_data(timestamp)
            self.output_connections_data(timestamp)
            self.output_adressess_data(timestamp)
            no_traffic = False
        # body2: In case no traffic is detected
        if no_traffic:
            self._stdscr.addstr("<NO TRAFFIC>")
        # footer
        self._stdscr.addstr("")

    def output_process_data(self, timestamp):
        for (process, process_network_data) in self._ui_state.processes:
            _str = (
                f'process: <{timestamp}> '
                f'"{process}" up/down Bps: '
                f'{process_network_data.total_bytes_uploaded}/{process_network_data.total_bytes_downloaded} '
                f'connections: {process_network_data.connection_count}',
            )
            self._stdscr.addstr(0, 0, _str)

    def output_connections_data(self, timestamp):
        for (conn, conn_network_data) in self._ui_state.connections:
            display_str = connection.display_connection_string(
                conn, self._ip_to_host, conn_network_data.interface_name
            )
            _str = (
                f'connection: <{timestamp}> {display_str} '
                f'up/down Bps: {conn_network_data.total_bytes_uploaded}/{conn_network_data.total_bytes_downloaded} '
                f'process: "{conn_network_data.process_name}"'
            )
            self._stdscr.addstr(0, 0, _str)

    def output_adressess_data(self, timestamp):
        for (remote_addr, remote_addr_net_data) in self._ui_state.remote_addresses:
            _str = (
                f'remote_address: <{timestamp}> '
                f'{connection.display_ip_or_host(remote_addr, self._ip_to_host)} '
                f'up/down Bps: '
                f'{remote_addr_net_data.total_bytes_uploaded}/{remote_addr_net_data.total_bytes_downloaded} '
                f'connections: {remote_addr_net_data.connection_count}'
            )
            self._stdscr.addstr(0, 0, _str)

    def draw(self, paused, show_dns, elapsed_time, ui_offset, stdscr):
        children = self.get_tables_to_display()
        header = header_details.HeaderDetails(self._ui_state, elapsed_time, paused)
        help_text = HelpText(paused, show_dns)
        layout = Layout(header=header, children=children, footer=help_text)
        layout.render(stdscr)

    def get_tables_to_display(self):
        children = list()
        if self._opts.processes:
            children.append(self._ui_state.create_processes_table())
        if self._opts.addresses:
            children.append(self._ui_state.create_remote_addresses_table(self._ip_to_host))
        if self._opts.connections:
            children.append(self._ui_state.create_connections_table(self._ip_to_host))
        if not (self._opts.processes or self._opts.addresses or self._opts.connections):
            children = [
                self._ui_state.create_processes_table() +
                self._ui_state.create_remote_addresses_table(self._ip_to_host) +
                self._ui_state.create_connections_table(self._ip_to_host)
            ]
        return children

    def get_table_count(self):
        return len(self.get_tables_to_display())

    def update_state(self, connections_to_procs, utilization, ip_to_host):
        self._ui_state.update(connections_to_procs, utilization)
        self._ip_to_host.extend(ip_to_host)

    def end(self):
        self._stdscr.clear()
        self._stdscr.show_cursor()
