import openai


def rate_listing(text: str, api_key: str) -> str:
    """Use ChatGPT to rate a listing."""
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": text}],
    )
    return response.choices[0].message["content"].strip()
