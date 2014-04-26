"""Menu models / controllers. These are owned by the MenuView, which renders
based on the Menu's current settings. When a new collector is activated,
it binds its various sub-views to Menu select events."""

import curses

class OptionGroup(object):
    def __init__(self, group_name, group_options, multi_select=False):
        self.name = group_name
        self.options = [{'name': option, 'active': False}
                        for option in group_options]
        self.multi_select = multi_select

    def __len__(self):
        return len(self.options)

    def deactivate_all(self):
        for option in self.options:
            option['active'] = False

class Menu(object):
    def __init__(self):
        self.position = 0
        self.options = []
        self.registry = {}

    def process_char(self, char):
        if char == curses.KEY_DOWN:
            self.position = min(self.total_options - 1, self.position + 1)
        elif char == curses.KEY_UP:
            self.position = max(0, self.position - 1)
        elif char == curses.KEY_ENTER:
            self.toggle_option_at_position()

    @property
    def total_options(self):
        total = 0
        for option_group in self.options:
            total += len(option_group)
        return total

    def toggle_option(self, group_name, option_name, activate=None):
        for group in self.options:
            if group_name == group.name:
                for option in group.options:
                    if option['name'] == option_name:
                        if activate is None:
                            option['active'] = not option['active']
                        else:
                            option['active'] = activate
                break

    def option_at_position(self):
        group_start, group_end = -1, -1
        for group in self.options:
            group_start = group_end + 1
            group_end += len(group)
            if self.position <= group_end:
                return group, group.options[self.position - group_start]
        raise ValueError('position out of bounds')

    def toggle_option_at_position(self):
        option_group, option = self.option_at_position()
        if not option_group.multi_select:
            option_group.deactivate_all()
        option['active'] = not option['active']

class MainMenu(Menu):
    def __init__(self, data, window_manager):
        super(MainMenu, self).__init__()
        self.data = data
        self.window_manager = window_manager
        self.options = [OptionGroup('collectors',
                                    [collector['name'] for collector in self.data.config['collectors']])]
        self.set_active_collector()

    def set_active_collector(self):
        for index, collector_doc in enumerate(self.data.config['collectors']):
            if "{}View".format(collector_doc['type']) == self.window_manager.views['main'].__class__.__name__:
                self.toggle_option('collectors', collector_doc['name'], activate=True)
