from dataclasses import dataclass
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


def load_config(path: str | Path = "config.json") -> SearchConditions:
    path = Path(path)
    if not path.exists():
        return SearchConditions()
    with path.open() as f:
        data = json.load(f)
    search = data.get("search", {})
    market = search.get("market", Market.SECONDARY.value)
    return SearchConditions(
        max_price=search.get("max_price"),
        rooms=search.get("rooms"),
        market=Market(market),
        min_area=search.get("min_area"),
    )
