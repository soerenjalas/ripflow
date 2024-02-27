import logging
from typing import List
from .connectors.source import SourceConnector
from .connectors.sink import SinkConnector
from .analyzers import BaseAnalyzer
from .supervisor import Supervisor, RestartPolicy
import sys
import zmq
from .utils import Child, ZMQFactory, CommsFactory


class MiddleLayerAnalyzer(object):
    """_summary_

    Parameters
    ----------
    source_connector : SourceConnector
        Connector for incoming data
    sink_connector : SinkConnector
        Connector for outgoing data
    analyzer : BaseAnalyzer
        Analyzer object that processes the incoming data
    n_workers : int, default 2
        Number of analysis processes
    log_file_path : str, default "server.log"
        Path to log file
    log_level : str, default 'INFO'
        Logging level options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    """

    def __init__(
        self,
        source_connector: SourceConnector,
        sink_connector: SinkConnector,
        analyzer: BaseAnalyzer,
        n_workers: int = 2,
        log_file_path: str = "server.log",
        log_level: str = "INFO",
    ) -> None:
        """Construct main server object"""
        # Map string log level to logging constant
        log_level = getattr(logging, log_level.upper())
        # Create logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        # Create file handler and set level to log_level
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(log_level)
        # Create stream handler for output to stdout
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(log_level)
        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        # Add formatter to file handler
        file_handler.setFormatter(formatter)
        # Add file handler to logger
        self.logger.addHandler(file_handler)
        # Log a test message
        self.logger.debug("Logger initialized")
        # Initialize connectors
        self.source_connector = source_connector
        # Set logger for source connector
        self.source_connector.logger = self.logger
        # Initialize sink connector
        self.sink_connector = sink_connector
        # Set logger for sink connector
        self.sink_connector.logger = self.logger
        self.analyzer = analyzer
        # Set logger for analyzer
        self.analyzer.logger = self.logger

        # Parameters of comm layer
        self.source_socket_address = "ipc://source"
        self.sender_socket_address = "ipc://sender"

        self.comms_factory = ZMQFactory()
        self.producer_comms_config = {
            "socket_type": zmq.PUSH,
            "bind_address": self.source_socket_address,
        }
        self.worker_input_comms_config = {
            "socket_type": zmq.PULL,
            "connect_address": self.source_socket_address,
        }
        self.worker_output_comms_config = {
            "socket_type": zmq.PUSH,
            "connect_address": self.sender_socket_address,
        }
        self.sender_comms_config = {
            "socket_type": zmq.PULL,
            "bind_address": self.sender_socket_address,
        }

        # Process registries
        self.n_workers = n_workers
        self.n_senders = analyzer.n_outputs
        self.workers = [
            Worker(
                logger=self.logger,
                comms_factory=self.comms_factory,
                input_comms_config=self.worker_input_comms_config,
                output_comms_config=self.worker_output_comms_config,
                analyzer=self.analyzer,
                sink_connector=self.sink_connector,
                n_senders=self.n_senders,
                worker_id=i,
            )
            for i in range(self.n_workers)
        ]
        self.senders = [
            Sender(
                logger=self.logger,
                comms_factory=self.comms_factory,
                comms_config=self.sender_comms_config,
                sink_connector=self.sink_connector,
                idx=i,
            )
            for i in range(self.n_senders)
        ]
        self.producer = Producer(
            logger=self.logger,
            comms_factory=self.comms_factory,
            comms_config=self.producer_comms_config,
            source_connector=self.source_connector,
        )

        # Supervisor definition
        self.restart_policy = RestartPolicy(
            n_restart=3, restart_delay=5, reset_window=60
        )  # Restart policy for processes
        self.supervisor = Supervisor(
            logger=self.logger
        )  # Supervisor for managing processes
        self.supervisor.add_process(self.producer, self.restart_policy)
        for worker in self.workers:
            self.supervisor.add_process(worker, self.restart_policy)
        for sender in self.senders:
            self.supervisor.add_process(sender, self.restart_policy)

    def event_loop(self, background=False):
        """Start main event loop

        Parameters
        ----------
        background : bool, optional
            Whether to launch the main loop in the
            background. If true will spawn subprocess and continue,
            by default False.
        """
        self.supervisor.start_all_processes()
        # self.producer.launch()
        # time.sleep(1)
        # for sender in self.senders:
        #     sender.launch()
        # time.sleep(1)
        # for worker in self.workers:
        #     worker.launch()


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
            data = self.input_socket.recv_pyobj()
            data = self.analyzer.run(data)
            for idx in range(self.n_senders):
                prop = data[idx]
                msg = self.sink_connector.serializer.serialize(prop)
                self.output_sockets[idx].send(msg)

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
