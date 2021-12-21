"""

    serank
    ~~~~~~

    TV series rankings.

"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, Iterable, List, Optional, TypeVar

from contexttimer import Timer
import requests

T = TypeVar("T")


@dataclass(frozen=True)
class EpisodeRating:
    value: float
    votes: int


@dataclass
class Episode:
    index: int  # 1-based
    title: str
    rating: EpisodeRating
    airing_date: datetime
    description: str

    @property
    def tag(self) -> str:
        index = str(self.index).zfill(2)
        return f"e{index}"


@dataclass
class Season:
    index: int  # 1-based
    episodes: List[Episode]
    isfinal: bool = field(default=True)

    @property
    def tag(self) -> str:
        index = str(self.index).zfill(2)
        return f"s{index}"

    @property
    def votes(self) -> int:
        """Return a sum of rating votes for all episodes of this season.
        """
        return sum(e.rating.votes for e in self.episodes)

    @property
    def avg_rating(self) -> float:
        """Return average episode rating weighted by its votes count for this season.
        """
        return sum(e.rating.value * e.rating.votes for e in self.episodes) / self.votes

    @property
    def avg_rating_str(self) -> str:
        return f"{self.avg_rating:.2f}"

    @property
    def avg_votes(self) -> int:
        """Return an average votes count per episode for this season.
        """
        return int(sum(e.rating.votes for e in self.episodes) / len(self.episodes))

    @property
    def avg_votes_str(self) -> str:
        return f"{self.avg_votes:,}"


@dataclass
class Series:
    title: str
    seasons: List[Season]

    @property
    def votes(self) -> int:
        """Return a sum of rating votes for all seasons of this series.
        """
        return sum(s.votes for s in self.seasons)

    @property
    def avg_rating(self) -> float:
        """Return average season rating weighted by its votes count for this series.
        """
        return sum(s.avg_rating * s.votes for s in self.seasons) / self.votes

    @property
    def avg_rating_str(self) -> str:
        return f"{self.avg_rating:.2f}"

    @property
    def avg_votes(self) -> int:
        return int(sum(s.avg_votes for s in self.seasons) / len(self.seasons))

    @property
    def avg_votes_str(self) -> str:
        return f"{self.avg_votes:,}"


def markup(url: str, headers=None) -> str:
    """Retrieve markup from ``url``.
    """
    with Timer() as t:
        if headers:
            result = requests.get(url, headers=headers).text
        else:
            result = requests.get(url).text

    print(f"Retrieved markup from: {url} in {t.elapsed:.2f} seconds.")
    return result


def from_iterable(iterable: Iterable[T], predicate: Callable[[T], bool]) -> Optional[T]:
    """Return item from ``iterable`` based on ``predicate`` or ``None``.
    """
    return next((item for item in iterable if predicate(item)), None)

