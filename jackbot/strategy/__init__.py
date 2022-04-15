import json

from jackbot.api.wss.v2_impl import V2WssApiHandler
from jackbot.context import GameStrategy, JackboxGameContext
from jackbot.join_enums import JoinReason
from jackbot.room import RoomInfo
from jackbot.singleton import Singleton
from jackbot.utils import str_list_public


class DummyStrategy(GameStrategy):
    def __init__(self, context: JackboxGameContext) -> None:
        super().__init__(context)

    async def can_join(self, room_info: RoomInfo) -> JoinReason:
        return JoinReason.GAME_CAN_JOIN

    async def on_room_update(self, value) -> None:
        self.context.log.info("Received room update! - %s" % value)

    async def on_game_update(self, value) -> None:
        self.context.log.info("Received game update! - %s" % value)


class GameInfo:
    def __init__(self) -> None:
        self.name = None
        self.app_tag = None
        self.app_uuid = None
        self.pack = None
        self.strategy_type = None
        self.handler_type = None

    def __str__(self) -> str:
        var_info = str_list_public(self, 16)
        return f"Game info for '{self.app_tag}':\n{var_info}"


class JackboxGameRegistry(metaclass=Singleton):
    DEFAULT_CLIENT = "DEFAULT"
    SINGLETON_INSTANCE = None

    def __init__(self):
        self.tag_database = {
            f"{self.DEFAULT_CLIENT}": (DummyStrategy, V2WssApiHandler)
        }
        self.uuid_database = {
            f"{self.DEFAULT_CLIENT}": (DummyStrategy, V2WssApiHandler)
        }

    def load_from(self, json_file_path: str) -> None:
        with open(json_file_path, 'r') as f:
            raw = json.load(f)
            games = raw["games"]

            for game in games:
                info = GameInfo()
                info.name = game["name"]
                info.app_tag = game["tag"]
                info.app_uuid = game["uuid"]
                info.pack = game["pack"]
                info.strategy_type = DummyStrategy
                info.handler_type = V2WssApiHandler

                self.tag_database[info.app_tag] = info
                self.uuid_database[info.app_uuid] = info

    def register(self, app_tag: str, strategy_type) -> None:
        self.tag_database[app_tag].strategy_type = strategy_type

    def get_game_by_tag(self, app_tag: str) -> GameInfo:
        selector = app_tag
        return (
            self.tag_database[selector]
            if app_tag in self.tag_database else
            None
        )

    def get_game_by_uuid(self, app_id: str) -> GameInfo:
        selector = app_id
        return (
            self.tag_database[selector]
            if selector in self.tag_database else
            None
        )
