from io import BytesIO

import shortuuid
from PIL import Image
from django.core.files.base import ContentFile


# Necessary because of a bug that add white line to image borders

def crop_image_white_line(image):
    image = Image.open(image)
    cropped_image = image.crop((10, 10, image.width - 10, image.height - 10))
    formatter = BytesIO()
    cropped_image.save(formatter, format='PNG', quality=100)

    name = shortuuid.uuid() + '.png'
    return ContentFile(formatter.getvalue(), name)
