from openai import OpenAI


def rate_listing(text: str, api_key: str) -> str:
    """Use ChatGPT to rate a listing."""
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": text}],
    )
    return response.choices[0].message.content.strip()


def extract_location(text: str, api_key: str) -> str:
    """Use ChatGPT to guess the location from a description."""
    client = OpenAI(api_key=api_key)
    prompt = (
        "Extract the most precise address or district mentioned in the listing "
        "description. Respond with a short phrase or leave empty if unknown.\n\n"
        f"{text}"
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
