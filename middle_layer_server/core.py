import logging
from .connectors.source import SourceConnector
from .connectors.sink import SinkConnector
from .analyzers import BaseAnalyzer
from multiprocessing import Process
import zmq
import time


class PythonMiddleLayerServer(object):
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

    def __init__(self,
                 source_connector: SourceConnector,
                 sink_connector: SinkConnector = None,
                 analyzer: BaseAnalyzer = None,
                 n_workers: int = 2,
                 log_file_path: str = "server.log",
                 log_level: str='INFO'
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
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # Add formatter to file handler
        file_handler.setFormatter(formatter)
        # Add file handler to logger
        self.logger.addHandler(file_handler)
        # Log a test message
        self.logger.debug('Logger initialized')
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
        self.sender_sockets = list()
        self.context = zmq.Context()
        self.n_workers = n_workers
        self.n_senders = analyzer.n_outputs
        # Process registries
        self.workers = list()
        self.senders = list()
        self.main_producer = None

        self.running = False

    def event_loop(self, background=False):
        """Start main event loop

        Parameters
        ----------
        background : bool, optional
            Whether to launch the main loop in the
            background. If true will spawn subprocess and continue,
            by default False.
        """
        self._launch_workers()
        self._launch_senders()
        time.sleep(1)
        if not background:
            self._producer_routine()
        else:
            self._launch_producer()

    def _connect_worker(self):
        """Connect worker IO sockets"""
        self.worker_data_socket = self.context.socket(zmq.PULL)
        self.worker_data_socket.connect(self.worker_socket_address)
        for idx in range(self.n_senders):
            socket = self.context.socket(zmq.PUSH)
            socket.connect(self.sender_socket_address + f"_{idx:d}")
            self.sender_sockets.append(socket)

    def _connect_sender(self, idx: int):
        """Connect sender to processed data stream"""
        self.sender_data_socket = self.context.socket(zmq.PULL)
        self.sender_data_socket.bind(self.sender_socket_address + f"_{idx:d}")

    def _connect_producer(self):
        self.input_socket = self.context.socket(zmq.PUSH)
        self.input_socket.bind(self.worker_socket_address)

    def _worker_routine(self, worker_id: int = 0):
        self._connect_worker()
        self.logger.info(f'Worker {worker_id} launched')
        while True:
            data = self.worker_data_socket.recv_pyobj()
            data = self.analyzer.run(data)
            for idx in range(self.n_senders):
                prop = data[idx]
                msg = self.sink_connector.serializer.serialize(prop)
                self.sender_sockets[idx].send(msg)

    def _sender_routine(self, idx: int):
        self._connect_sender(idx)
        self.sink_connector.connect_subprocess(idx)
        self.logger.info(f'Sender {idx} launched')
        while True:
            msg = self.sender_data_socket.recv()
            self.sink_connector.send(msg)

    def _producer_routine(self):
        """Listen for incoming events."""
        self.running = True
        self.source_connector.connect()
        self._connect_producer()
        while self.running:
            data = self.source_connector.get_data()
            self.input_socket.send_pyobj(data)

    def _launch_senders(self):
        for idx in range(self.n_senders):
            self.senders.append(
                Process(target=self._sender_routine, args=(idx,))
            )
        for process in self.senders:
            process.daemon = True
            process.start()

    def _launch_workers(self):
        self.workers = [Process(target=self._worker_routine, args=(idx,)
                        for idx in range(self.n_workers)]
        for process in self.workers:
            process.daemon = True
            process.start()

    def _launch_producer(self):
        self.main_producer = Process(target=self._producer_routine)
        self.main_producer.daemon = True
        self.main_producer.start()
        self.logger.info('Producer launched')


