from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional
import json


class Market(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"


@dataclass
class SearchConditions:
    max_price: Optional[int] = None
    rooms: Optional[int] = None
    market: Market = Market.SECONDARY
    min_area: Optional[int] = None


@dataclass
class Config:
    search: SearchConditions = field(default_factory=SearchConditions)
    headless: bool = True


def load_config(path: str | Path = "config.json") -> Config:
    path = Path(path)
    if not path.exists():
        return Config()
    with path.open() as f:
        data = json.load(f)
    search = data.get("search", {})
    market = search.get("market", Market.SECONDARY.value)
    headless = data.get("headless", True)
    return Config(
        search=SearchConditions(
            max_price=search.get("max_price"),
            rooms=search.get("rooms"),
            market=Market(market),
            min_area=search.get("min_area"),
        ),
        headless=headless,
    )
