from bot.watchbot import WatchBot

import discord
from discord.ext import commands


class LolAccCog(commands.Cog, name="LolAcc"):
    def __init__(self, bot: WatchBot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx: discord.ext.commands.Context, member: discord.Member=None, lol_server: str, lol_name: str):
        if member is None:
            member = ctx.message.author
    
    # add your own account: s10!add_user Faker KR
    @commands.command(aliases=["add", "adduser"])
    async def add_user(self, ctx: discord.commands.Context, league_name: str, server_name: str):
        pass

    # add another person's account: s10!add_user @DISCORD_ID Get Controlled EUW
    # should only be usable by an "admin"