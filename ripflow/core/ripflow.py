from ripflow.analyzers import BaseAnalyzer
from ripflow.connectors.sink import SinkConnector
from ripflow.connectors.source import SourceConnector
from .processes import Producer, Sender, Worker
from .supervisor import RestartPolicy
from .supervisor import Supervisor
from .utils import ZMQFactory
import zmq
import logging
import sys


class Ripflow(object):
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
