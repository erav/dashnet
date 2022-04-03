
import curses

COLOR_WHITE_ON_BLACK = 1
COLOR_YELLOW_ON_BLACK = 2


class DefaultSkin:
    def __init__(self):
        curses.init_color(curses.COLOR_BLACK, 0, 0, 0)
        curses.init_pair(COLOR_WHITE_ON_BLACK, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(COLOR_YELLOW_ON_BLACK, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    @property
    def default_title_attr(self):
        return curses.color_pair(COLOR_YELLOW_ON_BLACK) | curses.A_BOLD

    @property
    def bg_color(self):
        return curses.color_pair(COLOR_WHITE_ON_BLACK)