"""The window manager. Creates a bunch of curses frames with various
functions. The "main" window is reserved for rendering Views that
display data aggregated by the various collectors."""

import curses

class WindowManager(object):
    def __init__(self, data):
        self.data = data
        self.screen = None

    def start(self):
        self.screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
        self.screen.keypad(1)

    def close(self):
        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()
