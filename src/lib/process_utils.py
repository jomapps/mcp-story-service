import multiprocessing
import logging

def worker_function(target, args):
    """
    A wrapper function for the target function to be executed in a separate process.
    """
    try:
        target(*args)
    except Exception as e:
        logging.exception(f"Error in worker process: {e}")
        raise

def create_process(target, args) -> multiprocessing.Process:
    """
    Creates a new process.
    """
    return multiprocessing.Process(target=worker_function, args=(target, args))

def terminate_process(process: multiprocessing.Process):
    """
    Terminates a process.
    """
    try:
        if process.is_alive():
            process.terminate()
    except Exception as e:
        logging.exception(f"Error terminating process: {e}")
    finally:
        # Always join to clean up the process
        try:
            process.join(timeout=5.0)
        except Exception as e:
            logging.exception(f"Error joining process: {e}")
