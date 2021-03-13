from typing import Union
from datetime import datetime
from discord.ext import commands
from bot.watchbot import WatchBot
from bot.common_utils.exceptions import BadArgumentError
from bot.database_interface.tables.felonies import Felony
from bot.database_interface.utils import query_utils
from bot.database_interface.session.session_handler import session_scope
from bot.common_utils import embed_builder, league_utils


class SummonsCog(commands.Cog, name="Summons"):
    def __init__(self, bot: WatchBot):
        self.bot = bot

    @commands.command(name="leaderboard", aliases=["lb, lboard"])
    async def leaderboard(self, ctx: commands.Context) -> None:
        embed = embed_builder.make_leaderboard_embed(ctx=ctx)
        await ctx.send(embed=embed)