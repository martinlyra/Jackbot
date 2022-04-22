import asyncio
import logging
from jackbot.orcale import AiTextOracle

prompts = [
    "A good punishment for an unruly child is to simply look him in the eye and tell him _____",
    "Something you shouldn't say to a mafia godfather",
    "What you say three times to summon Donald Trump",
    "Ctrl + Shift + Alt + 6 is the little known keyboard shortcut to do this",
    "The most awesome thing to say before you dramatically flip a scarf over your shoulder",
    "A shocking thing to see digging through your garbage at night",
    "A terrible thing to tell your kid when the dog dies",
    "What a caveman says right after sex"
]


async def async_main():
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    oracle = AiTextOracle(logger)
    print("aitextgen is ready!")
    for prompt in prompts:
        await oracle.generate_answer(prompt)
        print("\n")

if __name__ == "__main__":
    asyncio.run(async_main())
