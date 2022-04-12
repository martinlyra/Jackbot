import asyncio
import json
import requests
import websockets
import uuid


class GameClient:
    def __init__(self) -> None:
        pass

    def on_recieve(self, msg_type, data) -> None:
        print(msg_type, data)


class HttpApiHandler:
    def __init__(self) -> None:
        pass

    async def fetch(self, path) -> str:
        raise NotImplementedError()


class WssApiHandler:
    def __init__(self) -> None:
        pass

    async def connect(self) -> str:
        raise NotImplementedError()

    async def fetch(self, path) -> str:
        raise NotImplementedError()

    async def send(self, path, args) -> None:
        raise NotImplementedError()

    async def recieve(self) -> str:
        raise NotImplementedError()

    async def close(self) -> None:
        raise NotImplementedError()


def mapping_to_uri(d: dict) -> str:
    return "?" + "&".join([
        "%s=%s" % (k, d[k])
        for k in d
    ])


class V2WssApiHandler(WssApiHandler):
    BASE_API_URI = "wss://{0}/api/v2/rooms/{1}/play"

    CONNECT_TIMEOUT = 10

    def __init__(self, host, code) -> None:
        self.host = host
        self.full_uri = self.BASE_API_URI.format(host, code)
        self.json_decoder = json.decoder.JSONDecoder()
        self.socket = None
        self.guid = uuid.uuid1()

    async def connect(self, join_as: str) -> bool:
        try:
            args = {
                "role": "player",
                "name": join_as,
                "format": "json",
                "user-id": self.guid
            }
            self.socket = await websockets.connect(
                self.full_uri + mapping_to_uri(args),
                subprotocols=["ecast-v0"],
            )

            await self.recieve(self.CONNECT_TIMEOUT)
            return True
        except Exception as e:
            print(e.with_traceback(None))
            return False

    async def recieve(self, timeout=100):
        response = await asyncio.wait_for(
            self.socket.recv(),
            timeout
        )
        result: dict = self.json_decoder.decode(response)

        opcode = result["opcode"]
        if opcode == "error":
            error = result["result"]
            raise Exception("WSS Error %i - %s" % (
                error["code"],
                error["msg"]
            ))

        return response


class V2HttpMode:
    UNSECURE = 1
    SECURE = 2


class V2HttpApiHandler(HttpApiHandler):
    PREFERRED_MODE = V2HttpMode.SECURE
    BASE_API_URL = "ecast.jackboxgames.com/api/v2"

    def __init__(self) -> None:
        self.__url_cache = None
        self.__mode = self.PREFERRED_MODE

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


class RoomProbeData:
    def from_json(json):
        inst = RoomProbeData()
        inst.ok = json["ok"]
        if (inst.ok):
            inst.body = json["body"]
        else:
            inst.error = json["error"]
        return inst

    def __init__(self) -> None:
        self.code = None
        self.ok = False
        self.error = None

    def __str__(self) -> str:
        var_info = str_list_public(self)
        return f"Probe for '{self.code}':\n{var_info}"


class RoomInfo:
    def __init__(self, body_json) -> None:
        self.app_id = body_json["appId"]
        self.app_tag = body_json["appTag"]
        self.audicene_enabled = body_json["audienceEnabled"]
        self.audicene_host = body_json["audienceHost"]
        self.code = body_json["code"]
        self.host = body_json["host"]
        self.locked = body_json["locked"]
        self.full = body_json["full"]
        self.moderation_enabled = body_json["moderationEnabled"]
        self.password_required = body_json["passwordRequired"]
        self.twitch_locked = body_json["twitchLocked"]
        self.locale = body_json["locale"]
        self.keep_alive = body_json["keepalive"]

    def __str__(self) -> str:
        var_info = str_list_public(self, 16)
        return f"Probe for '{self.code}':\n{var_info}"


async def try_find_room(api: HttpApiHandler, code: str) -> RoomProbeData:
    msg = await api.fetch(f"rooms/{code}")
    probe = RoomProbeData.from_json(msg.json())
    probe.code = code
    if (probe.ok):
        return (probe, RoomInfo(probe.body))
    return (probe, None)


def str_list_public(obj, padding: int = 8):
    var_name_fmt = "%%-%is" % padding
    return "\n".join([
        "-%s: %s" % (var_name_fmt % n, v)
        for n, v in public_attributes(obj)
    ])


def public_attributes(obj):
    d = obj.__dict__
    return [(k, d[k]) for k in d if not str.startswith(k, "__")]


async def async_main_http():
    api: HttpApiHandler = V2HttpApiHandler()

    probe, room = await try_find_room(api, "DODL")
    print(probe, room)

    # Join?
    wssapi: V2WssApiHandler = V2WssApiHandler(room.host, room.code)
    result = await wssapi.connect("AmongUs")
    print(result)

if __name__ == "__main__":
    asyncio.run(async_main_http())
