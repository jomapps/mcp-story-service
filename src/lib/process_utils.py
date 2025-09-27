import multiprocessing
import logging

def worker_function(target, args):
    """
    A wrapper function for the target function to be executed in a separate process.
    """
    try:
        target(*args)
    except Exception as e:
        logging.error(f"Error in worker process: {e}")

def create_process(target, args) -> multiprocessing.Process:
    """
    Creates a new process.
    """
    return multiprocessing.Process(target=worker_function, args=(target, args))

def terminate_process(process: multiprocessing.Process):
    """
    Terminates a process.
    """
    if process.is_alive():
        process.terminate()
        process.join()
