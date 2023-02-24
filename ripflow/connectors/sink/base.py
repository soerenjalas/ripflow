import pprint
import logging
from typing import Optional
from ...serializers import Serializer


class SinkConnector(object):
    """Base class for source connectors."""

    def __init__(self, serializer: Serializer):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.serializer: Serializer = serializer

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    def initialize(self):
        raise NotImplementedError

    def connect_subprocess(self, idx: int):
        raise NotImplementedError

    def send(self, data: bytes):
        raise NotImplementedError


class STDOUTSinkConnector(SinkConnector):
    def __init__(self, serializer: Serializer):
        super().__init__(serializer)
        self.printer = pprint.PrettyPrinter()

    def connect_subprocess(self):
        pass

    def send(self, data):
        self.printer.pprint(data)
