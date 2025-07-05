import logging
import googlemaps
from datetime import datetime
from typing import List, Dict, Tuple, Optional


def _summarize_transit_steps(steps: List[dict]) -> Dict[str, Optional[int | List[str]]]:
    """Return summary info for a leg's steps."""
    walk_sec = 0
    types: List[str] = []
    for step in steps:
        mode = step.get("travel_mode")
        dur = step.get("duration", {}).get("value") or 0
        if mode == "WALKING":
            walk_sec += dur
        elif mode == "TRANSIT":
            det = step.get("transit_details", {})
            line = det.get("line", {})
            vehicle = line.get("vehicle", {})
            vtype = vehicle.get("type")
            short = line.get("short_name") or line.get("name")
            part = vtype or "TRANSIT"
            if short:
                part = f"{part} {short}"
            types.append(part)
    return {
        "walk": int(walk_sec // 60),
        "transport": types,
        "transfers": max(len(types) - 1, 0),
    }


def geocode_address(address: str, api_key: str) -> Optional[Tuple[float, float]]:
    """Return (lat, lng) for a given address using Google Maps Geocoding API."""
    logging.debug("Geocoding address %s", address)
    client = googlemaps.Client(key=api_key)
    try:
        results = client.geocode(address)
    except Exception as exc:  # pragma: no cover - network errors
        logging.error("Geocoding failed for %s: %s", address, exc, exc_info=True)
        return None
    if not results:
        return None
    location = results[0].get("geometry", {}).get("location")
    if not location:
        return None
    lat_lng = location.get("lat"), location.get("lng")
    logging.debug("Geocoded %s -> %s", address, lat_lng)
    return lat_lng


def transit_routes(
    origin: Tuple[float, float],
    destination: str,
    departure: datetime,
    api_key: str,
) -> List[dict]:
    """Return up to two best transit routes with summary info."""
    logging.debug("Requesting transit routes from %s to %s", origin, destination)
    client = googlemaps.Client(key=api_key)
    try:
        routes = client.directions(
            origin=origin,
            destination=destination,
            mode="transit",
            departure_time=departure,
        )
    except Exception as exc:  # pragma: no cover - network errors
        logging.error(
            "Failed to get directions from %s to %s: %s", origin, destination, exc, exc_info=True
        )
        return []
    if not routes:
        logging.warning("No routes found from %s to %s", origin, destination)
        return []
    result: List[dict] = []
    for route in routes[:2]:
        leg = route.get("legs", [{}])[0]
        dur_sec = leg.get("duration", {}).get("value")
        steps = leg.get("steps", [])
        summary = _summarize_transit_steps(steps)
        summary["minutes"] = int(dur_sec // 60) if dur_sec is not None else None
        result.append(summary)
    return result


def evaluate_location(address: str, pois: List[str], departure: datetime, api_key: str) -> Dict[str, Optional[int]]:
    """Return coordinates and transit times to points of interest."""
    logging.info("Evaluating location for %s", address)
    coords = geocode_address(address, api_key)
    if not coords:
        logging.warning("Could not geocode address %s", address)
        return {"lat": None, "lng": None}
    lat, lng = coords
    results: Dict[str, Optional[int]] = {"lat": lat, "lng": lng}
    for poi in pois:
        routes = transit_routes((lat, lng), poi, departure, api_key)
        minutes = routes[0]["minutes"] if routes else None
        results[poi] = minutes
        results[f"{poi}_routes"] = routes
    logging.debug("Evaluation results for %s: %s", address, results)
    return results
