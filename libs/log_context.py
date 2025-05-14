import logging
import threading

class RunLogContext:
    """
    Ein Context Manager für run-spezifisches Logging.
    
    Diese Implementierung nutzt das "Ambient Context Pattern", bei dem Kontext-Informationen
    implizit durch den Call Stack propagiert werden, ohne sie explizit als Parameter
    weitergeben zu müssen. Dies wird durch thread-lokalen Speicher (threading.local) 
    erreicht.
    
    Vorteile:
    - Logger kann überall im Code ohne expliziten Kontext verwendet werden
    - Funktionen in der Aufrufkette müssen den Kontext nicht kennen
    - Externe Bibliotheken können den Logger ohne Anpassung nutzen
    - Thread-sicher durch Isolation des Kontexts pro Thread
    
    Beispiel:
        with RunLogContext(run_id):
            logger.info("Diese Nachricht wird im Run-Kontext geloggt")
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
    Filter für die Trennung von App- und Run-spezifischen Logs.
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
    Erstellt einen Logger, der automatisch die run_id aus dem RunLogContext hinzufügt.
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
