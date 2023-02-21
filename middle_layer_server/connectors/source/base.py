import logging

class SourceConnector(object):
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

    def connect(self):
        raise NotImplementedError

    def get_data(self):
        raise NotImplementedError
