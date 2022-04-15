class WssError(Exception):
    def __init__(self, *args: object) -> None:
        data = args[0]
        self.code = data["error"]
        self.message = data["msg"]
        super().__init__("WSS Error %i - %s" % (
            self.code,
            self.message
        ))
