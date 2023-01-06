from templated_mail.mail import BaseEmailMessage


class RegistrationEmail(BaseEmailMessage):
    endpoint = 'registration_email'
    template_name = 'email/registration_email.html'


class LoginEmail(BaseEmailMessage):
    endpoint = 'login_email'
    template_name = 'email/login_email.html'


class WelcomeEmail(BaseEmailMessage):
    endpoint = 'welcome'
    template_name = "email/welcome.html"


class ResetPasswordEmail(BaseEmailMessage):
    endpoint = 'reset_password'
    template_name = 'email/password_reset.html'


class TokenVerificationEmail(BaseEmailMessage):
    template_name = 'email/token_verification.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['code'] = context.get('code')
        return context
