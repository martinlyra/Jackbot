class HttpApiHandler:
    def __init__(self) -> None:
        pass

    async def fetch(self, path) -> str:
        raise NotImplementedError()
