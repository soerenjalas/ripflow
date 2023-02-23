import time
import zmq
import json
import random
import unittest
from ripflow.core import MiddleLayerAnalyzer
from ripflow.connectors.source import TestSourceConnector as SourceConnector
from ripflow.connectors.sink import ZMQSinkConnector
from ripflow.serializers import JsonSerializer
from ripflow.analyzers import TestAnalyzer as Analyzer


def subscribe(socket_port, n):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://127.0.0.1:{socket_port}")
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    messages = list()
    t0 = time.time()
    for i in range(n):
        message = socket.recv().decode("utf-8")
        messages.append(json.loads(message))
        if time.time() - t0 > n * 1.1:
            raise TimeoutError()
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
        self.server = MiddleLayerAnalyzer(
            source_connector=self.source_connector,
            sink_connector=self.sink_connector,
            analyzer=self.analyzer,
            n_workers=1,
        )

    def test_event_loop(self):
        self.server.event_loop(background=True)
        self.assertEqual(subscribe(self.sink_socket, 10), self.test_sequence)


if __name__ == "__main__":
    unittest.main()
