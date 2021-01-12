from bot.watchbot import WatchBot
from bot.lol_data import opgg_handler
from bot.common_utils.exceptions import OpGGParsingError, BadArgumentError
from bot.common_utils import embed_builder
from bot.database_interface.session.session_handler import session_scope
from bot.database_interface.tables.users import User
from bot.database_interface.utils import query_utils
from bot.common_utils import decorators

try:
    # try to find a
    from bot.common_utils.admin_secrets import _BOT_ADMINS
except ImportError:
    _BOT_ADMINS = []

import asyncio
from typing import Optional, List, Tuple
import discord
from discord.ext import commands


class LolAccCog(commands.Cog, name="LolAcc"):
    def __init__(self, bot: WatchBot):
        self.bot = bot
        self.confirmation_emojis = ("👍", "👎")

    # add your own account: s10!add_user Faker KR
    @commands.command(aliases=["add", "adduser"])
    async def add_user(
        self,
        ctx: commands.Context,
        discord_member: Optional[discord.Member] = None,
        server_name: str = "euw",
        *league_name: str,
    ):
        """
        Adds a new LoL account to the database, with confirmation dialogue.

        Args:
            ctx (discord.ext.commands.Context): Discord context
            discord_member (Optional[discord.Member], optional): Only usable by admins. If entered, adds the LoL account to that Discord user instead. Defaults to None.
            server_name (Optional[str]): LoL server. Defaults to "euw".
            league_name (str): LoL ingame name
        """

        if isinstance(league_name, (tuple, list)):
            # if a summoner with spaces in it is passed, this argument is a tuple.
            league_name = " ".join(league_name)
        # lower case server to comply with naming in Enum
        server_name = server_name.lower()
        if discord_member:
            if not ctx.message.author.id in _BOT_ADMINS:
                # if the command's invoker is not an admin, you can't add accounts for other people > fail
                raise commands.CheckFailure(
                    "You are not one of the bot's admins, and can thus not link another user's account!"
                )
        else:
            # else, we're adding the league account for the invoking user
            discord_member = ctx.message.author

        # check if the User we're trying to add already exists
        query_options = {"league_name": league_name, "server_name": server_name}
        if query_utils._check_if_something_exists(model=User, options=query_options):
            # User already exists > abort
            await ctx.send(
                f"A table entry for {league_name} ({server_name}) already exists! Aborting..."
            )
            self.bot.logger.info(f"{ctx.message.author} tried adding an already existing account.")
            return

        # try to get the opgg URL of given account
        opgg_url = opgg_handler.construct_url_by_name_and_server(
            league_name=league_name.lower(), server_name=server_name.lower()
        )
        if not opgg_handler._does_url_belong_to_valid_account(url=opgg_url):
            await ctx.message.delete()
            raise OpGGParsingError(f"No valid account exists for {league_name} ({server_name})!")
        # make an embed for the confirmation message
        # (showing all params and the generated opgg URL)
        embed = embed_builder.make_account_add_confirmation_embed(
            league_name=league_name,
            server_name=server_name,
            discord_user=discord_member,
            opgg_url=opgg_url,
            emojis=self.confirmation_emojis,
        )
        confirmation_msg = await ctx.send(embed=embed)
        # add both reaction options to the confirmation message
        for emoji in self.confirmation_emojis:
            await confirmation_msg.add_reaction(emoji)

        # now wait for either of the reactions to be added by user (confirm or abort)
        def check_if_react(reaction: discord.Reaction, user: discord.User) -> bool:
            """
            Listener to check for the user invoking the command to add a specific reaction.
            Defined inside function scope (and not a lambda) to make "abort" case easier in the reaction.
            In case of user reaction with the "abort" emoji, an `asyncio.TimeoutError` is raised instead.
            """
            if user != ctx.message.author:
                # if the reacting user is not the author, ignore
                return
            if str(reaction.emoji) == self.confirmation_emojis[1]:
                # added emoji is the "negative" emoji > abort
                raise asyncio.TimeoutError
                # if it's not the "negative" emoji, check if it's the positive one
            return str(reaction.emoji) == self.confirmation_emojis[0]

        try:
            # register a listener to the confirmation message to listen for the confirmation emojis
            reaction, user = await self.bot.wait_for(
                "reaction_add", timeout=60.0, check=check_if_react
            )
        except asyncio.TimeoutError:
            # Raised in 2 cases:
            # 1) if the timeout by the `wait_for` function is exceeded
            # 2) raised by `check_if_react`, if reacted with the "negative" emote.
            self.bot.logger.info(f"User {ctx.message.author} aborted adding the account")
            await ctx.send("Alright. Did not add the account.")
        else:
            # the user reacted positively!
            await ctx.send(
                f"Successfully added {league_name} (server: {server_name}) to the database!"
            )
            # create the user, and save to DB
            new_user = User(
                discord_id=discord_member.id,
                league_name=league_name,
                server_name=server_name,
                opgg_link=opgg_url,
            )
            with session_scope() as session:
                session.add(new_user)
                # TODO(jonas): load current match here (outside of task loop)?
        finally:
            # finally, delete both the invoking message and the confirmation message
            await confirmation_msg.delete()
            await ctx.message.delete()

    @commands.command(aliases=["list", "list_accs"])
    @decorators.is_bot_admin()
    async def list_accounts(self, ctx: commands.Context):
        """
        Lists all the accounts in the database.
        Only usable by bot admins.

        Args:
            ctx (commands.Context): Discord context
        """
        # get all instances of the User model
        all_accounts = query_utils.get_all_instances_of_something(User)
        # ..and construct a nice looking embed
        # listing all accounts, grouped by discord user
        list_embed = embed_builder.make_list_accounts_embed(accounts=all_accounts, ctx=ctx)
        list_embed.set_footer(text=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        await ctx.send(embed=list_embed)

    @commands.command(aliases=["del", "delete_user", "remove", "rm"])
    @decorators.is_bot_admin()
    async def delete(self, ctx: commands.Context, int_id: int):
        """
        Deletes a linked LoL account by its (internal) database ID.
        Only usable by bot admins.

        Args:
            ctx (commands.Context): Discord context
            int_id (int): The User instance's ID to be deleted

        Raises:
            BadArgumentError: When the `int_id` couldn't be found in the database
        """
        # first check whether a User instance with that ID exists
        query_options = {"id": int_id}
        if not query_utils._check_if_something_exists(model=User, options=query_options):
            # doesn't exist > notify user
            raise BadArgumentError(f"Account of ID `{int_id}` does not exist!")

        # get string-version of deleted model instance, and notify user
        msg = query_utils.delete_first_instance_by_filter(model=User, options=query_options)
        await ctx.send(f"Successfully deleted user:\n{msg}")