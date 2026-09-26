"""
Optional AI touch: reads a file's text and suggests which syllabus module
it most likely belongs to. The facilitator always confirms/overrides this
before it's saved -- it's a convenience, not an authority.
Requires: pip install requests python-dotenv
Set GEMINI_API_KEY in a .env file (free tier: https://ai.google.dev/)
"""

import os
import requests

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


class TagSuggestionError(Exception):
    pass


def suggest_module(file_text_excerpt, module_list):
    """
    file_text_excerpt: a short chunk of the uploaded file's text (first ~1000 chars)
    module_list: a ModuleList instance -- used to give the AI valid options only
    Returns the suggested module code (str), or None if suggestion fails
    (the caller should fall back to asking the facilitator to pick manually).
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None  # no key configured -- skip the AI step entirely, not fatal

    valid_codes = [m.code for m in module_list.all()]
    if not valid_codes:
        return None

    prompt = (
        "Given this excerpt from a training document, pick the single best "
        f"matching module code from this list ONLY: {valid_codes}. "
        "Reply with just the code, nothing else.\n\n"
        f"Excerpt:\n{file_text_excerpt[:1000]}"
    )

    try:
        response = requests.post(
            f"{GEMINI_URL}?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        # only accept it if it's actually a valid code -- otherwise ignore
        return text if text in valid_codes else None
    except (requests.RequestException, KeyError, IndexError):
        # network error or unexpected response shape -- fail quietly,
        # facilitator just picks the module manually instead
        return None
