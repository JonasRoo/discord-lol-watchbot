from bot.common_utils.exceptions import ChannelNotFoundError

from typing import Iterable
from operator import itemgetter
from discord import ChannelType
import discord.enums

channel_name_prios = {"alert": 1, "punish": 2, "general": -1}


def _pick_one_text_announcement_channel(channels: Iterable[ChannelType]) -> ChannelType:
    # get all the text channels
    channels = [c for c in channels if c.category == discord.enums.ChannelType.text]
    desired_channels = []
    # iterate over all channels, and find all the channels
    # we would potentially want based on our preferences
    for channel in channels:
        if channel.name in channel_name_prios.keys():
            desired_channels.append((channel, channel_name_prios[channel.name]))

    # no channel with desired name has been found > can't do this
    if not desired_channels:
        raise ChannelNotFoundError(f"Could not find a channel for this operation.")

    # pick and return channel with highest priority
    return sorted(desired_channels, key=itemgetter(1), reverse=True)[0]