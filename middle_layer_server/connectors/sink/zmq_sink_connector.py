import zmq
from .base import SinkConnector
from ...serializers import Serializer


class ZMQSinkConnector(SinkConnector):
    """Sink connector for ZMQ PUB-SUB pattern

    Parameters
    ----------
    port : Int
        Port of zmq socket
    serializer : Serializer
        Serialization object for outgoing data
    """

    def __init__(self, port: int, serializer: Serializer) -> None:
        self.port = port
        self.serializer = serializer
        self.socket = None

    def initialize(self):
        """Open zmq PUB socket
        """
        context = zmq.Context()
        self.socket = context.socket(zmq.PUB)
        self.socket.bind(f"tcp://*:{self.port}")

    def send(self, data):
        message = self.serializer.serialize(data)
        self.socket.send_json(message)

