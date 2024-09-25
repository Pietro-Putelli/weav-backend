from django.core.files.storage import FileSystemStorage


class RemoteStorage(FileSystemStorage):
    def _save(self, name, content):
        return super()._save(name, content)

    def get_available_name(self, name):
        return name
