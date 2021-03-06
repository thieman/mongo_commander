"""Each View receives the ClusterData object and the window
to which it is allowed to render. These control all of the
display logic not directly related to window layout."""

import curses
import random
import time
import logging
from operator import itemgetter
from collections import OrderedDict

from .menus import MainMenu, MongoTopMenu, MongoStatMenu, TailMenu, TailGrepMenu
from .widgets import StreamWidget
from .curses_util import movedown

class View(object):
    def __init__(self, data, window):
        self.data = data
        self.window = window

    def process_char(self, char):
        pass

    def render(self):
        raise NotImplementedError()

class CollectorView(View):
    def __init__(self, data, window, collector_name):
        super(CollectorView, self).__init__(data, window)
        self.collector_name = collector_name
        y, x = self.window.getmaxyx()
        self.subwindow = self.window.derwin(y - 4, x - 2, 3, 1)

    def update_subwindow(self):
        raise NotImplementedError()

    def render(self):
        self.window.clear()
        self.window.border(0)
        self.window.move(1, 1)
        self.window.addstr(self.collector_name, curses.A_BOLD)
        self.subwindow.clear()
        self.update_subwindow()
        self.subwindow.refresh()

class TitleView(View):
    def __init__(self, *args, **kwargs):
        super(TitleView, self).__init__(*args, **kwargs)
        self.saying = None
        self.sayings = ["Never give up. Never surrender!",
                        "HindenburgDB: It's humongous, but it's also on fire.",
                        "I am become Mongo, destroyer of data.",
                        "#dropDatabase WUB-WUB-WUB-WUB-WUB-WUB-WUB-WUB",
                        "This, too, shall pass.",
                        "Please direct all hate tweets to @eliothorowitz.",
                        "Oh, nobody told you about $SHITTY_DEFAULT_BEHAVIOR?",
                        "Call a DBA for elections lasting over four hours.",
                        "Because you chose a database that uses JavaScript.",
                        "If Mongo breaks, just try again, you probably hit a call to /dev/random.",
                        "Knock knock. Who's there? [object Object]."]

    def get_motivational(self):
        if int(time.time()) % 60 == 0 or not self.saying:
            self.saying = random.choice(self.sayings)
        return self.saying

    def render(self):
        self.window.clear()
        self.window.addstr(0, 1, 'Mongo Commander - {}'.format(self.get_motivational()), curses.A_BOLD)

class MiniView(View):
    def __init__(self, *args, **kwargs):
        super(MiniView, self).__init__(*args, **kwargs)

    def render(self):
        self.window.clear()
        prompt = self.data.get('prompt', None)
        if prompt:
            self.window.addstr(0, 1, prompt)
        else:
            self.window.addstr(0, 1, 'Arrow keys to navigate menus, m for collector menu, ENTER to select, q to exit')

class MenuView(View):
    def __init__(self, window_manager, *args, **kwargs):
        super(MenuView, self).__init__(*args, **kwargs)
        self.window_manager = window_manager
        self.menu = MainMenu(self.data, self.window_manager)

    def render(self):
        self.window.clear()
        self.window.border(0)
        self.window.move(1, 1)
        self.window.addstr(self.menu.heading.upper(), curses.A_BOLD)
        self.window.move(3, 1)
        position = 0
        for option_group in self.menu.options:
            self.window.addstr(option_group.name.upper().replace('_', ' '), curses.A_BOLD)
            movedown(self.window, 2, 3)
            for option in option_group.options:
                if self.menu.position == position:
                    y, x = self.window.getyx()
                    self.window.addstr(y, 1, "> ", curses.A_BOLD)
                self.window.addstr(option['name'], curses.color_pair(4 if option['active'] else 3))
                movedown(self.window, 1, 3)
                position += 1
            movedown(self.window, 1, 1)

    def process_char(self, char):
        self.menu.process_char(char)
        self.render()

class StatusView(View):
    def __init__(self, *args, **kwargs):
        super(StatusView, self).__init__(*args, **kwargs)

    def render(self):
        self.window.clear()
        self.window.border(0)
        self.window.addstr(1, 1, 'NODE STATUS', curses.A_BOLD)
        self.window.addstr(3, 1, 'PRIMARIES', curses.A_BOLD)
        self.window.move(5, 1)
        nodes = self.get_nodes_status_for_render()
        for node in sorted(nodes['primary'], key=itemgetter('name')):
            self.window.addstr("{}: {}/{}".format(node['name'],
                                                  node['healthy'],
                                                  node['total']),
                               curses.color_pair(2 if node['healthy'] == node['total'] else 1))
            movedown(self.window, 1, 1)
        movedown(self.window, 1, 1)
        self.window.addstr('SECONDARIES', curses.A_BOLD)
        movedown(self.window, 2, 1)
        for node in sorted(nodes['secondary'], key=itemgetter('name')):
            self.window.addstr("{}: {}/{}".format(node['name'],
                                                  node['healthy'],
                                                  node['total']),
                               curses.color_pair(2 if node['healthy'] == node['total'] else 1))
            movedown(self.window, 1, 1)

    def get_nodes_status_for_render(self):
        nodes = {'primary': [], 'secondary': []}
        for listener in self.data.listeners:
            is_primary = self.data.get('{}.primary'.format(listener.node_name), False)
            total_threads, healthy_threads = 0, 0
            for thread in listener.threads:
                total_threads += 1
                latest = self.data.get('latest.{}.{}'.format(thread.node_name,
                                                             thread.collector.name), 0)
                if thread.is_alive() and (time.time() - int(latest) < 60
                                          or thread.collector._infrequent):
                    healthy_threads += 1
            node_doc = {'name': listener.node_name,
                        'total': total_threads, 'healthy': healthy_threads}
            nodes['primary' if is_primary else 'secondary'].append(node_doc)
        return nodes

class MongoTopView(CollectorView):
    def __init__(self, *args, **kwargs):
        super(MongoTopView, self).__init__(*args, **kwargs)
        self.menu = MongoTopMenu(self.collector_name)

    def update_subwindow(self):
        pass

class MongoStatView(CollectorView):
    def __init__(self, *args, **kwargs):
        super(MongoStatView, self).__init__(*args, **kwargs)
        self.menu = MongoStatMenu(self.collector_name)

    def update_subwindow(self):
        pass

class TailView(CollectorView):
    def __init__(self, *args, **kwargs):
        super(TailView, self).__init__(*args, **kwargs)
        self.menu = TailMenu(self.collector_name)
        self.widget = StreamWidget(self.data)

    def update_subwindow(self):
        # get keys we are currently interested in from menu settings
        from operator import itemgetter
        current_keys = ["TailSlowLog.{}".format(node)
                        for node in map(itemgetter('name'), self.data.config['nodes'])]
        self.widget.source_keys = current_keys
        self.widget.apply_to_window(self.subwindow)

class TailGrepView(CollectorView):
    def __init__(self, *args, **kwargs):
        super(TailGrepView, self).__init__(*args, **kwargs)
        self.menu = TailGrepMenu(self.collector_name)

    def update_subwindow(self):
        pass
