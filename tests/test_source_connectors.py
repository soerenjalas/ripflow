
def test_pydoocs_connector():
    from middle_layer_server.connectors.source import PydoocsSourceConnector
    Connector = PydoocsSourceConnector(source_properties=["FLASH.LASER/MOD24.CAM/Input.11.NF/IMAGE_EXT_ZMQ"])
    Connector.connect()
    collected_data = list()
    for i in range(10):
        data = Connector.get_data()
        collected_data.append(data)
    assert len(collected_data) == 10
    print(data)

if __name__ == "__main__":
    test_pydoocs_connector()
        