from .base import SourceConnector
import pydoocs as pd
import time
import numpy as np


class PydoocsSourceConnector(SourceConnector):
    """Source connector that connects to native DOOCS zmq properties.

    Parameters
    ----------
    source_properties : list
        List of DOOCS adresses which the connector should listen to
    timeout: float
        Time in seconds without data after which the connection is closed.
        Infinit if -1.

    """

    def __init__(self, source_properties: list, timeout: float = 2) -> None:
        """Construct PydoocsSourceConnector object."""
        self.source_properties = source_properties
        self.cycles = int(1e6)
        self.connected = False
        self.timeout = timeout

    def connect(self) -> None:
        """Connect DOOCS zmq sockets."""
        pd.connect(self.source_properties, cycles=self.cycles)
        self.connected = True
        time.sleep(0.1)

    def disconnect(self) -> None:
        """Disconnect sockets."""
        pd.disconnect()
        self.connected = False

    def get_data(self):
        """Read incoming data.

        Method is blocking until new data arives or timeout runs out

        Returns
        -------
        list
            List with incoming data.

        Raises
        ------
        TimeoutError
            No data within time specified in timeout
        """
        out = None
        t0 = time.time()
        dt = 0
        if self.timeout == -1:
            timeout = np.inf
        else:
            timeout = self.timeout
        while (not out) and (dt < timeout):
            out = pd.getdata()
            dt = time.time() - t0
        if dt > timeout:
            raise TimeoutError("Source connection timed out")
        return out
