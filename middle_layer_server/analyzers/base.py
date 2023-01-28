class BaseAnalyzer(object):
    def run(self, data):
        return data

class ImageProjector(BaseAnalyzer):
    """Example analysis class"""

    def run(self, data):
        """Replace raw image with projected image."""
        image = data[0]['data']
        image = image.astype(int).sum(axis=0)
        data[0]['data'] = image
        return data
