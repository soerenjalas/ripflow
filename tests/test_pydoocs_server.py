from middle_layer_server.core import PythonMiddleLayerServer
from middle_layer_server.connectors.source import PydoocsSourceConnector
from middle_layer_server.connectors.sink import ZMQSinkConnector
from middle_layer_server.serializers import JsonSerializer
from middle_layer_server.analyzers import ImageProjector
import time
import zmq
import json
# from pprint import pprint as print

sink_socket = 1337


def subscribe(socket_port, n):
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://127.0.0.1:{socket_port}")
    socket.setsockopt(zmq.SUBSCRIBE, b"")
    messages = list()
    t0 = time.time()
    for i in range(n):
        message = socket.recv().decode('utf-8')
        messages.append(json.loads(message)['macropulse'])
        if time.time()-t0 > n * 1.1:
            raise TimeoutError()
    return len(messages)


def test_server():
    source_connector = PydoocsSourceConnector(
        source_properties=["FLASH.LASER/HIDRAPP1.CAM/PA_OUT.34.FF/IMAGE_EXT_ZMQ"])
    sink_connector = ZMQSinkConnector(port=sink_socket,
                                    serializer=JsonSerializer())

    analyzer = ImageProjector(fake_load=0.2)
    server = PythonMiddleLayerServer(
        source_connector=source_connector,
        sink_connector=sink_connector,
        analyzer=analyzer,
        n_workers=10)

    server.event_loop(background=True)

    n1 = subscribe(sink_socket, 10)
    assert n1 == 10
    n2 = subscribe(sink_socket+1, 10)
    assert n2 == 10


if __name__ == '__main__':
    test_server()
