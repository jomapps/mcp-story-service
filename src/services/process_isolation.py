import multiprocessing
from typing import Dict, Any, Callable

class ProcessIsolationManager:
    def __init__(self):
        self.processes: Dict[str, multiprocessing.Process] = {}

    def run_in_isolated_process(self, project_id: str, target: Callable, args: tuple) -> None:
        """
        Runs a target function in a separate process for the given project ID.
        """
        if project_id in self.processes and self.processes[project_id].is_alive():
            # A process for this project is already running.
            # In a real implementation, you might want to join the existing process
            # or handle this case in a more sophisticated way.
            return

        process = multiprocessing.Process(target=target, args=args)
        self.processes[project_id] = process
        process.start()

    def get_process(self, project_id: str) -> multiprocessing.Process:
        """
        Returns the process for the given project ID.
        """
        return self.processes.get(project_id)

    def terminate_process(self, project_id: str) -> None:
        """
        Terminates the process for the given project ID.
        """
        process = self.processes.get(project_id)
        if process:
            try:
                if process.is_alive():
                    process.terminate()
                    process.join(timeout=5.0)
                    if process.is_alive():
                        process.kill()
                        process.join()
            except Exception as e:
                import logging
                logging.exception(f"Error terminating process for project {project_id}: {e}")
            finally:
                # Always remove the process from the dict
                del self.processes[project_id]
