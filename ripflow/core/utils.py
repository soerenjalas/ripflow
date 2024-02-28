from abc import ABC, abstractmethod
from multiprocessing import Process
import zmq
import logging
from typing import List, Any


class CommsFactory(ABC):
    @abstractmethod
    def create_context(self) -> None:
        pass

    @abstractmethod
    def create_socket(self, context, **kwargs) -> Any:
        pass

    @abstractmethod
    def cleanup(self, context, sockets) -> None:
        pass


class ZMQFactory(CommsFactory):
    """
    Factory class for zmq context and socket creation
    """

    def create_context(self) -> zmq.Context:
        return zmq.Context()

    def create_socket(self, context, **kwargs):
        # Verify required arguments
        if "socket_type" not in kwargs:
            raise ValueError(
                f"Missing required argument: 'socket_type' not in {kwargs}"
            )

        socket_type = kwargs.get("socket_type")
        bind_address = kwargs.get("bind_address", None)
        connect_address = kwargs.get("connect_address", None)

        if not bind_address and not connect_address:
            raise ValueError(
                "Either 'bind_address' or 'connect_address' must be provided"
            )
        if socket_type not in [zmq.PUSH, zmq.PULL, zmq.PUB, zmq.SUB, zmq.REQ, zmq.REP]:
            raise ValueError(f"Invalid 'socket_type': {socket_type}")

        socket = context.socket(socket_type)
        if bind_address:
            socket.bind(bind_address)
        if connect_address:
            socket.connect(connect_address)
        return socket

    def cleanup(self, context: zmq.Context, sockets: List[zmq.Socket]) -> None:
        for socket in sockets:
            socket.close()
        context.term()


class ProcessMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if "main_routine" not in attrs:
            raise NotImplementedError(f"{name} must implement the main_routine method")

        original_init = attrs.get("__init__", lambda self: None)

        def __init__(self, *args, **kwargs) -> None:
            original_init(self, *args, **kwargs)
            self.process = None

        attrs["__init__"] = __init__

        def launch(self) -> None:
            if self.process is None or not self.process.is_alive():
                self.process = Process(target=self.main_routine, daemon=True)
                self.process.start()
                self.logger.info(f"{name} process launched")

        attrs["launch"] = launch

        def stop(self) -> None:
            if self.process and self.process.is_alive():
                self.process.terminate()
                self.process.join()
                self.logger.info(f"{name} process stopped")

        attrs["stop"] = stop

        def is_alive(self) -> bool:
            return self.process is not None and self.process.is_alive()

        attrs["is_alive"] = is_alive

        return super().__new__(cls, name, bases, attrs)


class Child(metaclass=ProcessMetaclass):
    """
    Base class for producer, worker and sender processes
    """

    def __init__(self, logger: logging.Logger, comms_factory: CommsFactory) -> None:
        self.logger = logger
        self.comms_factory = comms_factory

    def main_routine(self):
        # To be implemented by subclasses
        raise NotImplementedError
