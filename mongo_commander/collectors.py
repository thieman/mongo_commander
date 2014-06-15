"""Collectors contain information on the commands to run on the
Mongo nodes and how to process the data that is returned."""

import time
from datetime import datetime
import logging

def get_collector_class(collector_doc):
    collectors = {'MongoTop': MongoTop,
                  'MongoStat': MongoStat,
                  'Tail': Tail,
                  'TailGrep': TailGrep}
    return collectors[collector_doc['type']]

class Collector(object):
    # if True, thread does not go unhealthy on long wait for output
    _infrequent = False

    def __init__(self, data, controller, collector_doc):
        self.data = data
        self.controller = controller
        self.collector_doc = collector_doc
        self.name = collector_doc.get('name')
        self.poll_interval = 1  # seconds between running command

    def _datum(self, data):
        return {'data': data,
                'time': datetime.utcnow(),
                'node_name': self.controller.node_name,
                'collector_name': self.collector_doc['name'],
                'collector_type': self.collector_doc['type']}

    @property
    def setup_command(self):
        """Optional command to run on the remote host when originally
        connecting to the node. This command should return quickly.
        The stdout and stderr of this process are passed to
        setup_process_return."""
        pass

    def setup_process_return(self, stdout):
        """Receives the stdout and stderr of the command run in setup_command,
        if it is implemented."""
        raise NotImplementedError()

    @property
    def command(self):
        """Command to run on the remote node. If this command returns, it is run
        again after poll_interval seconds. Lines returned from this command are
        streamed to process."""
        raise NotImplementedError()

    def process(self, stdout):
        """Receives lines from stdout of the process run by command."""
        raise NotImplementedError()

class MongoTop(Collector):
    def __init__(self, *args, **kwargs):
        super(MongoTop, self).__init__(*args, **kwargs)
        self.path = self.collector_doc.get('path')
        self.host = self.collector_doc.get('host')
        self.port = self.collector_doc.get('port')

    @property
    def command(self):
        command = self.path or "mongotop"
        if self.host:
            command += " --host {}".format(self.host)
        if self.port:
            command += " --port {}".format(self.port)
        return command

    def process(self, stdout):
        for line in stdout:
            self.data.push('{}.{}'.format(self.name, self.controller.node_name),
                           self._datum(line), 500)

class MongoStat(Collector):
    def __init__(self, *args, **kwargs):
        super(MongoStat, self).__init__(*args, **kwargs)
        self.path = self.collector_doc.get('path')
        self.host = self.collector_doc.get('host')
        self.port = self.collector_doc.get('port')

    @property
    def command(self):
        command = self.path or "mongostat"
        if self.host:
            command += " --host {}".format(self.host)
        if self.port:
            command += " --port {}".format(self.port)
        return command

    def process(self, stdout):
        for line in stdout:
            self.data.push('{}.{}'.format(self.name, self.controller.node_name),
                           self._datum(line), 500)

class MongoStat(Collector):
    def __init__(self, *args, **kwargs):
        super(MongoStat, self).__init__(*args, **kwargs)
        self.path = self.collector_doc.get('path')
        self.host = self.collector_doc.get('host')
        self.port = self.collector_doc.get('port')

    @property
    def command(self):
        command = self.path or "mongostat"
        if self.host:
            command += " --host {}".format(self.host)
        if self.port:
            command += " --port {}".format(self.port)
        return command

    def process(self, stdout):
        for line in stdout:
            self.data.push('{}.{}'.format(self.name, self.controller.node_name),
                           self._datum(line), 500)

class Tail(Collector):
    _infrequent = True

    def __init__(self, *args, **kwargs):
        super(Tail, self).__init__(*args, **kwargs)
        self.file = self.collector_doc.get('file')

    @property
    def command(self):
        return "tail -0f {}".format(self.file)

    def process(self, stdout):
        for line in stdout:
            self.data.push('{}.{}'.format(self.name, self.controller.node_name),
                           self._datum(line), 500)

class TailGrep(Collector):
    _infrequent = True

    def __init__(self, *args, **kwargs):
        super(TailGrep, self).__init__(*args, **kwargs)
        self.file = self.collector_doc.get('file')
        self.grep = self.collector_doc.get('grep')

    @property
    def command(self):
        return "tail -0f {} | grep -E {}".format(self.file, self.grep)

    def process(self, stdout):
        for line in stdout:
            self.data.push('{}.{}'.format(self.name, self.controller.node_name),
                           self._datum(line), 500)
