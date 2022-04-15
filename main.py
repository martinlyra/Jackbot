import asyncio
import json
import random
from typing import Iterable
import requests
import websockets
import websockets.exceptions
import uuid
import logging
import sys
import os


class HttpApiHandler:
    def __init__(self) -> None:
        pass

    async def fetch(self, path) -> str:
        raise NotImplementedError()


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


def mapping_to_uri(d: dict) -> str:
    return "?" + "&".join([
        "%s=%s" % (k, d[k])
        for k in d
    ])


class WssError(Exception):
    def __init__(self, *args: object) -> None:
        data = args[0]
        self.code = data["error"]
        self.message = data["msg"]
        super().__init__("WSS Error %i - %s" % (
            self.code,
            self.message
        ))


class V2WssApiHandler(WssApiHandler):
    BASE_API_URI = "wss://{0}/api/v2/rooms/{1}/play"

    CONNECT_TIMEOUT = 10

    def __init__(self, log: logging.Logger, host, code, uuid) -> None:
        self.log = log
        self.host = host
        self.code = code
        self.full_uri = self.BASE_API_URI.format(host, code)

        self.uuid = uuid
        self.packet_counter = 0

        self.json_decoder = json.decoder.JSONDecoder()
        self.socket: websockets.client.WebSocketClientProtocol = None

    def is_connected(self) -> bool:
        return (
            self.socket is not None
            and not self.socket.closed
        )

    async def connect(self, join_as: str) -> bool:
        try:
            args = {
                "role": "player",
                "name": join_as,
                "format": "json",
                "user-id": self.uuid
            }
            self.socket = await websockets.connect(
                self.full_uri + mapping_to_uri(args),
                subprotocols=["ecast-v0"],
            )
            await self.recieve(self.CONNECT_TIMEOUT)
            return True
        except Exception as e:
            self.log.error(e)
            await self.close()
            return False

    async def close(self) -> None:
        await self.socket.close()

    async def recieve(self, timeout=None) -> tuple:
        response = await asyncio.wait_for(
            self.socket.recv(),
            timeout
        )
        self.log.info("RECV - '%s'" % response)

        try:
            parsed = self.__parse_response(response)
            return parsed
        except WssError as e:
            self.log.error(e)
            raise e

    def __parse_response(self, packet) -> tuple:
        data: dict = self.json_decoder.decode(packet)

        opcode = data["opcode"]
        result = data["result"]
        match opcode:
            case "error":
                raise WssError(result)
            case _:
                return (opcode, result)


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


class MinigameClient:
    def __init__(self, api: WssApiHandler, log: logging.Logger) -> None:
        self.api = api
        self.log = log

        self.is_finished = False
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        self.receive_handler = None

    async def join(self, join_as) -> bool:
        result = await self.api.connect(join_as)
        self.log.info("Result on join: %s" % result)
        return result

    async def listen_api(self) -> None:
        self.log.info("Started listening to Jackbox Services API")
        should_be_listening = True
        while self.api.is_connected() and should_be_listening:
            try:
                operation, data = await self.api.recieve(None)
                self.log.debug("Recieved %s ::: %s" % (operation, data))
                await self.on_recieve(operation, data)
            except websockets.exceptions.ConnectionClosedOK:
                should_be_listening = False
        self.log.info("Stopped listening to Jackbox Services API")

    async def on_recieve(self, operation, data) -> None:
        match operation:
            case "client/disconnected":
                await self.api.close()
                self.is_finished = True
            case _:
                pass

    def should_quit(self) -> bool:
        return (not self.api.is_connected()) or self.is_finished

    async def play_until_finished(self) -> None:
        self.receive_handler = self.loop.create_task(self.listen_api())

        while not self.should_quit():
            await asyncio.sleep(1)
        return


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
        var_info = str_list_public(self, 24)
        return f"Room Info for '{self.code}':\n{var_info}"


async def try_find_room(api: HttpApiHandler, code: str) -> RoomProbeData:
    msg = await api.fetch(f"rooms/{code}")
    probe = RoomProbeData.from_json(msg.json())
    probe.code = code
    if (probe.ok):
        return (probe, RoomInfo(probe.body))
    return (probe, None)


def str_list_public(obj, padding: int = 8):
    var_name_fmt = "%%%is" % padding
    return "\n".join([
        "-%s: %s" % (var_name_fmt % n, v)
        for n, v in public_attributes(obj)
    ])


def public_attributes(obj):
    d = obj.__dict__
    return [(k, d[k]) for k in d if not str.startswith(k, "__")]


DEFAULT_CLIENT = "DEFAULT"
APP_TAG_CLIENT_MAP = {
    # "quiplash2": (MinigameClient, V2WssApiHandler),
    f"{DEFAULT_CLIENT}": (MinigameClient, V2WssApiHandler)
}


def create_game_logger(path, file_prefix) -> logging.Logger:
    logger = logging.getLogger('game')
    logger.setLevel(logging.DEBUG)
    fn = f"{path}/{file_prefix}.game.log"
    if not os.path.exists(path):
        os.makedirs(path)
    fh = logging.FileHandler(fn)
    logger.addHandler(fh)
    return logger


def create_wss_api_logger(path, file_prefix) -> logging.Logger:
    logger = logging.getLogger('api_wss')
    logger.setLevel(logging.DEBUG)
    fn = f"{path}/{file_prefix}.wss_api.log"
    if not os.path.exists(path):
        os.makedirs(path)
    fh = logging.FileHandler(fn)
    logger.addHandler(fh)
    return logger


def prod(list: Iterable) -> any:
    return list[0] * (prod(list[1:]) if len(list) > 1 else 1)


async def async_try_play_once(join_code: str, join_as: str):
    logging.basicConfig()
    main_logger = logging.getLogger(__name__)
    main_logger.setLevel(logging.DEBUG)
    main_logger.addHandler(logging.FileHandler("main.log"))

    api: HttpApiHandler = V2HttpApiHandler(main_logger)

    # Probe for room first
    probe, room = await try_find_room(api, join_code)
    main_logger.debug(probe)
    main_logger.debug(room)
    if not probe.ok:
        main_logger.info(
            "Probe for room '%s' failed: %s" %
            (join_code, probe.error)
        )
        return

    # Setup
    # Select client
    app_tag = room.app_tag
    select_tag = DEFAULT_CLIENT
    if app_tag in APP_TAG_CLIENT_MAP.keys():
        select_tag = app_tag
    client_type, handler_type = APP_TAG_CLIENT_MAP[select_tag]

    name_seq = [ord(c) for c in join_as]
    name_seed = (prod(name_seq) - sum(name_seq)) * sum(name_seq)

    uuid_node = uuid.getnode()

    rand = random.Random()
    rand.seed(name_seed + uuid_node)

    uuid_seq = rand.getrandbits(128)
    uuid_gen = uuid.UUID(int=uuid_seq)

    this_uuid = uuid_gen.__str__()
    main_logger.info(
        "Assigned UUID: %s from seed produced from name: %i and node %i"
        % (this_uuid, name_seed, uuid_node)
    )

    game_logger = create_game_logger(
        "logs/%s/" % (join_code),
        "%s-%s" % (this_uuid, app_tag)
    )
    wss_api_logger = create_wss_api_logger(
        "logs/%s/" % (join_code),
        "%s-%s" % (this_uuid, app_tag)
    )

    wss_api: WssApiHandler = handler_type(
        wss_api_logger,
        room.host,
        room.code,
        this_uuid
    )
    client: MinigameClient = client_type(
        wss_api,
        game_logger
    )

    # Join?
    result = await client.join(join_as)
    if result:
        # Joined, let's play
        main_logger.info(
            "Succesfully joined room '%s' as '%s'!"
            % (join_code, join_as)
        )
        main_logger.info(f"Playing '{app_tag}' until finished...")
        await client.play_until_finished()
    else:
        # Couldn't join
        main_logger.info("Join was not successful, going home.")

if __name__ == "__main__":
    nargs = len(sys.argv)
    code = sys.argv[1]
    name = sys.argv[2] if nargs >= 2 else "Pyamgos"
    asyncio.run(async_try_play_once(code, name))
