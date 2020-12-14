from bot.watchbot import WatchBot
from bot.database_interface.session.session_handler import session_scope
from bot.database_interface.utils import query_utils
from bot.database_interface.tables.users import User
from bot.database_interface.tables.felonies import Felony
from bot.database_interface.tables.matches import Match
from bot.common_utils.exceptions import MemberNotFoundError
from bot.common_utils import embed_builder
from bot.common_utils import league_utils, discord_utils
from bot.lol_data import opgg_handler

from typing import Dict, Any
from datetime import datetime
import discord
from discord.ext import commands, tasks

_DEF_MINUTES_BETWEEN_MATCH_CALLS = 14.0


class SurveillanceCog(commands.Cog, name="Surveillance"):
    def __init__(self, bot: WatchBot):
        self.bot = bot
        self.fetch_matches.start()

    def cog_unload(self):
        self.fetch_matches.cancel()

    @tasks.loop(minutes=_DEF_MINUTES_BETWEEN_MATCH_CALLS)
    async def fetch_matches(self) -> None:
        accounts = query_utils.get_all_instances_of_something(model=User)
        # fetch possible live game data for every account we have saved
        for account in accounts:
            game_data = opgg_handler.get_live_game_data_played(
                league_name=account["league_name"], server_name=account["server_name"]
            )
            if game_data is not None:
                # live game was found > we have data to process!
                match = Match(
                    user_id=account["id"],
                    map=game_data["game_mode"],
                    champion=league_utils._convert_champ_name(name=game_data["champion"]),
                    summoner_one=game_data["spells"][0],
                    summoner_two=game_data["spells"][1],
                )
                await self._maybe_save_match(match=match, account=account)
                await self.maybe_police(match=match, account=account)
            else:
                self.bot.logger.info(f"No active match found for {account['league_name']}.")

    async def _maybe_save_match(self, match: Match, account: Dict[str, Any]) -> None:
        # before inserting: let's check whether our new match might be a duplicate
        with session_scope() as session:
            last_match = (
                session.query(Match)
                .filter_by(user_id=account["id"])
                .order_by(Match.played_at.desc())
                .first()
            )
            # criteria to label a match as a "duplicate":
            # 1) the game info needs to be the same (map, champ, summoner spells)
            # 2) the time elapsed since that last match is smaller than the time we wait between task executions
            # (if last_match does not exist, it's always safe to write)
            delta = datetime.utcnow() - (last_match.played_at if last_match else datetime.min)
            if (
                delta.seconds // 60 < _DEF_MINUTES_BETWEEN_MATCH_CALLS
                and match.has_almost_same_info(other=last_match)
            ):
                self.bot.logger.info(f"TASK:\tDid not add duplicate match")
            else:
                self.bot.logger.info(f"TASK:\tAdded new match {match}")
                session.add(match)

    async def maybe_police(self, match: Match, account: Dict[str, Any]) -> None:
        if query_utils._check_if_something_exists(
            model=Felony, options={"champion": match.champion}
        ):
            for guild in self.bot.guilds:
                await self.push_punish_message(guild=guild, account=account, match=match)

    @fetch_matches.before_loop
    async def before_fetch_matches(self):
        """
        Wait for bot to join all guilds to prevent
        catch perpetrator before joining.
        """
        self.bot.logger.info("TASK:\tWaiting for bot to be ready before fetching matches...")
        await self.bot.wait_until_ready()

    async def push_punish_message(
        embed: discord.Embed, guild: discord.Guild, account: Dict[str, Any], match: Match
    ) -> None:
        # pick highest prio channel to send alert msg to
        channel_to_broadcast = discord_utils._pick_one_text_announcement_channel(guild=guild)
        # construct the op.gg URL for live-game
        opgg_url = opgg_handler.construct_url_by_name_and_server(
            league_name=account["league_name"],
            server_name=account["server_name"],
            mode="spectator",
        )
        # build alert embed and send it to picked channel
        embed = embed_builder.make_announcement_embed(
            match=match,
            url=opgg_url,
            channel=channel_to_broadcast,
            user_id=account["discord_id"],
        )
        await channel_to_broadcast.send(embed=embed)
