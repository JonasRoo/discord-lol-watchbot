from bot.common_utils.exceptions import OpGGParsingError
from bot.database_interface.tables.users import Server
from bot.common_utils import league_utils

from typing import Tuple, Optional, Dict, Iterable
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import re
import logging
import requests
from requests.exceptions import HTTPError

# standard headers for a "regular" user
_HTTP_STANDARD_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
    "accept-encoding": "gzip, deflate, br",
    "accept": "application/json, text/javascript, */*; q=0.01",
}

# TODO(jonas): refactor this into enum
_OPGG_TEMPLATES = {
    # (default) match history
    "history": "https://{server}.op.gg/summoner/userName={ign}",
    # live game
    "spectator": "https://{server}.op.gg/summoner/spectator/userName={ign}&",
    # overview of champions played in past seasons (& normal games)
    "champions": "https://{server}.op.gg/summoner/champions/userName={ign}&",
    # rank overview in league
    "league": "https://{server}.op.gg/summoner/league/userName={ign}&",
}


def _get_internal_logger() -> logging.Logger:
    """
    Fetches the watchbot's internal logger.

    Returns:
        logging.Logger: Logger
    """
    return logging.getLogger("lol_watchbot")


def _validate_opgg_params(
    server_name: Optional[str] = None,
    mode: Optional[str] = None,
    league_name: Optional[str] = None,
):
    """
    Validates various input parameters for opgg constructors.

    Args:
        server_name (Optional[str], optional): an opgg server name. Defaults to None.
        mode (Optional[str], optional): an opgg page mode. Defaults to None.
        league_name (Optional[str], optional): a lol ingame name. Defaults to None.

    Raises:
        OpGGParsingError: if any of the input parameters are invalid
    """
    # various validation of input
    if mode is not None and not mode in _OPGG_TEMPLATES:
        raise OpGGParsingError(f"mode needs to be one of {_OPGG_TEMPLATES.keys()}!")
    if server_name is not None and not server_name in Server.list():
        raise OpGGParsingError(f"server needs to be one of\n`{Server.list()}`!")
    if league_name is None or not league_name:
        raise OpGGParsingError("league ingame name can't be empty!")


def construct_url_by_name_and_server(
    league_name: str, server_name: str, mode: Optional[str] = "history"
) -> str:
    """
    Constructs an OP.GG URL given a name and server, with a requested page mode.

    Args:
        league_name (str): lol ingame name
        server_name (str): a (valid) league of legends server endpoint on op.gg
        mode (str, optional): op.gg "mode", which part of the site to view. Defaults to "history".

    Raises:
        OPGGParsingError: when input parameters are invalid

    Returns:
        str: a valid ready-to-query op.gg page.
    """
    # various validation of input
    _validate_opgg_params(server_name, mode, league_name)

    return _OPGG_TEMPLATES[mode].format(
        server=server_name,
        # ensures that non-ASCII characters in name are requested correctly
        ign=quote_plus(league_name, encoding="UTF-8"),
    )


def convert_opgg_url_to(mode: str, url: str) -> str:
    """
    Converts any variation of an opgg URL to any other,
    leaving summonerName and server.

    Args:
        mode (str): the mode / opgg endpoint to swap to
        url (str): the base URL to change

    Returns:
        str: opgg url with same league_name and server_name, but new desired mode

    Raises:
        AttributeError: when op.gg URL is malconstructed
    """
    _validate_opgg_params(mode=mode)

    server_re = r"^https?://(.{1,4})\.op\.gg.*"
    name_re = r".*userName=([^&]+)&?$"

    server_name, league_name = (
        re.search(server_re, url).group(1),
        re.search(name_re, url).group(1),
    )

    return construct_url_by_name_and_server(league_name, server_name, mode)


def _does_url_belong_to_valid_account(url: str) -> bool:
    """
    Verifies that an account associated with a constructed URL exists.

    Args:
        url (str): URL to request.

    Returns:
        bool: True, if the request yielded a valid op.gg; False, if not.
    """
    # get the default logger of the bot
    logger = _get_internal_logger()
    try:
        # request the URL
        r = requests.get(url=url, headers=_HTTP_STANDARD_HEADERS)
        r.raise_for_status()
    except HTTPError as e:
        # raise_for_status() raises HTTPError
        logger.error(f"Unsuccessful HTTP request for URL=`{url}`")
        return False

    # HTTP request was successful > check HTML content
    soup = BeautifulSoup(r.content, features="html.parser")
    # if this class is found, the summoner could not be found (on that server)
    summoner_not_found_div = soup.find("div", {"class": "SummonerNotFoundLayout"})
    if summoner_not_found_div is not None:
        logger.error(f"Summoner not found for URL=`{url}`")
        return False

    # all verification steps passed > summoner name exists on that server
    return True


def verify_summoner_on_server(league_name: str, server_name: str) -> bool:
    """
    Verifies whether a summoner exists on a given server.

    Returns:
        bool: True, if summoner is valid. False, if invalid.
    """
    url = construct_url_by_name_and_server(league_name=league_name, server_name=server_name)
    return _does_url_belong_to_valid_account(url=url)


def get_table_row_of_summoner_from_table(
    table_bodies: Iterable[BeautifulSoup], league_name: str
) -> BeautifulSoup:
    """
    Iterates over the live-game table, and returns the row of the `league_name`.
    Structure of the `table_bodies` looks like:
    <tbody (team A)>
        <tr (one per summoner / header)>
            <`n times` td (one per data point)>
    <tbody (team B)>
        <[same as for team B]>

    Args:
        table_bodies (Iterable[BeautifulSoup]): A list of table-bodies (this will be 2 bodies, one per each team)
        league_name (str): The league name to return the table_row for (case-insensitive)

    Raises:
        ValueError: If the summoner can't be found in either of the table bodies

    Returns:
        BeautifulSoup: [description]
    """
    # for each table body (1 for each team)
    for table_body in table_bodies:
        # for each row within that body (5 per body)
        for table_row in table_body.findAll("tr"):
            # check whether it's our summoner
            summoner_cell = table_row.find("td", {"class": "SummonerName Cell"})
            summoner_name = summoner_cell.find("a").contents[0]
            if summoner_name.lower() == league_name.lower():
                # found the summoner! > extract champion
                return table_row

    raise ValueError(f"Could not locate summoner {league_name} in either of the table bodies!")


def _extract_data_from_live_game_soup(
    soup: BeautifulSoup, league_name: str
) -> Optional[Dict[str, str]]:
    """
    Extracts data from live-gaem played by scraping the opgg livegame HTML.

    Args:
        soup (BeautifulSoup): The soup of the opgg livegame endpoint response

    Returns:
        Optional[Dict[str, str]]: None, if summoner not ingame; the champ name, if ingame.
    """
    logger = _get_internal_logger()
    # if this div exists, the summoner is not currently in a live game
    if soup.find("div", {"class": "SpectatorError"}) is not None:
        return None

    # the summoner is in fact in a live game > scrape data!
    data = {}
    # GAME MODE (e.g. HA, SR etc.)
    data["game_mode"] = soup.find("small", {"class": "MapName"}).contents[0]

    # find both table bodies (1 for each team)
    table_bodies = soup.findAll("tbody", {"class": "Body"})
    summoner_table_row = get_table_row_of_summoner_from_table(table_bodies, league_name)

    # SUMMONER SPELLS
    spell_container = summoner_table_row.find("td", {"class": "SummonerSpell Cell"})
    # one cell per summoner
    spell_cells = spell_container.findAll("div", {"class": "Spell"})
    data["spells"] = [cell["title"] for cell in spell_cells]

    # CHAMP
    champ_cell = summoner_table_row.find("td", {"class": "ChampionImage Cell"})
    # lower case and remove non alpha-chars
    data["champion"] = league_utils._convert_champ_name(champ_cell.find("a")["title"])

    logger.info(f"\tFound data: {data}!")
    return data


def get_live_game_data_played(league_name: str, server_name: str) -> Optional[Dict[str, str]]:
    """
    Finds the currently played champion IF a given summoner is ingame;
    returns None, if he's not ingame

    Args:
        league_name (str): name of summoner to search for
        server_name (str): (valid) server to look for

    Returns:
        Optional[Dict[str, str]]: game data (map, summoners, champ), if summoner is ingame; None, if not ingame
    """
    # get top-level logger
    logger = _get_internal_logger()

    # construct url for the live game
    url = construct_url_by_name_and_server(
        league_name=league_name, server_name=server_name, mode="spectator"
    )
    logger.info(f"Retrieving live game for {league_name}...")

    # send the HTTP request
    r = requests.get(url=url, headers=_HTTP_STANDARD_HEADERS)
    try:
        r.raise_for_status()
    except HTTPError as e:
        logger.error(f"Encountered error getting live game for {league_name}: {e}")

    # scrape champ played for given league_name
    soup = BeautifulSoup(r.content, features="html.parser")
    return _extract_data_from_live_game_soup(soup, league_name)
