"""The window manager. Creates a bunch of curses frames with various
functions. The "main" window is reserved for rendering Views that
display data aggregated by the various collectors."""

import time
import curses
import threading

from . import views

MENU_WIDTH = 40
STATUS_WIDTH = 40

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
        self.render_thread = None

    def start(self):
        self.screen = curses.initscr()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()
        setup_window(self.screen)
        self._create_windows()
        self._start_render_thread()
        self._main_loop()

    def close(self):
        curses.curs_set(1)
        self.screen.immedok(False)
        self.screen.keypad(0)
        curses.nocbreak()
        curses.echo()
        curses.endwin()

    def view_class_for_collector(self, collector_doc):
        return getattr(views, "{}View".format(collector_doc['type']))

    def change_main_view(self, menu_options):
        collector_name = self.views['menu'].menu.get_active_in_group('collectors')[0]
        collector_doc = [collector
                         for collector in self.data.config.get('collectors')
                         if collector['name'] == collector_name][0]
        view_class = self.view_class_for_collector(collector_doc)
        view = view_class(self.data, self.windows['main'], collector_name)
        self.views['main'] = view
        self.views['main'].render()
        self.change_to_view_menu(view)

    def change_to_view_menu(self, view):
        self.views['menu'].menu = view.menu
        self.views['menu'].render()

    def change_to_main_menu(self):
        menu_view = views.MenuView(self, self.data, self.windows['menu'])
        menu_view.menu.on_change(self.change_main_view)
        self.views['menu'] = menu_view
        menu_view.render()

    def _create_windows(self):
        y, x = self.screen.getmaxyx()

        self.windows['title'] = curses.newwin(1, x, 0, 0)
        self.windows['mini'] = curses.newwin(1, x, y-1, 0)
        self.windows['menu'] = curses.newwin(y - 2, MENU_WIDTH, 1, 0)
        self.windows['status'] = curses.newwin(y - 2, STATUS_WIDTH, 1, x - STATUS_WIDTH)
        self.windows['main'] = curses.newwin(y - 2, x - (MENU_WIDTH + STATUS_WIDTH), 1, MENU_WIDTH)

        for window in self.windows.values():
            setup_window(window)

        self.views['title'] = views.TitleView(self.data, self.windows['title'])
        self.views['mini'] = views.MiniView(self.data, self.windows['mini'])
        self.views['status'] = views.StatusView(self.data, self.windows['status'])
        initial_collector = self.data.config['collectors'][0]
        initial_view_class = self.view_class_for_collector(initial_collector)
        self.views['main'] = initial_view_class(self.data, self.windows['main'], initial_collector['name'])

        self.change_to_main_menu()
        self.change_to_view_menu(self.views['main'])

    def _redraw_windows(self):
        y, x = self.screen.getmaxyx()
        self.screen.clear()
        curses.resizeterm(y, x)
        self.screen.refresh()

    def _periodic_render(self):
        while True:
            for view in self.views.values():
                try:
                    view.render()
                except:
                    pass
            time.sleep(1)

    def _start_render_thread(self):
        self.render_thread = threading.Thread(target=self._periodic_render)
        self.render_thread.daemon = True
        self.render_thread.start()

    def _main_loop(self):
        while True:
            char = self.screen.getch()
            if char == 10:
                char = curses.KEY_ENTER
            if char >= 0 and char <= 255:
                char = chr(char).lower()
            if char == 'q':
                self.close()
                break
            if char == 'm':
                self.change_to_main_menu()
                continue
            for view in self.views.values():
                view.process_char(char)
