"""Widgets abstract out common View rendering patterns like displaying
a list of logging messages or a bar chart. They typically take the ClusterData
object, a window, and a list of keys they should care about from ClusterData.
They then draw directly onto the window."""

from operator import itemgetter

from .curses_util import movedown, movex

class Widget(object):
    def __init__(self, data):
        self.data = data
        self.source_keys = []

    def apply_to_window(self, window):
        raise NotImplementedError()

class StreamWidget(Widget):
    """Display line-by-line text data from a stream."""
    def _gather_data(self):
        return reduce(list.__add__, map(lambda key: self.data.get(key, []), self.source_keys))

    def apply_to_window(self, window):
        data_for_render = self._gather_data()
        if not data_for_render:
            return
        window.move(0, 0)
        first_jump = len(data_for_render[0]['time'].strftime('%c')) + 3
        second_jump = first_jump + max(map(len, map(itemgetter('node_name'), data_for_render))) + 3
        for datum in sorted(data_for_render, key=itemgetter('time'))[-10:]:
            window.addstr('{} - '.format(datum['time'].strftime('%c')))
            movex(window, first_jump)
            window.addstr('{} - '.format(datum['node_name']))
            movex(window, second_jump)
            window.addstr(str(datum['data']).strip())
            movedown(window, x=0)
