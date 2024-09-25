import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from django.conf import settings
from django.template.loader import render_to_string

from languages.language import get_language_content
from .utils import build_token_url, build_token_qr_url

EMAIL_HOST = settings.EMAIL_HOST
EMAIL_PORT = settings.EMAIL_PORT
EMAIL_HOST_USER = settings.EMAIL_HOST_USER
EMAIL_HOST_PASSWORD = settings.EMAIL_HOST_PASSWORD


# Define Email Base Class


class BaseEmail:
    def __init__(self, subject, template, context):
        self.server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        self.server.starttls()
        self.server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

        self.subject = subject
        self.template = template
        self.context = context

    def send(self, to_email):
        message = MIMEMultipart()
        message["From"] = formataddr(("Weav", "weav.it"))
        message["Subject"] = self.subject

        template_path = f"email/{self.template}"

        html_text = render_to_string(template_path, self.context)
        html = MIMEText(html_text, "html")
        message.attach(html)

        self.server.sendmail(EMAIL_HOST_USER, to_email, message.as_string())

        self.server.quit()


# Define Email Token Base Class


class TokenBaseEmail(BaseEmail):
    def __init__(self, subject, template, context):
        token = context["token"]

        context["token_url"] = build_token_url(token)
        context["qr_url"] = build_token_qr_url(token)

        super().__init__(subject, template, context)


# All Email Classes

# Context values:
# username


class WelcomeEmail(BaseEmail):
    def __init__(self, context):
        template = "welcome.html"

        user_id = context["user_id"]
        language, _ = get_language_content(user_id)

        context["language"] = language

        subject = f"👋 {language['welcome_to']} Weav"

        username = context.get("username")

        if username:
            context["preview"] = f"Hey {username} {language['thank_you_for_joining']}"

        super().__init__(subject, template, context)


# Context values:
# username
# token


class LoginEmail(TokenBaseEmail):
    def __init__(self, context):
        template = "login.html"
        subject = "🔓 Sleek Login"

        user = context.get("user")
        username = user.username
        language, _ = get_language_content(user)

        context["language"] = language

        if username:
            context["preview"] = f"Hey {username} {language['welcome_back']}"

        super().__init__(subject, template, context)


# Context values:
# username
# token


class RegistrationEmail(TokenBaseEmail):
    def __init__(self, context):
        template = "registration.html"

        user = context.get("user")
        username = user.username
        language, _ = get_language_content(user)

        context["language"] = language

        subject = f"🍸 {language['complete_registration']}"

        if username:
            context["preview"] = f"Hey {username} {language['welcome_to']} Weav"

        super().__init__(subject, template, context)
