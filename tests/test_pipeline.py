import time
import zmq
import json
import random

# from pprint import pprint as print

sink_socket = 1337

test_sequence = list()
for i in range(10):
    data = {
        "data": random.random(),
        "type": "FLOAT",
        "timestamp": time.time() + i,
        "macropulse": i,
        "miscellaneous": {},
        "name": "test",
    }
    test_sequence.append(data)


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


def test_server():
    from middle_layer_analyzer.core import MiddleLayerAnalyzer
    from middle_layer_analyzer.connectors.source import TestSourceConnector
    from middle_layer_analyzer.connectors.sink import ZMQSinkConnector
    from middle_layer_analyzer.serializers import JsonSerializer
    from middle_layer_analyzer.analyzers import TestAnalyzer

    source_connector = TestSourceConnector(test_sequence)
    sink_connector = ZMQSinkConnector(port=sink_socket, serializer=JsonSerializer())

    analyzer = TestAnalyzer(fake_load=0.05)
    server = MiddleLayerAnalyzer(
        source_connector=source_connector,
        sink_connector=sink_connector,
        analyzer=analyzer,
        n_workers=1,
    )

    server.event_loop(background=True)
    print("Waiting for data to be processed")
    out = subscribe(sink_socket, 10)
    assert len(out) == 10
    assert out == test_sequence
    return


if __name__ == "__main__":
    test_server()
