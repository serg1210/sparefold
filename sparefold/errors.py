"""Expected failures. CLI turns these into a message and a non-zero exit."""


class SparefoldError(Exception):
    """A failure the operator can act on. Not a bug."""


class ClaimError(SparefoldError):
    pass


class SubmitError(SparefoldError):
    pass


class SchemaError(SparefoldError):
    pass
