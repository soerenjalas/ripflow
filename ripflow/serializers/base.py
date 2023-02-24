class Serializer(object):
    """Base class for serializers"""

    def serialize(self, data: dict) -> bytes:
        raise NotImplementedError
