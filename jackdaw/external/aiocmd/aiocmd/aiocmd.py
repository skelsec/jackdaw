import asyncio
import inspect
import shlex
import signal
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

try:
    from prompt_toolkit.completion.nested import NestedCompleter
except ImportError:
    from aiocmd.nested_completer import NestedCompleter


class ExitPromptException(Exception):
    pass


class PromptToolkitCmd:
    """Baseclass for custom CLIs

    Works similarly to the built-in Cmd class. You can inherit from this class and implement:
        - do_<action> - This will add the "<action>" command to the cli.
                        The method may receive arguments (required) and keyword arguments (optional).
        - _<action>_completions - Returns a custom Completer class to use as a completer for this action.
    Additionally, the user cant change the "prompt" variable to change how the prompt looks, and add
    command aliases to the 'aliases' dict.
    """
    ATTR_START = "do_"
    prompt = "$ "
    doc_header = "Documented commands:"
    aliases = {"?": "help", "exit": "quit"}

    def __init__(self, ignore_sigint=True):
        self.completer = self._make_completer()
        self.session = None
        self._ignore_sigint = ignore_sigint
        self._currently_running_task = None

    async def run(self):
        if self._ignore_sigint and sys.platform != "win32":
            asyncio.get_event_loop().add_signal_handler(signal.SIGINT, self._sigint_handler)
        self.session = PromptSession(enable_history_search=True, key_bindings=self._get_bindings())
        try:
            with patch_stdout():
                await self._run_prompt_forever()
        finally:
            if self._ignore_sigint and sys.platform != "win32":
                asyncio.get_event_loop().remove_signal_handler(signal.SIGINT)
            self._on_close()

    async def _run_prompt_forever(self):
        while True:
            try:
                result = await self.session.prompt_async(self.prompt, completer=self.completer)
            except EOFError:
                return

            if not result:
                continue
            args = shlex.split(result)
            if args[0] in self.command_list:
                try:
                    self._currently_running_task = asyncio.ensure_future(
                        self._run_single_command(args[0], args[1:]))
                    await self._currently_running_task
                except asyncio.CancelledError:
                    print()
                    continue
                except ExitPromptException:
                    return
            else:
                print("Command %s not found!" % args[0])

    def _sigint_handler(self):
        if self._currently_running_task:
            self._currently_running_task.cancel()

    def _get_bindings(self):
        bindings = KeyBindings()
        bindings.add("c-c")(lambda event: self._interrupt_handler(event))
        return bindings

    async def _run_single_command(self, command, args):
        command_real_args, command_real_kwargs = self._get_command_args(command)
        if len(args) < len(command_real_args) or len(args) > (len(command_real_args)
                                                              + len(command_real_kwargs)):
            print("Bad command args. Usage: %s" % self._get_command_usage(command, command_real_args,
                                                                          command_real_kwargs))
            return

        try:
            com_func = self._get_command(command)
            if asyncio.iscoroutinefunction(com_func):
                await com_func(*args)
            else:
                com_func(*args)
            return
        except (ExitPromptException, asyncio.CancelledError):
            raise
        except Exception as ex:
            print("Command failed: ", ex)

    def _interrupt_handler(self, event):
        event.cli.current_buffer.text = ""

    def _make_completer(self):
        return NestedCompleter({com: self._completer_for_command(com) for com in self.command_list})

    def _completer_for_command(self, command):
        if not hasattr(self, "_%s_completions" % command):
            return WordCompleter([])
        return getattr(self, "_%s_completions" % command)()

    def _get_command(self, command):
        if command in self.aliases:
            command = self.aliases[command]
        return getattr(self, self.ATTR_START + command)

    def _get_command_args(self, command):
        args = [param for param in inspect.signature(self._get_command(command)).parameters.values()
                if param.default == param.empty]
        kwargs = [param for param in inspect.signature(self._get_command(command)).parameters.values()
                  if param.default != param.empty]
        return args, kwargs

    def _get_command_usage(self, command, args, kwargs):
        return ("%s %s %s" % (command,
                              " ".join("<%s>" % arg for arg in args),
                              " ".join("[%s]" % kwarg for kwarg in kwargs),
                              )).strip()

    @property
    def command_list(self):
        return [attr[len(self.ATTR_START):]
                for attr in dir(self) if attr.startswith(self.ATTR_START)] + list(self.aliases.keys())

    def do_help(self):
        print()
        print(self.doc_header)
        print("=" * len(self.doc_header))
        print()

        get_usage = lambda command: self._get_command_usage(command, *self._get_command_args(command))
        max_usage_len = max([len(get_usage(command)) for command in self.command_list])
        for command in sorted(self.command_list):
            command_doc = self._get_command(command).__doc__
            print(("%-" + str(max_usage_len + 2) + "s%s") % (get_usage(command), command_doc or ""))

    def do_quit(self):
        """Exit the prompt"""
        raise ExitPromptException()

    def _on_close(self):
        """Optional hook to call on closing the cmd"""
        pass
