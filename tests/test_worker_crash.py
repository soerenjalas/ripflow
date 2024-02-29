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
from typing import List


class ZMQSubscriber:
    def __init__(self, socket_port):
        """
        Initialize the ZMQ Subscriber with the given port.

        :param socket_port: Port to connect to.
        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.socket_port = socket_port
        self.poller = zmq.Poller()

    def connect(self):
        """
        Connects to the specified port and prepares the socket for receiving messages.
        """
        self.socket.connect(f"tcp://127.0.0.1:{self.socket_port}")
        self.socket.setsockopt(zmq.SUBSCRIBE, b"")
        self.poller.register(self.socket, zmq.POLLIN)
        print(f"Connected to tcp://127.0.0.1:{self.socket_port}")

    def receive_messages(self, n, timeout: float = 10000):
        """
        Receives up to n messages with a specified timeout.

        :param n: Number of messages to receive.
        :param timeout: Timeout in milliseconds.
        :return: List of received messages.
        """
        messages: List[str] = []
        start_time = time.time()

        while len(messages) < n:
            elapsed_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            if elapsed_time > timeout:
                break

            socks = dict(self.poller.poll(timeout - elapsed_time))
            if socks.get(self.socket) == zmq.POLLIN:
                msg = self.socket.recv().decode("utf-8")
                messages.append(json.loads(msg))

        return messages


class TestRipflow(unittest.TestCase):
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
        self.tester = ZMQSubscriber(self.sink_socket)
        self.tester.connect()

    def tearDown(self):
        self.server.stop()
        self.tester.socket.close()
        self.tester.context.term()

    def test_event_loop_with_worker_crash(self):
        expected_crash_point = 5
        self.analyzer.crash_after = expected_crash_point
        self.server.event_loop()
        time.sleep(0.3)

        received_messages = self.tester.receive_messages(n=10, timeout=10000)
        print(
            "Received messages:",
            [received_message["macropulse"] for received_message in received_messages],
        )
        if received_messages:
            received_macropulses = [
                msg["macropulse"] for msg in received_messages if "macropulse" in msg
            ]

            # Find the first macropulse value after the expected crash point, accounting for potential loss
            post_crash_macropulses = [
                mp for mp in received_macropulses if mp > expected_crash_point
            ]

            # Ensure there's evidence of post-crash processing
            self.assertTrue(
                post_crash_macropulses,
                "No messages received post-crash, indicating possible failure in recovery.",
            )
        else:
            self.fail("No messages received, indicating a failure in the system.")


if __name__ == "__main__":
    unittest.main()
