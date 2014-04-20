"""The window manager. Creates a bunch of curses frames with various
functions. The "main" window is reserved for rendering Views that
display data aggregated by the various collectors."""

import time
import curses
import threading

from .views import TitleView, MiniView, StatusView

def setup_window(window):
    window.keypad(1)
    window.immedok(True)

class WindowManager(object):
    def __init__(self, data):
        self.data = data
        self.screen = None
        self.render_thread = None
        self.windows = {}
        self.views = {}

    def start(self):
        self.screen = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.noecho()
        curses.cbreak()
        setup_window(self.screen)
        self._create_windows()
        self._start_render_thread()
        self._main_loop()

    def close(self):
        self.screen.immedok(False)
        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def _create_windows(self):
        y, x = self.screen.getmaxyx()

        self.windows['title'] = curses.newwin(1, x, 0, 0)
        self.windows['mini'] = curses.newwin(1, x, y-1, 0)
        self.windows['status'] = curses.newwin(y - 4, 40, 1, x - 40)
        self.windows['main'] = curses.newwin(y - 4, x - 40, 1, 0)

        for window in self.windows.values():
            setup_window(window)

        self.views['title'] = TitleView(self.data, self.windows['title'])
        self.views['mini'] = MiniView(self.data, self.windows['mini'])
        self.views['status'] = StatusView(self.data, self.windows['status'])

    def _redraw_windows(self):
        y, x = self.screen.getmaxyx()
        self.screen.clear()
        curses.resizeterm(y, x)
        self.screen.refresh()

    def _periodic_render(self):
        while True:
            for view in self.views.values():
                try:
                    view.periodic_render()
                except:
                    pass
            time.sleep(1)

    def _start_render_thread(self):
        self.render_thread = threading.Thread(target=self._periodic_render)
        self.render_thread.daemon = True
        self.render_thread.start()

    def _main_loop(self):
        while True:
            char_code = self.screen.getch()
            if char_code >= 0 and char_code <= 255:
                char = chr(char_code).lower()
                if char == 'q':
                    self.close()
                    break
                else:
                    for view in self.views.values():
                        view.process_char(char)
