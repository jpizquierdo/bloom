"""Service-layer errors, kept free of any web-framework coupling.

Routes/handlers translate these into HTTP responses; services stay agnostic.
"""


class NotFoundError(Exception):
    """A requested resource does not exist or is not visible to the caller.

    Used for private resources (brews, tastings): an ownership failure raises
    this rather than a distinct "forbidden", so the API does not leak the
    existence of other users' resources.
    """


class ForbiddenError(Exception):
    """The resource is visible to the caller but they may not modify it.

    Used for shared resources (beans): everyone can read them, but only the
    owner (or an admin) may edit or delete, so a 403 is the honest answer.
    """
