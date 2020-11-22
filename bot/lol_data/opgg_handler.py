from typing import Tuple, Optional

from urllib.parse import quote_plus
from bs4 import BeautifulSoup
import logging
import requests
from requests.exceptions import HTTPError

_HTTP_STANDARD_HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36",
    "accept-encoding": "gzip, deflate, br",
    "accept": "application/json, text/javascript, */*; q=0.01",
}

_OPGG_TEMPLATES = {
    # (default) match history
    "history": "https://{}.op.gg/summoner/userName={}",
    # live game
    "live_game": "https://{}.op.gg/summoner/spectator/userName={}&",
    # overview of champions played in past seasons (& normal games)
    "champions": "https://{}.op.gg/summoner/champions/userName={}&",
    # rank overview in league
    "league": "https://{}.op.gg/summoner/league/userName={}&",
}

_VALID_LEAGUE_SERVERS = [
    "euw",
    "eune",
    "lan",
    "las",
    "oce",
    "kr",
    "ru",
    "jp",
    "br",
    "tr",
    "na",
]


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
        AttributeError:
            1. when league_name is empty
            2. when server_name is invalid
            3. mode is invalid

    Returns:
        str: a valid ready-to-query op.gg page.
    """
    if not mode in _OPGG_TEMPLATES:
        raise AttributeError(f"mode needs to be one of {_OPGG_TEMPLATES.keys()}!")
    if not server_name in _VALID_LEAGUE_SERVERS:
        raise AttributeError(f"server needs to be one of {_VALID_LEAGUE_SERVERS}!")
    if not league_name:
        raise AttributeError("league ingame name can't be empty!")

    return _OPGG_TEMPLATES[mode].format(
        server_name,
        quote_plus(league_name, encoding="UTF-8"),
    )


def _does_url_belong_to_valid_account(url: str) -> bool:
    """
    Verifies that an account associated with a constructed URL exists.

    Args:
        url (str): URL to request.

    Returns:
        bool: True, if the request yielded a valid op.gg; False, if not.
    """
    # get the default logger of the bot
    logger = logging.getLogger("lol_watchbot")
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
    url = construct_url_by_name_and_server(
        league_name=league_name, server_name=server_name
    )
    return _does_url_belong_to_valid_account(url=url)


def get_live_game_champ_played(league_name: str, server_name: str) -> Optional[str]:
    """
    Finds the currently played champion IF a given summoner is ingame;
    returns None, if he's not ingame

    Args:
        league_name (str): name of summoner to search for
        server_name (str): (valid) server to look for

    Returns:
        Optional[str]: the champion's name, if summoner is ingame; None, if not ingame
    """
    # get top-level logger
    logger = logging.getLogger("lol_watchbot")

    # construct url for the live game
    url = construct_url_by_name_and_server(
        league_name=league_name, server_name=server_name, mode="live_game"
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
    # if this div exists, the summoner is not currently in a live game
    if soup.find("div", {"class": "SpectatorError"}) is not None:
        return None

    # the summoner is in fact in a live game > scrape his champ!

    # find both table bodies (1 for each team)
    table_bodies = soup.findAll("tbody", {"class": "Body"})

    # for each table body (1 for each team)
    for table_body in table_bodies:
        # for each row within that body (5 per body)
        for table_row in table_body.findAll("tr"):
            # check whether it's our summoner
            summoner_cell = table_row.find("td", {"class": "SummonerName Cell"})
            summoner_name = summoner_cell.find("a").contents[0]
            if summoner_name.lower() == league_name.lower():
                # found the summoner! > extract champion
                champ_cell = table_row.find("td", {"class": "ChampionImage Cell"})
                champ_name = champ_cell.find("a")["title"]
                logger.info(f"\tFound champion: {champ_name}!")
                return champ_name


if __name__ == "__main__":
    # test url construction
    url = construct_url_by_name_and_server(league_name="ζξζ ι ζξζ", server_name="euw")
    print(url)

    # test summoner verification
    is_summoner_valid = verify_summoner_on_server(
        league_name="ζξζ ι ζξζ", server_name="euw"
    )
    print(is_summoner_valid)

    # test getting active game of inactive account
    champ_played = get_live_game_champ_played(
        league_name="ζξζ ι ζξζ", server_name="euw"
    )
    print(champ_played)