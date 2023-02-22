import logging
from typing import Optional, List
from .connectors.source import SourceConnector
from .connectors.sink import SinkConnector
from .analyzers import BaseAnalyzer
from multiprocessing import Process
import zmq
import time


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
        self.worker_socket_address = "ipc://workers"
        self.sender_socket_address = "ipc://sender"

        # Process registries
        self.n_workers = n_workers
        self.n_senders = analyzer.n_outputs
        self.workers = [Worker(self, worker_id=i) for i in range(self.n_workers)]
        self.senders = [Sender(self, idx=i) for i in range(self.n_senders)]
        self.producer = Producer(self)

    def event_loop(self, background=False):
        """Start main event loop

        Parameters
        ----------
        background : bool, optional
            Whether to launch the main loop in the
            background. If true will spawn subprocess and continue,
            by default False.
        """
        for worker in self.workers:
            worker.launch()
        for sender in self.senders:
            sender.launch()
        time.sleep(1)
        if not background:
            self.producer._producer_routine()
        else:
            self.producer.launch()


class Producer(object):
    """_summary_

    Parameters
    ----------
    server : MiddleLayerAnalyzer
        Server object to connect to
    """

    def __init__(self, server: MiddleLayerAnalyzer) -> None:
        """Construct producer object"""
        self.logger: logging.Logger = server.logger
        self.source_connector: SourceConnector = server.source_connector
        self.worker_socket_address: str = server.worker_socket_address
        self.process: Optional[Process] = None

    def launch(self) -> None:
        self.process = Process(target=self._producer_routine, daemon=True)
        self.process.start()
        self.logger.info("Producer launched")

    def _producer_routine(self):
        """Listen for incoming events."""
        self.context = zmq.Context()
        self.running = True
        self.source_connector.connect()
        self._connect_producer()
        while self.running:
            data = self.source_connector.get_data()
            self.input_socket.send_pyobj(data)

    def _connect_producer(self):
        self.input_socket = self.context.socket(zmq.PUSH)
        self.input_socket.bind(self.worker_socket_address)


class Worker(object):
    """
    A worker object that connects to a server and processes data using an analyzer.

    Parameters
    ----------
    server : MiddleLayerAnalyzer
        Server object to connect to
    worker_id : int, optional
        Worker id, by default 0
    """

    def __init__(self, server: MiddleLayerAnalyzer, worker_id: int = 0) -> None:
        """Construct worker object"""
        self.logger = server.logger
        self.worker_id = worker_id
        self.analyzer = server.analyzer
        self.sink_connector = server.sink_connector
        self.sender_socket_address = server.sender_socket_address
        self.worker_socket_address = server.worker_socket_address
        self.n_senders = server.n_senders
        self.sender_sockets: List[zmq.Socket] = list()
        self.process: Optional[Process] = None

    def launch(self) -> None:
        """
        Launch worker process.
        """
        self.process = Process(target=self._worker_routine, args=(self.worker_id,))
        self.process.daemon = True
        self.process.start()
        self.logger.info(f"Worker {self.worker_id} launched")

    def _worker_routine(self, worker_id: int = 0):
        """
        Worker routine that receives and processes data.

        Parameters
        ----------
        worker_id : int, optional
            Worker id, by default 0
        """
        self.context = zmq.Context()
        self._connect_worker()
        self.logger.info(f"Worker {worker_id} launched")
        while True:
            data = self.worker_data_socket.recv_pyobj()
            data = self.analyzer.run(data)
            for idx in range(self.n_senders):
                prop = data[idx]
                msg = self.sink_connector.serializer.serialize(prop)
                self.sender_sockets[idx].send(msg)

    def _connect_worker(self) -> None:
        """
        Connect worker IO sockets.
        """
        self.worker_data_socket = self.context.socket(zmq.PULL)
        self.worker_data_socket.connect(self.worker_socket_address)
        for idx in range(self.n_senders):
            socket = self.context.socket(zmq.PUSH)
            socket.connect(self.sender_socket_address + f"_{idx:d}")
            self.sender_sockets.append(socket)


class Sender(object):
    """
    Sender object for processing and sending data.

    Parameters
    ----------
    server : MiddleLayerAnalyzer
        Server object to connect to.
    idx : int
        Sender id.
    """

    def __init__(self, server: MiddleLayerAnalyzer, idx: int) -> None:
        """Construct sender object"""
        self.logger = server.logger
        self.idx = idx
        self.sink_connector = server.sink_connector
        self.sender_socket_address = server.sender_socket_address
        self.process: Optional[Process] = None

    def launch(self) -> None:
        """Launch the sender process."""
        self.process = Process(target=self._sender_routine, args=(self.idx,))
        self.process.daemon = True
        self.process.start()
        self.logger.info(f"Sender {self.idx} launched")

    def _sender_routine(self, idx: int) -> None:
        """
        The sender routine.

        Parameters
        ----------
        idx : int
            The sender id.
        """
        self.context = zmq.Context()
        self._connect_sender(idx)
        self.sink_connector.connect_subprocess(idx)
        self.logger.info(f"Sender {idx} launched")
        while True:
            msg = self.sender_data_socket.recv()
            self.sink_connector.send(msg)

    def _connect_sender(self, idx: int):
        """Connect sender to processed data stream"""
        self.sender_data_socket = self.context.socket(zmq.PULL)
        self.sender_data_socket.bind(self.sender_socket_address + f"_{idx:d}")
