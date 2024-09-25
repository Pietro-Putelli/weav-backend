from PIL import Image

PROFILE_IMAGE_SIZE = (400, 400)


def resize_image_profile(image_path):
    image = Image.open(image_path)
    image = image.resize(PROFILE_IMAGE_SIZE)
    return image
