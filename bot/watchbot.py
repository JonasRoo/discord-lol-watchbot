import os
import logging
import discord
from discord.ext import commands
from bot.database_interface import bot_declarative_base
from bot.common_utils.embed_builder import make_error_message_embed
from bot.common_utils.exceptions import OpGGParsingError, BadArgumentError

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
        from bot.cogs.surveillance_cog import SurveillanceCog
        from bot.cogs.felony_cog import FelonyCog

        self.add_cog(TestCog(bot=self))
        self.add_cog(LolAccCog(bot=self))
        self.add_cog(SurveillanceCog(bot=self))
        self.add_cog(FelonyCog(bot=self))

        self.add_listener(func=self.command_logging, name="on_command")

    def run(self, *args, **kwargs):
        super().run(os.environ.get("LOL_WATCHBOT_DISCORD_TOKEN"), *args, **kwargs)

    async def on_ready(self):
        self.logger.info(f"{self.user.name} connected to Discord and online.")
        self.logger.info(f"Joined guilds: {self.guilds}")

    async def command_logging(self, ctx: discord.ext.commands.Context):
        self.logger.info(
            f"CMD-INVOKED\t{ctx.message.content} | {ctx.author.name} | {ctx.channel.name} | {ctx.guild.name}"
        )

    async def on_command_error(self, ctx, error):
        """
        Custom error handler to relay inforation back to user and log.
        """
        if isinstance(error, commands.CommandNotFound):
            embed = make_error_message_embed(
                error_message=f"Command `{ctx.invoked_with}` was not found!"
            )
        elif isinstance(error, commands.CommandInvokeError):
            embed = make_error_message_embed(error_message=f"Error invoking `{ctx.invoked_with}.`")
        elif isinstance(error, commands.CheckFailure):
            # raised when an invoking user does not pass (permission) checks
            embed = make_error_message_embed(
                error_message=f"Did not pass (permissions) checks while calling `{ctx.invoked_with}`.",
                details=error.__str__(),
            )
        elif isinstance(error, OpGGParsingError):
            embed = make_error_message_embed(
                error_message=f"Error interacting with the OP.GG endpoint while calling `{ctx.invoked_with}`.",
                details=error.__str__(),
            )
        elif isinstance(error, BadArgumentError):
            embed = make_error_message_embed(
                error_message=f"Error parsing one of your arguments for the command `{ctx.invoked_with}`.",
                details=error.__str__(),
            )

        else:
            # another exception that we're not handling > internal error
            embed = make_error_message_embed(
                error_message=f"Internal error while invoking `{ctx.invoked_with}`. Please use the `!help` command!"
            )

        # finally, we send the error embed and log our error
        await ctx.send(embed=embed)
        self.logger.error(error)
