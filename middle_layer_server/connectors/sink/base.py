import pprint


class SinkConnector(object):
    """Base class for source connectors."""
    def initialize(self):
        raise NotImplementedError

    def connect_subprocess(self):
        raise NotImplementedError
 
    def send(self, data):
        raise NotImplementedError


class STDOUTSinkConnector(SinkConnector):
    def initialize(self):
        self.printer = pprint.PrettyPrinter()

    def send(self, data):
        self.printer.pprint(data)
