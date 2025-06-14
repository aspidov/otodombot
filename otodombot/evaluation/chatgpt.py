from openai import OpenAI


def rate_listing(text: str, api_key: str) -> str:
    """Use ChatGPT to rate a listing based on a short summary."""
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


def extract_address(
    description: str, page_address: str, html: str, api_key: str
) -> str:
    """Use ChatGPT to extract a full address from the listing page."""
    client = OpenAI(api_key=api_key)
    trimmed_html = html[:12000]
    prompt = (
        "Given the raw address snippet and the listing description, "
        "find the most precise address of the property. "
        "Respond with only the address or leave empty if unsure.\n\n"
        f"Address snippet: {page_address}\n\nDescription:\n{description}\n\nHTML:\n{trimmed_html}"
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()
