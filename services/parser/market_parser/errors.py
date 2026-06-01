class AdapterError(Exception):
    def __init__(self, marketplace: str, message: str) -> None:
        super().__init__(message)
        self.marketplace = marketplace


class AdapterUnavailableError(AdapterError):
    pass


class AdapterRateLimitedError(AdapterError):
    pass
