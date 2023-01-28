class SourceConnector(object):
    """Base class for source connectors."""

    def connect(self):
        raise NotImplementedError

    def get_data(self):
        raise NotImplementedError
