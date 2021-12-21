"""

    serank.imdb
    ~~~~~~~~~~~

    Parse IMDb.

"""
from itertools import count
from typing import List, Optional, Tuple
from datetime import datetime

from bs4 import BeautifulSoup
from bs4 import ResultSet, Tag

from serank import EpisodeRating, Episode, Season, Series, markup


class EpisodeListPage:
    """Parse IMDb Episode List page for data of all episodes in a given season.
    """
    URL_TEMPLATE = "https://www.imdb.com/title/{}/episodes?season={}"

    def __init__(self, titleid: str, season_index: int) -> None:
        self._url = self.URL_TEMPLATE.format(titleid, season_index)
        self._markup = markup(self._url)
        self._soup = BeautifulSoup(self._markup, "lxml")
        self._infos: ResultSet = self._soup.find_all("div", class_="info", itemprop="episodes")
        self._episodes = [self._parse_info(i, info) for i, info in enumerate(self._infos, start=1)]
        self._isfinal = self._soup.find("a", id="load_next_episodes") is None
        self._season = Season(season_index, self._episodes, self._isfinal)

    def _parse_info(self, index: int, info: Tag) -> Episode:
        title = info.find("a", itemprop="name").text
        desc = info.find("div", class_="item_description").text.strip()
        airdate = info.find("div", class_="airdate").text.strip().replace(".", "")
        airdate = datetime.strptime(airdate, "%d %b %Y")
        rating_widget = info.find("div", class_="ipl-rating-widget")
        rating = self._parse_rating_widget(rating_widget)
        return Episode(index, title, rating, airdate, desc)

    @staticmethod
    def _parse_rating_widget(rating_widget: Tag) -> EpisodeRating:
        rating = float(rating_widget.find("span", class_="ipl-rating-star__rating").text)
        votes = rating_widget.find("span", class_="ipl-rating-star__total-votes").text[1:-1]
        votes = int(votes.replace(",", ""))
        return EpisodeRating(rating, votes)

    @property
    def season(self) -> Season:
        return self._season


class SearchPageTitleList:
    """Parse IMDb Search Page's title list for IMDb Title ID.
    """
    URL_TEMPLATE = "https://www.imdb.com/find?q={}"

    def __init__(self, query: str) -> None:
        self._query = query
        self._url = self.URL_TEMPLATE.format("+".join(query.split()))
        headers = {"accept-language": "en"}
        self._markup = markup(self._url, headers=headers)
        self._soup = BeautifulSoup(self._markup, "lxml")
        self._table = self._soup.find("table", class_="findList")
        self._title, self._titleid = self._parse_table(self._table)

    @staticmethod
    def _parse_table(table: Tag) -> Tuple[Optional[str], Optional[str]]:
        rows = table.find_all("tr")
        title, titleid = None, None
        for row in rows:
            td = row.find("td", class_="result_text")
            if "(TV Series)" in td.text:
                a = td.find("a")
                title = a.text
                href = a.attrs["href"]
                titleid = href[7:-1]
                break

        return title, titleid

    @property
    def title(self) -> Optional[str]:
        return self._title

    @property
    def titleid(self) -> Optional[str]:
        return self._titleid


class Parser:
    """Parse IMDb for tv series data.
    """
    def __init__(self, title_query="") -> None:
        self._title, self._id = None, None
        self.data = []
        if title_query:
            self.parse(title_query)

    def parse(self, title_query) -> None:
        print(f"Querying IMDb with {title_query!r}...")
        pagelist = SearchPageTitleList(title_query)
        if not pagelist.title:
            raise ValueError(f"No results for: {title_query!r}.")
        self._title, self._id = pagelist.title, pagelist.titleid
        print(f"Found title={self._title!r} and ID={self._id}.")
        print("Retrieving seasons data...")
        seasons = self._seasons()
        if seasons:
            print(f"Data for {self._title!r} retrieved succeffully.")
            self.data.append(Series(self._title, seasons))

    def _seasons(self) -> List[Season]:
        counter = count(start=1)
        result = []
        while True:
            index = next(counter)
            season = EpisodeListPage(self._id, index).season
            result.append(season)
            print(f"Retrieved data for season #{index}.")
            if season.isfinal:
                print("Reached final season.")
                break

        return result
