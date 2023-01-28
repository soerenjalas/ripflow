from middle_layer_server.core import PythonMiddleLayerServer
from middle_layer_server.connectors.source import PydoocsSourceConnector
from middle_layer_server.connectors.sink import STDOUTSinkConnector
from middle_layer_server.analyzers import BaseAnalyzer


source_connector = PydoocsSourceConnector(
    source_properties=["FLASH.LASER/MOD24.CAM/Input.11.NF/IMAGE_EXT_ZMQ"])
sink_connector = STDOUTSinkConnector()
analyzer = BaseAnalyzer()

server = PythonMiddleLayerServer(
    source_connector=source_connector,
    sink_connector=sink_connector,
    analyzer=analyzer)

server.event_loop()
