import googlemaps


def evaluate_location(address: str, api_key: str) -> dict:
    """Evaluate location using Google Maps API."""
    gmaps = googlemaps.Client(key=api_key)
    geocode = gmaps.geocode(address)
    if not geocode:
        return {}
    location = geocode[0]["geometry"]["location"]
    return location
