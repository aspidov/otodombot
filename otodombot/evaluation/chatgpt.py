import openai


def rate_listing(text: str, api_key: str) -> str:
    """Use ChatGPT to rate a listing."""
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": text}],
    )
    return response.choices[0].message["content"].strip()


def extract_location(text: str, api_key: str) -> str:
    """Use ChatGPT to guess the location from a description."""
    openai.api_key = api_key
    prompt = (
        "Extract the most precise address or district mentioned in the listing "
        "description. Respond with a short phrase or leave empty if unknown.\n\n"
        f"{text}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message["content"].strip()
