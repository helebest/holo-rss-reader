"""
Process exit codes used by the CLI.
"""

OK = 0
PARAM_ERROR = 2
NETWORK_ERROR = 3
PARSE_ERROR = 4
STORAGE_ERROR = 5


def from_error_kind(error_kind: str) -> int:
    """
    Map internal error kinds to process exit codes.
    """
    if error_kind == "network":
        return NETWORK_ERROR
    if error_kind == "parse":
        return PARSE_ERROR
    if error_kind == "storage":
        return STORAGE_ERROR
    if error_kind == "validation":
        return PARAM_ERROR
    return NETWORK_ERROR
