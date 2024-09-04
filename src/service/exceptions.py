class ServiceError(Exception):
    pass


class DuplicateError(ServiceError):
    pass


class InvalidArgumentTypeError(ServiceError):
    pass


class ExtraArgumentError(ServiceError):
    pass


"""invalid arg type -> dbapi"""
"""DuplicateError -> integrity """
"""Extra arg -> Compile"""
