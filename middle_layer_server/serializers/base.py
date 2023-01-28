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
        # Check that data is a list as expected
        if isinstance(data, list):
            for prop in data:
                for key, item in prop.items():
                    if isinstance(item, np.ndarray):
                        # convert array to list
                        prop[key] = item.tolist()
        else:
            raise ValueError(f'Invalid datatype. Expected list \
                               of dicts, but got {type(data)}.')

        return json.dumps(data)
