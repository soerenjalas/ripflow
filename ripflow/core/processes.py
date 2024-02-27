from ripflow.analyzers import BaseAnalyzer
from ripflow.connectors.sink import SinkConnector
from typing import List
from ripflow.connectors.source import SourceConnector
from .utils import CommsFactory
from .utils import Child
import zmq
import time


import logging


class Producer(Child):
    """_summary_

    Parameters
    ----------
    server : MiddleLayerAnalyzer
        Server object to connect to
    """

    def __init__(
        self,
        logger: logging.Logger,
        comms_factory: CommsFactory,
        comms_config: dict,
        source_connector: SourceConnector,
    ) -> None:
        """Construct producer object"""
        super().__init__(logger, comms_factory)
        self.source_connector = source_connector
        self.comms_config = comms_config

    def main_routine(self):
        """Listen for incoming events."""
        self.context = self.comms_factory.create_context()
        self.source_connector.connect()
        self._connect_producer()
        while True:
            try:
                data = self.source_connector.get_data()
                self.input_socket.send_pyobj(data)
            except Exception as e:
                self.logger.error(f"Error in producer main_routine: {e}")
                break

    def _connect_producer(self):
        self.input_socket = self.comms_factory.create_socket(
            self.context, **self.comms_config
        )


class Worker(Child):
    def __init__(
        self,
        logger: logging.Logger,
        comms_factory: CommsFactory,
        input_comms_config: dict,
        output_comms_config: dict,
        analyzer: BaseAnalyzer,
        sink_connector: SinkConnector,
        n_senders: int,
        worker_id: int = 0,
    ) -> None:
        """
        Initialize the Worker object.

        Args:
            logger (logging.Logger): The logger object for logging messages.
            comms_factory (CommsFactory): The factory object for creating communication objects.
            input_comms_config (dict): The configuration for input communication.
            output_comms_config (dict): The configuration for output communication.
            analyzer (BaseAnalyzer): The analyzer object for analyzing data.
            sink_connector (SinkConnector): The sink connector object for connecting to sinks.
            n_senders (int): The number of senders.
            worker_id (int, optional): The ID of the worker. Defaults to 0.
        """
        super().__init__(logger, comms_factory)
        self.input_comms_config = input_comms_config
        self.output_comms_config = output_comms_config
        self.analyzer = analyzer
        self.sink_connector = sink_connector
        self.n_senders = n_senders
        self.worker_id = worker_id
        self.output_sockets: List[zmq.Socket] = list()

    def main_routine(self):
        self.context = self.comms_factory.create_context()
        self._connect_worker()
        self.logger.info(f"Worker {self.worker_id} launched")
        while True:
            try:
                data = self.input_socket.recv_pyobj()
                data = self.analyzer.run(data)
                for idx in range(self.n_senders):
                    prop = data[idx]
                    msg = self.sink_connector.serializer.serialize(prop)
                    self.output_sockets[idx].send(msg)
            except Exception as e:
                self.logger.error(f"Error in worker main_routine: {e}")
                self.comms_factory.cleanup(
                    self.context, self.output_sockets + [self.input_socket]
                )
                break

    def _connect_worker(self):
        self.input_socket = self.comms_factory.create_socket(
            self.context, **self.input_comms_config
        )
        base_config = self.output_comms_config.copy()
        for idx in range(self.n_senders):
            # Modify the specific configuration for each sender
            config = base_config.copy()
            address_key = (
                "bind_address" if "bind_address" in config else "connect_address"
            )
            config[address_key] = config[address_key] + f"_{idx}"
            socket = self.comms_factory.create_socket(self.context, **config)
            self.output_sockets.append(socket)


class Sender(Child):
    """
    Represents a sender in the ripflow system.

    Parameters
    ----------
    logger : logging.Logger
        The logger object for logging messages.
    comms_factory : CommsFactory
        The factory object for creating communication objects.
    comms_config : dict
        The configuration for the communication objects.
    idx : int
        The sender id.
    sink_connector : SinkConnector
        The sink connector object for sending messages to the sink.

    Attributes
    ----------
    idx : int
        The sender id.
    comms_config : dict
        The configuration for the communication objects.
    sink_connector : SinkConnector
        The sink connector object for sending messages to the sink.
    """

    def __init__(
        self,
        logger: logging.Logger,
        comms_factory: CommsFactory,
        comms_config: dict,
        idx: int,
        sink_connector: SinkConnector,
    ) -> None:
        super().__init__(logger, comms_factory)
        self.idx = idx
        self.comms_config = comms_config
        self.sink_connector = sink_connector

    def main_routine(self) -> None:
        """
        The sender routine.

        Parameters
        ----------
        idx : int
            The sender id.
        """
        self.context = self.comms_factory.create_context()
        self._connect_sender()
        self.sink_connector.connect_subprocess(self.idx)
        self.logger.info(f"Sender {self.idx} launched")
        while True:
            msg = self.input_socket.recv()
            self.sink_connector.send(msg)

    def _connect_sender(self):
        """Connect sender to processed data stream"""
        config = self.comms_config.copy()
        address_key = "bind_address" if "bind_address" in config else "connect_address"
        config[address_key] = config[address_key] + f"_{self.idx}"
        self.input_socket = self.comms_factory.create_socket(self.context, **config)
