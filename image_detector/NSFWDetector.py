import requests
import json
from django.conf import settings


def is_moderated_source_valid(source):
    absolute_url = f"http://{settings.DOMAIN}:8080" + source.url
    response = requests.get(f"http://127.0.0.1:5000/?url={absolute_url}")

    response = json.loads(response.text)
    string_score = response.get("score")
    score = round(string_score, 2)

    return score < 0.6
