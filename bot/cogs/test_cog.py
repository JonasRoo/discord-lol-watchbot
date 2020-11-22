from bot.watchbot import WatchBot

from discord.ext import commands


class TestCog(commands.Cog, name="Test"):
    def __init__(self, bot: WatchBot):
        self.bot = bot

    @commands.command()
    async def test(self, ctx, argument):
        self.bot.logger.info(f"{argument} (type={type(argument)}")
        await ctx.send(f"**{argument} please stop enjoying s10?**")