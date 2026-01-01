from .fifo import dispatch as fifo_dispatch
from .prioq import dispatch as priority_dispatch

_ALG_REGISTRY: dict[str, callable] = {
    "fifo": fifo_dispatch,
    "priority": priority_dispatch,
}

def get_algorithm(name: str = ""):
    # TODO: When we have a logging system, log a warning if the algorithm is not found
    return _ALG_REGISTRY.get(
        name.lower(), # Case-insensitive lookup
        fifo_dispatch # Default to fifo_dispatch if not found
    )

__all__ = [
    "fifo_dispatch",
    "get_algorithm",
]