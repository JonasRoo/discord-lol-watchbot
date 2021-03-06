from discord.ext import commands

try:
    from bot.common_utils.admin_secrets import _BOT_ADMINS
except ImportError:
    _BOT_ADMINS = []


def is_bot_admin():
    """
    Checks whether the invoking user is considered an admin of the bot.

    Args:
        ctx (Context): The context of the invoking message.

    Returns:
        bool: True, if the invoking user is an admin; False, if not
    """

    async def predicate(ctx):
        if ctx.author.id not in _BOT_ADMINS:
            return False
        return True

    return commands.check(predicate)
