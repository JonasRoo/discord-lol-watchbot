import os
from discord.ext import commands
import sqlite3

from database_interface import bot_declarative_base


discord_token = os.environ.get("LOL_WATCHBOT_DISCORD_TOKEN")
client = commands.Bot(command_prefix="s10!")


@client.event
async def on_ready():
    # client.sqlite_connection = sqlite3.connect("db.sqlite3")
    print("Database connection established. Bot ready!")


@client.command(name="test", aliases=["test2", "test3"])
async def test(ctx, *args):
    print(dir(ctx))
    print(f"Author = {ctx.author}")
    print(f"Channel = {ctx.channel}")
    print(f"Message = {ctx.message}")
    await ctx.send("test worked!")


if __name__ == "__main__":
    client.run(discord_token)