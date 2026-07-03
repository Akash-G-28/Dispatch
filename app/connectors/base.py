from abc import ABC, abstractmethod


class ConnectorError(RuntimeError):
    pass


class BaseConnector(ABC):
    name: str

    @abstractmethod
    async def healthcheck(self) -> dict: ...

