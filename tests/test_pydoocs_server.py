from middle_layer_server.core import PythonMiddleLayerServer
from middle_layer_server.connectors.source import PydoocsSourceConnector
from middle_layer_server.connectors.sink import ZMQSinkConnector
from middle_layer_server.serializers import JsonSerializer
from middle_layer_server.analyzers import ImageProjector
import time
import zmq

sink_socket = 1337


def subscribe():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://localhost:{sink_socket}")
    for i in range(10):
        message = message = socket.recv()
        print(message)


source_connector = PydoocsSourceConnector(
    source_properties=["FLASH.LASER/MOD24.CAM/Input.11.NF/IMAGE_EXT_ZMQ"])
sink_connector = ZMQSinkConnector(port=sink_socket,
                                  serializer=JsonSerializer())
analyzer = ImageProjector()

server = PythonMiddleLayerServer(
    source_connector=source_connector,
    sink_connector=sink_connector,
    analyzer=analyzer)

server.event_loop(background=True)
while True:
    time.sleep(10)

subscribe()
