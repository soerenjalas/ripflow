# Source Connector API

Source connectors deal with the incoming data from the source system. They are responsible for reading the data from the source system and providing it to the worker processes.
The source connector API is designed to be flexible and allow for easy implementation of different types of data sources.

## SourceConnector

This object is an abstract class that defines the basis for all source connectors. It provides the following methods:

* `connect()` - This method is called when the connector is first initialized. It is responsible for setting up the connection to the source system and performing any other initialization tasks.
* `get_data()`- This method is used to poll new data from the source system. The function should be blocking until new data is available. The function should return a list of dictionaries.

A custom source connector should inherit from this class and implement the `connect()` and `get_data()` methods.
Example:

```python
from typing import List, Dict
from ripflow.connectors.source import SourceConnector
import time
import json

class JsonFileSourceConnector(SourceConnector):
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def connect(self) -> None:
        self.file = open(self.filename, "r")

    def get_data(self) -> List[Dict]:
        while True:
            line = self.file.readline()
            if not line:
                # File is empty, wait for new entries
                time.sleep(1)
            else:
                return [json.loads(line)]
```

## PydoocsSourceConnector

This source connector is used to read data from the [DOOCS](https://doocs.desy.de/) system. It utilizes the DOOCS zmq interface to read data from zmq capable DOOCS properties. The connector is configured using the following parameters:

* source_properties - A list of DOOCS properties to read from.
* timeout - Timeout in seconds. If no data is available within the timeout, the connector will raise a TimeoutError.

Example:

```python
source_connector = PydoocsSourceConnector(
    source_properties=["FLASH.LASER/HIDRAPP1.CAM/PA_OUT.34.FF/IMAGE_EXT_ZMQ"])
```
