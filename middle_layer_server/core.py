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
    """

    def __init__(self,
                 source_connector: SourceConnector,
                 sink_connector: SinkConnector = None,
                 analyzer: BaseAnalyzer = None,
                 n_workers: int = 2,
                 ) -> None:
        """Construct main server object"""
        self.source_connector = source_connector
        self.sink_connector = sink_connector
        self.analyzer = analyzer
        # Initialize sink connector
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

    def _worker_routine(self):
        self._connect_worker()
        while True:
            data = self.worker_data_socket.recv_pyobj()
            # print('worker: {}'.format(data[0]['macropulse']))
            data = self.analyzer.run(data)
            for idx in range(self.n_senders):
                prop = data[idx]
                msg = self.sink_connector.serializer.serialize(prop)
                self.sender_sockets[idx].send(msg)

    def _sender_routine(self, idx: int):
        self._connect_sender(idx)
        self.sink_connector.connect_subprocess(idx)
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
            # print('producer: {}'.format(data[0]['macropulse']))
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
        self.workers = [Process(target=self._worker_routine)
                        for _ in range(self.n_workers)]
        for process in self.workers:
            process.daemon = True
            process.start()

    def _launch_producer(self):
        self.main_producer = Process(target=self._producer_routine)
        self.main_producer.daemon = True
        self.main_producer.start()

    
