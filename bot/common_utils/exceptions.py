from discord.ext import commands


class OpGGParsingError(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BadArgumentError(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)