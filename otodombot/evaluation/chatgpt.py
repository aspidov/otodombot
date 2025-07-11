import logging
from openai import OpenAI
from bs4 import BeautifulSoup


def rate_listing(text: str, api_key: str) -> str:
    logging.debug("Requesting listing summary from ChatGPT")
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Дай очень короткое саммари по объявлению на русском языке для последующего оценочного анализа. Очень коротко!! НЕ более 400 символов, но надо короче!!! Сам текст объявления: " +  text}],
    )
    summary = response.choices[0].message.content.strip()
    logging.debug("Received summary: %s", summary)
    return summary


def extract_address(
    description: str, page_address: str, html: str, api_key: str
) -> str:
    """Use ChatGPT to extract a full address from the listing page."""
    logging.debug("Extracting address via ChatGPT")
    client = OpenAI(api_key=api_key)

    # Parse the HTML and try to get only the main listing content instead of the
    # entire page. This helps the model focus on the actual ad text rather than
    # boilerplate or agency info.
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    block = ""
    candidates = [
        {"data-sentry-element": "MainContent"},
        {"data-cy": "adPageMainContent"},
        {"data-cy": "adPageAdDescription"},
        {"id": "adPageMainContent"},
        {"class": "offer-details"},
    ]
    for attrs in candidates:
        el = soup.find(attrs=attrs)
        if el:
            block = el.get_text(" ", strip=True)
            break
    if not block:
        el = soup.find("article") or soup.find("main") or soup.body
        if el:
            block = el.get_text(" ", strip=True)

    trimmed_block = block[:10000]

    prompt = (
        "Given the raw address snippet, the listing description and the main "
        "content block from the page, locate the address of the flat itself "
        "(not the agency). Respond only with the address or leave empty if "
        "unsure.\n\n"
        f"Description:\n{description}\n\nListing content:\n{trimmed_block}"
    )
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    address = response.choices[0].message.content.strip()
    logging.debug("Extracted address: %s", address)
    return address
