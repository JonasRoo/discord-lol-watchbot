from bot.watchbot import WatchBot
from bot.database_interface.session.session_handler import session_scope
from bot.database_interface.utils import query_utils
from bot.database_interface.tables.users import User
from bot.database_interface.tables.matches import Match
from bot.lol_data import opgg_handler

from datetime import datetime
from discord.ext import commands, tasks

_DEF_MINUTES_BETWEEN_MATCH_CALLS = 14.0


class SurveillanceCog(commands.Cog, name="Surveillance"):
    def __init__(self, bot: WatchBot):
        self.bot = bot
        self.fetch_matches.start()

    def cog_unload(self):
        self.fetch_matches.cancel()

    @tasks.loop(minutes=_DEF_MINUTES_BETWEEN_MATCH_CALLS)
    async def fetch_matches(self):
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
                    champion=game_data["champion"],
                    summoner_one=game_data["spells"][0],
                    summoner_two=game_data["spells"][1],
                )
                # before inserting: let's check whether our new map might be a duplicate
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
                    delta = datetime.utcnow() - last_match.played_at
                    if (
                        delta.seconds // 60 < _DEF_MINUTES_BETWEEN_MATCH_CALLS
                        and match.has_almost_same_info(other=last_match)
                    ):
                        self.bot.logger.info(
                            f"TASK:\tDid not add new match as time_passed is too little and info is the same"
                        )
                    else:
                        self.bot.logger.info(f"TASK:\tAdded new match {match}")
                        session.add(match)

    @fetch_matches.before_loop
    async def before_fetch_matches(self):
        self.bot.logger.info(
            "TASK:\tWaiting for bot to be ready before fetching matches..."
        )
        await self.bot.wait_until_ready()

    @commands.command(name="livetest")
    async def get_live_game_data(self, ctx):
        matches = query_utils.get_all_instances_of_something(model=Match)
        msgs = [m for m in matches]
        await ctx.send("\n".join(msgs))