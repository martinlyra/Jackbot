from jackbot.context import GameStrategy


class Quiplash2Strategy(GameStrategy):
    async def on_game_update(self, value) -> None:
        if "state" in value:
            state = value["state"]
            match state:
                case "Gameplay_AnswerQuestion":
                    question = value["question"]
                    qid = question["id"]
                    # prompt = question["prompt"]

                    await self.act({
                        "answer": "HHHH",
                        "questionId": qid
                    })
