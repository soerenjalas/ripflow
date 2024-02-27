import time
from typing import Optional
import logging


class BaseAnalyzer(object):
    def __init__(self):
        self._logger = None

    @property
    def logger(self):
        if self._logger is None:
            self._logger = logging.getLogger(self.__class__.__name__)
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger

    def run(self, data):
        return data

    @property
    def n_outputs(self):
        return NotImplementedError


class TestAnalyzer(BaseAnalyzer):
    """Test analyzer class."""

    def __init__(
        self, fake_load: float = 0.0, crash_after: Optional[int] = None
    ) -> None:
        """
        Initialize the CrashableTestAnalyzer.

        :param fake_load: Simulated load or delay in processing, in seconds.
        :param crash_after: Number of calls to `run` after which the analyzer should simulate a crash.
                            If None, the analyzer will not crash.
        """
        self.fake_load = fake_load
        self.crash_after = crash_after
        self.calls = 0  # Count the number of calls to `run`

    @property
    def n_outputs(self):
        return 1

    def run(self, data):
        """
        Return input data. Simulate a crash if conditions are met.
        """
        # Simulate processing load
        if self.fake_load > 0:
            time.sleep(self.fake_load)

        # Increment the call counter
        self.calls += 1

        # Check if it's time to simulate a crash
        if self.crash_after is not None and self.calls > self.crash_after:
            raise Exception("Simulated crash in CrashableTestAnalyzer")

        return [data]


class ImageProjector(BaseAnalyzer):
    """Example analysis class"""

    def __init__(self, fake_load: float = 0.0) -> None:
        self.fake_load = fake_load

    @property
    def n_outputs(self):
        return 2

    def run(
        self,
        data,
    ):
        """Replace raw image with projected image."""
        raw = data[0]
        out = []
        image = raw["data"].astype(int)
        proj = {}
        proj["data"] = image.sum(axis=0)
        proj["macropulse"] = raw["macropulse"]
        proj["name"] = "Projection"
        proj["timestamp"] = raw["timestamp"]
        proj["miscellaneous"] = raw["miscellaneous"]
        proj["type"] = "SPECTRUM"

        sum = {}
        sum["data"] = image.sum().astype(float)
        sum["macropulse"] = raw["macropulse"]
        sum["name"] = "Sum"
        sum["timestamp"] = raw["timestamp"]
        sum["miscellaneous"] = raw["miscellaneous"]
        sum["type"] = "FLOAT"

        out = [proj, sum]
        time.sleep(self.fake_load)
        return out
