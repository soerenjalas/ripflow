import unittest
import numpy as np
import avro.schema
from avro.io import BinaryDecoder
from io import BytesIO
from middle_layer_analyzer.serializers import JsonSerializer, AvroSerializer


class TestSerializers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.avro_schema = """
        {
            "namespace": "example.avro",
            "type": "record",
            "name": "Test",
            "fields": [
                {"name": "data", "type": {"type": "array", "items": "float"}},
                {"name": "type", "type": "string"},
                {"name": "timestamp", "type": "double"},
                {"name": "macropulse", "type": "int"},
                {"name": "miscellaneous", "type":{"type": "map", "values": "string"}},
                {"name": "name", "type": "string"}
            ]
        }
        """
        cls.data = {
            "data": np.array([1.0, 2.0, 3.0]),
            "type": "A_FLOAT",
            "timestamp": 1645633217.123456,
            "macropulse": 12345,
            "miscellaneous": {"key": "value"},
            "name": "test",
        }

    def test_serialize_avro(self):
        data = self.data.copy()

        serializer = AvroSerializer(self.avro_schema)
        serialized_data = serializer.serialize(data)

        reader_schema = avro.schema.parse(self.avro_schema)
        bytes_reader = BytesIO(serialized_data)
        decoder = BinaryDecoder(bytes_reader)
        datum_reader = avro.io.DatumReader(reader_schema)

        decoded_data = datum_reader.read(decoder)
        # Convert numpy array to list to compare with original data
        data["data"] = data["data"].tolist()
        self.assertEqual(decoded_data, data)

    def test_serialize(self):
        serializer = JsonSerializer()
        data = self.data.copy()
        expected_result = b'{"data": [1.0, 2.0, 3.0], "type": "A_FLOAT", "timestamp": 1645633217.123456, "macropulse": 12345, "miscellaneous": {"key": "value"}, "name": "test"}'
        result = serializer.serialize(data)
        self.assertEqual(result, expected_result)
