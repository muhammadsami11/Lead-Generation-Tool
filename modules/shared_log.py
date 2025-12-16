import queue

# Shared logging queue used by frontend and backend modules to communicate status/messages
LOG_QUEUE = queue.Queue()

def log_status(message: str):
    """Put a status message into the shared queue for the frontend to read."""
    try:
        LOG_QUEUE.put(str(message))
    except Exception:
        # Best-effort: avoid crashing callers if logging fails
        pass
