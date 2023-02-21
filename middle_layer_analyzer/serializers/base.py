import numpy as np
import json


class Serializer(object):
    """Base class for serializers"""

    def serialize(self, data):
        raise NotImplementedError


class JsonSerializer(Serializer):
    """Simple Json string serializer"""

    def serialize(self, data):
        """Serialize data."""
        for key, item in data.items():
            if isinstance(item, np.ndarray):
                # convert array to list
                data[key] = item.tolist()
        return json.dumps(data).encode("utf-8")
