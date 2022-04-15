from jackbot.api.http import HttpApiHandler
from jackbot.utils import str_list_public


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
