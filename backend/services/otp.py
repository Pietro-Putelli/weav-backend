import requests
import shortuuid
from django.conf import settings
from twilio.rest import Client
from .telegram import send_telegram


def get_otp_code():
    s = shortuuid.ShortUUID(alphabet="0123456789")
    return s.random(length=6)


client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


def send_telegram_otp(phone, otp_code):
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    message = f"{phone} - {otp_code}"

    send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(send_message_url)


def send_otp_to(phone, otp_code):
    if settings.DEBUG or settings.TWILIO_DISABLED:
        message = f"{phone} - {otp_code}"
        send_telegram(message)

        return "message.sid"

    if not settings.TWILIO_DISABLED:
        try:
            message = client.messages.create(
                from_=settings.TWILIO_PHONE_NUMBER,
                to=phone,
                body=f"Your OTP code is {otp_code}",
            )

            return message.sid

        except Exception as error:
            print("Unable to use Twilio API", error)
            return None
