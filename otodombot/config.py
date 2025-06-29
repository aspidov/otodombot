from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List
import json


DEFAULT_BASE_URL = "https://www.otodom.pl/pl/oferty/sprzedaz/mieszkanie,rynek-wtorny/warszawa"

@dataclass
class SearchConditions:
    max_price: Optional[int] = None
    rooms: Optional[List[int]] = None
    min_area: Optional[int] = None
    sorts: List[str] = field(default_factory=lambda: ["DEFAULT"])
    build_year_min: Optional[int] = None


@dataclass
class CommuteSettings:
    pois: List[str] = field(default_factory=list)
    day: str = "Tuesday"
    time: str = "09:00"
    thresholds: dict[str, int] = field(default_factory=dict)


@dataclass
class Config:
    search: SearchConditions = field(default_factory=SearchConditions)
    headless: bool = True
    base_url: str = DEFAULT_BASE_URL
    commute: CommuteSettings = field(default_factory=CommuteSettings)
    reparse_after_days: int = 7
    max_pages: int = 5


def load_config(path: str | Path = "config.json") -> Config:
    path = Path(path)
    if not path.exists():
        return Config()
    with path.open() as f:
        data = json.load(f)
    search = data.get("search", {})
    headless = data.get("headless", True)
    base_url = data.get("base_url", DEFAULT_BASE_URL)
    reparse_after_days = int(data.get("reparse_after_days", 7))
    max_pages = int(data.get("max_pages", 5))
    commute_data = data.get("commute", {})

    rooms_value = search.get("rooms")
    rooms: Optional[List[int]]
    if isinstance(rooms_value, list):
        rooms = [int(r) for r in rooms_value if isinstance(r, int) or (isinstance(r, str) and r.isdigit())]
        if not rooms:
            rooms = None
    elif rooms_value is not None:
        try:
            rooms = [int(rooms_value)]
        except (TypeError, ValueError):
            rooms = None
    else:
        rooms = None

    commute = CommuteSettings(
        pois=commute_data.get("pois", []),
        day=commute_data.get("day", "Tuesday"),
        time=commute_data.get("time", "09:00"),
        thresholds={k: int(v) for k, v in commute_data.get("thresholds", {}).items() if isinstance(v, (int, str)) and str(v).isdigit()},
    )

    sorts_value = search.get("sorts", ["DEFAULT"])
    if isinstance(sorts_value, list):
        sorts = [str(s).upper() for s in sorts_value if isinstance(s, (str, int))]
        if not sorts:
            sorts = ["DEFAULT"]
    elif sorts_value is not None:
        sorts = [str(sorts_value).upper()]
    else:
        sorts = ["DEFAULT"]

    return Config(
        search=SearchConditions(
            max_price=search.get("max_price"),
            rooms=rooms,
            min_area=search.get("min_area"),
            sorts=sorts,
            build_year_min=search.get("build_year_min"),
        ),
        headless=headless,
        base_url=base_url,
        commute=commute,
        reparse_after_days=reparse_after_days,
        max_pages=max_pages,
    )
