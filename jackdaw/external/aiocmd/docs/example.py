import asyncio

from prompt_toolkit.completion import WordCompleter

from aiocmd import aiocmd


class MyCLI(aiocmd.PromptToolkitCmd):

    def __init__(self, my_name="My CLI"):
        super().__init__()
        self.prompt = "%s $ " % my_name
        self.aliases["nap"] = "sleep"

    def do_my_action(self):
        """This will appear in help text"""
        print("You ran my action!")

    def do_add(self, x, y):
        print(int(x) + int(y))

    def do_echo(self, to_echo):
        print(to_echo)

    async def do_sleep(self, sleep_time=1):
        await asyncio.sleep(int(sleep_time))

    def _add_completions(self):
        return WordCompleter([str(i) for i in range(9)])

    def _sleep_completions(self):
        return WordCompleter([str(i) for i in range(1, 60)])


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(MyCLI().run())
