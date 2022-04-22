from enum import IntEnum
import logging
from math import floor
from aitextgen import aitextgen
import regex

from jackbot.singleton import Singleton


BLANKS_PATTERN = regex.compile(r"_+")
PUNCTUATION_PATTERN = regex.compile(r"[.!?]+")


def count_tokens(text: str) -> None:
    return floor(len(text)/4)


def should_fill_in(text: str) -> bool:
    return len(BLANKS_PATTERN.findall(text)) > 0


def output_to_answer(prompt: str, aiout: str) -> str:
    ai_generated = aiout[len(prompt):]
    stripped = ai_generated.replace("\n", " ").strip()
    return PUNCTUATION_PATTERN.split(stripped)[0].strip()


class PromptAnswerMethod(IntEnum):
    FILLIN_BLANKS = 0
    QUIP = 1


class AiTextOracle(metaclass=Singleton):
    def __init__(self, logger: logging.Logger = None) -> None:
        self.ai = aitextgen()
        self.ai_temperature = 2.4

        self.logger = logger
        if logger is None:
            self.logger = logging.getLogger("aitextgen")
            self.logger.setLevel(logging.INFO)

        pass

    async def generate_answer(self, prompt: str) -> str:
        method = (
            PromptAnswerMethod.FILLIN_BLANKS
            if should_fill_in(prompt) else
            PromptAnswerMethod.QUIP
        )
        self.logger.debug("PROMPT: %s" % prompt)
        self.logger.debug("METHOD: %s" % method)
        match method:
            case PromptAnswerMethod.FILLIN_BLANKS:
                return await self.answer_fillin_blanks(prompt)
            case PromptAnswerMethod.QUIP:
                return await self.answer_quip(prompt)

    async def answer_fillin_blanks(self, prompt: str) -> str:
        pieces = BLANKS_PATTERN.split(prompt)

        p = pieces[0]

        ntokens = count_tokens(p)
        min_n = ntokens + 2
        max_n = ntokens + 8

        return await self.get_clean_answer(p, min_n, max_n)

    async def answer_quip(self, prompt: str) -> str:
        p = "Q: %s?\nA:" % prompt

        ntokens = count_tokens(p)
        min_n = ntokens + 2
        max_n = ntokens + 8

        return await self.get_clean_answer(p, min_n, max_n)

    async def get_clean_answer(self, prompt, min_tokens, max_tokens) -> str:
        output = self.ai.generate(
            n=1,
            prompt=prompt,
            temperature=self.ai_temperature,
            min_length=min_tokens,
            max_length=max_tokens,
            return_as_list=True
        )[0]

        answer = output_to_answer(prompt, output)
        self.logger.debug("ANSWER: %s" % answer)
        self.logger.debug("LENGTH: %i" % len(answer))
        return answer
