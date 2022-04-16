import asyncio
import json
import logging
import websockets

from jackbot.api.wss import WssApiHandler
from jackbot.api.wss.error import WssError


def mapping_to_uri(d: dict) -> str:
    return "?" + "&".join([
        "%s=%s" % (k, d[k])
        for k in d
    ])


class V2WssApiHandler(WssApiHandler):
    BASE_API_URI = "wss://{0}/api/v2/rooms/{1}/play"

    CONNECT_TIMEOUT = 10
    MAX_SEND_TRIES = 3

    def __init__(self, log: logging.Logger, host, code, uuid) -> None:
        self.log = log
        self.host = host
        self.code = code
        self.full_uri = self.BASE_API_URI.format(host, code)

        self.uuid = uuid
        self.packet_counter = 0

        self.json_decoder = json.decoder.JSONDecoder()
        self.json_encoder = json.encoder.JSONEncoder()
        self.socket: websockets.client.WebSocketClientProtocol = None

    def is_connected(self) -> bool:
        return (
            self.socket is not None
            and not self.socket.closed
        )

    async def connect(self, join_as: str) -> tuple:
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
            welcome = await self.recieve(self.CONNECT_TIMEOUT)
            return (True, welcome)
        except Exception as e:
            self.log.error(e)
            await self.close()
            return (False, None)

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
                return (opcode, result, data)

    async def send(self, message, expect_reply=True) -> None:
        # Prepare the message for sending
        self.packet_counter += 1
        this_packet_counter = self.packet_counter
        message["seq"] = this_packet_counter

        to_send = self.json_encoder.encode(message)

        # Actually dispatch the message to server
        send_attempt = 0
        successful = False
        while send_attempt < self.MAX_SEND_TRIES and not successful:
            send_attempt += 1
            self.log.debug("SEND - (Try %i): %s" % (send_attempt, to_send))
            try:
                await self.socket.send(to_send)

                if expect_reply:
                    opcode, _, reply = await self.recieve(100)
                    if reply["re"] == this_packet_counter and opcode == "ok":
                        successful = True
                    else:
                        successful = False
                else:
                    successful = True
            except TimeoutError:
                pass
            except Exception as e:
                self.log.error("SEND - ERROR!: %s", e)
                raise e
