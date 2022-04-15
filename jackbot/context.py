import asyncio
import logging
import websockets

from jackbot.api.wss import WssApiHandler
from jackbot.join_enums import JoinReason
from jackbot.player_info import PlayerInfo
from jackbot.room import RoomInfo


class JackboxGameContext:
    pass


class GameStrategy:
    def __init__(self, context: JackboxGameContext) -> None:
        self.context = context
        self.customer_id = None

    async def can_join(self, room_info: RoomInfo) -> JoinReason:
        return JoinReason.GAME_NOT_SUPPORTED

    async def on_join(self, body) -> None:
        pass

    async def on_room_update(self, value) -> None:
        pass

    async def on_game_update(self, value) -> None:
        pass

    async def on_finished(self, body) -> None:
        pass

    async def act(self, action) -> None:
        await self.context.send(action)


class JackboxGameContext:
    def __init__(
        self,
        player: PlayerInfo,
        api: WssApiHandler,
        log: logging.Logger
    ) -> None:
        self.api = api
        self.log = log

        self.is_finished = False
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

        self.player_info = player
        self.costumer_key = "bc:customer:%s" % player.uuid

        self.game_handler: GameStrategy = None
        self.receive_handler = None

    def set_strategy(self, strategy_type):
        self.game_handler = strategy_type(self)

    async def join(self, join_as) -> bool:
        result, (_, welcome, _) = await self.api.connect(join_as)
        self.log.debug("Result on join: '%s', welcome: %s" % (result, welcome))

        # Set player details
        self.player_info.id = welcome["id"]
        self.player_info.secret = welcome["secret"]
        self.player_info.device = welcome["deviceId"]

        if result:
            await self.game_handler.on_join(welcome)
        return result

    async def listen_api(self) -> None:
        self.log.info("Started listening to Jackbox Services API")
        should_be_listening = True
        while self.api.is_connected() and should_be_listening:
            try:
                operation, data, f = await self.api.recieve(None)
                self.log.debug("Recieved %s ::: %s" % (operation, data))
                await self.on_recieve(operation, data, f)
            except websockets.exceptions.ConnectionClosedOK:
                should_be_listening = False
        self.log.info("Stopped listening to Jackbox Services API")

    async def on_recieve(self, operation: str, data: str, full: dict) -> None:
        match operation:
            case "client/disconnected":
                await self.api.close()
                await self.game_handler.on_finished(data)
                self.is_finished = True
            case "object":
                await self.handle_object(data)
            case _:
                self.log.error(
                    "Unknown opcode received: %s. - Packet: %s"
                    % (operation, full)
                )

    async def handle_object(self, data: str) -> None:
        key = data["key"]
        val = data["val"]

        match key:
            case "bc:room":
                await self.game_handler.on_room_update(val)
            case self.costumer_key:
                await self.game_handler.on_game_update(val)
            case _:
                self.log.error(
                    "Unknown object key received: %s. - Packet: %s"
                    % (key, data)
                )

    async def send(self, message: dict, to_whom: int = 1) -> None:
        data: dict = {
            "opcode": "client/send",
            "params": {
                "from": self.player_info.id,
                "to": to_whom,
                "body": message
            }
        }

        await self.api.send(data)

    def should_quit(self) -> bool:
        return (not self.api.is_connected()) or self.is_finished

    async def play_until_finished(self) -> None:
        self.receive_handler = self.loop.create_task(self.listen_api())

        while not self.should_quit():
            await asyncio.sleep(1)
        return
