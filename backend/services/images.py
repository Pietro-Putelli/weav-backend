import base64
import boto3
import shortuuid
from PIL import Image
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
import re
import io
import PIL.Image as Image

# Necessary because of a bug that add white line to image borders


def crop_image_white_line(image):
    image = Image.open(image)
    cropped_image = image.crop((10, 10, image.width - 10, image.height - 10))
    formatter = BytesIO()
    cropped_image.save(formatter, format="PNG", quality=100)

    name = shortuuid.uuid() + ".png"
    return ContentFile(formatter.getvalue(), name)


def encode_base_64(image):
    image_file = image.read()
    encoded_image = base64.b64encode(image_file).decode("utf-8")

    return f"data:image/png;base64,{encoded_image}"


def create_boto_client():
    return boto3.client(
        "rekognition",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


# AWS Rekognition API
# https://docs.aws.amazon.com/rekognition/latest/dg/moderation.html
# Explicit Nudity, Violence, Visually Disturbing, Hate Symbols


def format_moderation_response(response):
    prohibited_labels = [
        "Explicit Nudity",
        "Violence",
        "Visually Disturbing",
        "Hate Symbols",
    ]

    moderation_labels = response["ModerationLabels"]

    for label in moderation_labels:
        if label["Name"] in prohibited_labels:
            return False
    return True


def moderate_image(url):
    match = re.search(r"(/users.*)", url)
    filename = match.group(1)[1:]

    client = create_boto_client()

    response = client.detect_moderation_labels(
        Image={"S3Object": {"Bucket": "weav-app", "Name": filename}},
        MinConfidence=70,
    )

    return format_moderation_response(response)


def moderate_image_bytes(image):
    image_obj = Image.open(image)

    img_byte_arr = io.BytesIO()
    image_obj.save(img_byte_arr, format="PNG")
    img_byte_arr = img_byte_arr.getvalue()

    client = create_boto_client()

    response = client.detect_moderation_labels(
        Image={"Bytes": img_byte_arr},
        MinConfidence=70,
    )

    return format_moderation_response(response)
