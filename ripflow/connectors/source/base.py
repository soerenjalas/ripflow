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
    """Test source connector that can simulate a crash."""

    def __init__(self, data_sequence, crash_point=None):
        """
        Initialize the BaseConnector object.

        Args:
            data_sequence (list): The data sequence to be processed.
            crash_point (int, optional): The crash point index. Defaults to None.
        """
        self.data_sequence = data_sequence
        self.crash_point = crash_point
        self.iterator = 0

    def connect(self):
        # Assuming there's a logger setup in the parent class
        self.logger.info("Connecting to crashable test source")

    def get_data(self):
        # Simulate a crash at the defined point
        if self.crash_point is not None and self.iterator == self.crash_point:
            raise Exception("Simulated crash in TestSourceConnector")

        # Proceed with normal data retrieval
        while self.iterator >= len(self.data_sequence):
            time.sleep(1)  # Sleep to simulate waiting for more data in a real scenario
        data = self.data_sequence[self.iterator]
        self.iterator += 1
        time.sleep(0.05)  # Simulate some delay in data retrieval
        return data

    def reset(self):
        self.iterator = 0
