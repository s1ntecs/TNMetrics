class DomainError(Exception):
    pass


class NotFoundError(DomainError):
    pass


class PermissionDeniedError(DomainError):
    pass


class ValidationError(DomainError):
    pass
