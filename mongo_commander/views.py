"""Each View receives the ClusterData object and the window
to which it is allowed to render. These control all of the
display logic not directly related to window layout."""

import time

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
        self.window.addstr(1, 1, 'NODE STATUS')
        self.window.move(3, 1)
        healthy = True
        total_threads, healthy_threads = 0, 0
        for listener in self.data.listeners:
            for thread in listener.threads:
                total_threads += 1
                latest = self.data.get('latest.{}.{}'.format(thread.node_name,
                                                             thread.collector.name), 0)
                if (not thread.is_alive()) or time.time() - int(latest) > 60:
                    healthy = False
                else:
                    healthy_threads += 1
            self.window.addstr("{}: {}".format(listener.node_name,
                                               "HEALTHY" if healthy else "UNHEALTHY"))
            y, x = self.window.getyx()
            self.window.move(y+1, 1)

    def periodic_render(self):
        self.render()
