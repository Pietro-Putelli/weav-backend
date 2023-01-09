from templated_mail.mail import BaseEmailMessage


class RegistrationEmail(BaseEmailMessage):
    endpoint = 'registration'
    template_name = 'email/registration.html'


class LoginEmail(BaseEmailMessage):
    endpoint = 'login'
    template_name = 'email/login.html'


class WelcomeEmail(BaseEmailMessage):
    endpoint = 'welcome'
    template_name = "email/welcome.html"
