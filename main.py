import asyncio
from math import prod
import random
import uuid
import logging
import sys

from jackbot.api.http import HttpApiHandler
from jackbot.api.http.v2_impl import V2HttpApiHandler
from jackbot.api.wss import WssApiHandler
from jackbot.context import JackboxGameContext
from jackbot.player_info import PlayerInfo
from jackbot.strategy import JackboxGameRegistry
from jackbot.logging import create_game_logger, create_wss_api_logger
from jackbot.room import try_find_room
from jackbot.strategy.quiplash2 import Quiplash2Strategy


async def async_try_play_once(join_code: str, join_as: str):
    logging.basicConfig()
    main_logger = logging.getLogger(__name__)
    main_logger.setLevel(logging.DEBUG)
    main_logger.addHandler(logging.FileHandler("logs/main.log"))

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
    game_info = JackboxGameRegistry().get_game_by_tag(app_tag)
    if game_info is None:
        main_logger.error("Unknown game! Known by tag '%s'" % app_tag)
        return

    strategy_type = game_info.strategy_type
    handler_type = game_info.handler_type

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

    player_info = PlayerInfo()
    player_info.name = join_as
    player_info.uuid = this_uuid

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
    context = JackboxGameContext(
        player_info,
        wss_api,
        game_logger
    )
    context.set_strategy(strategy_type)

    # Join?
    result = await context.join(join_as)
    if result:
        # Joined, let's play
        main_logger.info(
            "Succesfully joined room '%s' to play '%s' as '%s'!"
            % (join_code, game_info.name, join_as)
        )
        main_logger.info(f"Playing '{app_tag}' until finished...")
        await context.play_until_finished()
    else:
        # Couldn't join
        main_logger.info("Join was not successful, going home.")

if __name__ == "__main__":
    nargs = len(sys.argv)
    code = sys.argv[1]
    name = sys.argv[2] if nargs >= 2 else "Pyamgos"

    JackboxGameRegistry().load_from("./jackbox_games.json")
    JackboxGameRegistry().register("quiplash2", Quiplash2Strategy)
    asyncio.run(async_try_play_once(code, name))
