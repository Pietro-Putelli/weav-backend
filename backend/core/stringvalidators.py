import phonenumber_field
import email_validator


def get_username_type(username):
    try:
        phonenumber_field.parse(str(username), None)
        return 'phone'
    except phonenumber_field.NumberParseException:
        pass

    try:
        email_validator.validate_email(str(username))
        return 'email'
    except email_validator.EmailNotValidError:
        pass

    return None
