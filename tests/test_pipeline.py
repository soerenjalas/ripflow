import time
import zmq
import json
import random
import unittest
from ripflow import Ripflow
from ripflow.connectors.source import TestSourceConnector as SourceConnector
from ripflow.connectors.sink import ZMQSinkConnector
from ripflow.serializers import JsonSerializer
from ripflow.analyzers import TestAnalyzer as Analyzer


def subscribe(socket_port, n, timeout=5000):
    """
    Subscribe to n messages with a timeout.

    :param socket_port: Port to connect to.
    :param n: Number of messages to receive.
    :param timeout: Timeout in milliseconds.
    :return: List of received messages.
    """
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://127.0.0.1:{socket_port}")
    socket.setsockopt(zmq.SUBSCRIBE, b"")

    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    messages = []
    start_time = time.time()

    while len(messages) < n:
        elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        if elapsed_time > timeout:
            raise TimeoutError("Subscription timed out waiting for messages.")

        socks = dict(poller.poll(timeout - elapsed_time))
        if socks.get(socket) == zmq.POLLIN:
            msg = socket.recv().decode("utf-8")
            messages.append(json.loads(msg))
    socket.close()
    context.term()
    return messages


class TestMiddleLayerAnalyzer(unittest.TestCase):
    def setUp(self):
        self.sink_socket = 1337
        self.test_sequence = list()
        for i in range(10):
            data = {
                "data": random.random(),
                "type": "FLOAT",
                "timestamp": time.time() + i,
                "macropulse": i,
                "miscellaneous": {},
                "name": "test",
            }
            self.test_sequence.append(data)
        self.source_connector = SourceConnector(self.test_sequence)
        self.sink_connector = ZMQSinkConnector(
            port=self.sink_socket, serializer=JsonSerializer()
        )
        self.analyzer = Analyzer(fake_load=0.05)
        self.server = Ripflow(
            source_connector=self.source_connector,
            sink_connector=self.sink_connector,
            analyzer=self.analyzer,
            n_workers=1,
        )

    def test_event_loop(self):
        self.server.event_loop(background=True)
        received = subscribe(self.sink_socket, 10)
        self.assertEqual(received, self.test_sequence)


if __name__ == "__main__":
    unittest.main()
