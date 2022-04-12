import asyncio
import requests


class JackboxAPIHandler:
    def __init__(self) -> None:
        pass

    async def fetch(self, path) -> str:
        raise NotImplementedError()


class V2Mode:
    HTTP = 1
    HTTP_SECURE = 2


class V2ApiHandler(JackboxAPIHandler):
    PREFERRED_MODE = V2Mode.HTTP_SECURE
    BASE_API_URL = "ecast.jackboxgames.com/api/v2"

    def __init__(self) -> None:
        self.__url_cache = None
        self.__mode = self.PREFERRED_MODE

    def __base_url(self) -> str:
        if(self.__url_cache is None):
            protocol = (
                "https"
                if self.__mode is V2Mode.HTTP_SECURE else
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


class JackboxRoomData:
    def from_json(json):
        inst = JackboxRoomData()
        inst.ok = json["ok"]
        inst.error = json["error"]
        return inst

    def __init__(self) -> None:
        self.code = None
        self.ok = False
        self.error = None

    def __str__(self) -> str:
        var_info = "\n".join([
            "-%8s: %s" % (n, v)
            for n, v in public_attributes(self)
        ])
        return f"Room '{self.code}':\n{var_info}"


async def try_join_room(api: JackboxAPIHandler, code: str) -> JackboxRoomData:
    msg = await api.fetch(f"rooms/{code}")
    room = JackboxRoomData.from_json(msg.json())
    room.code = code
    return room


def public_attributes(obj):
    d = obj.__dict__
    return [(k, d[k]) for k in d if not str.startswith(k, "__")]


async def async_main_http():
    api: JackboxAPIHandler = V2ApiHandler()
    room = try_join_room(api, "AAAA")
    print(room)

if __name__ == "__main__":
    asyncio.run(async_main_http())
