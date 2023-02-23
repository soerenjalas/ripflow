import logging
import numpy as np
import time


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


class TestSourceConnector(SourceConnector):
    """Test source connector."""

    def __init__(self, data_sequence):
        self.data_sequence = data_sequence
        self.iterator = 0

    def connect(self):
        self.logger.info("Connecting to test source")

    def get_data(self):
        while self.iterator >= len(self.data_sequence):
            time.sleep(1)
        data = self.data_sequence[self.iterator]
        self.iterator += 1
        time.sleep(0.05)
        return data
