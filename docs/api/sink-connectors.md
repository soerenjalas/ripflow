# Sink Connector API

Sink connectors handle the outgoing stream of the processed data. They are responsible for publishing the processed data to the desired destination.

## SinkConnector
`ripflow.connectors.sink.SinkConnector`

This object is an abstract class that defines the basis for all sink connectors. It provides the following methods:

* `connect_subprocess(idx)` - This method is called when the connector is first initialized. It is responsible for setting up the connection to the destination system and performing any other initialization tasks. The `idx`argument is the index of the data array that is generated by the workers. For each data entry an individual sender process is spawned.
* `send(data)` - This method is called whenever new data is made available by the worker processes. The data is provided as bytes.

The `SinkConnector` requires a `Serializer` object that defines the transformation of the internal data format into the messages that are sent out by the `SinkConnector`. The `Serializer` object is provided as the `serializer` argument to the `SinkConnector` constructor.

Custom sink connectors should inherit from this class and implement the `connect_subprocess()` and `send()` methods.

Example:

```python
from typing import List, Dict
from ripflow.connectors.sink import SinkConnector
from ripflow.serializers import Serializer
import time

class FileSinkConnector(SinkConnector):
    def __init__(self, serializer: Serializer, filename: str) -> None:
        self.filename = filename
        self.serializer = serializer

    def connect_subprocess(self) -> None:
        self.file = open(self.filename, "r")

    def send(self, data: bytes) -> None:
        self.file.write(data)
        self.file.flush()
```

## ZmqSinkConnector
`ripflow.connectors.sink.ZmqSinkConnector`

This sink connector is used to publish data via the [ZeroMQ](https://zeromq.org/) protocol. Specifically, this sink connector makes use of a zmq pub socket. The connector is configured using the following parameters:

* `port` - The port to publish the data on.
* `serializer` - A `Serializer` object that defines the transformation of the internal data format into the messages that are sent as bytes over the zmq socket.

Example:

```python
from ripflow.serializers import JsonSerializer
from ripflow.connectors.sink import ZmqSinkConnector

sink_connector = ZMQSinkConnector(port=1337, serializer=JsonSerializer())
```