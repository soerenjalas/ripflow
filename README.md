# Python middle layer framework for DOOCS

This repository provides a framework that shall act as a communication layer between DOOCS and Python.

The framework is meant to work in combination with a DOOCS gateway server that reads data on defined zmq sockes and publishes them as native DOOCS properties. 

This repository contains the Python classes to build a middle layer application that reads data from various sources (e.g. DOOCS zmq properties) and apply arbitrary analysis pipelines onto the data using overlapping worker threads. The processed data is then published via zmq or other programmable sink connectors.

A basic middle layer analysis server can look like the following:

```python
# Define connector for incoming data (here pydoocs zmq)
source_connector = PydoocsSourceConnector(
    source_properties=["FLASH.LASER/MOD24.CAM/Input.11.NF/IMAGE_EXT_ZMQ"])
# Define output connector
sink_connector = ZMQSinkConnector(port=1337, serializer=JsonSerializer())
# Define analysis pipeline
analyzer = BaseAnalyzer()

# Create server instance
server = PythonMiddleLayerServer(
    source_connector=source_connector,
    sink_connector=sink_connector,
    analyzer=analyzer)

# Run event loop
server.event_loop()
```