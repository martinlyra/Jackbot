import requests

from jackbot.api.http import HttpApiHandler


class V2HttpMode:
    UNSECURE = 1
    SECURE = 2


class V2HttpApiHandler(HttpApiHandler):
    PREFERRED_MODE = V2HttpMode.SECURE
    BASE_API_URL = "ecast.jackboxgames.com/api/v2"

    def __init__(self, log) -> None:
        self.__url_cache = None
        self.__mode = self.PREFERRED_MODE
        self.log = log

    def __base_url(self) -> str:
        if(self.__url_cache is None):
            protocol = (
                "https"
                if self.__mode is V2HttpMode.SECURE else
                "http"
            )
            base = self.BASE_API_URL
            self.__url_cache = f"{protocol}://{base}"
        return self.__url_cache

    def __get(self, path) -> str:
        target = f"{self.__base_url()}/{path}"
        print(target)
        response = requests.get(target)
        return response

    async def fetch(self, path) -> str:
        return self.__get(path)
