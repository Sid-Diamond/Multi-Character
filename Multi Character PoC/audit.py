"""Optional second evaluation stage for saved subject and judge results."""


def require_available(enabled):
    """Reject an audit request before any paid model calls until it is specified."""
    if type(enabled) is not bool:
        raise ValueError("audit must be true or false")
    if enabled:
        raise NotImplementedError("The new-run audit method is not configured; set audit to False")


def append_rows(experiment, rows):
    """Future audit: append count rows with the same fields and outcome='strict'."""
    raise NotImplementedError("The new-run audit method is not configured")
