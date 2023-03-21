import threading
import contextvars
from types import SimpleNamespace


class Local:
    # TODO: we "delete" things per-context by setting their value to
    # this sentinel object. We can't just remove them from the top-level
    # storage object as that would delete the key in other contexts too.
    # This does mean that the storage object potentially grows without
    # bounds if you keep creating new locals? (Is this a problem? is there
    # a better way to do it?)
    DELETED = object()
    
    def __init__(self, thread_critical=False):
        self._thread_lock = threading.RLock()
        # TODO: this is set to a unique value to avoid context vars
        # conflicting (is this necessary) 
        self._context_id_prefix = f"asgiref_local_{id(self)}"
        if thread_critical:
            # thread_critical not maintained across threads 
            # (even when using async_to_sync), but is maintained with context
            # otherwise (TODO: is that right?)
            self._storage = threading.local()
        else:
            self._storage = SimpleNamespace()

    def __getattr__(self, key):
        with self._thread_lock:
            try:
                value = getattr(self._storage, key).get()
            except (AttributeError, LookupError):
                raise AttributeError(f"{self!r} object has no attribute {key!r}")
            else:
                # Local.DELETED is a sentinel to tell us if object has been deleted
                # in the local context (the same may still exist in a different context
                # so we never delete the key from the _storage entirely)
                if value is Local.DELETED:
                    raise AttributeError(f"{self!r} object has no attribute {key!r}")
                return value

    def __setattr__(self, key, value):
        if key in ("_storage", "_context_id_prefix", "_thread_lock"):
            return super().__setattr__(key, value)
        
        with self._thread_lock:

            if not hasattr(self._storage, key):
                setattr(self._storage, key, contextvars.ContextVar(
                    f"{self._context_id_prefix}_{key}"
                ))

            getattr(self._storage, key).set(value)

    def __delattr__(self, key):
        with self._thread_lock:
            if hasattr(self._storage, key):
                getattr(self._storage, key).set(Local.DELETED)

        
