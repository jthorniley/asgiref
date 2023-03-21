import contextvars
import threading

class CVar:
    def __init__(self):
        self._lock = threading.RLock()
        with self._lock:
            self._data = contextvars.ContextVar("asgiref-cvar")

    def __getattr__(self, key):
        with self._lock:
            storage_object = self._data.get({})
            try:
                return storage_object[key]
            except KeyError:
                raise AttributeError(key)
        
    def __setattr__(self, key, value) -> None:
        if key in ("_data", "_lock"):
            return super().__setattr__(key, value)

        with self._lock:
            storage_object = self._data.get({})
            storage_object[key] = value
            self._data.set(storage_object)

    def __delattr__(self, key) -> None:
        with self._lock:
            storage_object = self._data.get({})
            del storage_object[key]
            self._data.set(storage_object)
        

class Local:
    """Local storage for async tasks."""
    def __init__(self, thread_critical=False):
        if thread_critical:
            # Thread-local storage
            self._storage = threading.local()
        else:
            # Contextvar storage
            self._storage = CVar()

    def __getattr__(self, key):
        return getattr(self._storage, key)
            
    def __setattr__(self, key, value):
        if key == "_storage":
            return super().__setattr__(key, value)

        setattr(self._storage, key, value)

    def __delattr__(self, key):
        delattr(self._storage, key)

        
