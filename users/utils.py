from io import BytesIO

import qrcode
from django.core.files.base import ContentFile


class UserCache(object):
    def __init__(self, username, email, name):
        self.username = username
        self.email = email
        self.name = name


def generate_qrcode(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=5,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    pil_img = qr.make_image(fill_color="white", back_color="#110D21")

    formatter = BytesIO()
    pil_img.save(formatter, format='PNG', quality=100)
    image = ContentFile(formatter.getvalue(), name=f'{data}.png')

    return image
