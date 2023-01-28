from .connectors.source import SourceConnector
from .connectors.sink import SinkConnector
from .analyzers import BaseAnalyzer
from multiprocessing import Process, Queue, Event


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
    max_queue_size : int, default 10
        Maximum number of events being process concurrently, event overflow will lead to data loss
    n_workers : int, default 2
        Number of analysis processes
    """

    def __init__(self,
                 source_connector: SourceConnector,
                 sink_connector: SinkConnector = None,
                 analyzer: BaseAnalyzer = None,
                 max_queue_size: int = 10,
                 n_workers: int = 2,
                 ) -> None:
        """Construct main server object"""
        self.source_connector = source_connector
        self.sink_connector = sink_connector
        self.analyzer = analyzer
        # Initialize sink connector
        sink_connector.initialize()
        # Connect source
        source_connector.connect()
        # Initialize event queue
        self.queue = Queue(maxsize=max_queue_size)
        self.n_workers = n_workers
        self.workers = None
        self.launch_workers()

    def process_events(self):
        while True:
            data = self.queue.get()
            data = self.analyzer.run(data)
            self.sink_connector.send(data)

    def launch_workers(self):
        self.workers = [Process(target=self.process_events)
                        for _ in range(self.n_workers)]
        for process in self.workers:
            process.start()

    def event_loop(self):
        while True:
            data = self.source_connector.get_data()
            self.queue.put(data)
