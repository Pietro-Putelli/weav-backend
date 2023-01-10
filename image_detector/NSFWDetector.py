import json
import requests
from django.conf import settings


def is_moderated_source_valid(source):
    absolute_url = f"http://app:8000" + source.url
    response = requests.get(f"http://nsfw:5000/?url={absolute_url}")

    response = json.loads(response.text)

    string_score = float(response.get("score"))
    score = round(string_score, 2)

    return score < 0.6
