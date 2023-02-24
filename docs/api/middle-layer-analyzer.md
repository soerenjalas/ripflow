# MiddleLayerAnalyzer
`ripflow.middle_layer_analyzer.MiddleLayerAnalyzer`

The `MiddleLayerAnalyzer` class is a Python object that provides an interface for analyzing incoming data from a `SourceConnector` and processing it using a provided Analyzer object. The processed data is then sent to an external system via a `SinkConnector`. The class is designed to work in parallel using multiple worker processes and is responsible for managing worker and sender processes using ZeroMQ sockets.

The class has the following parameters:

* `source_connector` : SourceConnector object that provides incoming data to the analyzer.
*  `sink_connector` : SinkConnector object that sends the processed data to an external system.
*  `analyzer` : Analyzer object that processes the incoming data, that inherits from the `BaseAnalyzer` base class.
*  `n_workers` : integer, number of worker processes to use for parallel processing. The default value is 2.
*  `log_file_path` : string, path to the log file. The default value is "server.log".
*  `log_level` : string, level of logging to use. The default value is "INFO".


The class provides the following method for starting the main event loop:

* `event_loop(background=False)` : starts the main event loop for processing incoming data using worker and sender processes. If background is False, the producer routine is launched and the process runs in the current thread and therefore blocks the code. If background is True, the producer routine is launched in a separate process and the method returns immediately.


The class uses ZeroMQ sockets for interprocess communication, allowing for efficient and scalable parallel processing of incoming data. Overall, the MiddleLayerAnalyzer class is a flexible and powerful tool for analyzing and processing large amounts of data in parallel.
