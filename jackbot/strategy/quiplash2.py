import random
from jackbot.context import GameStrategy, JackboxGameContext
from jackbot.orcale import AiTextOracle


class Quiplash2VotingState:
    def __init__(self, json: dict) -> None:
        self.choices: dict = json["choices"]
        self.question_id: int = json["question"]["id"]
        self.prompt: str = json["question"]["prompt"]


class Quiplash2Strategy(GameStrategy):
    def __init__(self, context: JackboxGameContext) -> None:
        super().__init__(context)

        self.vote_state: Quiplash2VotingState = None

    async def game_vote(self) -> None:
        if self.vote_state is not None:
            prompt = self.vote_state.prompt
            choices = self.vote_state.choices

            choice = None
            if type(choices) is list:
                choice = random.choice(list(range(len(choices))))
            else:  # Should be a dict
                choice = random.choice(list(choices.keys()))

            self.context.log.info(
                "Voting '%s' -> '%s' for prompt \"%s\""
                % (choice, choices[choice], prompt)
            )
            await self.act({
                "vote": choice
            })
        else:
            self.context.log.error(
                "Error voting, there were no state to infer from!"
            )

    async def game_answer_question(self, question: dict) -> None:
        if question is not None:  # Make an answer
            qid = question["id"]
            prompt = question["prompt"]

            answer = await AiTextOracle().generate_answer(prompt)

            await self.act({
                "answer": answer,
                "questionId": qid
            })
        else:
            pass

    async def on_room_update(self, value) -> None:
        if "state" in value:
            state = value["state"]
            match state:
                case "Gameplay_Vote" | "Gameplay_R3Vote":
                    self.vote_state = Quiplash2VotingState(value)
                case _:
                    pass

    async def on_game_update(self, value) -> None:
        if "state" in value:
            state = value["state"]
            match state:
                case "Gameplay_AnswerQuestion":
                    question = value["question"]
                    if question is not None:
                        await self.game_answer_question(question)
                    else:
                        pass
                case "Gameplay_Vote" | "Gameplay_R3Vote":
                    done_voting = (
                        value["doneVoting"]
                        if state == "Gameplay_Vote" else
                        value["votesLeft"] <= 0.0
                    )
                    if not done_voting:
                        await self.game_vote()
                    else:
                        pass
