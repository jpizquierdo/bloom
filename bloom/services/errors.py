"""Service-layer errors, kept free of any web-framework coupling.

Routes/handlers translate these into HTTP responses; services stay agnostic.
"""


class NotFoundError(Exception):
    """A requested resource does not exist or is not accessible to the caller.

    Ownership failures raise this too (rather than a distinct "forbidden"),
    so the API does not leak the existence of other users' resources.
    """
