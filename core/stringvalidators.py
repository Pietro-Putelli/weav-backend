import phonenumbers
import email_validator


def get_username_type(username):
    try:
        phonenumbers.parse(str(username), None)
        return 'phone'
    except phonenumbers.NumberParseException:
        pass

    try:
        email_validator.validate_email(str(username))
        return 'email'
    except email_validator.EmailNotValidError:
        pass

    return None
