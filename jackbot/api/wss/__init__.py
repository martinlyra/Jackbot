
class WssApiHandler:
    def __init__(self) -> None:
        pass

    def is_connected(self) -> bool:
        raise NotImplementedError()

    async def connect(self, join_as) -> bool:
        raise NotImplementedError()

    async def send(self, path, args) -> None:
        raise NotImplementedError()

    async def recieve(self, timeout) -> tuple:
        raise NotImplementedError()

    async def close(self) -> None:
        raise NotImplementedError()
