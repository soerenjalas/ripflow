from .base import Serializer
import numpy as np
import json
from typing import Any


class JsonSerializer(Serializer):
    """JSON serializer with NumPy support"""

    def serialize(self, data: dict) -> bytes:
        def encode(obj: Any) -> Any:
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj

        return json.dumps(data, default=encode).encode("utf-8")
