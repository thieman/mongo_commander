"""Each View receives the ClusterData object and the window
to which it is allowed to render. These control all of the
display logic not directly related to window layout."""

import curses
import time
from operator import itemgetter

from .curses_util import movedown

class View(object):
    def __init__(self, data, window):
        self.data = data
        self.window = window

    def process_char(self, char):
        raise NotImplementedError()

    def periodic_render(self):
        pass

class TitleView(View):
    def __init__(self, *args, **kwargs):
        super(TitleView, self).__init__(*args, **kwargs)

    def process_char(self, char):
        self.window.addstr(char)

class MiniView(View):
    def __init__(self, *args, **kwargs):
        super(MiniView, self).__init__(*args, **kwargs)

    def process_char(self, char):
        self.window.addstr(char)

class StatusView(View):
    def __init__(self, *args, **kwargs):
        super(StatusView, self).__init__(*args, **kwargs)

    def process_char(self, char):
        self.window.addstr(char)

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
                if thread.is_alive() and time.time() - int(latest) < 60:
                    healthy_threads += 1
            node_doc = {'name': listener.node_name,
                        'total': total_threads, 'healthy': healthy_threads}
            nodes['primary' if is_primary else 'secondary'].append(node_doc)
        return nodes

    def periodic_render(self):
        self.render()
