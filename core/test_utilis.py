from django.core.files.uploadedfile import SimpleUploadedFile


def get_mocked_file(name, type=None):
    file_type = "image/png"

    return SimpleUploadedFile(name=name, content=b'', content_type=file_type)
