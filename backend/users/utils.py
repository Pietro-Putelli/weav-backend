from django.conf import settings
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from services.apple_token import get_sign_in_with_apple_secret
import requests
import jwt


def verify_login_token(method, token):
    if method == "google":
        return verify_google_token(token)

    return verify_apple_token(token)


def verify_apple_token(token):
    client_secret, client_id = get_sign_in_with_apple_secret()

    headers = {"content-type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": token,
        "grant_type": "authorization_code",
        "redirect_uri": "https://example-app.com/redirect",
    }

    response = requests.post(
        "https://appleid.apple.com/auth/token", data=data, headers=headers
    )
    response_dict = response.json()
    id_token = response_dict.get("id_token", None)

    if "error" not in response_dict and id_token is not None:
        decoded_token = jwt.decode(id_token, options={"verify_signature": False})

        email = decoded_token.get("email", None)

        return email

    return None


def verify_google_token(token):
    try:
        user_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=60,
        )

        email = user_info.get("email", None)

        return email

    except ValueError as error:
        print(error)
        return None
