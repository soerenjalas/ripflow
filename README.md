# Python middle layer analysis framework

## Introduction

This Python package provides a framework to parallelize data analysis tasks in arbitrary data streams.

The package contains the Python classes to build a middle layer application that reads data from various sources and applies arbitrary analysis pipelines onto the data using overlapping worker processes. The processed data is then published via programmable sink connectors.

A basic middle layer analysis server can look like the following:

```python
from middle_layer_server.core import PythonMiddleLayerServer
from middle_layer_server.connectors.source import PydoocsSourceConnector
from middle_layer_server.connectors.sink import ZMQSinkConnector
from middle_layer_server.serializers import JsonSerializer
from middle_layer_server.analyzers import ImageProjector

# Define connector for incoming data (here pydoocs zmq)
source_connector = PydoocsSourceConnector(
    source_properties=["FLASH.LASER/MOD24.CAM/Input.11.NF/IMAGE_EXT_ZMQ"])
# Define analysis pipeline, here simulate a 200 ms latency
analyzer = ImageProjector(fake_load=0.2)
# Define output connector. This one serializes the data
# as a json string and sends each property via a ZMQ PUB socket
sink_connector = ZMQSinkConnector(port=1337, serializer=JsonSerializer())

# Create server instance
server = PythonMiddleLayerServer(
        source_connector=source_connector,
        sink_connector=sink_connector,
        analyzer=analyzer,
        n_workers=10)

# Run event loop. Can be run blocking in main process or send to a child
server.event_loop(background=False)
