import logging
import threading

class RunLogContext:
    """
    A context manager for run-specific logging.
    
    This implementation uses the "Ambient Context Pattern", where context information
    is implicitly propagated through the call stack without explicitly passing it as parameters
    must be avoided. This is achieved through thread-local storage (threading.local) 
    isolation.
    
    Benefits:
    - The logger can be used anywhere in the code without explicit context
    - Functions in the call chain do not need to know about the context
    - External libraries can use the logger without modification
    - Thread-safe through isolation of context per thread
    
    Example:
        with RunLogContext(run_id):
            logger.info("This message is logged in the run context")
    """
    _thread_local = threading.local()

    @classmethod
    def get_current_run_id(cls):
        return getattr(cls._thread_local, 'run_id', None)

    def __init__(self, run_id):
        self.run_id = run_id

    def __enter__(self):
        RunLogContext._thread_local.run_id = self.run_id
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        RunLogContext._thread_local.run_id = None


class LogFilter(logging.Filter):
    """
    Filter for separating app-specific and run-specific logs.
    """
    def __init__(self, is_run_specific):
        super().__init__()
        self.is_run_specific = is_run_specific

    def filter(self, record):
        record_has_run = hasattr(record, 'run_id') and record.run_id is not None
        if self.is_run_specific:
            return record_has_run
        return not record_has_run


def get_logger(name=None):
    """
    Creates a logger that automatically adds the run_id from the RunLogContext.
    """
    logger = logging.getLogger(name)

    def wrap_log_method(method):
        def wrapped(*args, **kwargs):
            extra = kwargs.get('extra', {})
            run_id = RunLogContext.get_current_run_id()
            if run_id is not None:
                extra['run_id'] = run_id
            kwargs['extra'] = extra
            return method(*args, **kwargs)
        return wrapped

    logger.info = wrap_log_method(logger.info)
    logger.debug = wrap_log_method(logger.debug)
    logger.warning = wrap_log_method(logger.warning)
    logger.error = wrap_log_method(logger.error)
    logger.critical = wrap_log_method(logger.critical)

    return logger
