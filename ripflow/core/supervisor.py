from ripflow.core.utils import Child


import time
from datetime import datetime, timedelta
from threading import Thread


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
    def __init__(self, logger=None):
        self._processes = {}  # Stores Child processes with their policies and metadata
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
        }

    def start_all_processes(self):
        """
        Starts all managed child processes.
        """
        for process in self._processes.keys():
            self.start_process(process)

    def start_process(self, process: Child):
        """
        Starts a single child process and initializes its monitoring thread.
        """
        # Ensure the process isn't already running
        if not process.is_alive():  # type: ignore
            process.launch()  # type: ignore
            self.logger.info(f"Supervisor: Process {process} started.")
        else:
            self.logger(f"Supervisor: Process {process} is already running.")

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
            print(
                f"Process {process} restarted. Count: {process_info['restart_count']}"
            )
        else:
            print(f"Process {process} reached maximum restart limit.")

    def stop_process(self, process: Child):
        """
        Stops a given process.
        """
        process.stop()  # type: ignore
        if process in self._processes:
            process_info = self._processes[process]
            if process_info["thread"]:
                process_info["thread"].join()  # Wait for monitoring thread to finish
            del self._processes[process]

    def _monitor_process(self, process: Child):
        """
        Monitors a process and restarts it if it stops unexpectedly.
        """
        while True:
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
