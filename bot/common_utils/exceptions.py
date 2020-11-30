from discord.ext import commands, tasks


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


class ChannelNotFoundError(commands.CommandError):
    """
    Class used to describe errors occuring when no suitable channel could be found for a certain event.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class MemberNotFoundError(commands.CommandError):
    """
    Class used to describe errors occuring when a member can't be found by ID.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)