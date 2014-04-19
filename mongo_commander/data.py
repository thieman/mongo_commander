""" This module is responsible for connecting to and polling the
cluster's Mongo nodes to extract relevant performance data that
is then available to the frontend through the ClusterData instance. """

import os
import inspect
import getpass
import threading
import time
import logging

import yaml
import paramiko

from .collectors import get_collector_class

this_file_location = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
default_config_location = os.path.realpath(os.path.join(this_file_location,
                                                        'config.yml'))
SENTINEL = object()

class ClusterData(object):
    def __init__(self, config_path):
        self.config_path = config_path or default_config_location
        self.load_config()
        self.nodes = self.config['nodes']
        self.lock = threading.RLock()
        self._dict = {}
        self.listeners = []

    def __getitem__(self, key):
        self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def load_config(self):
        with open(self.config_path, 'r') as f:
            self.config = yaml.load(f.read())
        if self.config['ssh']['auth_type'] == 'password':
            self.ssh_password = getpass.getpass("SSH key password: ")
        else:
            self.ssh_password = None

    def get(self, dot_key, default=SENTINEL):
        with self.lock:
            value = self._deep_get(dot_key)
            if value == SENTINEL:
                if default == SENTINEL:
                    raise KeyError("{} not found".format(dot_key))
                else:
                    value = default
        return value

    def set(self, dot_key, value):
        with self.lock:
            self._deep_set(dot_key, value)

    def push(self, dot_key, value, truncate_to=None):
        with self.lock:
            self._deep_append(dot_key, value, truncate_to)

    def _deep_get(self, dot_key, get_dict=None):
        if get_dict is None:
            get_dict = self._dict
        split = dot_key.split('.', 1)
        if split[0] not in get_dict:
            return SENTINEL
        return get_dict[split[0]] if len(split) == 1 else dot(get_dict[split[0]], split[1])

    def _deep_set(self, dot_key, value, set_dict=None):
        if set_dict is None:
            set_dict = self._dict
        split = dot_key.split('.', 1)
        if len(split) == 1:
            set_dict[split[0]] = value
            return
        if split[0] not in set_dict:
            set_dict[split[0]] = {}
        self._deep_set(split[1], value, set_dict[split[0]])

    def _deep_append(self, dot_key, value, truncate_to, set_dict=None):
        if set_dict is None:
            set_dict = self._dict
        split = dot_key.split('.', 1)
        if len(split) == 1:
            if split[0] not in set_dict:
                set_dict[split[0]] = []
            set_dict[split[0]].append(value)
            if truncate_to:
                set_dict[split[0]] = set_dict[split[0]][-1 * truncate_to:]
            return
        if split[0] not in set_dict:
            set_dict[split[0]] = {}
        self._deep_append(split[1], value, truncate_to, set_dict[split[0]])

    def start_polling(self):
        auth_kwargs = {}
        if self.config['ssh']['auth_type'] == 'password':
            auth_kwargs['ssh_password'] = self.ssh_password
        elif self.config['ssh']['auth_type'] == 'key':
            auth_kwargs['ssh_key_path'] = os.path.expanduser(self.config['ssh']['key_path'])

        for node in self.nodes:
            listener = NodeListenerController(self, node.get('name'), node.get('host'))
            self.listeners.append(listener)
            listener.start_threads()

    def status(self):
        status = {}
        for listener in self.listeners:
            status[listener] = {}
            for thread in listener.threads:
                status[listener][thread] = thread.is_alive()
        return status

class NodeListenerController(object):
    def __init__(self, data, node_name, node_address):
        self.data = data
        self.node_name = node_name
        self.node_address = node_address
        self.threads = []

    def start_threads(self):
        for collector_doc in self.data.config['collectors']:
            thread = NodeListenerThread(self.data, self, collector_doc)
            thread.daemon = True
            self.threads.append(thread)
            thread.start()

class NodeListenerThread(threading.Thread):
    def __init__(self, data, controller, collector_doc):
        super(NodeListenerThread, self).__init__()
        self.data = data
        self.controller = controller
        self.collector = get_collector_class(collector_doc)(data, controller, collector_doc)
        self.node_name = self.controller.node_name
        self.node_address = self.controller.node_address
        self.ssh_user = self.data.config.get('ssh').get('user')
        self.ssh_auth_type = self.data.config.get('ssh').get('auth_type')
        self.ssh_password = self.data.ssh_password
        self.ssh_key_path = os.path.expanduser(self.data.config.get('ssh').get('key_path'))
        self.ssh = paramiko.SSHClient()

    def run(self):
        self.connect()
        try:
            stdin, stdout, stderr = self.ssh.exec_command(self.collector.command)
            while True:
                self.collector.process(stdout.readlines(sizehint=1024))
                time.sleep(1)
        finally:
            self.ssh.close()

    def connect(self):
        auth_kwargs = {}
        if self.ssh_password:
            auth_kwargs['password'] = self.ssh_password
        if self.ssh_key_path:
            auth_kwargs['key_filename'] = self.ssh_key_path
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.node_address, username=self.ssh_user,
                         **auth_kwargs)
