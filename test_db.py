from jackbot.strategy import JackboxGameRegistry
from jackbot.strategy.quiplash2 import Quiplash2Strategy


if __name__ == "__main__":
    JackboxGameRegistry().load_from("./jackbox_games.json")
    JackboxGameRegistry().register("quiplash2", Quiplash2Strategy)
    print(JackboxGameRegistry().tag_database)
    print(JackboxGameRegistry().uuid_database)

    print(JackboxGameRegistry().get_game_by_tag("quiplash2"))
