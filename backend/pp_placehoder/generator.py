from io import BytesIO

from django.core.files.base import ContentFile

from .placeholder import PlaceholderPic


def _get_name_initials(name):
    words = name.split(" ")
    initials = ""

    try:
        initials += words[0][0]
    except IndexError:
        return initials.upper()

    try:
        initials += words[1][0]
    except IndexError:
        pass

    return initials.upper()


def generate_profile_placeholder(name):
    initials = _get_name_initials(name)
    image = PlaceholderPic(initials).image

    formatter = BytesIO()
    image.save(formatter, format='PNG', quality=100)
    return ContentFile(formatter.getvalue(), 'profile.picture.png')
