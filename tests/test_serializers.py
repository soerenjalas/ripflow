import unittest
import numpy as np
import avro.schema
from avro.io import BinaryDecoder
from io import BytesIO
from middle_layer_analyzer.serializers import JsonSerializer, AvroSerializer


class TestJsonSerializer(unittest.TestCase):
    def test_serialize(self):
        serializer = JsonSerializer()

        data = {
            "a": 1,
            "b": "hello",
            "c": np.array([1, 2, 3]),
            "d": {"e": np.array([4, 5, 6]), "f": "world"},
        }

        expected_result = b'{"a": 1, "b": "hello", "c": [1, 2, 3], "d": {"e": [4, 5, 6], "f": "world"}}'

        result = serializer.serialize(data)

        self.assertEqual(result, expected_result)


class TestAvroSerializer(unittest.TestCase):
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

    def test_serialize_with_numpy(self):
        data = {
            "data": np.array([1.0, 2.0, 3.0]),
            "type": "A_FLOAT",
            "timestamp": 1645633217.123456,
            "macropulse": 12345,
            "miscellaneous": {"key": "value"},
            "name": "test",
        }

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
