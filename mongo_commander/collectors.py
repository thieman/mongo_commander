"""Collectors contain information on the commands to run on the
Mongo nodes and how to process the data that is returned."""

import time

def get_collector_class(collector_doc):
    collectors = {'MongoTop': MongoTop,
                  'MongoStat': MongoStat}
    return collectors[collector_doc['type']]

class BaseCollector(object):
    def __init__(self, data, controller, collector_doc):
        self.data = data
        self.controller = controller
        self.poll_interval = 1  # seconds between running command

    @property
    def setup_command(self):
        """Optional command to run on the remote host when originally
        connecting to the node. This command should return quickly.
        The stdout and stderr of this process are passed to
        setup_process_return."""
        pass

    def setup_process_return(self, stdout, stderr):
        """Receives the stdout and stderr of the command run in setup_command,
        if it is implemented."""
        raise NotImplementedError()

    @property
    def command(self):
        """Command to run on the remote node. If this command returns, it is run
        again after poll_interval seconds. Lines returned from this command are
        streamed to process."""
        raise NotImplementedError()

    def process(self, stdout, stderr):
        """Receives lines from stdout and stderr of the process run by command."""
        pass

class MongoTop(BaseCollector):
    def __init__(self, data, controller, collector_doc):
        super(MongoTop, self).__init__(data, controller, collector_doc)
        self.host = collector_doc.get('host')
        self.port = collector_doc.get('port')

    @property
    def command(self):
        command = "/opt/mongodb/bin/mongotop"
        if self.host:
            command += " --host {}".format(self.host)
        if self.port:
            command += " --port {}".format(self.port)
        return command

    def process(self, stdout, stderr):
        for line in stdout:
            self.data.append('mongotop.{}'.format(self.controller.node_address), line)

class MongoStat(BaseCollector):
    def __init__(self, data, controller, collector_doc):
        super(MongoStat, self).__init__(data, controller, collector_doc)
        self.host = collector_doc.get('host')
        self.port = collector_doc.get('port')

    @property
    def command(self):
        command = "/opt/mongodb/bin/mongostat"
        if self.host:
            command += " --host {}".format(self.host)
        if self.port:
            command += " --port {}".format(self.port)
        return command

    def process(self, stdout, stderr):
        for line in stdout:
            self.data.append('mongostat.{}'.format(self.controller.node_address), line)
