from ripflow.core.utils import Child
import logging
from typing import Dict

import time
from datetime import datetime, timedelta
from threading import Thread, Event


class RestartPolicy:
    def __init__(self, n_restart: int, restart_delay: int, reset_window: int):
        self._n_restart = n_restart
        self._restart_delay = restart_delay
        self._reset_window = reset_window

    @property
    def n_restart(self):
        return self._n_restart

    @property
    def restart_delay(self):
        return self._restart_delay

    @property
    def reset_window(self):
        return self._reset_window


class Supervisor(object):
    def __init__(self, logger: logging.Logger):
        self._processes: Dict[Child, Dict] = (
            {}
        )  # Stores Child processes with their policies and metadata
        self.logger = logger

    def add_process(self, process: Child, policy: RestartPolicy):
        """
        Adds a process to the supervisor with a specified restart policy.
        """
        self._processes[process] = {
            "policy": policy,
            "restart_count": 0,
            "last_restart": None,
            "reset_timer": datetime.now(),
            "thread": None,  # Placeholder for the monitoring thread
            "stop_event": Event(),  # Event to signal the monitoring thread to stop
        }

    def start_all_processes(self, delay: float = 0):
        """
        Starts all managed child processes.
        """
        for process in self._processes.keys():
            self.start_process(process)
            time.sleep(delay)

    def start_process(self, process: Child):
        """
        Starts a single child process and initializes its monitoring thread.
        """
        # Ensure the process isn't already running
        if not process.is_alive():  # type: ignore
            process.launch()  # type: ignore
            self.logger.info(f"Supervisor: Process {process} started.")
        else:
            self.logger.info(f"Supervisor: Process {process} is already running.")

    def _reset_restart_count(self, process: Child):
        """
        Resets the restart count for a process based on the reset_window.
        """
        process_info = self._processes[process]
        if datetime.now() >= process_info["reset_timer"]:
            process_info["restart_count"] = 0
            process_info["reset_timer"] = datetime.now() + timedelta(
                seconds=process_info["policy"].reset_window
            )

    def restart_process(self, process: Child):
        """
        Attempts to restart a process according to its restart policy.
        """
        process_info = self._processes[process]
        policy = process_info["policy"]

        self._reset_restart_count(process)

        if process_info["restart_count"] < policy.n_restart:
            time.sleep(policy.restart_delay)  # Wait before restarting
            process.launch()  # type: ignore
            process_info["restart_count"] += 1
            process_info["last_restart"] = datetime.now()
            self.logger.info(
                f"Process {process} restarted. Count: {process_info['restart_count']}"
            )
        else:
            self.logger.info(f"Process {process} reached maximum restart limit.")

    def stop_process(self, process: Child):
        """
        Stops a given process.
        """
        process.stop()  # type: ignore
        if process in self._processes:
            process_info = self._processes[process]
            process_info["stop_event"].set()  # Signal monitoring thread to stop
            if process_info["thread"]:
                process_info["thread"].join()  # Wait for monitoring thread to finish
            del self._processes[process]

    def _monitor_process(self, process: Child):
        """
        Monitors a process and restarts it if it stops unexpectedly.
        """
        stop_event = self._processes[process]["stop_event"]
        while not stop_event.is_set():
            if not process.is_alive():  # type: ignore
                self.logger.info(f"Supervisor: Process {process} stopped unexpectedly.")
                self.restart_process(process)
            time.sleep(1)  # Polling interval

    def monitor_processes(self):
        """
        Starts monitoring threads for all managed processes.
        """
        for process in self._processes.keys():
            if not self._processes[process]["thread"]:
                thread = Thread(target=self._monitor_process, args=(process,))
                thread.start()
                self._processes[process]["thread"] = thread
                self.logger.info(
                    f"Supervisor: Monitoring thread for process {process} started."
                )

    def stop(self):
        """
        Stops all managed processes.
        """
        # Create a list of keys to iterate over
        processes_to_stop = list(self._processes.keys())
        for process in processes_to_stop:
            self.stop_process(process)
