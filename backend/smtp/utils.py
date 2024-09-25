from django.conf import settings


# Build token url for templates
def build_token_url(token):
    return f"{settings.DOMAIN}?token={token.value}"


# Build token qrcode url for templates
def build_token_qr_url(token):
    return f"{settings.DOMAIN}/media/qr_codes/{token.value[0:22]}.png"
