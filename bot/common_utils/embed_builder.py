from bot.database_interface import bot_declarative_base
from typing import Tuple, List
import discord


def make_account_add_confirmation_embed(
    league_name: str,
    server_name: str,
    discord_user: discord.User,
    opgg_url: str,
    emojis: Tuple[str],
) -> discord.Embed:

    # construct container embed to add fields to
    embed = discord.Embed(
        title="🚨 New surveillance mission received 🚨", colour=discord.Colour.red()
    )
    confirmation_message = f"Confirm by using {emojis[0]}, abort by using {emojis[1]}!"

    embed = (
        embed.add_field(name="Subject", value=discord_user.mention, inline=False)
        .add_field(name="Ingame Name", value=league_name, inline=True)
        .add_field(name="Server Name", value=server_name.upper(), inline=True)
        .add_field(name="Confirm adding", value=confirmation_message, inline=False)
        .add_field(name="op.gg URL", value=opgg_url, inline=False)
    )

    return embed


def make_list_accounts_embed(accounts: List[bot_declarative_base]) -> discord.Embed:
    embed = discord.Embed(title="📃✍ List of all accounts", colour=discord.Colour.red())

    for idx, account in enumerate(accounts):
        (
            embed.add_field(
                name="Discord ID",
                value=f"<@!{account['discord_id']}>",
            )
            .add_field(name="Ingame", value=account["league_name"])
            .add_field(name="Server", value=account["server_name"].upper())
            .add_field(name="op.gg", value=f"[link]({account['opgg_link']})")
            .add_field(name="Internal ID", value=account["id"])
            .add_field(name="\u200b", value="--------------------------", inline=False)
        )

    return embed