from bot.common_utils.exceptions import ChannelNotFoundError

from typing import Iterable
from operator import itemgetter
from discord import ChannelType
import discord.enums

channel_name_prios = {"alert": 1, "tracking": 2, "general": -1}


def _pick_one_text_announcement_channel(guild: discord.Guild) -> ChannelType:
    # get all the text channels
    # looks like: [(channel: ChannelType, priority: int)]
    desired_channels = []
    # iterate over all channels, and find all the channels
    # we would potentially want based on our preferences
    for channel in guild.text_channels:
        if channel.name in channel_name_prios.keys():
            desired_channels.append((channel, channel_name_prios[channel.name]))

    # no channel with desired name has been found > can't do this
    if not desired_channels:
        raise ChannelNotFoundError(f"Could not find a channel for this operation.")

    # pick and return channel with highest priority (items here are tuples)
    return min(desired_channels, key=itemgetter(1))[0]