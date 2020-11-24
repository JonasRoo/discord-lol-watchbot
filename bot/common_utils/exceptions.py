from discord.ext import commands


class OpGGParsingError(commands.CommandError):
    """
    Class used to describe errors occuring during interaction with any op.gg endpoint.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BadArgumentError(commands.CommandError):
    """
    Class used to describe erroneous arguments used when invoking a command.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)