from .base import Serializer
import avro.schema
import avro.io
import io
import numpy as np
from typing import Any


class AvroSerializer(Serializer):
    """Avro serializer with NumPy support"""

    def __init__(self, schema_str: str):
        self.schema = avro.schema.parse(schema_str)

    def serialize(self, data: dict) -> bytes:
        writer_schema = self.schema
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        datum_writer = avro.io.DatumWriter(writer_schema)

        def encode(obj: Any) -> Any:
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj

        datum = {k: encode(v) for k, v in data.items()}
        datum_writer.write(datum, encoder)
        serialized_data = bytes_writer.getvalue()

        return serialized_data
