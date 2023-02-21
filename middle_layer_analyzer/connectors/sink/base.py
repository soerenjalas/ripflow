import pprint
import logging


class SinkConnector(object):
    """Base class for source connectors."""

    def __init__(self):
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    def initialize(self):
        raise NotImplementedError

    def connect_subprocess(self):
        raise NotImplementedError

    def send(self, data):
        raise NotImplementedError


class STDOUTSinkConnector(SinkConnector):
    def initialize(self):
        self.printer = pprint.PrettyPrinter()

    def connect_subprocess(self):
        pass

    def send(self, data):
        self.printer.pprint(data)
