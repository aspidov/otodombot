import googlemaps
from datetime import datetime
from typing import List, Dict, Tuple, Optional


def geocode_address(address: str, api_key: str) -> Optional[Tuple[float, float]]:
    """Return (lat, lng) for a given address using Google Maps Geocoding API."""
    client = googlemaps.Client(key=api_key)
    try:
        results = client.geocode(address)
    except Exception:
        return None
    if not results:
        return None
    location = results[0].get("geometry", {}).get("location")
    if not location:
        return None
    return location.get("lat"), location.get("lng")


def transit_duration(origin: Tuple[float, float], destination: str, departure: datetime, api_key: str) -> Optional[int]:
    """Return transit duration in minutes between origin and destination."""
    client = googlemaps.Client(key=api_key)
    try:
        routes = client.directions(
            origin=origin,
            destination=destination,
            mode="transit",
            departure_time=departure,
        )
    except Exception:
        return None
    if not routes:
        return None
    leg = routes[0].get("legs", [{}])[0]
    duration = leg.get("duration")
    if not duration:
        return None
    seconds = duration.get("value")
    return int(seconds // 60) if seconds is not None else None


def evaluate_location(address: str, pois: List[str], departure: datetime, api_key: str) -> Dict[str, Optional[int]]:
    """Return coordinates and transit times to points of interest."""
    coords = geocode_address(address, api_key)
    if not coords:
        return {"lat": None, "lng": None}
    lat, lng = coords
    results: Dict[str, Optional[int]] = {"lat": lat, "lng": lng}
    for poi in pois:
        minutes = transit_duration((lat, lng), poi, departure, api_key)
        results[poi] = minutes
    return results
