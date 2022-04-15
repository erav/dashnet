
import curses

FG_RED = 1
FG_CYAN = 2

USE_DEFAULT_COLOR = -1


class DefaultSkin:
    def __init__(self):
        if curses.has_colors():
            curses.use_default_colors()
            curses.init_pair(FG_RED, curses.COLOR_RED, -1)
            curses.init_pair(FG_CYAN, curses.COLOR_GREEN, -1)

    @property
    def default_title_attr(self):
        return 0 | curses.A_BOLD


class CyanSkin(DefaultSkin):
    def __init__(self):
        super().__init__()

    @property
    def default_title_attr(self):
        return curses.color_pair(FG_CYAN) | curses.A_BOLD if curses.has_colors() else 0 | curses.A_BOLD


class RedSkin(DefaultSkin):
    def __init__(self):
        super().__init__()

    @property
    def default_title_attr(self):
        return curses.color_pair(FG_RED) | curses.A_BOLD if curses.has_colors() else 0 | curses.A_BOLD
