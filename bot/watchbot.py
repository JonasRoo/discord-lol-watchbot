import os
import logging
import discord
from discord.ext import commands

COMMAND_PREFIX = "s10!"

# explicitely declare intents to enable member privileges
intents = discord.Intents.default()
intents.members = True


class WatchBot(commands.Bot):
    """
    A bot that can track linked lol accounts and judge them for their champion choices.
    """

    def __init__(self, **options):
        super().__init__(
            COMMAND_PREFIX,
            intents=intents,
            case_insensitive=True,
            **options,
        )

        self.logger = logging.getLogger("lol_watchbot")

        # local import so that the cogs can import the bot (e.g. for logging)
        from bot.cogs.test_cog import TestCog
        from bot.cogs.lolacc_cog import LolAccCog

        self.add_cog(TestCog(bot=self))
        self.add_cog(LolAccCog(bot=self))

        self.add_listener(func=self.command_logging, name="on_command")

    def run(self, *args, **kwargs):
        super().run(os.environ.get("LOL_WATCHBOT_DISCORD_TOKEN"), *args, **kwargs)

    async def on_ready(self):
        self.logger.info(f"{self.user.name} connected to Discord and online.")
        self.logger.info(f"Joined guilds: {self.guilds}")

    async def command_logging(self, ctx: discord.ext.commands.Context):
        self.logger.info(
            f"CMD\t{ctx.message.content} | {ctx.author.name} | {ctx.channel.name} | {ctx.guild.name}"
        )

    async def on_command_error(self, ctx, error):
        """
        Custom error handler to relay inforation back to user and log.
        """
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"Command `{ctx.invoked_with}` was not found!!")
        # can't use "CommandInvokeError" since this is thrown EVERY TIME there's a command invoking error!
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(f"Error invoking `{ctx.invoked_with}.`")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(
                f"Did not pass (permissions) checks while calling `{ctx.invoked_with}.\nError message:\n{error}`"
            )

        self.logger.error(error)
