from typing import Union
from discord.ext import commands
from bot.watchbot import WatchBot
from bot.common_utils.exceptions import BadArgumentError
from bot.database_interface.tables.felonies import Felony
from bot.database_interface.utils import query_utils
from bot.database_interface.session.session_handler import session_scope
from bot.common_utils import embed_builder


class FelonyCog(commands.Cog, name="Felony"):
    def __init__(self, bot: WatchBot):
        self.bot = bot

    @commands.command(name="addfelony", aliases=["addf"])
    async def add_felony(self, ctx: commands.Context, champ_name: str) -> None:
        # TODO(jonas): refactor this into a `parsing_util` module
        if not champ_name or not any([c.isalpha() for c in champ_name]):
            # if champ_name not provided or no alphabet chars contained, it's invalid
            raise BadArgumentError("Please provide a valid champion name!")
        # cases where this matters: e.g. "Rek'Sai", "Xin Zhao"
        parsed_name = "".join([c for c in champ_name if c.isalpha()])
        # check if an ACTIVE entry for this champion already exists
        if query_utils._check_if_something_exists(
            model=Felony, options={"champion": parsed_name, "is_active": True}
        ):
            await ctx.send(f"Champion {champ_name} already is an active felony!")
        else:
            # no active entry exists yet > commit it to DB
            with session_scope() as session:
                # we LOWER CASE everything
                felony = Felony(champion=parsed_name.lower())
                session.add(felony)
            await ctx.send(f"Successfully added `{parsed_name.title()}` to the database!")

    @commands.command(name="inactivatefelony", aliases=["remfel", "remf", "disfel"])
    async def inactivate_felony(self, ctx: commands.Context, id_or_name: Union[int, str]) -> None:
        which_key = "id" if isinstance(id_or_name, int) else "champion"
        query_options = {which_key: id_or_name, "is_active": True}
        if isinstance(id_or_name, str):
            # if a champ name was parsed > lower case it
            query_options[which_key] = id_or_name.lower()
        felony = query_utils.get_latest_instance_of_something(
            model=Felony, time_field=Felony.date_added, options=query_options
        )
        if felony is None:
            await ctx.send(f"No active felony exists for {id_or_name}!")
        else:
            with session_scope() as session:
                felony_object = session.query(Felony).filter_by(**felony).first()
                felony_object.is_active = False
            await ctx.send(f"Successfully altered entry for {id_or_name}!")

    @commands.command(name="listfelonies", aliases=["listf", "allf"])
    async def list_felonies(self, ctx: commands.Context, kind: str = "all") -> None:
        embed = embed_builder.make_list_felonies_embed(
            only_active_ones=(kind and "active" in kind.lower())
        )

        await ctx.send(embed=embed)
