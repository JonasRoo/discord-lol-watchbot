from typing import Tuple, List, Dict, Any, Optional
import discord
from discord.ext import commands

from bot.database_interface import bot_declarative_base
from bot.database_interface.tables.matches import Match
from bot.database_interface.tables.felonies import Felony
from bot.database_interface.utils import query_utils

_WARNING_ICON_URL = (
    r"https://cdn.iconscout.com/icon/free/png-256/warning-notice-sign-symbol-38020.png"
)
_SURVEILLANCE_ICON_URL = (
    r"https://cdn.discordapp.com/attachments/779441923773431838/780599206645334056/bruh.png"
)
_LIST_ICON_URL = (
    r"https://everestalexander.files.wordpress.com/2015/11/moses10commandmentstrans.gif"
)
_POLICE_MAN_ICON_URL = r"https://purepng.com/public/uploads/large/purepng.com-policemanpolicemanhuman-securitysafetypolicecop-142152696325297fsg.png"


def make_error_message_embed(error_message: str, details: Optional[str] = None) -> discord.Embed:
    """
    Constructs an embed for errors occuring during runtime of the bot.

    Args:
        error_message (str): The (general) error message that occured.
        details (Optional[str], optional): Optional details message of the error. Defaults to None.

    Returns:
        discord.Embed: A populated error message embed.
    """
    embed = discord.Embed(title="⚠️ Error encountered ⚠️", colour=discord.Colour.red())
    embed.set_thumbnail(url=_WARNING_ICON_URL)
    # in any case, add our general error message to the embed
    embed.add_field(name="Error message", value=error_message, inline=False)
    if details is not None:
        # if we have details available to us, add those as well
        embed.add_field(name="\u200b", value="\u200b", inline=False)  # spacing
        embed.add_field(name="Details", value=details, inline=False)

    return embed


def make_account_add_confirmation_embed(
    league_name: str,
    server_name: str,
    discord_user: discord.User,
    opgg_url: str,
    emojis: Tuple[str],
) -> discord.Embed:
    """
    Constructs an account adding confirmation embed

    Args:
        league_name (str): LoL ingame name
        server_name (str): LoL server name
        discord_user (discord.User): The discord user to link the LoL account to
        opgg_url (str): op.gg URL corresponding to previous arguments
        emojis (Tuple[str]): "positive" and "negative" reaction emojis

    Returns:
        discord.Embed: populated confirmation embed
    """
    # construct container embed to add fields to
    embed = discord.Embed(
        title="🚨 New surveillance mission received 🚨", colour=discord.Colour.red()
    )
    embed.set_thumbnail(url=_SURVEILLANCE_ICON_URL)
    # explanatory message to handling of dialog
    confirmation_message = f"Confirm by using {emojis[0]}, abort by using {emojis[1]}!"

    # --- Layout: ---
    # [Discord @]
    # [ingame_name]   [server_name]
    # [confirmation_explanatory_text]
    # [opgg_url]
    embed = (
        embed.add_field(name="Subject", value=discord_user.mention, inline=False)
        .add_field(name="Ingame Name", value=league_name, inline=True)
        .add_field(name="Server Name", value=server_name.upper(), inline=True)
        .add_field(name="Confirm adding", value=confirmation_message, inline=False)
        .add_field(name="op.gg URL", value=opgg_url, inline=False)
    )

    return embed


def group_acc_dict_by_discord_user(
    accounts: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Nests User account dictionaries under unique discord_id's
    Resulting structure:
    {discord_id1: [account1, account2], discord_id2: [account1], [...]}

    Args:
        accounts (List[Dict[str, Any]]): (Unnested) list of User instances

    Returns:
        Dict[str, List[Dict[str, Any]]]: Nested list of User instances
    """
    grouped = {}
    for account in accounts:
        if grouped.get(account["discord_id"]):
            # there's already a dictionary key for this unique discord ID
            # > append the User account instance to the already existing list in its value
            grouped[account["discord_id"]].append(account)
        else:
            # there's no dict key for this discord id > create it, and attach account
            grouped[account["discord_id"]] = [account]

    return grouped


def make_list_accounts_embed(
    accounts: List[Dict[str, Any]], ctx: commands.Context
) -> discord.Embed:
    """
    Constructs a nicely formatted embed listing all User accounts, grouped by discord user

    Args:
        accounts (List[Dict[str, Any]]): List of User instance dicts
        ctx (commands.Context): invoking discord context of command (to get user's names)

    Returns:
        discord.Embed: Populated embed listing all linked User accounts
    """
    embed = discord.Embed(title="📃✍ List of all accounts", colour=discord.Colour.red())
    embed.set_thumbnail(url=_LIST_ICON_URL)

    # for each discord user and all their linked accounts, we add a new embed field
    for discord_id, acc_list in group_acc_dict_by_discord_user(accounts).items():
        # for each account in the list, construct a string like:
        # [internal_id] [ingame_name] ([server]) > [opgg_link]
        accounts_linked = [
            f"> `[{account['id']}]` {account['league_name']} ({account['server_name'].upper()}) 👉 [opgg]({account['opgg_link']})"
            for account in acc_list
        ]
        # get the discord user owning these accounts by ID
        owning_user = ctx.guild.get_member(discord_id) or "AnonymousUser"
        embed.add_field(
            name=f"👤 {owning_user.display_name}",
            value="\n".join(accounts_linked),
            inline=False,
        )

    return embed


def make_announcement_embed(
    match: Match, url: str, channel: discord.ChannelType, user_id: int
) -> discord.Embed:
    # check if we can grab a member of the match's discord_id in that location
    member = channel.guild.get_member(user_id)
    if member is None:
        raise MemberNotFoundError(
            f"A member of ID {match.user_id} could not be found on this server!"
        )

    embed = discord.Embed(title="🚨 S10 ABUSE DETECTED 🚨", colour=discord.Colour.red())
    embed.set_thumbnail(url=_POLICE_MAN_ICON_URL)

    # TODO(jonas): make the bot join the VC, then play a siren sound
    return (
        embed.add_field(name="FELLON", value=member.mention, inline=False)
        .add_field(name="S10 ABUSE CHAMPION", value=match.champion, inline=False)
        .add_field(name="LINK", value=url, inline=False)
    )


def make_list_felonies_embed(only_active_ones: bool = True) -> discord.Embed:
    """
    Constructs a nicely formatted embed listing all User accounts, grouped by discord user

    Args:
        accounts (List[Dict[str, Any]]): List of User instance dicts
        ctx (commands.Context): invoking discord context of command (to get user's names)

    Returns:
        discord.Embed: Populated embed listing all linked User accounts
    """
    embed = discord.Embed(
        title=f"👮‍♂️🚔 List of all {'active' if only_active_ones else ''} felonies",
        colour=discord.Colour.red(),
    )
    embed.set_thumbnail(url=_POLICE_MAN_ICON_URL)

    if only_active_ones:
        felonies = query_utils.get_all_instances_of_something(
            model=Felony, options={"is_active": True}
        )
    else:
        felonies = query_utils.get_all_instances_of_something(model=Felony)

    active_felony_strings: Dict[str, List[str]] = {True: [], False: []}
    # we divide the dateset into 2 subgroups: active and inactive felonies
    for felony in felonies:
        formatted = (
            f"`{felony['id']}`\t{felony['champion'].title()} (added: {felony['date_added'].date()})"
        )
        # append the formatted string to the corresponding subset
        active_felony_strings[felony["is_active"]].append(formatted)

    embed.add_field(
        name="🚨 Active felonies",
        value="\n".join(active_felony_strings[True] or "\u200b"),
        inline=False,
    )
    if not only_active_ones and active_felony_strings[False]:
        # we also want to see inactive ones
        embed.add_field(
            name="☠ Inactive felonies",
            value="\n".join(active_felony_strings[False] or "\u200b"),
            inline=False,
        )

    return embed
