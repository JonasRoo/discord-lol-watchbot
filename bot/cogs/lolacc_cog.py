from bot.watchbot import WatchBot
from bot.lol_data import opgg_handler
import asyncio

try:
    from bot.admin_secrets import _BOT_ADMINS
except ImportError:
    _BOT_ADMINS = []

from typing import Optional
import discord
from discord.ext import commands


class LolAccCog(commands.Cog, name="LolAcc"):
    def __init__(self, bot: WatchBot):
        self.bot = bot
        self.confirmation_emojis = ("👍", "👎")

    # @commands.command()
    # async def test(self, ctx: discord.ext.commands.Context, member: discord.Member=None, lol_server: str, lol_name: str):
    #     if member is None:
    #         member = ctx.message.author

    # add your own account: s10!add_user Faker KR
    @commands.command(aliases=["add", "adduser"])
    async def add_user(
        self,
        ctx: discord.ext.commands.Context,
        league_name: str,
        server_name: str,
        discord_id: Optional[str] = None,
    ):
        # try to verify the account on op.gg. Asks the user for final confirmation before writing to database
        if discord_id:
            if not ctx.message.author.id in _BOT_ADMINS:
                # if the command's invoker is not an admin, you can't add accounts for other people > fail
                raise commands.CheckFailure(
                    "You are not one of the bot's admins, and can thus not link another user's account!"
                )

        # TODO: check if account is already in the database
        # try to get the opgg URL of given account > raises AttributeError if failing
        try:
            opgg_url = opgg_handler.construct_url_by_name_and_server(
                league_name=league_name.lower(), server_name=server_name.lower()
            )
        except AttributeError as e:
            raise commands.CommandInvokeError(
                f"Error parsing league_name={league_name}, server_name={server_name}! Error raised: {str(e)}"
            )

        confirmation_msg = await ctx.send(
            f"Is this the op.gg you were looking for?\n"
            f"React with {self.confirmation_emojis[0]} to confirm, "
            f"{self.confirmation_emojis[1]} to abort!\n"
            f"{opgg_url}"
        )
        for emoji in self.confirmation_emojis:
            await confirmation_msg.add_reaction(emoji)

        # now wait for either of the reactions to be added by user (confirm or abort)
        def check_if_react(reaction, user):
            if user == ctx.message.author:
                if str(reaction.emoji) == self.confirmation_emojis[1]:
                    raise asyncio.TimeoutError
                else:
                    return str(reaction.emoji) == self.confirmation_emojis[0]

        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=60.0, check=check_if_react
            )
        except asyncio.TimeoutError:
            await ctx.send("Alright. Aborted adding the account.")
        else:
            await ctx.send(
                f"Successfully added {league_name} (server: {server_name}) to the database!"
            )
        finally:
            await confirmation_msg.delete()
            await ctx.message.delete()