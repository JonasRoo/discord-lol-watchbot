from bot.common_utils.exceptions import ChannelNotFoundError

from typing import Optional, Dict
from operator import itemgetter
from discord import ChannelType
import discord

_channel_name_prios = {"alert": 1, "tracking": 2, "general": -1}


def _pick_one_text_announcement_channel(
    guild: discord.Guild, preferences: Optional[Dict[str, int]] = None
) -> ChannelType:
    """
    From a discord guild, picks and returns one text_channel
    to broadcast an announcement in based on pre-defined name preferences.

    Args:
        guild (discord.Guild): A guild (discord "server")
        preferences (Optional[Dict[str, int]]): Optional naming preferences {name: score}. Higher score = better. Defaults to None.

    Raises:
        ChannelNotFoundError: If no channel matches pre-defined preferences.

    Returns:
        ChannelType: The most-preferred channel.
    """
    preferences = preferences or _channel_name_prios
    # get all the text channels, looks like: [(channel: ChannelType, priority: int)]
    desired_channels = []
    # iterate over all channels, and find all the channels we would potentially want based on our preferences
    for channel in guild.text_channels:
        if channel.name in preferences.keys():
            desired_channels.append((channel, preferences[channel.name]))

    # no channel with desired name has been found > can't do this
    if not desired_channels:
        raise ChannelNotFoundError(f"Could not find a channel for this operation.")

    # pick and return channel with highest priority (items here are tuples)
    return max(desired_channels, key=itemgetter(1))[0]
