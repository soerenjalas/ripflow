import zmq
from .base import SinkConnector
from ...serializers import Serializer


class ZMQSinkConnector(SinkConnector):
    """Sink connector for ZMQ PUB-SUB pattern

    Parameters
    ----------
    port : Int
        Port of zmq socket, additional sender subprocesses will
        utilize port+n to open their respective sockets
    serializer : Serializer
        Serialization object for outgoing data
    """

    def __init__(self, port: int, serializer: Serializer) -> None:
        self.port = port
        self.serializer = serializer
        self.socket = None
        self.context = None

    def connect_subprocess(self, idx: int):
        """Connect subprocess to sink connector

        Parameters
        ----------
        idx : int
            Identifier of sender subprocess
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{self.port+idx}")
        self._logger.info(
            f"Sender {idx} connected to ZMQ pub socket on port {self.port+idx}"
        )

    def send(self, message):
        self.socket.send(message)
