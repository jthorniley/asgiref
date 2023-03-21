import threading
import contextvars

class CVar:
    def __init__(self):
        self._data = contextvars.ContextVar("asgiref-cvar")
        self._data.set({})

    def __getattr__(self, key):
        storage_object = self._data.get()
        try:
            return storage_object[key]
        except KeyError:
            raise AttributeError(key)
        
    def __setattr__(self, key, value) -> None:
        if key == "_data":
            return super().__setattr__(key, value)
        
        storage_object = self._data.get()
        storage_object[key] = value
        self._data.set(storage_object)

    def __delattr__(self, key) -> None:
        storage_object = self._data.get()
        del storage_object[key]
        self._data.set(storage_object)
        

class Local:
    def __init__(self, thread_critical=False):
        self._thread_lock = threading.RLock()

        if thread_critical:
            # Thread-local storage
            self._storage = threading.local()
        else:
            # Contextvar storage
            self._storage = CVar()

    def __getattr__(self, key):
        with self._thread_lock:
            return getattr(self._storage, key)
            
    def __setattr__(self, key, value):
        if key in ("_storage", "_thread_lock"):
            return super().__setattr__(key, value)
        
        with self._thread_lock:
            setattr(self._storage, key, value)

    def __delattr__(self, key):
        with self._thread_lock:
            delattr(self._storage, key)

        
