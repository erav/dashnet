
import curses

COLOR_WHITE_ON_BLACK = 1
COLOR_YELLOW_ON_BLACK = 2

USE_DEFAULT_COLOR = -1


class DefaultSkin:
    def __init__(self):
        if curses.has_colors():
            curses.use_default_colors()
            # curses.init_color(curses.COLOR_BLACK, 0, 0, 0)
            # curses.init_pair(COLOR_WHITE_ON_BLACK, curses.COLOR_WHITE, curses.COLOR_BLACK)
            # curses.init_pair(COLOR_YELLOW_ON_BLACK, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    @property
    def default_title_attr(self):
        # return curses.color_pair(COLOR_YELLOW_ON_BLACK) | curses.A_BOLD if curses.has_colors() else USE_DEFAULT_COLOR
        return 0

    @property
    def bg_color(self):
        # return curses.color_pair(COLOR_WHITE_ON_BLACK) if curses.has_colors() else USE_DEFAULT_COLOR
        return USE_DEFAULT_COLOR