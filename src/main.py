
import os
import sys

import curses

from display.ui import Ui

_package_path = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)
sys.path.insert(0, _package_path)


class Opts:
    @property
    def processes(self):
        return True

    @property
    def addresses(self):
        return True

    @property
    def connections(self):
        return True

    @property
    def total_utilization(self):
        return True


def main(stdscr):
    ui = Ui(stdscr, Opts())
    ui.draw(False, True, 0, 0, stdscr)


curses.wrapper(main)



